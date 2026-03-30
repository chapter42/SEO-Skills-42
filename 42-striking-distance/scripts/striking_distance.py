#!/usr/bin/env python3
"""
Striking Distance Keyword Finder — Find pages ranking 4-20 where the
target keyword is missing from title, H1, meta description, or URL.

Combines GSC Performance data with optional Screaming Frog crawl data
to identify the highest-ROI on-page optimization opportunities.

Opportunity score: impressions x (1 - CTR) x (1 / position)
"""

import sys
import json
import csv
import re
import argparse
from typing import Optional
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

GSC_COLUMN_MAP = {
    "query": ["top queries", "query", "queries", "search query", "keyword"],
    "page": ["top pages", "page", "pages", "url", "landing page", "address"],
    "clicks": ["clicks"],
    "impressions": ["impressions"],
    "ctr": ["ctr", "click through rate"],
    "position": ["position", "avg. position", "average position"],
}

SF_COLUMN_MAP = {
    "url": ["address", "url", "page", "top pages"],
    "title": ["title 1", "title", "page title"],
    "h1": ["h1-1", "h1", "heading 1"],
    "meta_description": [
        "meta description 1",
        "meta description",
        "description",
    ],
}

# Expected CTR by position (Google organic, approximate)
EXPECTED_CTR = {
    1: 0.270,
    2: 0.155,
    3: 0.085,
    4: 0.070,
    5: 0.055,
    6: 0.040,
    7: 0.033,
    8: 0.028,
    9: 0.024,
    10: 0.020,
    11: 0.015,
    12: 0.012,
    13: 0.010,
    14: 0.009,
    15: 0.008,
    16: 0.007,
    17: 0.006,
    18: 0.005,
    19: 0.005,
    20: 0.004,
}


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


def normalize_url(url: str) -> str:
    """Normalize URL for matching: lowercase, strip trailing slash."""
    url = url.strip().lower()
    if url.endswith("/") and len(url) > 1:
        url = url.rstrip("/")
    return url


def keyword_in_text(keyword: str, text: str, word_boundary: bool = True) -> bool:
    """
    Check if keyword appears in text.
    Case-insensitive. Word-boundary aware when word_boundary=True.
    """
    if not text or not keyword:
        return False
    keyword_clean = keyword.strip().lower()
    text_clean = text.strip().lower()

    if word_boundary:
        # Escape regex special chars in keyword, then wrap with word boundaries
        escaped = re.escape(keyword_clean)
        pattern = r"(?:^|\b)" + escaped + r"(?:\b|$)"
        return bool(re.search(pattern, text_clean))
    else:
        return keyword_clean in text_clean


def keyword_in_url(keyword: str, url: str) -> bool:
    """Check if keyword appears in URL path (hyphens treated as spaces)."""
    if not keyword or not url:
        return False
    parsed = urlparse(url.lower())
    path = parsed.path.replace("-", " ").replace("_", " ").replace("/", " ")
    keyword_clean = keyword.strip().lower()
    return keyword_in_text(keyword_clean, path, word_boundary=False)


# ---------------------------------------------------------------------------
# GSC parsing
# ---------------------------------------------------------------------------

def parse_gsc_csv(filepath: str) -> list[dict]:
    """Parse GSC Performance export CSV."""
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        col_map = normalize_columns(headers, GSC_COLUMN_MAP)

        required = ["query", "page", "impressions", "position"]
        missing = [c for c in required if c not in col_map]
        if missing:
            print(f"ERROR: Missing required GSC columns: {missing}")
            print(f"  Found headers: {headers}")
            sys.exit(1)

        for row in reader:
            if not row or len(row) < len(col_map):
                continue
            try:
                entry = {
                    "query": row[col_map["query"]].strip(),
                    "page": row[col_map["page"]].strip(),
                    "clicks": int(row[col_map.get("clicks", -1)]) if "clicks" in col_map else 0,
                    "impressions": int(row[col_map["impressions"]].replace(",", "")),
                    "ctr": parse_ctr(row[col_map["ctr"]]) if "ctr" in col_map else 0.0,
                    "position": float(row[col_map["position"]].replace(",", ".")),
                }
                rows.append(entry)
            except (ValueError, IndexError):
                continue
    return rows


# ---------------------------------------------------------------------------
# Screaming Frog parsing
# ---------------------------------------------------------------------------

def parse_sf_csv(filepath: str) -> dict:
    """
    Parse Screaming Frog Internal:HTML export.
    Returns dict keyed by normalized URL.
    """
    pages = {}
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        col_map = normalize_columns(headers, SF_COLUMN_MAP)

        if "url" not in col_map:
            print(f"ERROR: No URL/Address column found in SF export.")
            print(f"  Found headers: {headers}")
            sys.exit(1)

        for row in reader:
            if not row or len(row) <= col_map["url"]:
                continue
            url = normalize_url(row[col_map["url"]])
            pages[url] = {
                "title": row[col_map["title"]].strip() if "title" in col_map and len(row) > col_map["title"] else "",
                "h1": row[col_map["h1"]].strip() if "h1" in col_map and len(row) > col_map["h1"] else "",
                "meta_description": row[col_map["meta_description"]].strip() if "meta_description" in col_map and len(row) > col_map["meta_description"] else "",
            }
    return pages


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def classify_opportunity(in_title: bool, in_h1: bool, in_meta: bool, in_url: bool, sf_available: bool) -> str:
    """Classify the opportunity based on where the keyword is missing."""
    if not sf_available:
        # Without SF data, can only check URL
        return "URL_MATCH" if in_url else "URL_MISSING"

    if not in_title and not in_h1:
        return "BOTH_MISSING"
    if not in_title:
        return "TITLE_MISSING"
    if not in_h1:
        return "H1_MISSING"
    if not in_meta:
        return "META_MISSING"
    if in_title and in_h1 and in_meta and in_url:
        return "PRESENT_ALL"
    if in_url and not in_title and not in_h1:
        return "URL_ONLY"
    return "PRESENT_ALL"


def calculate_opportunity_score(impressions: int, ctr: float, position: float) -> float:
    """Calculate opportunity score: impressions x (1 - CTR) x (1 / position)."""
    if position <= 0:
        position = 1
    return impressions * (1.0 - ctr) * (1.0 / position)


def estimate_uplift(impressions: int, current_ctr: float, current_position: float) -> int:
    """Estimate traffic uplift if page moves to position 3."""
    target_position = 3
    target_ctr = EXPECTED_CTR.get(target_position, 0.085)
    if current_ctr >= target_ctr:
        return 0
    uplift = impressions * (target_ctr - current_ctr)
    return max(0, int(round(uplift)))


def analyze_striking_distance(
    gsc_data: list[dict],
    sf_data: Optional[dict],
    min_impressions: int = 100,
    min_position: float = 4.0,
    max_position: float = 20.0,
    min_opportunity: float = 50.0,
) -> dict:
    """
    Main analysis: filter, check keyword presence, score, classify.
    Returns structured results as dict.
    """
    sf_available = sf_data is not None and len(sf_data) > 0

    # Step 1: Filter to striking distance range
    filtered = [
        row for row in gsc_data
        if min_position <= row["position"] <= max_position
        and row["impressions"] >= min_impressions
    ]

    # Step 2: Analyze each query x page pair
    opportunities = []
    for row in filtered:
        query = row["query"]
        page_url = row["page"]
        page_normalized = normalize_url(page_url)

        # URL check (always available)
        in_url = keyword_in_url(query, page_url)

        # SF data checks
        in_title = False
        in_h1 = False
        in_meta = False
        current_title = ""
        current_h1 = ""
        current_meta = ""

        if sf_available and page_normalized in sf_data:
            sf_page = sf_data[page_normalized]
            current_title = sf_page.get("title", "")
            current_h1 = sf_page.get("h1", "")
            current_meta = sf_page.get("meta_description", "")
            in_title = keyword_in_text(query, current_title)
            in_h1 = keyword_in_text(query, current_h1)
            in_meta = keyword_in_text(query, current_meta, word_boundary=False)

        # Classify
        classification = classify_opportunity(in_title, in_h1, in_meta, in_url, sf_available)

        # Skip if keyword is present everywhere
        if classification == "PRESENT_ALL":
            continue

        # Score
        score = calculate_opportunity_score(
            row["impressions"], row["ctr"], row["position"]
        )

        if score < min_opportunity:
            continue

        uplift = estimate_uplift(
            row["impressions"], row["ctr"], row["position"]
        )

        opportunities.append({
            "query": query,
            "page": page_url,
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": row["ctr"],
            "position": row["position"],
            "in_title": in_title,
            "in_h1": in_h1,
            "in_meta": in_meta,
            "in_url": in_url,
            "current_title": current_title,
            "current_h1": current_h1,
            "current_meta": current_meta,
            "classification": classification,
            "opportunity_score": round(score, 1),
            "estimated_uplift": uplift,
        })

    # Sort by opportunity score descending
    opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

    # Aggregate: pages with multiple keywords in range
    page_keyword_counts = {}
    for opp in opportunities:
        page = opp["page"]
        if page not in page_keyword_counts:
            page_keyword_counts[page] = {
                "page": page,
                "keywords": [],
                "total_impressions": 0,
                "positions": [],
            }
        page_keyword_counts[page]["keywords"].append(opp["query"])
        page_keyword_counts[page]["total_impressions"] += opp["impressions"]
        page_keyword_counts[page]["positions"].append(opp["position"])

    multi_keyword_pages = []
    for page_data in page_keyword_counts.values():
        if len(page_data["keywords"]) >= 2:
            page_data["avg_position"] = round(
                sum(page_data["positions"]) / len(page_data["positions"]), 1
            )
            page_data["keyword_count"] = len(page_data["keywords"])
            multi_keyword_pages.append(page_data)
    multi_keyword_pages.sort(key=lambda x: x["keyword_count"], reverse=True)

    # Summary counts
    title_missing = sum(1 for o in opportunities if "TITLE" in o["classification"] or o["classification"] == "BOTH_MISSING")
    h1_missing = sum(1 for o in opportunities if "H1" in o["classification"] or o["classification"] == "BOTH_MISSING")
    both_missing = sum(1 for o in opportunities if o["classification"] == "BOTH_MISSING")
    meta_missing = sum(1 for o in opportunities if o["classification"] == "META_MISSING")
    total_uplift = sum(o["estimated_uplift"] for o in opportunities)

    return {
        "summary": {
            "total_gsc_rows": len(gsc_data),
            "in_striking_distance": len(filtered),
            "opportunities_found": len(opportunities),
            "keyword_missing_title": title_missing,
            "keyword_missing_h1": h1_missing,
            "keyword_missing_both": both_missing,
            "keyword_missing_meta": meta_missing,
            "estimated_total_uplift": total_uplift,
            "sf_data_available": sf_available,
            "position_range": f"{min_position}-{max_position}",
            "min_impressions": min_impressions,
        },
        "opportunities": opportunities,
        "multi_keyword_pages": multi_keyword_pages,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Striking Distance Keyword Finder — find quick-win SEO opportunities"
    )
    parser.add_argument(
        "--gsc", required=True, help="Path to GSC Performance export CSV"
    )
    parser.add_argument(
        "--sf-crawl", default=None, help="Path to Screaming Frog Internal:HTML export CSV"
    )
    parser.add_argument(
        "--min-impressions", type=int, default=100,
        help="Minimum monthly impressions (default: 100)"
    )
    parser.add_argument(
        "--min-position", type=float, default=4.0,
        help="Minimum position for striking distance (default: 4)"
    )
    parser.add_argument(
        "--max-position", type=float, default=20.0,
        help="Maximum position for striking distance (default: 20)"
    )
    parser.add_argument(
        "--min-opportunity", type=float, default=50.0,
        help="Minimum opportunity score to include (default: 50)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path for JSON results (default: stdout)"
    )

    args = parser.parse_args()

    # Parse position range from --positions flag style (handled by caller)
    gsc_data = parse_gsc_csv(args.gsc)
    if not gsc_data:
        print("ERROR: No data found in GSC export.")
        sys.exit(1)

    sf_data = None
    if args.sf_crawl:
        sf_data = parse_sf_csv(args.sf_crawl)
        print(f"Loaded {len(sf_data)} pages from Screaming Frog export.", file=sys.stderr)

    print(f"Loaded {len(gsc_data)} rows from GSC export.", file=sys.stderr)
    print(f"Filtering: position {args.min_position}-{args.max_position}, min impressions {args.min_impressions}", file=sys.stderr)

    results = analyze_striking_distance(
        gsc_data=gsc_data,
        sf_data=sf_data,
        min_impressions=args.min_impressions,
        min_position=args.min_position,
        max_position=args.max_position,
        min_opportunity=args.min_opportunity,
    )

    print(f"\nFound {results['summary']['opportunities_found']} opportunities.", file=sys.stderr)
    print(f"Estimated total traffic uplift: +{results['summary']['estimated_total_uplift']} clicks/month", file=sys.stderr)

    output_json = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
