#!/usr/bin/env python3
"""
Readability Scorer — Bulk readability analysis across an entire site.

Calculates 5 readability metrics per page:
  1. Flesch Reading Ease
  2. Flesch-Kincaid Grade Level
  3. Gunning Fog Index
  4. SMOG Index
  5. Reading Time (words / 238 WPM)

Input: Screaming Frog "All Page Text" export directory or sitemap URL.
Output: JSON with per-page and site-wide metrics, plus Markdown report.

Usage:
    python readability_scorer.py /path/to/sf-export/ --audience b2b --min-words 100
    python readability_scorer.py https://example.com/sitemap.xml --limit 200 --audience b2c
"""

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
import time
from datetime import datetime
from typing import Optional
from urllib.parse import unquote

try:
    import textstat
except ImportError:
    print("ERROR: textstat package not installed. Run: pip install textstat")
    sys.exit(1)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

READING_SPEED_WPM = 238  # Average adult reading speed

AUDIENCE_THRESHOLDS = {
    "b2c": {"target_min": 6, "target_max": 8, "hard_flag": 10, "easy_flag": 4},
    "b2b": {"target_min": 8, "target_max": 12, "hard_flag": 14, "easy_flag": 6},
    "academic": {"target_min": 12, "target_max": 16, "hard_flag": 18, "easy_flag": 10},
}


# ---------------------------------------------------------------------------
# Text loading
# ---------------------------------------------------------------------------

def load_from_sf_export(directory: str, min_words: int) -> list[dict]:
    """Load text from Screaming Frog 'All Page Text' export directory.

    Each .txt file in the directory represents one page.
    Filename is typically the URL-encoded page path.
    """
    pages = []
    skipped = 0

    if not os.path.isdir(directory):
        print(f"ERROR: Directory not found: {directory}")
        sys.exit(1)

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()

        # Derive URL from filename
        url_slug = filename.replace(".txt", "")
        url = unquote(url_slug)

        word_count = len(text.split())
        if word_count < min_words:
            skipped += 1
            continue

        pages.append({
            "url": url,
            "text": text,
            "word_count": word_count,
            "source_file": filename,
        })

    print(f"Loaded {len(pages)} pages from SF export ({skipped} skipped, < {min_words} words)")
    return pages


def load_from_sitemap(sitemap_url: str, limit: int, min_words: int,
                      delay: float) -> list[dict]:
    """Fetch pages from a sitemap URL and extract text."""
    if requests is None or BeautifulSoup is None:
        print("ERROR: requests and beautifulsoup4 required for sitemap mode.")
        print("Run: pip install requests beautifulsoup4 lxml")
        sys.exit(1)

    # Fetch sitemap
    print(f"Fetching sitemap: {sitemap_url}")
    resp = requests.get(sitemap_url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "lxml-xml")
    urls = [loc.text.strip() for loc in soup.find_all("loc")]

    if not urls:
        # Try HTML parser as fallback
        soup = BeautifulSoup(resp.content, "html.parser")
        urls = [loc.text.strip() for loc in soup.find_all("loc")]

    print(f"Found {len(urls)} URLs in sitemap")
    if limit and len(urls) > limit:
        urls = urls[:limit]
        print(f"Limited to {limit} URLs")

    pages = []
    skipped = 0

    for i, url in enumerate(urls):
        try:
            time.sleep(delay)
            print(f"  [{i + 1}/{len(urls)}] Fetching: {url}")
            page_resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ReadabilityScorer/1.0)"
            })
            page_resp.raise_for_status()

            page_soup = BeautifulSoup(page_resp.text, "html.parser")

            # Remove non-content elements
            for tag in page_soup(["script", "style", "nav", "header", "footer",
                                   "aside", "noscript", "iframe"]):
                tag.decompose()

            # Try to find main content
            main = (page_soup.find("main")
                    or page_soup.find("article")
                    or page_soup.find("div", {"role": "main"})
                    or page_soup.find("div", class_=re.compile(r"content|post|entry|article"))
                    or page_soup.body
                    or page_soup)

            text = main.get_text(separator=" ", strip=True)
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            word_count = len(text.split())
            if word_count < min_words:
                skipped += 1
                continue

            pages.append({
                "url": url,
                "text": text,
                "word_count": word_count,
            })

        except Exception as e:
            print(f"    Error fetching {url}: {e}")
            skipped += 1

    print(f"Loaded {len(pages)} pages from sitemap ({skipped} skipped)")
    return pages


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_page(page: dict) -> dict:
    """Calculate all 5 readability metrics for a single page."""
    text = page["text"]

    fre = textstat.flesch_reading_ease(text)
    fkgl = textstat.flesch_kincaid_grade(text)
    fog = textstat.gunning_fog(text)
    smog = textstat.smog_index(text)
    reading_time = round(page["word_count"] / READING_SPEED_WPM, 1)

    return {
        "url": page["url"],
        "word_count": page["word_count"],
        "flesch_reading_ease": round(fre, 1),
        "flesch_kincaid_grade": round(fkgl, 1),
        "gunning_fog": round(fog, 1),
        "smog_index": round(smog, 1),
        "reading_time_min": reading_time,
    }


def aggregate_stats(scores: list[dict]) -> dict:
    """Calculate site-wide aggregate statistics."""
    metrics = ["flesch_reading_ease", "flesch_kincaid_grade", "gunning_fog",
               "smog_index", "reading_time_min"]
    agg = {}

    for metric in metrics:
        values = [s[metric] for s in scores if s[metric] is not None]
        if not values:
            agg[metric] = {"mean": 0, "median": 0, "stdev": 0,
                           "p10": 0, "p90": 0, "min": 0, "max": 0}
            continue

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        p10_idx = max(0, int(n * 0.1))
        p90_idx = min(n - 1, int(n * 0.9))

        agg[metric] = {
            "mean": round(statistics.mean(values), 1),
            "median": round(statistics.median(values), 1),
            "stdev": round(statistics.stdev(values), 1) if len(values) > 1 else 0,
            "p10": round(sorted_vals[p10_idx], 1),
            "p90": round(sorted_vals[p90_idx], 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
        }

    return agg


def classify_pages(scores: list[dict], audience: str) -> dict:
    """Classify pages as OK, TOO HARD, or TOO EASY based on audience thresholds."""
    thresholds = AUDIENCE_THRESHOLDS[audience]
    classified = {"ok": [], "too_hard": [], "too_easy": []}

    for s in scores:
        fkgl = s["flesch_kincaid_grade"]
        if fkgl > thresholds["hard_flag"]:
            s["status"] = "HARD"
            classified["too_hard"].append(s)
        elif fkgl < thresholds["easy_flag"]:
            s["status"] = "EASY"
            classified["too_easy"].append(s)
        else:
            s["status"] = "OK"
            classified["ok"].append(s)

    return classified


def grade_distribution(scores: list[dict]) -> list[dict]:
    """Count pages in each grade level band."""
    bands = [
        ("Grade 1-4", 0, 4.99),
        ("Grade 5-6", 5, 6.99),
        ("Grade 7-8", 7, 8.99),
        ("Grade 9-10", 9, 10.99),
        ("Grade 11-12", 11, 12.99),
        ("Grade 13+", 13, 99),
    ]
    total = len(scores)
    distribution = []

    for label, low, high in bands:
        count = sum(1 for s in scores if low <= s["flesch_kincaid_grade"] <= high)
        pct = round(count / total * 100) if total > 0 else 0
        distribution.append({"band": label, "count": count, "pct": pct})

    return distribution


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_markdown_report(scores: list[dict], agg: dict, classified: dict,
                             distribution: list[dict], source: str,
                             audience: str, skipped_count: int) -> str:
    """Generate the READABILITY-REPORT.md content."""
    thresholds = AUDIENCE_THRESHOLDS[audience]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Readability Report",
        "",
        f"**Source:** {source}",
        f"**Pages analyzed:** {len(scores)}",
        f"**Pages skipped (below min words):** {skipped_count}",
        f"**Target audience:** {audience.upper()}",
        f"**Target grade level:** {thresholds['target_min']}-{thresholds['target_max']}",
        f"**Generated:** {now}",
        "",
        "---",
        "",
        "## Site-Wide Summary",
        "",
        "| Metric | Mean | Median | P10 | P90 | Min | Max |",
        "|--------|------|--------|-----|-----|-----|-----|",
    ]

    metric_labels = {
        "flesch_reading_ease": "Flesch Reading Ease",
        "flesch_kincaid_grade": "Flesch-Kincaid Grade",
        "gunning_fog": "Gunning Fog Index",
        "smog_index": "SMOG Index",
        "reading_time_min": "Reading Time (min)",
    }
    for metric, label in metric_labels.items():
        a = agg[metric]
        lines.append(
            f"| {label} | {a['mean']} | {a['median']} | {a['p10']} | {a['p90']} | {a['min']} | {a['max']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Grade Level Distribution",
        "",
        "| Grade Level | Pages | % |",
        "|-------------|-------|---|",
    ])
    for d in distribution:
        lines.append(f"| {d['band']} | {d['count']} | {d['pct']}% |")

    # Outliers: Too Hard
    lines.extend([
        "",
        "---",
        "",
        f"## Outliers: Too Hard (> Grade {thresholds['hard_flag']})",
        "",
    ])
    if classified["too_hard"]:
        lines.extend([
            "| URL | FKGL | FRE | Fog | SMOG | Words | Read Time |",
            "|-----|------|-----|-----|------|-------|-----------|",
        ])
        for s in sorted(classified["too_hard"],
                        key=lambda x: x["flesch_kincaid_grade"], reverse=True):
            lines.append(
                f"| {s['url']} | {s['flesch_kincaid_grade']} | {s['flesch_reading_ease']} | "
                f"{s['gunning_fog']} | {s['smog_index']} | {s['word_count']:,} | "
                f"{s['reading_time_min']} min |"
            )
    else:
        lines.append("No pages flagged as too hard.")

    # Outliers: Too Easy
    lines.extend([
        "",
        f"## Outliers: Too Easy (< Grade {thresholds['easy_flag']})",
        "",
    ])
    if classified["too_easy"]:
        lines.extend([
            "| URL | FKGL | FRE | Fog | SMOG | Words | Read Time |",
            "|-----|------|-----|-----|------|-------|-----------|",
        ])
        for s in sorted(classified["too_easy"],
                        key=lambda x: x["flesch_kincaid_grade"]):
            lines.append(
                f"| {s['url']} | {s['flesch_kincaid_grade']} | {s['flesch_reading_ease']} | "
                f"{s['gunning_fog']} | {s['smog_index']} | {s['word_count']:,} | "
                f"{s['reading_time_min']} min |"
            )
    else:
        lines.append("No pages flagged as too easy.")

    # Per-page scores
    lines.extend([
        "",
        "---",
        "",
        "## Per-Page Scores",
        "",
        "| URL | Words | FRE | FKGL | Fog | SMOG | Read Time | Status |",
        "|-----|-------|-----|------|-----|------|-----------|--------|",
    ])
    for s in sorted(scores, key=lambda x: x["flesch_kincaid_grade"], reverse=True):
        lines.append(
            f"| {s['url']} | {s['word_count']:,} | {s['flesch_reading_ease']} | "
            f"{s['flesch_kincaid_grade']} | {s['gunning_fog']} | {s['smog_index']} | "
            f"{s['reading_time_min']} min | {s.get('status', 'OK')} |"
        )

    # Recommendations
    mean_grade = agg["flesch_kincaid_grade"]["mean"]
    target_min = thresholds["target_min"]
    target_max = thresholds["target_max"]

    if target_min <= mean_grade <= target_max:
        grade_assessment = "within"
    elif mean_grade > target_max:
        grade_assessment = "above"
    else:
        grade_assessment = "below"

    hard_count = len(classified["too_hard"])
    easy_count = len(classified["too_easy"])
    long_pages = sum(1 for s in scores if s["reading_time_min"] > 8)
    long_pct = round(long_pages / len(scores) * 100) if scores else 0

    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        "",
        f"1. **Site average ({mean_grade}) is {grade_assessment} the target range "
        f"(grade {target_min}-{target_max}) for {audience.upper()} audience.**",
        f"2. **{hard_count} page(s) flagged as too hard** -- consider simplifying sentence "
        f"structure, replacing jargon with plain language, breaking long sentences.",
        f"3. **{easy_count} page(s) flagged as too easy** -- may lack depth for the target "
        f"audience; consider adding more substantive analysis.",
        f"4. **Reading time distribution:** {long_pct}% of pages exceed 8 minutes -- "
        f"consider adding summaries, tables of contents, or TL;DR sections for long content.",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def export_json(scores: list[dict], agg: dict, classified: dict,
                distribution: list[dict], output_path: str):
    """Export all data as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "page_count": len(scores),
        "aggregate": agg,
        "distribution": distribution,
        "outliers": {
            "too_hard": [s["url"] for s in classified["too_hard"]],
            "too_easy": [s["url"] for s in classified["too_easy"]],
        },
        "pages": scores,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bulk readability scoring for SEO content analysis."
    )
    parser.add_argument("source",
                        help="Path to SF text export directory or sitemap URL")
    parser.add_argument("--min-words", type=int, default=100,
                        help="Minimum word count to include a page (default: 100)")
    parser.add_argument("--limit", type=int, default=500,
                        help="Max pages to process from sitemap (default: 500)")
    parser.add_argument("--audience", default="b2c",
                        choices=["b2c", "b2b", "academic"],
                        help="Target audience for threshold scoring (default: b2c)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between requests for sitemap mode (default: 1.0)")
    parser.add_argument("--output", default="READABILITY-REPORT.md",
                        help="Output filename (default: READABILITY-REPORT.md)")

    args = parser.parse_args()

    # Determine input mode
    is_sitemap = args.source.startswith("http://") or args.source.startswith("https://")

    if is_sitemap:
        if requests is None:
            print("ERROR: requests and beautifulsoup4 required for sitemap mode.")
            print("Run: pip install requests beautifulsoup4 lxml")
            sys.exit(1)
        pages = load_from_sitemap(args.source, args.limit, args.min_words, args.delay)
        source_label = args.source
    else:
        pages = load_from_sf_export(args.source, args.min_words)
        source_label = os.path.abspath(args.source)

    if not pages:
        print("ERROR: No pages to analyze.")
        sys.exit(1)

    # Score all pages
    print(f"\nScoring {len(pages)} pages...")
    scores = []
    for i, page in enumerate(pages):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  [{i + 1}/{len(pages)}] Scoring...")
        scores.append(score_page(page))

    # Aggregate
    agg = aggregate_stats(scores)
    classified = classify_pages(scores, args.audience)
    distribution = grade_distribution(scores)

    # Calculate skipped count
    total_loaded = len(pages)  # pages already filtered by min_words in load functions
    skipped_count = 0  # already reported during loading

    # Generate report
    report = generate_markdown_report(scores, agg, classified, distribution,
                                       source_label, args.audience, skipped_count)

    # Write outputs
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport written to: {args.output}")

    json_path = args.output.replace(".md", ".json")
    export_json(scores, agg, classified, distribution, json_path)
    print(f"JSON exported to: {json_path}")

    # Summary
    thresholds = AUDIENCE_THRESHOLDS[args.audience]
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Pages analyzed:  {len(scores)}")
    print(f"Audience:        {args.audience.upper()}")
    print(f"Target grade:    {thresholds['target_min']}-{thresholds['target_max']}")
    print(f"Mean FKGL:       {agg['flesch_kincaid_grade']['mean']}")
    print(f"Median FKGL:     {agg['flesch_kincaid_grade']['median']}")
    print(f"Mean FRE:        {agg['flesch_reading_ease']['mean']}")
    print(f"Too hard:        {len(classified['too_hard'])} pages")
    print(f"Too easy:        {len(classified['too_easy'])} pages")
    print(f"OK:              {len(classified['ok'])} pages")


if __name__ == "__main__":
    main()
