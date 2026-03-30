#!/usr/bin/env python3
"""
Share of Voice Calculator

Calculate competitive Share of Voice -- what percentage of total search
visibility does each domain own for a set of keywords. Supports CTR-adjusted
SOV (4 built-in models + custom) and simple traffic-share mode.

Usage:
    python3 share_of_voice.py --input ranking-data.csv --output sov-results.json
    python3 share_of_voice.py --input ranking-data.csv --ctr-model awr --top-n 20
    python3 share_of_voice.py --input traffic-by-domain.csv --simple --output sov-results.json
    python3 share_of_voice.py --input ranking-data.csv --ctr-model custom --ctr-file curve.json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Built-in CTR curves
# ---------------------------------------------------------------------------

CTR_MODELS: dict[str, dict[int, float]] = {
    "sistrix": {
        1: 28.5, 2: 15.7, 3: 11.0, 4: 8.0, 5: 7.2,
        6: 5.1, 7: 4.0, 8: 3.2, 9: 2.8, 10: 2.5,
    },
    "awr": {
        1: 31.7, 2: 24.7, 3: 18.7, 4: 13.6, 5: 9.5,
        6: 6.2, 7: 4.2, 8: 3.1, 9: 2.4, 10: 1.9,
    },
    "conservative": {
        1: 20.0, 2: 12.0, 3: 8.0, 4: 5.5, 5: 4.0,
        6: 3.0, 7: 2.2, 8: 1.8, 9: 1.5, 10: 1.2,
    },
    "backlinko": {
        1: 27.6, 2: 15.8, 3: 11.0, 4: 8.4, 5: 6.3,
        6: 4.9, 7: 3.9, 8: 3.3, 9: 2.7, 10: 2.4,
    },
}


def load_custom_ctr(path: str) -> dict[int, float]:
    """Load a custom CTR curve from a JSON file."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    curve = data.get("curve", data)
    return {int(k): float(v) for k, v in curve.items()}


def get_ctr(model: dict[int, float], position: int) -> float:
    """Get CTR percentage for a given position. Returns 0 for positions
    beyond the model's range."""
    return model.get(position, 0.0)


# ---------------------------------------------------------------------------
# Domain normalisation
# ---------------------------------------------------------------------------

def normalize_domain(value: str) -> str:
    """Extract and normalize domain from URL or domain string."""
    value = value.strip()
    if not value:
        return value

    # If it looks like a URL, parse it
    if "://" in value or value.startswith("www."):
        if not value.startswith("http"):
            value = "https://" + value
        parsed = urlparse(value)
        domain = parsed.netloc or parsed.path.split("/")[0]
    else:
        domain = value.split("/")[0]

    # Strip www. and lowercase
    domain = domain.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    # Strip port
    if ":" in domain:
        domain = domain.split(":")[0]
    return domain


# ---------------------------------------------------------------------------
# CSV parsing with flexible column names
# ---------------------------------------------------------------------------

KEYWORD_COLUMNS = {"keyword", "query", "search_term", "term"}
VOLUME_COLUMNS = {"volume", "search_volume", "sv", "avg_monthly_searches"}
DOMAIN_COLUMNS = {"domain", "url", "site", "landing_page", "result_url"}
POSITION_COLUMNS = {"position", "rank", "pos"}
TRAFFIC_COLUMNS = {"traffic", "organic_traffic", "estimated_traffic", "est_traffic"}
KW_COUNT_COLUMNS = {"keywords", "keyword_count", "kw_count", "organic_keywords"}


def _find_column(headers: list[str], candidates: set[str]) -> str | None:
    """Find the first header that matches any candidate (case-insensitive)."""
    for h in headers:
        if h.lower().strip() in candidates:
            return h
    return None


# ---------------------------------------------------------------------------
# Standard mode: ranking data with CTR model
# ---------------------------------------------------------------------------

def parse_ranking_csv(path: str, top_n: int = 10) -> list[dict]:
    """Parse ranking CSV. Returns list of
    {keyword, volume, domain, position} dicts."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []

        kw_col = _find_column(headers, KEYWORD_COLUMNS)
        vol_col = _find_column(headers, VOLUME_COLUMNS)
        dom_col = _find_column(headers, DOMAIN_COLUMNS)
        pos_col = _find_column(headers, POSITION_COLUMNS)

        if not kw_col:
            raise ValueError(f"No keyword column found. Headers: {headers}")
        if not dom_col:
            raise ValueError(f"No domain/url column found. Headers: {headers}")
        if not pos_col:
            raise ValueError(f"No position column found. Headers: {headers}")

        rows = []
        for row in reader:
            keyword = row[kw_col].strip()
            domain = normalize_domain(row[dom_col])
            if not keyword or not domain:
                continue

            try:
                position = int(float(row[pos_col]))
            except (ValueError, TypeError):
                continue

            if position < 1 or position > top_n:
                continue

            volume = 0
            if vol_col and row.get(vol_col):
                try:
                    vol_str = row[vol_col].replace(",", "").strip()
                    volume = int(float(vol_str))
                except (ValueError, TypeError):
                    volume = 0

            rows.append({
                "keyword": keyword,
                "volume": volume,
                "domain": domain,
                "position": position,
            })

    return rows


def calculate_sov(
    rows: list[dict],
    ctr_model: dict[int, float],
    highlight_domain: str | None = None,
) -> dict:
    """Calculate SOV from ranking rows + CTR model."""

    # Calculate estimated clicks per row
    for row in rows:
        ctr_pct = get_ctr(ctr_model, row["position"])
        row["ctr_pct"] = ctr_pct
        row["estimated_clicks"] = row["volume"] * (ctr_pct / 100.0)

    # Aggregate by domain
    domain_data: dict[str, dict] = defaultdict(lambda: {
        "estimated_clicks": 0.0,
        "keywords_ranked": 0,
        "position_sum": 0,
        "keyword_breakdown": [],
    })

    for row in rows:
        d = domain_data[row["domain"]]
        d["estimated_clicks"] += row["estimated_clicks"]
        d["keywords_ranked"] += 1
        d["position_sum"] += row["position"]
        d["keyword_breakdown"].append({
            "keyword": row["keyword"],
            "volume": row["volume"],
            "position": row["position"],
            "ctr_pct": row["ctr_pct"],
            "estimated_clicks": round(row["estimated_clicks"], 1),
        })

    total_clicks = sum(d["estimated_clicks"] for d in domain_data.values())

    # Build domain results
    domains = []
    for domain, data in domain_data.items():
        sov_pct = (data["estimated_clicks"] / total_clicks * 100) if total_clicks > 0 else 0
        avg_pos = data["position_sum"] / data["keywords_ranked"] if data["keywords_ranked"] > 0 else 0

        # Sort keyword breakdown by estimated clicks descending
        data["keyword_breakdown"].sort(
            key=lambda x: x["estimated_clicks"], reverse=True
        )

        # Calculate % of domain SOV per keyword
        for kw in data["keyword_breakdown"]:
            kw["pct_of_domain_sov"] = round(
                (kw["estimated_clicks"] / data["estimated_clicks"] * 100)
                if data["estimated_clicks"] > 0 else 0,
                1,
            )

        domains.append({
            "domain": domain,
            "sov_percent": round(sov_pct, 2),
            "estimated_clicks": round(data["estimated_clicks"], 1),
            "keywords_ranked": data["keywords_ranked"],
            "avg_position": round(avg_pos, 1),
            "keyword_breakdown": data["keyword_breakdown"],
        })

    # Sort by SOV descending
    domains.sort(key=lambda x: x["sov_percent"], reverse=True)

    # Unique keywords and total volume
    keywords_seen: dict[str, int] = {}
    for row in rows:
        if row["keyword"] not in keywords_seen:
            keywords_seen[row["keyword"]] = row["volume"]

    total_volume = sum(keywords_seen.values())

    # SOV distribution buckets
    distribution = {
        "> 10%": {"domains": 0, "combined_sov": 0.0},
        "5-10%": {"domains": 0, "combined_sov": 0.0},
        "2-5%": {"domains": 0, "combined_sov": 0.0},
        "1-2%": {"domains": 0, "combined_sov": 0.0},
        "< 1%": {"domains": 0, "combined_sov": 0.0},
    }
    for d in domains:
        pct = d["sov_percent"]
        if pct > 10:
            bucket = "> 10%"
        elif pct >= 5:
            bucket = "5-10%"
        elif pct >= 2:
            bucket = "2-5%"
        elif pct >= 1:
            bucket = "1-2%"
        else:
            bucket = "< 1%"
        distribution[bucket]["domains"] += 1
        distribution[bucket]["combined_sov"] += pct

    # Round distribution
    for bucket in distribution.values():
        bucket["combined_sov"] = round(bucket["combined_sov"], 1)

    return {
        "meta": {
            "total_keywords": len(keywords_seen),
            "total_domains": len(domains),
            "ctr_model": "custom" if not hasattr(ctr_model, "__name__") else "unknown",
            "total_search_volume": total_volume,
            "total_estimated_clicks": round(total_clicks, 1),
        },
        "domains": domains,
        "distribution": distribution,
    }


# ---------------------------------------------------------------------------
# Simple mode: traffic by domain
# ---------------------------------------------------------------------------

def parse_simple_csv(path: str) -> list[dict]:
    """Parse simple traffic-by-domain CSV."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []

        dom_col = _find_column(headers, DOMAIN_COLUMNS)
        traffic_col = _find_column(headers, TRAFFIC_COLUMNS)
        kw_col = _find_column(headers, KW_COUNT_COLUMNS)

        if not dom_col:
            raise ValueError(f"No domain column found. Headers: {headers}")
        if not traffic_col:
            raise ValueError(f"No traffic column found. Headers: {headers}")

        rows = []
        for row in reader:
            domain = normalize_domain(row[dom_col])
            if not domain:
                continue
            try:
                traffic_str = row[traffic_col].replace(",", "").strip()
                traffic = int(float(traffic_str))
            except (ValueError, TypeError):
                continue

            kw_count = 0
            if kw_col and row.get(kw_col):
                try:
                    kw_count = int(float(row[kw_col].replace(",", "").strip()))
                except (ValueError, TypeError):
                    kw_count = 0

            rows.append({
                "domain": domain,
                "traffic": traffic,
                "keywords": kw_count,
            })

    return rows


def calculate_simple_sov(rows: list[dict]) -> dict:
    """Calculate SOV from simple traffic data."""
    total_traffic = sum(r["traffic"] for r in rows)

    domains = []
    for row in rows:
        sov_pct = (row["traffic"] / total_traffic * 100) if total_traffic > 0 else 0
        domains.append({
            "domain": row["domain"],
            "sov_percent": round(sov_pct, 2),
            "estimated_clicks": row["traffic"],
            "keywords_ranked": row["keywords"],
            "avg_position": None,
            "keyword_breakdown": [],
        })

    domains.sort(key=lambda x: x["sov_percent"], reverse=True)

    return {
        "meta": {
            "total_keywords": sum(r["keywords"] for r in rows),
            "total_domains": len(domains),
            "ctr_model": "simple (traffic-based)",
            "total_search_volume": None,
            "total_estimated_clicks": total_traffic,
        },
        "domains": domains,
        "distribution": {},
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_sov(
    input_path: str,
    output_path: str = "sov-results.json",
    ctr_model_name: str = "sistrix",
    ctr_file: str | None = None,
    top_n: int = 10,
    simple: bool = False,
    highlight_domain: str | None = None,
) -> dict:
    """Run SOV calculation pipeline."""

    if simple:
        print(f"Simple mode: parsing traffic data from {input_path}")
        rows = parse_simple_csv(input_path)
        print(f"Parsed {len(rows)} domains")
        result = calculate_simple_sov(rows)
    else:
        # Load CTR model
        if ctr_model_name == "custom":
            if not ctr_file:
                print("Error: --ctr-file required when using custom CTR model", file=sys.stderr)
                sys.exit(1)
            ctr_model = load_custom_ctr(ctr_file)
            print(f"Loaded custom CTR curve from {ctr_file}")
        elif ctr_model_name in CTR_MODELS:
            ctr_model = CTR_MODELS[ctr_model_name]
        else:
            print(f"Unknown CTR model: {ctr_model_name}. Available: {', '.join(CTR_MODELS.keys())}, custom",
                  file=sys.stderr)
            sys.exit(1)

        # Extend CTR model to top_n positions if needed
        if top_n > max(ctr_model.keys()):
            # Extrapolate: positions beyond model get diminishing CTR
            last_pos = max(ctr_model.keys())
            last_ctr = ctr_model[last_pos]
            for pos in range(last_pos + 1, top_n + 1):
                # Decay by ~20% per position
                last_ctr = max(last_ctr * 0.8, 0.1)
                ctr_model[pos] = round(last_ctr, 2)

        print(f"Parsing ranking data from {input_path} (top {top_n}, CTR model: {ctr_model_name})")
        rows = parse_ranking_csv(input_path, top_n=top_n)
        print(f"Parsed {len(rows)} ranking entries")

        if not rows:
            print("No valid ranking data found. Check CSV format.", file=sys.stderr)
            sys.exit(1)

        result = calculate_sov(rows, ctr_model, highlight_domain)
        result["meta"]["ctr_model"] = ctr_model_name
        result["meta"]["top_n"] = top_n

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"Results written to {output_path}")

    # Print summary
    print(f"\n--- Share of Voice Summary ---")
    print(f"Total domains: {result['meta']['total_domains']}")
    print(f"Total estimated clicks: {result['meta']['total_estimated_clicks']:,.0f}")
    print(f"\nTop 10 domains:")
    for i, d in enumerate(result["domains"][:10], 1):
        print(f"  {i:2d}. {d['domain']:30s}  SOV: {d['sov_percent']:5.1f}%  "
              f"Clicks: {d['estimated_clicks']:>10,.0f}  "
              f"Keywords: {d['keywords_ranked']}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Calculate competitive Share of Voice"
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to ranking data CSV"
    )
    parser.add_argument(
        "--output", "-o", default="sov-results.json",
        help="Output JSON path (default: sov-results.json)",
    )
    parser.add_argument(
        "--ctr-model", default="sistrix",
        choices=["sistrix", "awr", "conservative", "backlinko", "custom"],
        help="CTR curve model (default: sistrix)",
    )
    parser.add_argument(
        "--ctr-file", default=None,
        help="Path to custom CTR curve JSON (required with --ctr-model custom)",
    )
    parser.add_argument(
        "--top-n", type=int, default=10,
        help="Only count positions 1-N (default: 10)",
    )
    parser.add_argument(
        "--simple", action="store_true",
        help="Simple mode: use traffic estimates directly",
    )
    parser.add_argument(
        "--domain", default=None,
        help="Highlight a specific domain in the output",
    )
    args = parser.parse_args()

    run_sov(
        input_path=args.input,
        output_path=args.output,
        ctr_model_name=args.ctr_model,
        ctr_file=args.ctr_file,
        top_n=args.top_n,
        simple=args.simple,
        highlight_domain=args.domain,
    )


if __name__ == "__main__":
    main()
