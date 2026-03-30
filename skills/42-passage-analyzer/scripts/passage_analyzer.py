"""
Passage Analyzer — Segment page content into passages and score AI-extractability.

Two scoring modes:
  1. Heuristic (default): 6-dimension scoring based on word patterns — no API needed
  2. Embeddings (--embeddings): real cosine similarity vs target queries — requires API

Usage:
    python3 passage_analyzer.py --text page.txt --output analysis.json
    python3 passage_analyzer.py --sf-text-dir ./sf-text-export/ --output analysis.json
    python3 passage_analyzer.py --text page.txt --embeddings --queries queries.csv --output analysis.json
    python3 passage_analyzer.py --sf-text-dir ./sf-export/ --sf-embeddings embeddings.csv --queries queries.csv --output analysis.json
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path


# --- Configuration ---

CONFIG = {
    "min_passage_words": 50,
    "max_passage_words": 250,
    "optimal_min_words": 134,
    "optimal_max_words": 167,
    "overlap_words": 30,
    "min_element_chars": 30,
}

SEMANTIC_WEIGHTS = {
    "h1": 3.0, "h2": 2.5, "h3": 2.0, "h4": 1.5, "h5": 1.2, "h6": 1.0,
    "article": 2.5, "main": 2.5, "section": 2.0, "blockquote": 1.8,
    "table": 1.5, "p": 1.0, "li": 0.8, "div": 0.6, "aside": 0.3,
    "span": 0.5, "td": 0.7, "th": 0.8,
}

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

REMOVE_SELECTORS = {
    "script", "style", "nav", "header", "footer", "aside",
    "noscript", "iframe", "svg", "form",
}

# Patterns that indicate a non-self-contained passage start
WEAK_OPENERS = re.compile(
    r"^(This|It|That|These|Those|They|He|She|However|Moreover|Furthermore|"
    r"Additionally|Also|But|And|Or|Yet|So|Thus|Hence|Therefore|"
    r"In addition|As a result|On the other hand|In contrast)\b",
    re.IGNORECASE,
)

# Data patterns (numbers, percentages, years, currency)
DATA_PATTERN = re.compile(
    r"\b\d+[\.,]?\d*\s*%|"           # percentages
    r"\$\d+|€\d+|£\d+|"             # currency
    r"\b\d{4}\b|"                    # years
    r"\b\d+[\.,]\d+\b|"             # decimal numbers
    r"\b\d+x\b|"                    # multipliers (3x, 10x)
    r"\b\d+\+\b|"                   # quantities (100+)
    r"\b(?:million|billion|thousand|hundred)\b",  # magnitude words
    re.IGNORECASE,
)

# Question words for Q&A format detection
QUESTION_PATTERN = re.compile(
    r"\b(what|how|why|when|where|who|which|can|does|is|are|should|will)\b.*\?",
    re.IGNORECASE,
)


# --- Text Processing ---

def clean_text(text: str) -> str:
    """Normalize whitespace and strip."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_sentences(text: str) -> int:
    """Count sentences using period/question/exclamation boundaries."""
    sentences = re.split(r"[.!?]+(?:\s|$)", text.strip())
    return len([s for s in sentences if len(s.strip()) > 10])


def split_at_sentence_boundary(text: str, max_words: int) -> tuple[str, str]:
    """Split text at the last sentence boundary before max_words."""
    words = text.split()
    if len(words) <= max_words:
        return text, ""

    # Find sentence boundaries within the word limit
    partial = " ".join(words[:max_words])
    last_period = max(partial.rfind(". "), partial.rfind("? "), partial.rfind("! "))

    if last_period > len(partial) * 0.3:  # Don't split too early
        return partial[:last_period + 1].strip(), partial[last_period + 2:].strip() + " " + " ".join(words[max_words:])
    else:
        # No good sentence boundary — split at word boundary
        return " ".join(words[:max_words]), " ".join(words[max_words:])


# --- Passage Segmentation ---

def segment_text_blocks(text: str) -> list[dict]:
    """Segment plain text into blocks based on heading detection.

    For SF text exports where we don't have HTML tags.
    Heuristic: short lines (<80 chars) followed by longer text = headings.
    """
    lines = text.split("\n")
    blocks = []
    current_heading = "Introduction"
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect heading-like lines
        is_heading = (
            len(line) < 80
            and not line.endswith(".")
            and not line.endswith(",")
            and len(line.split()) < 12
            and (line == line.title() or line == line.upper() or line.startswith("#"))
        )

        if is_heading and current_text:
            blocks.append({
                "section": current_heading,
                "text": clean_text(" ".join(current_text)),
                "tag": "p",
            })
            current_text = []
            current_heading = line.lstrip("#").strip()
        elif is_heading:
            current_heading = line.lstrip("#").strip()
        else:
            current_text.append(line)

    if current_text:
        blocks.append({
            "section": current_heading,
            "text": clean_text(" ".join(current_text)),
            "tag": "p",
        })

    return blocks


def create_passages(blocks: list[dict]) -> list[dict]:
    """Create passages from text blocks with heading-boundary splitting.

    Rules:
    - Each heading starts a new passage
    - Passages >max_words are split at sentence boundaries with overlap
    - Passages <min_words are merged with the next passage
    """
    raw_passages = []
    buffer_text = ""
    buffer_section = "Introduction"
    buffer_tag = "p"

    for block in blocks:
        # Heading-like content → flush buffer
        if block.get("tag") in HEADING_TAGS or block["section"] != buffer_section:
            if buffer_text.strip():
                raw_passages.append({
                    "section": buffer_section,
                    "text": buffer_text.strip(),
                    "tag": buffer_tag,
                })
            buffer_text = block["text"]
            buffer_section = block["section"]
            buffer_tag = block.get("tag", "p")
        else:
            buffer_text += " " + block["text"]

    # Flush remaining
    if buffer_text.strip():
        raw_passages.append({
            "section": buffer_section,
            "text": buffer_text.strip(),
            "tag": buffer_tag,
        })

    # Split oversized passages, merge undersized
    final_passages = []
    carry_over = ""

    for passage in raw_passages:
        text = passage["text"]

        # Prepend carry-over from previous merge
        if carry_over:
            text = carry_over + " " + text
            carry_over = ""

        words = text.split()

        if len(words) < CONFIG["min_passage_words"]:
            carry_over = text
            continue

        # Split if too long
        while len(words) > CONFIG["max_passage_words"]:
            chunk, remainder = split_at_sentence_boundary(
                " ".join(words), CONFIG["max_passage_words"]
            )
            final_passages.append({
                "section": passage["section"],
                "text": chunk,
                "tag": passage.get("tag", "p"),
            })

            # Overlap: carry last N words into next chunk
            overlap = chunk.split()[-CONFIG["overlap_words"]:]
            words = overlap + remainder.split()

        if words:
            final_passages.append({
                "section": passage["section"],
                "text": " ".join(words),
                "tag": passage.get("tag", "p"),
            })

    # Handle final carry-over
    if carry_over and final_passages:
        final_passages[-1]["text"] += " " + carry_over
    elif carry_over:
        final_passages.append({
            "section": "Continuation",
            "text": carry_over,
            "tag": "p",
        })

    # Assign IDs
    for i, p in enumerate(final_passages):
        p["id"] = f"P{i + 1:02d}"

    return final_passages


# --- Scoring ---

def score_passage(passage: dict) -> dict:
    """Score a passage on 6 dimensions (0-100 total)."""
    text = passage["text"]
    words = text.split()
    word_count = len(words)

    # 1. Length proximity (25 points)
    opt_min = CONFIG["optimal_min_words"]
    opt_max = CONFIG["optimal_max_words"]
    if opt_min <= word_count <= opt_max:
        length_score = 25
    else:
        distance = min(abs(word_count - opt_min), abs(word_count - opt_max))
        length_score = max(0, 25 - distance)

    # 2. Self-containment (20 points)
    self_score = 20
    if WEAK_OPENERS.match(text):
        self_score -= 10  # Starts with pronoun/connector → not self-contained
    first_sentence = re.split(r"[.!?]", text)[0]
    if len(first_sentence.split()) < 5:
        self_score -= 5  # Very short first sentence → likely fragment
    if not any(c in text for c in ".!?"):
        self_score -= 5  # No sentence endings → fragment

    # 3. Data density (20 points)
    data_matches = DATA_PATTERN.findall(text)
    data_score = min(20, len(data_matches) * 5)

    # 4. Structural quality (15 points)
    sent_count = count_sentences(text)
    if 2 <= sent_count <= 5:
        struct_score = 15
    elif sent_count == 1:
        struct_score = 8
    elif sent_count == 6:
        struct_score = 12
    else:
        struct_score = max(0, 15 - abs(sent_count - 4) * 2)

    # Bonus: first sentence is a claim (not a question, not a weak opener)
    if not WEAK_OPENERS.match(text) and not text.strip().startswith("?"):
        struct_score = min(15, struct_score + 2)

    # 5. Lexical diversity (10 points)
    unique_words = len(set(w.lower() for w in words))
    diversity_ratio = unique_words / max(word_count, 1)
    diversity_score = round(diversity_ratio * 10)
    # Sweet spot: 0.6-0.8
    if 0.6 <= diversity_ratio <= 0.8:
        diversity_score = min(10, diversity_score + 2)

    # 6. Question-answer format (10 points)
    section_heading = passage.get("section", "")
    qa_score = 0
    if QUESTION_PATTERN.search(section_heading):
        qa_score += 5  # Heading is a question
    if QUESTION_PATTERN.search(section_heading) and not WEAK_OPENERS.match(text):
        qa_score += 5  # And the passage directly answers it

    total = length_score + self_score + data_score + struct_score + diversity_score + qa_score
    total = max(0, min(100, total))

    return {
        "total": total,
        "length": length_score,
        "self_containment": max(0, self_score),
        "data_density": data_score,
        "structure": min(15, struct_score),
        "lexical_diversity": min(10, diversity_score),
        "qa_format": qa_score,
    }


def classify_score(score: int) -> str:
    """Classify passage score into rating."""
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "needs_work"
    elif score >= 20:
        return "poor"
    else:
        return "critical"


# --- Embedding-based Scoring ---

def load_queries(filepath: str) -> list[str]:
    """Load target queries from CSV (GSC export or custom keyword list)."""
    import csv

    queries = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, val in row.items():
                if key.lower().strip() in ("top queries", "query", "queries", "keyword", "keywords"):
                    q = val.strip()
                    if q:
                        queries.append(q)
                    break
    return list(dict.fromkeys(queries))  # deduplicate, preserve order


def embed_texts(texts: list[str], model: str = "text-embedding-004") -> "np.ndarray":
    """Embed a list of texts using Gemini. Returns numpy matrix."""
    import numpy as np
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: pip install google-generativeai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY or GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    all_emb = []
    batch_size = 100
    import time

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding batch {i // batch_size + 1} ({len(batch)} items)...", file=sys.stderr)
        result = genai.embed_content(model=f"models/{model}", content=batch)
        all_emb.extend(result["embedding"])
        if i + batch_size < len(texts):
            time.sleep(0.5)

    return np.array(all_emb, dtype=np.float32)


def cosine_similarity_matrix(A, B):
    """Cosine similarity between all rows of A and B. Returns (m, n) matrix."""
    import numpy as np
    A_norm = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-10)
    B_norm = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-10)
    return A_norm @ B_norm.T


def load_sf_embeddings(filepath: str) -> tuple[list[str], "np.ndarray"]:
    """Load pre-computed embeddings from SF embedding export CSV."""
    import csv
    import numpy as np

    urls = []
    vectors = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        url_col = next((c for c in reader.fieldnames if c.lower() in ("address", "url")), None)
        emb_col = next((c for c in reader.fieldnames if c.lower() in ("embeddings", "embedding")), None)

        if not url_col or not emb_col:
            print(f"ERROR: Expected 'Address' and 'Embeddings' columns", file=sys.stderr)
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
                continue

    return urls, np.array(vectors, dtype=np.float32)


def score_passages_with_embeddings(
    passages: list[dict],
    queries: list[str],
    model: str = "text-embedding-004",
    sf_embeddings_path: str | None = None,
) -> list[dict]:
    """Score passages using real cosine similarity against target queries.

    Two modes:
    Embeds passages and queries via Gemini text-embedding-004 (must match SF config).
    """
    import numpy as np

    passage_texts = [p["text"] for p in passages]

    # Embed passages
    print(f"Embedding {len(passage_texts)} passages via gemini/{model}...", file=sys.stderr)
    passage_matrix = embed_texts(passage_texts, model=model)

    # Embed queries
    print(f"Embedding {len(queries)} queries via gemini/{model}...", file=sys.stderr)
    query_matrix = embed_texts(queries, model=model)

    # Check dimension match
    if passage_matrix.shape[1] != query_matrix.shape[1]:
        print(f"ERROR: Dimension mismatch! Passages={passage_matrix.shape[1]}, "
              f"Queries={query_matrix.shape[1]}", file=sys.stderr)
        sys.exit(1)

    # Compute similarity: (n_passages × n_queries)
    print(f"Computing similarity ({len(passage_texts)}×{len(queries)})...", file=sys.stderr)
    sim_matrix = cosine_similarity_matrix(passage_matrix, query_matrix)

    # For each passage: top matching queries + scores
    embedding_scores = []
    for i, passage in enumerate(passages):
        query_scores = sim_matrix[i]
        top_indices = query_scores.argsort()[::-1][:5]  # top 5 queries

        top_matches = []
        for idx in top_indices:
            score = float(query_scores[idx])
            if score > 0.3:  # minimum relevance threshold
                top_matches.append({
                    "query": queries[idx],
                    "similarity": round(score, 4),
                })

        best_score = float(query_scores.max()) if len(query_scores) > 0 else 0
        avg_top3 = float(query_scores[query_scores.argsort()[::-1][:3]].mean()) if len(query_scores) >= 3 else best_score

        embedding_scores.append({
            "passage_id": passage["id"],
            "retrieval_score": round(best_score * 100, 1),  # 0-100 scale
            "avg_top3_similarity": round(avg_top3, 4),
            "best_query_match": top_matches[0] if top_matches else None,
            "top_query_matches": top_matches,
            "retrieval_rating": (
                "excellent" if best_score >= 0.80 else
                "good" if best_score >= 0.65 else
                "moderate" if best_score >= 0.50 else
                "weak" if best_score >= 0.35 else
                "no_match"
            ),
        })

    return embedding_scores


# --- Analysis ---

def analyze_page(text: str, url: str = "") -> dict:
    """Full passage analysis for a single page."""
    blocks = segment_text_blocks(text)
    passages = create_passages(blocks)

    scored_passages = []
    for passage in passages:
        words = passage["text"].split()
        scores = score_passage(passage)
        semantic_weight = SEMANTIC_WEIGHTS.get(passage.get("tag", "p"), 1.0)

        scored_passages.append({
            "id": passage["id"],
            "section": passage["section"],
            "word_count": len(words),
            "scores": scores,
            "rating": classify_score(scores["total"]),
            "semantic_weight": semantic_weight,
            "weighted_priority": round(scores["total"] * semantic_weight, 1),
            "preview": passage["text"][:200] + ("..." if len(passage["text"]) > 200 else ""),
            "text": passage["text"],
        })

    # Section-level aggregation
    sections = {}
    for p in scored_passages:
        sec = p["section"]
        if sec not in sections:
            sections[sec] = {"passages": [], "scores": []}
        sections[sec]["passages"].append(p["id"])
        sections[sec]["scores"].append(p["scores"]["total"])

    section_stats = {}
    for sec, data in sections.items():
        scores = data["scores"]
        section_stats[sec] = {
            "passage_count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 1),
            "best": max(scores),
            "worst": min(scores),
            "passage_ids": data["passages"],
        }

    # Summary stats
    all_scores = [p["scores"]["total"] for p in scored_passages]
    all_words = [p["word_count"] for p in scored_passages]
    optimal_count = sum(
        1 for w in all_words
        if CONFIG["optimal_min_words"] <= w <= CONFIG["optimal_max_words"]
    )

    summary = {
        "url": url,
        "total_passages": len(scored_passages),
        "avg_score": round(sum(all_scores) / max(len(all_scores), 1), 1),
        "avg_word_count": round(sum(all_words) / max(len(all_words), 1), 1),
        "optimal_length_count": optimal_count,
        "optimal_length_pct": round(optimal_count / max(len(all_words), 1) * 100, 1),
        "distribution": {
            "excellent": sum(1 for s in all_scores if s >= 80),
            "good": sum(1 for s in all_scores if 60 <= s < 80),
            "needs_work": sum(1 for s in all_scores if 40 <= s < 60),
            "poor": sum(1 for s in all_scores if 20 <= s < 40),
            "critical": sum(1 for s in all_scores if s < 20),
        },
    }

    # Top and bottom passages
    sorted_passages = sorted(scored_passages, key=lambda p: p["scores"]["total"], reverse=True)
    top_passages = sorted_passages[:5]
    bottom_passages = sorted_passages[-5:] if len(sorted_passages) > 5 else []

    return {
        "summary": summary,
        "sections": section_stats,
        "passages": scored_passages,
        "top_passages": [p["id"] for p in top_passages],
        "bottom_passages": [p["id"] for p in bottom_passages],
    }


def analyze_sf_text_dir(directory: str) -> list[dict]:
    """Analyze all .txt files in a Screaming Frog text export directory."""
    results = []
    txt_files = sorted(Path(directory).glob("*.txt"))

    if not txt_files:
        print(f"ERROR: No .txt files found in {directory}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(txt_files)} pages...", file=sys.stderr)

    for i, txt_file in enumerate(txt_files):
        if i % 50 == 0 and i > 0:
            print(f"  Progress: {i}/{len(txt_files)}", file=sys.stderr)

        text = txt_file.read_text(encoding="utf-8", errors="replace")
        if len(text.split()) < 50:
            continue

        # Use filename as URL proxy (SF names files by URL slug)
        url = txt_file.stem.replace("_", "/")
        result = analyze_page(text, url=url)
        results.append(result)

    print(f"Analyzed {len(results)} pages with sufficient content", file=sys.stderr)
    return results


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Passage-level content analysis for AI/RAG readiness")

    # Input sources
    parser.add_argument("--url", help="URL label (metadata only, doesn't fetch)")
    parser.add_argument("--html", help="HTML file to analyze")
    parser.add_argument("--text", help="Plain text file to analyze")
    parser.add_argument("--sf-text-dir", help="Screaming Frog 'All Page Text' export directory")

    # Embedding mode
    parser.add_argument("--embeddings", action="store_true", help="Enable embedding-based retrieval scoring")
    parser.add_argument("--queries", help="Target queries CSV (GSC export or keyword list) — required with --embeddings")
    parser.add_argument("--model", default="text-embedding-004", help="Gemini embedding model (default: text-embedding-004)")
    parser.add_argument("--sf-embeddings", help="SF embedding export CSV (optional, page-level)")

    # Output
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    # Validate embedding args
    if args.embeddings and not args.queries:
        print("ERROR: --embeddings requires --queries (GSC export or keyword CSV)", file=sys.stderr)
        sys.exit(1)
    # Embedding mode requires GOOGLE_API_KEY for Gemini
    if args.embeddings:
        if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
            print("ERROR: --embeddings requires GOOGLE_API_KEY or GEMINI_API_KEY env var", file=sys.stderr)
            sys.exit(1)

    # Parse content
    if args.sf_text_dir:
        results = analyze_sf_text_dir(args.sf_text_dir)
        output = {
            "mode": "bulk",
            "pages_analyzed": len(results),
            "pages": results,
        }
    elif args.text:
        text = Path(args.text).read_text(encoding="utf-8", errors="replace")
        result = analyze_page(text, url=args.url or args.text)
        output = {"mode": "single", "pages_analyzed": 1, "pages": [result]}
    elif args.html:
        html = Path(args.html).read_text(encoding="utf-8", errors="replace")
        for tag in REMOVE_SELECTORS:
            html = re.sub(rf"<{tag}[\s>].*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "\n", html)
        text = clean_text(text)
        result = analyze_page(text, url=args.url or args.html)
        output = {"mode": "single", "pages_analyzed": 1, "pages": [result]}
    else:
        print("ERROR: Provide --sf-text-dir, --text, or --html", file=sys.stderr)
        sys.exit(1)

    # Embedding-based retrieval scoring
    if args.embeddings:
        queries = load_queries(args.queries)
        if not queries:
            print("ERROR: No queries found in CSV", file=sys.stderr)
            sys.exit(1)

        print(f"\n=== Embedding Retrieval Analysis ===", file=sys.stderr)
        print(f"Queries loaded: {len(queries)}", file=sys.stderr)

        output["embedding_mode"] = True
        output["provider"] = "gemini"
        output["model"] = args.model
        output["total_queries"] = len(queries)

        for page in output["pages"]:
            all_passages = page["passages"]

            embedding_scores = score_passages_with_embeddings(
                passages=all_passages,
                queries=queries,
                model=args.model,
                sf_embeddings_path=args.sf_embeddings,
            )

            # Merge embedding scores into passage data
            emb_by_id = {e["passage_id"]: e for e in embedding_scores}
            for passage in all_passages:
                emb = emb_by_id.get(passage["id"])
                if emb:
                    passage["embedding"] = emb

            # Add retrieval summary to page
            if embedding_scores:
                retrieval_scores = [e["retrieval_score"] for e in embedding_scores]
                page["retrieval_summary"] = {
                    "avg_retrieval_score": round(sum(retrieval_scores) / len(retrieval_scores), 1),
                    "excellent_passages": sum(1 for s in retrieval_scores if s >= 80),
                    "good_passages": sum(1 for s in retrieval_scores if 65 <= s < 80),
                    "moderate_passages": sum(1 for s in retrieval_scores if 50 <= s < 65),
                    "weak_passages": sum(1 for s in retrieval_scores if 35 <= s < 50),
                    "no_match_passages": sum(1 for s in retrieval_scores if s < 35),
                    "best_passage": max(embedding_scores, key=lambda e: e["retrieval_score"]),
                    "query_coverage": len(set(
                        e["best_query_match"]["query"]
                        for e in embedding_scores
                        if e.get("best_query_match")
                    )),
                }
    else:
        output["embedding_mode"] = False

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    for page in output["pages"]:
        s = page["summary"]
        line = (f"\n{s.get('url', 'Page')}: {s['total_passages']} passages, "
                f"avg heuristic score {s['avg_score']}/100, "
                f"{s['optimal_length_pct']}% optimal length")

        if "retrieval_summary" in page:
            rs = page["retrieval_summary"]
            line += (f", avg retrieval {rs['avg_retrieval_score']}/100, "
                     f"{rs['excellent_passages']} excellent, "
                     f"{rs['query_coverage']} queries covered")

        print(line, file=sys.stderr)

    print(f"\nResults saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
