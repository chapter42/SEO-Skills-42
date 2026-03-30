#!/usr/bin/env python3
"""
eCommerce Taxonomy Discovery & Breadcrumb Relevancy Checker.

Mode 1 — Category Discovery:
  Extracts n-grams from product titles to find repeated phrases
  that could become new category/subcategory pages.

Mode 2 — Breadcrumb Relevancy:
  Compares product titles with their breadcrumb category path
  using fuzzy matching to detect miscategorized products.

Output: JSON to stdout for Claude to process into ECOM-TAXONOMY.md.
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

try:
    import nltk
    from nltk.util import ngrams as nltk_ngrams
except ImportError:
    nltk = None


# ---------------------------------------------------------------------------
# Stopwords (Dutch + English basics)
# ---------------------------------------------------------------------------

STOPWORDS_NL = {
    "de", "het", "een", "van", "en", "in", "is", "op", "te", "dat", "die",
    "voor", "zijn", "met", "aan", "er", "maar", "om", "ook", "als", "dan",
    "naar", "bij", "nog", "wel", "geen", "wat", "wordt", "uit", "tot",
    "was", "heeft", "deze", "niet", "meer", "over", "zou", "worden",
}

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "that", "this", "was", "are",
    "be", "has", "had", "have", "will", "can", "do", "does", "did", "not",
    "so", "if", "no", "up", "out", "all", "its", "as", "into", "more",
}

STOPWORDS = STOPWORDS_NL | STOPWORDS_EN


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

PRODUCT_COLUMN_MAP = {
    "title": ["title", "product title", "product name", "naam", "titel",
              "name", "product_name", "product_title", "item name"],
    "category": ["category", "categorie", "department", "afdeling",
                  "product category", "product_category", "cat", "type"],
    "url": ["url", "address", "page", "link", "product url", "product_url",
            "canonical", "permalink"],
}

BREADCRUMB_COLUMN_MAP = {
    "url": ["url", "address", "page", "link", "canonical"],
    "title": ["title 1", "title", "h1-1", "h1", "product title", "naam",
              "page title", "heading 1"],
    "breadcrumb": ["breadcrumb", "breadcrumbs", "breadcrumb list",
                    "breadcrumb path", "broodkruimel", "broodkruimels",
                    "breadcrumb-1", "breadcrumb 1"],
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
    # Fallback: simple comma-separated
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)


def tokenize(text: str) -> list[str]:
    """Lowercase, remove non-alpha, split, remove stopwords."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Mode 1: Category Discovery
# ---------------------------------------------------------------------------

def extract_ngrams(tokens: list[str], n: int) -> list[str]:
    """Extract n-grams from token list."""
    if len(tokens) < n:
        return []
    grams = []
    for i in range(len(tokens) - n + 1):
        grams.append(" ".join(tokens[i:i + n]))
    return grams


def discover_categories(
    filepath: str,
    min_frequency: int = 5,
    ngram_min: int = 2,
    ngram_max: int = 3,
) -> dict:
    """
    Discover potential new category pages from product title n-grams.

    Returns dict with:
      - categories: {category: [{ngram, count, example_titles}]}
      - existing_categories: list of known category names
      - summary: {total_suggestions, total_products_analyzed}
    """
    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), PRODUCT_COLUMN_MAP)

    title_col = col_map.get("title")
    category_col = col_map.get("category")
    url_col = col_map.get("url")

    if not title_col:
        return {"error": f"No title column found. Available: {list(rows[0].keys())}"}

    # Collect existing category names for cross-reference
    existing_categories = set()
    if category_col:
        for row in rows:
            cat = row.get(category_col, "").strip()
            if cat:
                existing_categories.add(cat.lower())

    # Group products by category
    products_by_category = defaultdict(list)
    for row in rows:
        title = row.get(title_col, "").strip()
        category = row.get(category_col, "Uncategorized").strip() if category_col else "All Products"
        if title:
            products_by_category[category].append(title)

    # Extract n-grams per category
    results = {}
    total_suggestions = 0

    for category, titles in products_by_category.items():
        ngram_counter = Counter()
        ngram_examples = defaultdict(list)

        for title in titles:
            tokens = tokenize(title)
            for n in range(ngram_min, ngram_max + 1):
                grams = extract_ngrams(tokens, n)
                for gram in grams:
                    ngram_counter[gram] += 1
                    if len(ngram_examples[gram]) < 3:
                        ngram_examples[gram].append(title)

        # Filter by frequency and check against existing categories
        suggestions = []
        for ngram, count in ngram_counter.most_common():
            if count < min_frequency:
                break

            # Check if this n-gram already matches an existing category
            already_exists = any(
                ngram in cat or cat in ngram
                for cat in existing_categories
            )

            suggestions.append({
                "ngram": ngram,
                "count": count,
                "already_exists": already_exists,
                "example_titles": ngram_examples[ngram][:3],
            })

        if suggestions:
            results[category] = suggestions
            total_suggestions += len([s for s in suggestions if not s["already_exists"]])

    return {
        "mode": "discover",
        "categories": results,
        "existing_categories": sorted(existing_categories),
        "summary": {
            "total_products_analyzed": sum(len(t) for t in products_by_category.values()),
            "total_parent_categories": len(products_by_category),
            "total_suggestions": total_suggestions,
            "min_frequency": min_frequency,
            "ngram_range": f"{ngram_min}-{ngram_max}",
        },
    }


# ---------------------------------------------------------------------------
# Mode 2: Breadcrumb Relevancy
# ---------------------------------------------------------------------------

def parse_breadcrumb(breadcrumb: str) -> list[str]:
    """Parse breadcrumb string into list of segments."""
    # Handle common separators: >, /, |, >>
    for sep in [" >> ", " > ", " / ", " | ", ">>", ">", "/", "|"]:
        if sep in breadcrumb:
            parts = [p.strip() for p in breadcrumb.split(sep) if p.strip()]
            if len(parts) > 1:
                return parts
    return [breadcrumb.strip()]


def check_breadcrumbs(
    filepath: str,
    threshold: float = 0.6,
) -> dict:
    """
    Check breadcrumb relevancy by comparing product titles with their
    breadcrumb category assignment.

    Returns dict with:
      - mismatches: [{url, title, breadcrumb, deepest_category, similarity, suggested}]
      - summary: {total_checked, total_mismatches, avg_similarity}
    """
    if fuzz is None:
        return {"error": "RapidFuzz not installed. Run: pip install rapidfuzz"}

    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), BREADCRUMB_COLUMN_MAP)

    url_col = col_map.get("url")
    title_col = col_map.get("title")
    breadcrumb_col = col_map.get("breadcrumb")

    if not title_col:
        return {"error": f"No title column found. Available: {list(rows[0].keys())}"}
    if not breadcrumb_col:
        return {"error": f"No breadcrumb column found. Available: {list(rows[0].keys())}"}

    # First pass: collect all known category names from breadcrumbs
    all_categories = set()
    for row in rows:
        bc = row.get(breadcrumb_col, "").strip()
        if bc:
            segments = parse_breadcrumb(bc)
            for seg in segments:
                if seg.lower() not in {"home", "homepage", "main"}:
                    all_categories.add(seg)

    # Second pass: check each product
    mismatches = []
    similarities = []
    total_checked = 0

    for row in rows:
        title = row.get(title_col, "").strip()
        breadcrumb = row.get(breadcrumb_col, "").strip()
        url = row.get(url_col, "").strip() if url_col else ""

        if not title or not breadcrumb:
            continue

        total_checked += 1
        segments = parse_breadcrumb(breadcrumb)

        # Get deepest category (last meaningful segment)
        deepest = segments[-1] if segments else ""
        if deepest.lower() in {"home", "homepage"}:
            deepest = segments[-2] if len(segments) > 1 else deepest

        # Calculate similarity between title and deepest category
        similarity = fuzz.token_sort_ratio(title.lower(), deepest.lower()) / 100.0
        similarities.append(similarity)

        if similarity < threshold:
            # Try to find a better matching category
            best_match = ""
            best_score = 0.0
            for cat in all_categories:
                score = fuzz.token_sort_ratio(title.lower(), cat.lower()) / 100.0
                if score > best_score and score > similarity:
                    best_score = score
                    best_match = cat

            mismatches.append({
                "url": url,
                "title": title,
                "breadcrumb": breadcrumb,
                "deepest_category": deepest,
                "similarity": round(similarity, 3),
                "suggested_category": best_match if best_match else None,
                "suggested_similarity": round(best_score, 3) if best_match else None,
            })

    # Sort mismatches by similarity (lowest first = worst matches)
    mismatches.sort(key=lambda x: x["similarity"])

    avg_similarity = sum(similarities) / len(similarities) if similarities else 0

    return {
        "mode": "breadcrumbs",
        "mismatches": mismatches,
        "summary": {
            "total_checked": total_checked,
            "total_mismatches": len(mismatches),
            "mismatch_rate": round(len(mismatches) / total_checked * 100, 1) if total_checked else 0,
            "avg_similarity": round(avg_similarity, 3),
            "threshold": threshold,
        },
        "categories_found": sorted(all_categories),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="eCommerce Taxonomy Discovery & Breadcrumb Relevancy"
    )
    subparsers = parser.add_subparsers(dest="command", help="Mode to run")

    # Discover command
    disc = subparsers.add_parser("discover", help="Discover missing category pages")
    disc.add_argument("csv_file", help="Product CSV file path")
    disc.add_argument("--min-frequency", type=int, default=5,
                      help="Minimum n-gram frequency to report (default: 5)")
    disc.add_argument("--ngram-range", default="2-3",
                      help="N-gram range, e.g., '2-3' for bigrams and trigrams")

    # Breadcrumbs command
    bc = subparsers.add_parser("breadcrumbs", help="Check breadcrumb relevancy")
    bc.add_argument("csv_file", help="Crawl CSV with breadcrumb data")
    bc.add_argument("--threshold", type=float, default=0.6,
                    help="Similarity threshold below which products are flagged (default: 0.6)")

    args = parser.parse_args()

    if args.command == "discover":
        ngram_parts = args.ngram_range.split("-")
        ngram_min = int(ngram_parts[0])
        ngram_max = int(ngram_parts[1]) if len(ngram_parts) > 1 else ngram_min

        result = discover_categories(
            filepath=args.csv_file,
            min_frequency=args.min_frequency,
            ngram_min=ngram_min,
            ngram_max=ngram_max,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "breadcrumbs":
        result = check_breadcrumbs(
            filepath=args.csv_file,
            threshold=args.threshold,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
