#!/usr/bin/env python3
"""
Product Title Optimization — Competitor Gap Analysis & SERP Patterns.

Mode 1 — gap:     Match products by MPN/SKU/GTIN, find missing title words.
Mode 2 — serp:    Analyze word frequency by position in SERP titles.
Mode 3 — standardize: Analyze title components for AI standardization.

Output: JSON to stdout for Claude to process into PRODUCT-TITLES.md.
"""

import sys
import json
import csv
import re
import argparse
from collections import Counter, defaultdict
from typing import Optional

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

PRODUCT_COLUMN_MAP = {
    "title": ["title", "product title", "product name", "naam", "titel",
              "name", "product_name", "product_title", "item name",
              "title 1", "page title"],
    "mpn": ["mpn", "manufacturer part number", "part number", "partnumber",
            "manufacturer_part_number", "mfr part", "artikelnummer"],
    "sku": ["sku", "product sku", "item sku", "product_sku", "sku_id",
            "item number", "itemnumber"],
    "gtin": ["gtin", "ean", "upc", "barcode", "ean13", "upc-a",
             "gtin13", "gtin-13", "product_ean"],
    "category": ["category", "categorie", "department", "afdeling",
                  "product category", "product_category", "cat", "type"],
    "brand": ["brand", "merk", "manufacturer", "fabrikant", "brand name"],
    "url": ["url", "address", "page", "link", "product url",
            "product_url", "canonical"],
}

SERP_COLUMN_MAP = {
    "title": ["title", "serp title", "result title", "page title",
              "title tag", "title 1", "naam"],
    "position": ["position", "rank", "ranking", "pos", "avg. position",
                  "average position"],
    "keyword": ["keyword", "query", "search query", "zoekwoord",
                 "search term", "top queries"],
    "category": ["category", "categorie", "group", "cluster"],
    "url": ["url", "address", "page", "result url", "link"],
}


def normalize_columns(headers: list[str], column_map: dict) -> dict:
    """Map actual CSV headers to canonical field names."""
    mapping = {}
    lower_headers = [h.strip().lower() for h in headers]
    for canonical, variants in column_map.items():
        for variant in variants:
            if variant in lower_headers:
                idx = lower_headers.index(variant)
                mapping[canonical] = headers[idx]
                break
    return mapping


def read_csv(filepath: str) -> list[dict]:
    """Read CSV with flexible encoding detection."""
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                reader = csv.DictReader(f, dialect=dialect)
                rows = list(reader)
                if rows:
                    return rows
        except (UnicodeDecodeError, csv.Error):
            continue
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)


def normalize_identifier(value: str) -> str:
    """Normalize MPN/SKU/GTIN for matching."""
    v = value.strip().lower()
    v = re.sub(r"[\s\-_/.]", "", v)
    v = v.lstrip("0")  # Remove leading zeros
    return v


def tokenize_title(title: str) -> set[str]:
    """Tokenize a product title into lowercase word set."""
    title = title.lower()
    # Keep alphanumeric and hyphens (model numbers like WH-1000XM5)
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", title)
    return set(tokens)


# ---------------------------------------------------------------------------
# Mode 1: Competitor Title Gap
# ---------------------------------------------------------------------------

def match_products(
    your_rows: list[dict],
    your_col_map: dict,
    comp_rows: list[dict],
    comp_col_map: dict,
) -> list[dict]:
    """Match products across catalogs by MPN/SKU/GTIN."""
    matches = []

    # Build lookup from identifier fields
    id_fields = ["mpn", "sku", "gtin"]

    # Index competitor products by all available identifiers
    comp_index = defaultdict(list)
    for i, row in enumerate(comp_rows):
        for field in id_fields:
            col = comp_col_map.get(field)
            if col and row.get(col, "").strip():
                norm = normalize_identifier(row[col])
                if norm:
                    comp_index[norm].append(i)

    # Match your products against competitor index
    matched_comp_indices = set()
    for your_row in your_rows:
        best_match = None
        match_field = None

        for field in id_fields:
            col = your_col_map.get(field)
            if col and your_row.get(col, "").strip():
                norm = normalize_identifier(your_row[col])
                if norm and norm in comp_index:
                    comp_idx = comp_index[norm][0]
                    if comp_idx not in matched_comp_indices:
                        best_match = comp_rows[comp_idx]
                        match_field = field
                        matched_comp_indices.add(comp_idx)
                        break

        # Fuzzy fallback on title if no exact ID match
        if not best_match and fuzz is not None:
            your_title_col = your_col_map.get("title")
            comp_title_col = comp_col_map.get("title")
            if your_title_col and comp_title_col:
                your_title = your_row.get(your_title_col, "")
                best_score = 0
                best_idx = -1
                for i, comp_row in enumerate(comp_rows):
                    if i in matched_comp_indices:
                        continue
                    comp_title = comp_row.get(comp_title_col, "")
                    score = fuzz.token_sort_ratio(your_title.lower(), comp_title.lower())
                    if score > best_score and score >= 90:
                        best_score = score
                        best_idx = i

                if best_idx >= 0:
                    best_match = comp_rows[best_idx]
                    match_field = "fuzzy_title"
                    matched_comp_indices.add(best_idx)

        if best_match:
            matches.append({
                "your_product": your_row,
                "competitor_product": best_match,
                "match_field": match_field,
            })

    return matches


def analyze_title_gaps(
    your_file: str,
    competitor_file: str,
) -> dict:
    """Find words in competitor titles missing from your titles."""
    your_rows = read_csv(your_file)
    comp_rows = read_csv(competitor_file)

    if not your_rows:
        return {"error": f"No rows found in {your_file}"}
    if not comp_rows:
        return {"error": f"No rows found in {competitor_file}"}

    your_col_map = normalize_columns(list(your_rows[0].keys()), PRODUCT_COLUMN_MAP)
    comp_col_map = normalize_columns(list(comp_rows[0].keys()), PRODUCT_COLUMN_MAP)

    your_title_col = your_col_map.get("title")
    comp_title_col = comp_col_map.get("title")

    if not your_title_col:
        return {"error": f"No title column in your file. Available: {list(your_rows[0].keys())}"}
    if not comp_title_col:
        return {"error": f"No title column in competitor file. Available: {list(comp_rows[0].keys())}"}

    # Match products
    matches = match_products(your_rows, your_col_map, comp_rows, comp_col_map)

    if not matches:
        return {
            "error": "No products matched between catalogs. Check MPN/SKU/GTIN columns.",
            "your_columns": list(your_rows[0].keys()),
            "competitor_columns": list(comp_rows[0].keys()),
        }

    # Analyze gaps
    missing_word_counter = Counter()
    missing_word_by_category = defaultdict(Counter)
    product_gaps = []

    your_cat_col = your_col_map.get("category")

    for match in matches:
        your_title = match["your_product"].get(your_title_col, "")
        comp_title = match["competitor_product"].get(comp_title_col, "")

        your_tokens = tokenize_title(your_title)
        comp_tokens = tokenize_title(comp_title)

        missing = comp_tokens - your_tokens
        # Filter out very short tokens and pure numbers
        missing = {w for w in missing if len(w) > 1 and not w.isdigit()}

        if missing:
            category = match["your_product"].get(your_cat_col, "All") if your_cat_col else "All"

            for word in missing:
                missing_word_counter[word] += 1
                missing_word_by_category[category][word] += 1

            # Get MPN for reference
            mpn = ""
            for field in ["mpn", "sku", "gtin"]:
                col = your_col_map.get(field)
                if col:
                    mpn = match["your_product"].get(col, "")
                    if mpn:
                        break

            product_gaps.append({
                "your_title": your_title,
                "competitor_title": comp_title,
                "missing_words": sorted(missing),
                "match_field": match["match_field"],
                "mpn": mpn,
                "category": category if your_cat_col else None,
            })

    # Build category summaries
    category_summaries = {}
    for cat, counter in missing_word_by_category.items():
        category_summaries[cat] = [
            {"word": word, "count": count}
            for word, count in counter.most_common(20)
        ]

    return {
        "mode": "gap",
        "summary": {
            "your_products": len(your_rows),
            "competitor_products": len(comp_rows),
            "matched_products": len(matches),
            "products_with_gaps": len(product_gaps),
            "unique_missing_words": len(missing_word_counter),
        },
        "top_missing_words": [
            {"word": word, "count": count}
            for word, count in missing_word_counter.most_common(50)
        ],
        "missing_by_category": category_summaries,
        "product_gaps": product_gaps[:100],  # Limit output size
    }


# ---------------------------------------------------------------------------
# Mode 2: SERP Title Patterns
# ---------------------------------------------------------------------------

def analyze_serp_patterns(filepath: str) -> dict:
    """Analyze word frequency by position in SERP titles."""
    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), SERP_COLUMN_MAP)

    title_col = col_map.get("title")
    position_col = col_map.get("position")
    keyword_col = col_map.get("keyword")
    category_col = col_map.get("category")

    if not title_col:
        return {"error": f"No title column found. Available: {list(rows[0].keys())}"}

    # Group by category or keyword if available
    grouping_col = category_col or keyword_col
    groups = defaultdict(list)

    for row in rows:
        title = row.get(title_col, "").strip()
        if not title:
            continue

        position = None
        if position_col:
            try:
                position = float(row.get(position_col, "0"))
            except (ValueError, TypeError):
                position = None

        group = row.get(grouping_col, "All").strip() if grouping_col else "All"
        groups[group].append({
            "title": title,
            "position": position,
        })

    # Analyze word frequency by position in title for each group
    results = {}

    for group, titles in groups.items():
        # Filter to top results if position data available
        if titles[0].get("position") is not None:
            titles = [t for t in titles if t["position"] and t["position"] <= 10]

        if not titles:
            continue

        position_words = defaultdict(Counter)  # {word_position: {word: count}}
        title_lengths = []

        for item in titles:
            words = re.findall(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*", item["title"])
            title_lengths.append(len(words))

            for i, word in enumerate(words):
                pos_key = i + 1  # 1-based position
                position_words[pos_key][word.lower()] += 1

        # Build pattern summary
        total_titles = len(titles)
        patterns = []
        for pos in sorted(position_words.keys()):
            if pos > 12:  # Limit to first 12 positions
                break
            counter = position_words[pos]
            top_words = counter.most_common(5)
            patterns.append({
                "position": pos,
                "top_words": [
                    {"word": w, "count": c, "percentage": round(c / total_titles * 100, 1)}
                    for w, c in top_words
                ],
                "total_titles_with_position": sum(counter.values()),
            })

        # Detect common structures
        structures = []
        # Check if brand tends to come first
        if 1 in position_words:
            top_first = position_words[1].most_common(1)
            if top_first and top_first[0][1] / total_titles > 0.3:
                structures.append(f"Position 1 dominated by: '{top_first[0][0]}' ({round(top_first[0][1]/total_titles*100)}%)")

        results[group] = {
            "total_titles_analyzed": total_titles,
            "avg_title_length_words": round(sum(title_lengths) / len(title_lengths), 1) if title_lengths else 0,
            "position_patterns": patterns,
            "structural_observations": structures,
        }

    return {
        "mode": "serp-pattern",
        "groups": results,
        "summary": {
            "total_titles": sum(len(t) for t in groups.values()),
            "total_groups": len(results),
        },
    }


# ---------------------------------------------------------------------------
# Mode 3: Standardization Analysis
# ---------------------------------------------------------------------------

def analyze_for_standardization(
    filepath: str,
    template: Optional[str] = None,
) -> dict:
    """Analyze product titles to detect components and inconsistencies."""
    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), PRODUCT_COLUMN_MAP)

    title_col = col_map.get("title")
    category_col = col_map.get("category")
    brand_col = col_map.get("brand")

    if not title_col:
        return {"error": f"No title column found. Available: {list(rows[0].keys())}"}

    # Collect titles by category
    titles_by_category = defaultdict(list)
    brands = set()

    for row in rows:
        title = row.get(title_col, "").strip()
        if not title:
            continue

        category = row.get(category_col, "All").strip() if category_col else "All"
        brand = row.get(brand_col, "").strip() if brand_col else ""

        if brand:
            brands.add(brand.lower())

        titles_by_category[category].append({
            "title": title,
            "brand": brand,
        })

    # Analyze each category
    category_analysis = {}

    for category, items in titles_by_category.items():
        titles = [item["title"] for item in items]
        title_lengths = [len(t) for t in titles]
        word_counts = [len(t.split()) for t in titles]

        # Detect common patterns
        first_words = Counter()
        separator_counts = Counter()

        for title in titles:
            words = title.split()
            if words:
                first_words[words[0].lower()] += 1

            # Count separators
            for sep in [" - ", " | ", " / ", " – ", " — "]:
                if sep in title:
                    separator_counts[sep] += 1

        # Check if brand appears first
        brand_first_count = 0
        for item in items:
            if item["brand"]:
                if item["title"].lower().startswith(item["brand"].lower()):
                    brand_first_count += 1

        brand_first_pct = round(brand_first_count / len(items) * 100, 1) if items else 0

        category_analysis[category] = {
            "total_titles": len(titles),
            "avg_title_length_chars": round(sum(title_lengths) / len(title_lengths), 1),
            "avg_title_length_words": round(sum(word_counts) / len(word_counts), 1),
            "min_length": min(title_lengths),
            "max_length": max(title_lengths),
            "brand_first_percentage": brand_first_pct,
            "common_first_words": [
                {"word": w, "count": c}
                for w, c in first_words.most_common(5)
            ],
            "separators_used": dict(separator_counts),
            "sample_titles": titles[:5],
        }

    return {
        "mode": "standardize",
        "template": template,
        "brands_found": sorted(brands),
        "categories": category_analysis,
        "summary": {
            "total_products": sum(len(t) for t in titles_by_category.values()),
            "total_categories": len(titles_by_category),
            "total_brands": len(brands),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Product Title Optimization — Gap Analysis & SERP Patterns"
    )
    subparsers = parser.add_subparsers(dest="command", help="Mode to run")

    # Gap analysis
    gap = subparsers.add_parser("gap", help="Competitor title gap analysis")
    gap.add_argument("your_file", help="Your products CSV")
    gap.add_argument("competitor_file", help="Competitor products CSV")

    # SERP patterns
    serp = subparsers.add_parser("serp-pattern", help="SERP title pattern analysis")
    serp.add_argument("csv_file", help="SERP titles CSV")

    # Standardization
    std = subparsers.add_parser("standardize", help="Title standardization analysis")
    std.add_argument("csv_file", help="Products CSV")
    std.add_argument("--template", default=None,
                     help="Title template, e.g., '{brand} {product} {color} {size}'")

    args = parser.parse_args()

    if args.command == "gap":
        result = analyze_title_gaps(args.your_file, args.competitor_file)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "serp-pattern":
        result = analyze_serp_patterns(args.csv_file)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "standardize":
        result = analyze_for_standardization(args.csv_file, args.template)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
