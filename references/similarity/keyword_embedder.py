"""
Keyword Embedder — Generate embeddings for keywords using the same provider as SF.

IMPORTANT: The provider and model MUST match what Screaming Frog used for its
page embeddings. Mixing embedding models produces incompatible vectors.

Usage:
    python3 keyword_embedder.py --keywords gsc.csv --provider openai --model text-embedding-3-small --output kw.npz
    python3 keyword_embedder.py --keywords keywords.csv --provider gemini --output kw.npz
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


def load_keywords_from_csv(filepath: str) -> list[str]:
    """Extract unique keywords from a CSV file.

    Supports GSC format (Top queries column) and custom format (keyword column).
    """
    keywords = set()

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            for key, val in row.items():
                if key.lower().strip() in ("top queries", "query", "queries", "keyword", "keywords"):
                    kw = val.strip()
                    if kw:
                        keywords.add(kw)

    result = sorted(keywords)
    print(f"Loaded {len(result)} unique keywords from {filepath}", file=sys.stderr)
    return result


def embed_gemini(texts: list[str], model: str = "text-embedding-004") -> np.ndarray:
    """Generate embeddings via Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: google-generativeai package not installed. Run: pip install google-generativeai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    all_embeddings = []
    batch_size = 100  # Gemini batch limit

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"  Embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1} ({len(batch)} items)...", file=sys.stderr)

        result = genai.embed_content(model=f"models/{model}", content=batch)
        all_embeddings.extend(result["embedding"])

        if i + batch_size < len(texts):
            time.sleep(0.5)

    return np.array(all_embeddings, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for keywords via Gemini")
    parser.add_argument("--keywords", required=True, help="CSV file with keywords (GSC export or custom)")
    parser.add_argument("--model", default="text-embedding-004", help="Gemini model (default: text-embedding-004)")
    parser.add_argument("--output", required=True, help="Output file (.npz)")
    args = parser.parse_args()

    keywords = load_keywords_from_csv(args.keywords)
    if not keywords:
        print("ERROR: No keywords found in CSV", file=sys.stderr)
        sys.exit(1)

    print(f"Embedding {len(keywords)} keywords with gemini/{args.model}...", file=sys.stderr)
    matrix = embed_gemini(keywords, model=args.model)

    np.savez_compressed(
        args.output,
        keywords=np.array(keywords),
        embeddings=matrix,
    )

    print(f"Saved {len(keywords)} keyword embeddings to {args.output} (dim={matrix.shape[1]})", file=sys.stderr)


if __name__ == "__main__":
    main()
