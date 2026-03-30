#!/usr/bin/env python3
"""
Content Decay Detector — Detect pages where traffic is declining vs their
historical peak. Combines decay detection, anomaly detection (rolling average),
and Google algorithm update correlation.

Classification: gradual decay, sudden drop, seasonal, recovering.
"""

import sys
import json
import csv
import re
import argparse
import math
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

GSC_COLUMN_MAP = {
    "page": ["page", "top pages", "url", "landing page", "address"],
    "date": ["date", "month", "period"],
    "clicks": ["clicks"],
    "impressions": ["impressions"],
    "ctr": ["ctr", "click through rate"],
    "position": ["position", "avg. position", "average position"],
}


# ---------------------------------------------------------------------------
# Known Google Algorithm Updates
# ---------------------------------------------------------------------------

ALGORITHM_UPDATES = [
    {"name": "March 2024 Core Update", "date": "2024-03-05", "type": "core"},
    {"name": "June 2024 Spam Update", "date": "2024-06-20", "type": "spam"},
    {"name": "August 2024 Core Update", "date": "2024-08-15", "type": "core"},
    {"name": "November 2024 Core Update", "date": "2024-11-11", "type": "core"},
    {"name": "December 2024 Spam Update", "date": "2024-12-19", "type": "spam"},
    {"name": "March 2025 Core Update", "date": "2025-03-13", "type": "core"},
    {"name": "June 2025 Core Update", "date": "2025-06-10", "type": "core"},
    {"name": "September 2025 Core Update", "date": "2025-09-15", "type": "core"},
    {"name": "December 2025 Core Update", "date": "2025-12-01", "type": "core"},
    {"name": "March 2026 Core Update", "date": "2026-03-10", "type": "core"},
]

# Pre-parse update dates
for update in ALGORITHM_UPDATES:
    update["_date"] = datetime.strptime(update["date"], "%Y-%m-%d")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_columns(headers: list[str], column_map: dict) -> dict:
    """Map CSV headers to canonical column names."""
    mapping = {}
    lower_headers = [h.strip().lower().lstrip("\ufeff") for h in headers]
    for canonical, variants in column_map.items():
        for i, header in enumerate(lower_headers):
            if header in variants:
                mapping[canonical] = i
                break
    return mapping


def parse_ctr(value: str) -> float:
    """Parse CTR value — handles both '3.75%' and '0.0375' formats."""
    value = value.strip().replace(",", ".")
    if value.endswith("%"):
        return float(value.rstrip("%")) / 100.0
    val = float(value)
    if val > 1:
        return val / 100.0
    return val


def parse_date(value: str) -> Optional[str]:
    """
    Parse various date formats and return YYYY-MM string.
    Supports: 2025-01, 2025-01-15, 01/15/2025, 15/01/2025, Jan 2025.
    """
    value = value.strip()

    # Already monthly: 2025-01
    if re.match(r"^\d{4}-\d{2}$", value):
        return value

    # ISO daily: 2025-01-15
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value[:7]

    # US format: 01/15/2025
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", value)
    if m:
        month, day, year = m.groups()
        # If month > 12, assume EU format (day/month/year)
        if int(month) > 12:
            month, day = day, month
        return f"{year}-{int(month):02d}"

    # Text month: Jan 2025, January 2025
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", value)
    if m:
        month_str, year = m.groups()
        try:
            dt = datetime.strptime(f"{month_str} {year}", "%b %Y")
            return dt.strftime("%Y-%m")
        except ValueError:
            try:
                dt = datetime.strptime(f"{month_str} {year}", "%B %Y")
                return dt.strftime("%Y-%m")
            except ValueError:
                pass

    return None


def month_to_date(month_str: str) -> datetime:
    """Convert YYYY-MM to datetime (first of month)."""
    return datetime.strptime(month_str + "-01", "%Y-%m-%d")


# ---------------------------------------------------------------------------
# GSC parsing
# ---------------------------------------------------------------------------

def parse_gsc_csv(filepath: str) -> list[dict]:
    """Parse GSC Performance export CSV with date dimension."""
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        col_map = normalize_columns(headers, GSC_COLUMN_MAP)

        required = ["page", "date", "clicks"]
        missing = [c for c in required if c not in col_map]
        if missing:
            print(f"ERROR: Missing required columns: {missing}")
            print(f"  Found headers: {headers}")
            print(f"  Ensure CSV has Page + Date + Clicks columns.")
            sys.exit(1)

        for row in reader:
            if not row or len(row) < len(col_map):
                continue
            try:
                date_str = parse_date(row[col_map["date"]])
                if not date_str:
                    continue

                entry = {
                    "page": row[col_map["page"]].strip(),
                    "month": date_str,
                    "clicks": int(float(row[col_map["clicks"]].replace(",", ""))),
                    "impressions": int(float(row[col_map["impressions"]].replace(",", ""))) if "impressions" in col_map else 0,
                    "ctr": parse_ctr(row[col_map["ctr"]]) if "ctr" in col_map else 0.0,
                    "position": float(row[col_map["position"]].replace(",", ".")) if "position" in col_map else 0.0,
                }
                rows.append(entry)
            except (ValueError, IndexError):
                continue
    return rows


# ---------------------------------------------------------------------------
# Monthly aggregation
# ---------------------------------------------------------------------------

def aggregate_monthly(rows: list[dict]) -> dict:
    """
    Aggregate daily/weekly data to monthly per page.
    Returns: {page_url: [{month, clicks, impressions, position}, ...]}
    """
    # Group by page + month
    grouped = defaultdict(lambda: defaultdict(lambda: {
        "clicks": 0, "impressions": 0, "positions": [], "ctr_values": []
    }))

    for row in rows:
        page = row["page"]
        month = row["month"]
        grouped[page][month]["clicks"] += row["clicks"]
        grouped[page][month]["impressions"] += row["impressions"]
        if row["position"] > 0:
            grouped[page][month]["positions"].append(row["position"])
        if row["ctr"] > 0:
            grouped[page][month]["ctr_values"].append(row["ctr"])

    # Build sorted time series per page
    result = {}
    for page, months in grouped.items():
        series = []
        for month, data in sorted(months.items()):
            avg_position = (
                sum(data["positions"]) / len(data["positions"])
                if data["positions"]
                else 0.0
            )
            avg_ctr = (
                sum(data["ctr_values"]) / len(data["ctr_values"])
                if data["ctr_values"]
                else 0.0
            )
            series.append({
                "month": month,
                "clicks": data["clicks"],
                "impressions": data["impressions"],
                "position": round(avg_position, 1),
                "ctr": round(avg_ctr, 4),
            })
        result[page] = series
    return result


# ---------------------------------------------------------------------------
# Peak detection and decay calculation
# ---------------------------------------------------------------------------

def detect_decay(
    series: list[dict],
    decay_threshold: float = 30.0,
    min_peak_clicks: int = 50,
) -> Optional[dict]:
    """
    Detect decay for a single page's time series.
    Returns decay info or None if no significant decay.
    """
    if len(series) < 2:
        return None

    # Find peak month
    peak_entry = max(series, key=lambda x: x["clicks"])
    peak_clicks = peak_entry["clicks"]

    if peak_clicks < min_peak_clicks:
        return None

    # Current = most recent month
    current_entry = series[-1]
    current_clicks = current_entry["clicks"]

    # Decay calculation
    if peak_clicks == 0:
        return None
    decay_pct = ((peak_clicks - current_clicks) / peak_clicks) * 100.0

    if decay_pct < decay_threshold:
        return None

    # Severity
    if decay_pct >= 80:
        severity = "Critical"
    elif decay_pct >= 50:
        severity = "High"
    elif decay_pct >= 30:
        severity = "Medium"
    else:
        severity = "Low"

    traffic_lost = peak_clicks - current_clicks

    return {
        "peak_month": peak_entry["month"],
        "peak_clicks": peak_clicks,
        "peak_impressions": peak_entry["impressions"],
        "peak_position": peak_entry["position"],
        "current_month": current_entry["month"],
        "current_clicks": current_clicks,
        "current_impressions": current_entry["impressions"],
        "current_position": current_entry["position"],
        "decay_percentage": round(decay_pct, 1),
        "severity": severity,
        "traffic_lost": traffic_lost,
    }


# ---------------------------------------------------------------------------
# Anomaly detection (rolling average)
# ---------------------------------------------------------------------------

def detect_anomalies(
    series: list[dict],
    window: int = 3,
    std_threshold: float = 2.0,
) -> list[dict]:
    """
    Detect anomalies using rolling average.
    Returns list of anomaly events.
    """
    if len(series) < window + 1:
        return []

    clicks = [entry["clicks"] for entry in series]

    # Calculate rolling averages
    rolling_avgs = []
    for i in range(len(clicks)):
        if i < window - 1:
            rolling_avgs.append(None)
        else:
            avg = sum(clicks[i - window + 1 : i + 1]) / window
            rolling_avgs.append(avg)

    # Calculate deltas from previous rolling average
    deltas = []
    for i in range(1, len(clicks)):
        if rolling_avgs[i - 1] is not None:
            delta = clicks[i] - rolling_avgs[i - 1]
            deltas.append({"index": i, "delta": delta})

    if not deltas:
        return []

    # Calculate mean and std of deltas
    delta_values = [d["delta"] for d in deltas]
    mean_delta = sum(delta_values) / len(delta_values)
    variance = sum((d - mean_delta) ** 2 for d in delta_values) / len(delta_values)
    std_delta = math.sqrt(variance) if variance > 0 else 1.0

    # Flag anomalies: delta < mean - (std_threshold * std)
    anomaly_threshold = mean_delta - (std_threshold * std_delta)

    anomalies = []
    for d in deltas:
        if d["delta"] < anomaly_threshold:
            idx = d["index"]
            prev_clicks = clicks[idx - 1] if idx > 0 else clicks[idx]
            drop_pct = (
                ((prev_clicks - clicks[idx]) / prev_clicks * 100)
                if prev_clicks > 0
                else 0
            )
            anomalies.append({
                "month": series[idx]["month"],
                "clicks": series[idx]["clicks"],
                "delta": round(d["delta"], 1),
                "drop_percentage": round(drop_pct, 1),
                "rolling_avg_before": round(rolling_avgs[idx - 1], 1) if rolling_avgs[idx - 1] else None,
            })

    return anomalies


# ---------------------------------------------------------------------------
# Algorithm update correlation
# ---------------------------------------------------------------------------

def correlate_with_updates(month_str: str, window_weeks: int = 4) -> Optional[dict]:
    """
    Check if a given month correlates with a known Google algorithm update.
    Returns the matching update or None.
    """
    event_date = month_to_date(month_str)
    # Check if any update falls within window_weeks before the event month end
    event_month_end = month_to_date(month_str) + timedelta(days=31)

    for update in ALGORITHM_UPDATES:
        update_date = update["_date"]
        # Update happened in the same month or the month before
        diff_days = (event_date - update_date).days
        if -31 <= diff_days <= (window_weeks * 7):
            return {
                "name": update["name"],
                "date": update["date"],
                "type": update["type"],
            }
    return None


# ---------------------------------------------------------------------------
# Pattern classification
# ---------------------------------------------------------------------------

def classify_pattern(
    series: list[dict],
    decay_info: dict,
    anomalies: list[dict],
) -> str:
    """
    Classify the decay pattern: gradual, sudden_drop, seasonal, recovering.
    """
    if not series or len(series) < 3:
        return "gradual"

    clicks = [entry["clicks"] for entry in series]

    # Check recovering: last 2 months trending up, but still below peak
    if len(clicks) >= 3:
        if clicks[-1] > clicks[-2] > clicks[-3] and clicks[-1] < decay_info["peak_clicks"]:
            return "recovering"

    # Check sudden drop: any single anomaly with > 40% drop
    for anomaly in anomalies:
        if anomaly["drop_percentage"] > 40:
            return "sudden_drop"

    # Check seasonal: look for similar pattern (simplified heuristic)
    # If there are 12+ months and the decay month is similar to a prior year dip
    if len(clicks) >= 12:
        # Compare current 3-month avg with same period last year
        recent_avg = sum(clicks[-3:]) / 3
        year_ago_avg = sum(clicks[-15:-12]) / 3 if len(clicks) >= 15 else None
        if year_ago_avg and year_ago_avg > 0:
            ratio = recent_avg / year_ago_avg
            if 0.7 <= ratio <= 1.3:
                return "seasonal"

    # Default: gradual decay
    return "gradual"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_content_decay(
    gsc_data: list[dict],
    period_months: int = 12,
    decay_threshold: float = 30.0,
    min_peak_clicks: int = 50,
    rolling_window: int = 3,
    anomaly_std: float = 2.0,
) -> dict:
    """
    Main analysis pipeline.
    Returns structured results as dict.
    """
    # Step 1: Aggregate to monthly
    monthly_data = aggregate_monthly(gsc_data)

    if not monthly_data:
        return {"error": "No data after aggregation."}

    # Determine analysis period
    all_months = set()
    for series in monthly_data.values():
        for entry in series:
            all_months.add(entry["month"])
    all_months_sorted = sorted(all_months)

    if not all_months_sorted:
        return {"error": "No valid date data found."}

    # Filter to period
    cutoff_index = max(0, len(all_months_sorted) - period_months)
    cutoff_month = all_months_sorted[cutoff_index]

    # Step 2-6: Analyze each page
    decaying_pages = []
    growing_pages = []
    total_traffic_lost = 0
    update_impacts = defaultdict(lambda: {"pages": 0, "total_decay": 0.0, "most_impacted": None, "most_impacted_decay": 0})

    for page, series in monthly_data.items():
        # Filter to period
        period_series = [e for e in series if e["month"] >= cutoff_month]
        if len(period_series) < 2:
            continue

        # Peak detection + decay
        decay_info = detect_decay(period_series, decay_threshold, min_peak_clicks)

        if decay_info is None:
            # Check if growing
            if len(period_series) >= 3:
                three_months_ago = period_series[-3]["clicks"] if len(period_series) >= 3 else 0
                current = period_series[-1]["clicks"]
                if three_months_ago > 0 and current > three_months_ago:
                    growth_pct = ((current - three_months_ago) / three_months_ago) * 100
                    if growth_pct > 10:
                        growing_pages.append({
                            "page": page,
                            "three_months_ago_clicks": three_months_ago,
                            "current_clicks": current,
                            "growth_percentage": round(growth_pct, 1),
                        })
            continue

        # Anomaly detection
        anomalies = detect_anomalies(period_series, rolling_window, anomaly_std)

        # Classify pattern
        pattern = classify_pattern(period_series, decay_info, anomalies)

        # Algorithm update correlation
        update_correlation = None
        # Check decay onset month (month after peak) and anomaly months
        months_to_check = [decay_info["peak_month"]]
        for anomaly in anomalies:
            months_to_check.append(anomaly["month"])

        for check_month in months_to_check:
            corr = correlate_with_updates(check_month)
            if corr:
                update_correlation = corr
                # Track update impact
                update_name = corr["name"]
                update_impacts[update_name]["pages"] += 1
                update_impacts[update_name]["total_decay"] += decay_info["decay_percentage"]
                if decay_info["decay_percentage"] > update_impacts[update_name]["most_impacted_decay"]:
                    update_impacts[update_name]["most_impacted"] = page
                    update_impacts[update_name]["most_impacted_decay"] = decay_info["decay_percentage"]
                break

        # Annotate anomalies with update correlation
        for anomaly in anomalies:
            anomaly["update_correlation"] = correlate_with_updates(anomaly["month"])

        total_traffic_lost += decay_info["traffic_lost"]

        decaying_pages.append({
            "page": page,
            "decay": decay_info,
            "pattern": pattern,
            "anomalies": anomalies,
            "update_correlation": update_correlation,
            "time_series": period_series,
        })

    # Sort by traffic lost (descending)
    decaying_pages.sort(key=lambda x: x["decay"]["traffic_lost"], reverse=True)
    growing_pages.sort(key=lambda x: x["growth_percentage"], reverse=True)

    # Summary counts
    critical_count = sum(1 for p in decaying_pages if p["decay"]["severity"] == "Critical")
    high_count = sum(1 for p in decaying_pages if p["decay"]["severity"] == "High")
    medium_count = sum(1 for p in decaying_pages if p["decay"]["severity"] == "Medium")
    total_anomalies = sum(len(p["anomalies"]) for p in decaying_pages)
    update_correlated = sum(1 for p in decaying_pages if p["update_correlation"])

    # Build update impact summary
    update_impact_list = []
    for name, impact in update_impacts.items():
        avg_decay = impact["total_decay"] / impact["pages"] if impact["pages"] > 0 else 0
        update_impact_list.append({
            "update_name": name,
            "pages_affected": impact["pages"],
            "avg_decay_percentage": round(avg_decay, 1),
            "most_impacted_page": impact["most_impacted"],
        })
    update_impact_list.sort(key=lambda x: x["pages_affected"], reverse=True)

    # Monthly traffic trend (all pages combined)
    monthly_totals = defaultdict(int)
    for series in monthly_data.values():
        for entry in series:
            if entry["month"] >= cutoff_month:
                monthly_totals[entry["month"]] += entry["clicks"]

    monthly_trend = []
    sorted_months = sorted(monthly_totals.keys())
    peak_total = max(monthly_totals.values()) if monthly_totals else 0
    prev_total = None
    for month in sorted_months:
        total = monthly_totals[month]
        mom_change = (
            round(((total - prev_total) / prev_total) * 100, 1)
            if prev_total and prev_total > 0
            else None
        )
        vs_peak = round(((total - peak_total) / peak_total) * 100, 1) if peak_total > 0 else 0
        monthly_trend.append({
            "month": month,
            "total_clicks": total,
            "vs_previous_month": mom_change,
            "vs_peak": vs_peak,
        })
        prev_total = total

    return {
        "summary": {
            "total_pages_analyzed": len(monthly_data),
            "pages_with_decay": len(decaying_pages),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "anomalies_detected": total_anomalies,
            "update_correlated_drops": update_correlated,
            "total_traffic_lost": total_traffic_lost,
            "period": f"{cutoff_month} to {all_months_sorted[-1]}",
            "decay_threshold": decay_threshold,
            "min_peak_clicks": min_peak_clicks,
        },
        "decaying_pages": decaying_pages,
        "growing_pages": growing_pages[:20],
        "update_impact": update_impact_list,
        "monthly_trend": monthly_trend,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_period(period_str: str) -> int:
    """Parse period string like '12m', '18m', '6m' to months."""
    m = re.match(r"^(\d+)m?$", period_str.strip().lower())
    if m:
        return int(m.group(1))
    return 12


def main():
    parser = argparse.ArgumentParser(
        description="Content Decay Detector — find pages losing traffic vs their peak"
    )
    parser.add_argument(
        "--gsc", required=True, help="Path to GSC Performance export CSV (with date dimension)"
    )
    parser.add_argument(
        "--period", default="12m",
        help="Analysis period (e.g., 6m, 12m, 18m, 24m; default: 12m)"
    )
    parser.add_argument(
        "--decay-threshold", type=float, default=30.0,
        help="Minimum decay percentage to flag (default: 30)"
    )
    parser.add_argument(
        "--min-peak-clicks", type=int, default=50,
        help="Minimum peak clicks to include page (default: 50)"
    )
    parser.add_argument(
        "--rolling-window", type=int, default=3,
        help="Rolling average window in months (default: 3)"
    )
    parser.add_argument(
        "--anomaly-std", type=float, default=2.0,
        help="Standard deviations for anomaly detection (default: 2.0)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path for JSON results (default: stdout)"
    )

    args = parser.parse_args()

    period_months = parse_period(args.period)

    gsc_data = parse_gsc_csv(args.gsc)
    if not gsc_data:
        print("ERROR: No data found in GSC export.")
        sys.exit(1)

    print(f"Loaded {len(gsc_data)} rows from GSC export.", file=sys.stderr)
    print(f"Analysis period: {period_months} months", file=sys.stderr)
    print(f"Decay threshold: {args.decay_threshold}%", file=sys.stderr)
    print(f"Min peak clicks: {args.min_peak_clicks}", file=sys.stderr)

    results = analyze_content_decay(
        gsc_data=gsc_data,
        period_months=period_months,
        decay_threshold=args.decay_threshold,
        min_peak_clicks=args.min_peak_clicks,
        rolling_window=args.rolling_window,
        anomaly_std=args.anomaly_std,
    )

    summary = results.get("summary", {})
    print(f"\nPages analyzed: {summary.get('total_pages_analyzed', 0)}", file=sys.stderr)
    print(f"Pages with decay: {summary.get('pages_with_decay', 0)}", file=sys.stderr)
    print(f"  Critical: {summary.get('critical_count', 0)}", file=sys.stderr)
    print(f"  High: {summary.get('high_count', 0)}", file=sys.stderr)
    print(f"  Medium: {summary.get('medium_count', 0)}", file=sys.stderr)
    print(f"Total traffic lost: {summary.get('total_traffic_lost', 0)} clicks/month", file=sys.stderr)

    # Serialize — strip internal time_series from output to keep JSON manageable
    output_data = {
        "summary": results["summary"],
        "decaying_pages": [
            {
                "page": p["page"],
                "decay": p["decay"],
                "pattern": p["pattern"],
                "anomalies": p["anomalies"],
                "update_correlation": p["update_correlation"],
            }
            for p in results["decaying_pages"]
        ],
        "growing_pages": results["growing_pages"],
        "update_impact": results["update_impact"],
        "monthly_trend": results["monthly_trend"],
    }

    output_json = json.dumps(output_data, indent=2, ensure_ascii=False, default=str)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
