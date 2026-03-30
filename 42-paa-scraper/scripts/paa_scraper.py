#!/usr/bin/env python3
"""
PAA Scraper — Recursively scrape People Also Ask questions and Related Searches.

Builds a hierarchical question tree from Google SERPs using DataForSEO API.
Supports recursive depth up to 5 levels with deduplication across branches.

Usage:
    python paa_scraper.py "best crm software" --depth 3 --related
    python paa_scraper.py keywords.csv --depth 2
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from base64 import b64encode
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests package not installed. Run: pip install requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class PAANode:
    """A node in the PAA/Related Searches tree."""

    def __init__(self, question: str, depth: int, parent: Optional[str] = None,
                 seed_keyword: Optional[str] = None):
        self.question = question
        self.depth = depth
        self.parent = parent
        self.seed_keyword = seed_keyword
        self.children: list["PAANode"] = []
        self.is_duplicate = False

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "depth": self.depth,
            "parent": self.parent,
            "seed_keyword": self.seed_keyword,
            "is_duplicate": self.is_duplicate,
            "children": [c.to_dict() for c in self.children],
        }


# ---------------------------------------------------------------------------
# Normalization & deduplication
# ---------------------------------------------------------------------------

def normalize_question(q: str) -> str:
    """Normalize a question for dedup: lowercase, strip punctuation, collapse spaces."""
    q = q.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------

class DataForSEOClient:
    """Client for DataForSEO SERP API."""

    BASE_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    def __init__(self, login: str, password: str):
        self.auth = b64encode(f"{login}:{password}".encode()).decode()

    def fetch_serp(self, keyword: str, location: str = "United States",
                   language: str = "en") -> dict:
        headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json",
        }
        payload = [
            {
                "keyword": keyword,
                "location_name": location,
                "language_code": language,
                "device": "desktop",
                "os": "windows",
            }
        ]
        resp = requests.post(self.BASE_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def extract_paa(self, data: dict) -> list[str]:
        """Extract PAA questions from DataForSEO response."""
        questions = []
        try:
            tasks = data.get("tasks", [])
            for task in tasks:
                results = task.get("result", [])
                for result in results:
                    items = result.get("items", [])
                    for item in items:
                        if item.get("type") == "people_also_ask":
                            for paa_item in item.get("items", []):
                                q = paa_item.get("title", "").strip()
                                if q:
                                    questions.append(q)
        except (KeyError, TypeError):
            pass
        return questions

    def extract_related(self, data: dict) -> list[str]:
        """Extract Related Searches from DataForSEO response."""
        searches = []
        try:
            tasks = data.get("tasks", [])
            for task in tasks:
                results = task.get("result", [])
                for result in results:
                    items = result.get("items", [])
                    for item in items:
                        if item.get("type") == "related_searches":
                            for rs_item in item.get("items", []):
                                q = rs_item.get("title", "").strip()
                                if q:
                                    searches.append(q)
        except (KeyError, TypeError):
            pass
        return searches




# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------

class PAATreeBuilder:
    """Recursively builds a PAA question tree with deduplication."""

    def __init__(self, client, max_depth: int = 3, delay: float = 1.0,
                 include_related: bool = False, location: str = "United States",
                 language: str = "en"):
        self.client = client
        self.max_depth = max_depth
        self.delay = delay
        self.include_related = include_related
        self.location = location
        self.language = language
        self.seen: set[str] = set()
        self.api_calls = 0

    def build(self, seed_keyword: str) -> tuple[PAANode, Optional[PAANode]]:
        """Build PAA tree (and optionally Related Searches tree) for a seed keyword.

        Returns:
            Tuple of (paa_root, related_root). related_root is None if --related is off.
        """
        paa_root = PAANode(seed_keyword, depth=0, seed_keyword=seed_keyword)
        related_root = None

        # Fetch initial SERP
        data = self._fetch(seed_keyword)
        self.api_calls += 1

        # Build PAA tree
        paa_questions = self.client.extract_paa(data)
        for q in paa_questions:
            norm = normalize_question(q)
            if norm not in self.seen:
                self.seen.add(norm)
                child = PAANode(q, depth=1, parent=seed_keyword,
                                seed_keyword=seed_keyword)
                paa_root.children.append(child)
                if self.max_depth > 1:
                    self._expand_paa(child)
            else:
                dup = PAANode(q, depth=1, parent=seed_keyword,
                              seed_keyword=seed_keyword)
                dup.is_duplicate = True
                paa_root.children.append(dup)

        # Build Related Searches tree
        if self.include_related:
            related_root = PAANode(seed_keyword, depth=0, seed_keyword=seed_keyword)
            related_searches = self.client.extract_related(data)
            for rs in related_searches:
                norm = normalize_question(rs)
                if norm not in self.seen:
                    self.seen.add(norm)
                    child = PAANode(rs, depth=1, parent=seed_keyword,
                                    seed_keyword=seed_keyword)
                    related_root.children.append(child)
                    if self.max_depth > 1:
                        self._expand_related(child)

        return paa_root, related_root

    def _fetch(self, keyword: str) -> dict:
        """Fetch SERP with rate limiting."""
        time.sleep(self.delay)
        return self.client.fetch_serp(keyword, self.location, self.language)

    def _expand_paa(self, node: PAANode):
        """Recursively expand a PAA node."""
        if node.depth >= self.max_depth:
            return

        data = self._fetch(node.question)
        self.api_calls += 1
        questions = self.client.extract_paa(data)

        for q in questions:
            norm = normalize_question(q)
            if norm not in self.seen:
                self.seen.add(norm)
                child = PAANode(q, depth=node.depth + 1, parent=node.question,
                                seed_keyword=node.seed_keyword)
                node.children.append(child)
                self._expand_paa(child)
            else:
                dup = PAANode(q, depth=node.depth + 1, parent=node.question,
                              seed_keyword=node.seed_keyword)
                dup.is_duplicate = True
                node.children.append(dup)

    def _expand_related(self, node: PAANode):
        """Recursively expand a Related Searches node."""
        if node.depth >= self.max_depth:
            return

        data = self._fetch(node.question)
        self.api_calls += 1
        searches = self.client.extract_related(data)

        for rs in searches:
            norm = normalize_question(rs)
            if norm not in self.seen:
                self.seen.add(norm)
                child = PAANode(rs, depth=node.depth + 1, parent=node.question,
                                seed_keyword=node.seed_keyword)
                node.children.append(child)
                self._expand_related(child)


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def tree_to_markdown(node: PAANode, indent: int = 0) -> str:
    """Convert a tree to indented Markdown list."""
    lines = []
    prefix = "  " * indent
    label = node.question
    if node.is_duplicate:
        label += " [seen]"
    if indent == 0:
        # Root node is the seed keyword, skip it
        for child in node.children:
            lines.append(tree_to_markdown(child, indent=0))
    else:
        lines.append(f"{prefix}- **{label}**" if indent == 1 else f"{prefix}- {label}")
        for child in node.children:
            lines.append(tree_to_markdown(child, indent=indent + 1))
    return "\n".join(lines)


def flatten_tree(node: PAANode) -> list[dict]:
    """Flatten tree to a list of dicts for CSV export."""
    results = []
    if node.depth > 0 and not node.is_duplicate:
        results.append({
            "question": node.question,
            "depth": node.depth,
            "parent": node.parent or "",
            "seed_keyword": node.seed_keyword or "",
        })
    for child in node.children:
        results.extend(flatten_tree(child))
    return results


def generate_report(seed_keyword: str, paa_root: PAANode,
                    related_root: Optional[PAANode], api_calls: int,
                    depth: int) -> str:
    """Generate the full PAA-TREE.md report."""
    flat_paa = flatten_tree(paa_root)
    flat_related = flatten_tree(related_root) if related_root else []
    total_unique = len(flat_paa) + len(flat_related)

    lines = [
        f"# PAA Tree: {seed_keyword}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Depth:** {depth}",
        f"**Total unique questions:** {total_unique}",
        f"**API calls made:** {api_calls}",
        "",
        "---",
        "",
        "## Hierarchical Question Tree",
        "",
        tree_to_markdown(paa_root),
        "",
    ]

    if related_root and related_root.children:
        lines.extend([
            "---",
            "",
            "## Related Searches Tree",
            "",
            tree_to_markdown(related_root),
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Flat Question List (for content planning)",
        "",
    ])
    for i, item in enumerate(flat_paa, 1):
        lines.append(f"{i}. {item['question']}")

    if flat_related:
        lines.extend([
            "",
            "## Flat Related Searches List",
            "",
        ])
        for i, item in enumerate(flat_related, 1):
            lines.append(f"{i}. {item['question']}")

    lines.extend([
        "",
        "---",
        "",
        "## Export",
        "",
        "CSV exported to: `paa-export.csv`",
    ])

    return "\n".join(lines)


def export_csv(flat_items: list[dict], output_path: str):
    """Export flat question list to CSV."""
    if not flat_items:
        return
    fieldnames = ["question", "depth", "parent", "seed_keyword"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_items)


def export_json(paa_root: PAANode, related_root: Optional[PAANode],
                output_path: str):
    """Export full tree structure as JSON."""
    data = {
        "paa_tree": paa_root.to_dict(),
        "related_tree": related_root.to_dict() if related_root else None,
        "generated": datetime.now().isoformat(),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def load_keywords(input_val: str) -> list[str]:
    """Load keywords from a string or CSV file path."""
    if os.path.isfile(input_val):
        keywords = []
        with open(input_val, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header and "keyword" in [h.lower().strip() for h in header]:
                idx = [h.lower().strip() for h in header].index("keyword")
                for row in reader:
                    if row and len(row) > idx and row[idx].strip():
                        keywords.append(row[idx].strip())
            else:
                # Single-column CSV or no header
                if header and header[0].strip():
                    keywords.append(header[0].strip())
                for row in reader:
                    if row and row[0].strip():
                        keywords.append(row[0].strip())
        return keywords
    else:
        return [input_val.strip()]


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def get_client(provider: str):
    """Create and return the appropriate API client."""
    if provider == "dataforseo":
        login = os.environ.get("DATAFORSEO_LOGIN")
        password = os.environ.get("DATAFORSEO_PASSWORD")
        if not login or not password:
            print("ERROR: Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD environment variables.")
            sys.exit(1)
        return DataForSEOClient(login, password)
    else:
        print(f"ERROR: Unknown provider '{provider}'. Use 'dataforseo'.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Recursively scrape People Also Ask questions from Google SERPs."
    )
    parser.add_argument("keyword", help="Seed keyword or path to CSV file")
    parser.add_argument("--depth", type=int, default=3, choices=range(1, 6),
                        help="Max recursion depth (1-5, default: 3)")
    parser.add_argument("--related", action="store_true",
                        help="Also build Related Searches tree")
    parser.add_argument("--provider", default="dataforseo",
                        choices=["dataforseo"],
                        help="SERP API provider (default: dataforseo)")
    parser.add_argument("--location", default="United States",
                        help="Geographic location for SERP results")
    parser.add_argument("--language", default="en",
                        help="Language code for SERP results")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between API requests (default: 1.0)")
    parser.add_argument("--output", default="PAA-TREE.md",
                        help="Output filename (default: PAA-TREE.md)")
    args = parser.parse_args()

    # Load keywords
    keywords = load_keywords(args.keyword)
    if not keywords:
        print("ERROR: No keywords found.")
        sys.exit(1)

    print(f"Seeds: {len(keywords)} keyword(s)")
    print(f"Depth: {args.depth}")
    print(f"Provider: {args.provider}")
    print(f"Related searches: {'yes' if args.related else 'no'}")
    print(f"Delay: {args.delay}s between requests")
    print()

    # Create client
    client = get_client(args.provider)

    # Process each keyword
    all_paa_flat = []
    all_related_flat = []
    all_reports = []
    total_api_calls = 0

    for kw in keywords:
        print(f"Processing: {kw}")
        builder = PAATreeBuilder(
            client=client,
            max_depth=args.depth,
            delay=args.delay,
            include_related=args.related,
            location=args.location,
            language=args.language,
        )
        paa_root, related_root = builder.build(kw)
        total_api_calls += builder.api_calls

        flat_paa = flatten_tree(paa_root)
        flat_related = flatten_tree(related_root) if related_root else []
        all_paa_flat.extend(flat_paa)
        all_related_flat.extend(flat_related)

        report = generate_report(kw, paa_root, related_root, builder.api_calls,
                                 args.depth)
        all_reports.append(report)

        # Export JSON per keyword
        json_path = f"paa-tree-{re.sub(r'[^a-z0-9]+', '-', kw.lower()).strip('-')}.json"
        export_json(paa_root, related_root, json_path)
        print(f"  Questions found: {len(flat_paa)}")
        print(f"  Related searches found: {len(flat_related)}")
        print(f"  API calls: {builder.api_calls}")
        print(f"  JSON: {json_path}")
        print()

    # Write combined Markdown report
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(all_reports))
    print(f"Report written to: {args.output}")

    # Write combined CSV
    csv_path = "paa-export.csv"
    all_flat = all_paa_flat + all_related_flat
    export_csv(all_flat, csv_path)
    print(f"CSV exported to: {csv_path}")

    # Summary
    print(f"\nTotal API calls: {total_api_calls}")
    print(f"Total unique PAA questions: {len(all_paa_flat)}")
    print(f"Total unique related searches: {len(all_related_flat)}")


if __name__ == "__main__":
    main()
