"""
SF Parser — Parse Screaming Frog export CSVs into structured data.

Usage:
    python3 sf_parser.py --embeddings embeddings.csv --output parsed.npz
    python3 sf_parser.py --internal internal_html.csv --near-duplicates near_dupes.csv --output parsed.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np


def parse_embeddings_csv(filepath: str) -> tuple[list[str], np.ndarray]:
    """Parse SF embedding export CSV into URL list + numpy matrix.

    SF format: Address,Embeddings
    Where Embeddings is a JSON array like [-0.0123,0.0456,...]

    Returns:
        urls: List of URL strings
        matrix: numpy array of shape (n_pages, embedding_dim)
    """
    urls = []
    vectors = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Detect column names (SF uses various capitalizations)
        fieldnames = reader.fieldnames
        url_col = next((c for c in fieldnames if c.lower() in ("address", "url")), None)
        emb_col = next((c for c in fieldnames if c.lower() in ("embeddings", "embedding")), None)

        if not url_col or not emb_col:
            print(f"ERROR: Expected columns 'Address' and 'Embeddings', found: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            url = row[url_col].strip()
            emb_str = row[emb_col].strip()

            if not emb_str or emb_str == "[]":
                continue

            try:
                vector = json.loads(emb_str)
                urls.append(url)
                vectors.append(vector)
            except json.JSONDecodeError:
                print(f"WARN: Could not parse embedding for {url}, skipping", file=sys.stderr)

    if not vectors:
        print("ERROR: No valid embeddings found in file", file=sys.stderr)
        sys.exit(1)

    matrix = np.array(vectors, dtype=np.float32)
    print(f"Parsed {len(urls)} page embeddings, dimension={matrix.shape[1]}", file=sys.stderr)
    return urls, matrix


def parse_internal_html_csv(filepath: str) -> list[dict]:
    """Parse SF Internal:HTML export for page metadata.

    Returns list of dicts with: url, title, h1, meta_description, word_count
    """
    pages = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [c.lower() for c in reader.fieldnames]

        # Map SF column names to our keys
        col_map = {}
        for fn in reader.fieldnames:
            fl = fn.lower()
            if fl in ("address", "url"):
                col_map["url"] = fn
            elif fl in ("title 1", "title"):
                col_map["title"] = fn
            elif fl in ("h1-1", "h1"):
                col_map["h1"] = fn
            elif fl in ("meta description 1", "meta description"):
                col_map["meta"] = fn
            elif fl in ("word count", "wordcount"):
                col_map["word_count"] = fn

        for row in reader:
            page = {
                "url": row.get(col_map.get("url", ""), "").strip(),
                "title": row.get(col_map.get("title", ""), "").strip(),
                "h1": row.get(col_map.get("h1", ""), "").strip(),
                "meta_description": row.get(col_map.get("meta", ""), "").strip(),
                "word_count": int(row.get(col_map.get("word_count", ""), "0") or 0),
            }
            if page["url"]:
                pages.append(page)

    print(f"Parsed {len(pages)} pages from Internal:HTML export", file=sys.stderr)
    return pages


def parse_near_duplicates_csv(filepath: str) -> list[dict]:
    """Parse SF Near Duplicates export.

    Returns list of dicts with: url, closest_match, similarity_pct, hash
    """
    results = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # SF uses various column names across versions
            url = ""
            closest = ""
            sim = 0.0
            hash_val = ""

            for key, val in row.items():
                kl = key.lower()
                if kl in ("address", "url"):
                    url = val.strip()
                elif "closest" in kl and "match" in kl:
                    closest = val.strip()
                elif "similarity" in kl:
                    try:
                        sim = float(val.strip().rstrip("%"))
                    except (ValueError, AttributeError):
                        sim = 0.0
                elif kl == "hash":
                    hash_val = val.strip()

            if url:
                results.append({
                    "url": url,
                    "closest_match": closest,
                    "similarity_pct": sim,
                    "hash": hash_val,
                })

    print(f"Parsed {len(results)} near-duplicate entries", file=sys.stderr)
    return results


def parse_semantic_similar_csv(filepath: str) -> list[dict]:
    """Parse SF Semantically Similar export (v22+).

    Returns list of dicts with: url, closest_semantic_match, semantic_score, count_similar
    """
    results = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            url = ""
            closest = ""
            score = 0.0
            count = 0

            for key, val in row.items():
                kl = key.lower()
                if kl in ("address", "url"):
                    url = val.strip()
                elif "closest" in kl and "semantic" in kl:
                    closest = val.strip()
                elif "semantic" in kl and "score" in kl:
                    try:
                        score = float(val.strip())
                    except (ValueError, AttributeError):
                        score = 0.0
                elif "no." in kl and "semantic" in kl:
                    try:
                        count = int(val.strip())
                    except (ValueError, AttributeError):
                        count = 0

            if url:
                results.append({
                    "url": url,
                    "closest_semantic_match": closest,
                    "semantic_score": score,
                    "count_similar": count,
                })

    print(f"Parsed {len(results)} semantic similarity entries", file=sys.stderr)
    return results


def parse_gsc_csv(filepath: str) -> list[dict]:
    """Parse Google Search Console performance export.

    Handles both the simple format (queries only) and the full format (queries + pages).
    """
    results = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            entry = {}
            for key, val in row.items():
                kl = key.lower().strip()
                if kl in ("top queries", "query", "queries", "keyword"):
                    entry["query"] = val.strip()
                elif kl in ("page", "url", "pages"):
                    entry["page"] = val.strip()
                elif kl == "clicks":
                    try:
                        entry["clicks"] = int(val.strip().replace(",", ""))
                    except (ValueError, AttributeError):
                        entry["clicks"] = 0
                elif kl == "impressions":
                    try:
                        entry["impressions"] = int(val.strip().replace(",", ""))
                    except (ValueError, AttributeError):
                        entry["impressions"] = 0
                elif kl == "ctr":
                    try:
                        entry["ctr"] = float(val.strip().rstrip("%")) / 100
                    except (ValueError, AttributeError):
                        entry["ctr"] = 0.0
                elif kl == "position":
                    try:
                        entry["position"] = float(val.strip())
                    except (ValueError, AttributeError):
                        entry["position"] = 0.0

            if "query" in entry:
                results.append(entry)

    print(f"Parsed {len(results)} GSC entries", file=sys.stderr)
    return results


def main():
    parser = argparse.ArgumentParser(description="Parse Screaming Frog and GSC exports")
    parser.add_argument("--embeddings", help="SF embedding export CSV")
    parser.add_argument("--internal", help="SF Internal:HTML export CSV")
    parser.add_argument("--near-duplicates", help="SF Near Duplicates export CSV")
    parser.add_argument("--semantic-similar", help="SF Semantically Similar export CSV")
    parser.add_argument("--exact-duplicates", help="SF Exact Duplicates export CSV")
    parser.add_argument("--gsc", help="Google Search Console export CSV")
    parser.add_argument("--output", required=True, help="Output file (.npz for embeddings, .json for metadata)")
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.embeddings:
        urls, matrix = parse_embeddings_csv(args.embeddings)
        np.savez_compressed(
            output_path,
            urls=np.array(urls),
            embeddings=matrix,
        )
        print(f"Saved embeddings to {output_path} ({matrix.shape})", file=sys.stderr)

    else:
        data = {}

        if args.internal:
            data["pages"] = parse_internal_html_csv(args.internal)

        if args.near_duplicates:
            data["near_duplicates"] = parse_near_duplicates_csv(args.near_duplicates)

        if args.semantic_similar:
            data["semantic_similar"] = parse_semantic_similar_csv(args.semantic_similar)

        if args.gsc:
            data["gsc"] = parse_gsc_csv(args.gsc)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved parsed data to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
