#!/usr/bin/env python3
"""
SERP-Based Keyword Clustering

Clusters keywords by analyzing shared organic SERP URLs.
If two keywords share N+ of the same ranking URLs, they belong
to the same topic cluster and should be targeted by the same page.

Usage:
    python3 serp_cluster.py --input serp-data.csv --output serp-clusters.json
    python3 serp_cluster.py --input serp-data.csv --min-overlap 4 --algorithm core
    python3 serp_cluster.py --input serp-data.csv --top-n 20 --algorithm clique
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from itertools import combinations
from urllib.parse import urlparse, urlunparse


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalize URL for comparison: lowercase, strip trailing slash, remove
    query params and fragments."""
    url = url.strip()
    if not url:
        return url
    parsed = urlparse(url.lower())
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


# ---------------------------------------------------------------------------
# CSV parsing with flexible column names
# ---------------------------------------------------------------------------

KEYWORD_COLUMNS = {"keyword", "query", "search_term", "term"}
RANK_COLUMNS = {"rank", "position", "pos"}
URL_COLUMNS = {"url", "link", "result_url", "landing_page", "result"}


def _find_column(headers: list[str], candidates: set[str]) -> str | None:
    """Find the first header that matches any candidate (case-insensitive)."""
    for h in headers:
        if h.lower().strip() in candidates:
            return h
    return None


def parse_serp_csv(path: str, top_n: int = 10) -> dict[str, list[str]]:
    """Parse SERP CSV and return {keyword: [url1, url2, ...]} limited to top_n
    results per keyword, ordered by rank."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []

        kw_col = _find_column(headers, KEYWORD_COLUMNS)
        rank_col = _find_column(headers, RANK_COLUMNS)
        url_col = _find_column(headers, URL_COLUMNS)

        if not kw_col:
            raise ValueError(
                f"No keyword column found. Headers: {headers}. "
                f"Expected one of: {KEYWORD_COLUMNS}"
            )
        if not url_col:
            raise ValueError(
                f"No URL column found. Headers: {headers}. "
                f"Expected one of: {URL_COLUMNS}"
            )

        # Collect rows
        raw: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for row in reader:
            kw = row[kw_col].strip()
            url = normalize_url(row[url_col])
            if not kw or not url:
                continue

            rank = 999
            if rank_col and row.get(rank_col):
                try:
                    rank = int(float(row[rank_col]))
                except (ValueError, TypeError):
                    rank = 999

            raw[kw].append((rank, url))

    # Sort by rank, dedupe, limit to top_n
    keyword_urls: dict[str, list[str]] = {}
    for kw, entries in raw.items():
        entries.sort(key=lambda x: x[0])
        seen: set[str] = set()
        urls: list[str] = []
        for _, url in entries:
            if url not in seen:
                seen.add(url)
                urls.append(url)
            if len(urls) >= top_n:
                break
        keyword_urls[kw] = urls

    return keyword_urls


# ---------------------------------------------------------------------------
# Overlap matrix
# ---------------------------------------------------------------------------

def build_overlap_matrix(
    keyword_urls: dict[str, list[str]],
) -> dict[tuple[str, str], int]:
    """Build pairwise overlap counts. Returns {(kw_a, kw_b): overlap_count}."""
    # Pre-compute sets
    kw_sets: dict[str, set[str]] = {
        kw: set(urls) for kw, urls in keyword_urls.items()
    }
    keywords = sorted(kw_sets.keys())
    overlaps: dict[tuple[str, str], int] = {}

    for i, kw_a in enumerate(keywords):
        for kw_b in keywords[i + 1:]:
            count = len(kw_sets[kw_a] & kw_sets[kw_b])
            if count > 0:
                overlaps[(kw_a, kw_b)] = count

    return overlaps


# ---------------------------------------------------------------------------
# Jaccard similarity
# ---------------------------------------------------------------------------

def jaccard(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Clustering algorithms
# ---------------------------------------------------------------------------

def _build_adjacency(
    keywords: list[str],
    overlaps: dict[tuple[str, str], int],
    min_overlap: int,
) -> dict[str, set[str]]:
    """Build adjacency list from overlap matrix."""
    adj: dict[str, set[str]] = defaultdict(set)
    for (kw_a, kw_b), count in overlaps.items():
        if count >= min_overlap:
            adj[kw_a].add(kw_b)
            adj[kw_b].add(kw_a)
    return adj


def cluster_connected_components(
    keywords: list[str],
    overlaps: dict[tuple[str, str], int],
    min_overlap: int,
) -> list[list[str]]:
    """Connected components: any path of edges >= min_overlap connects keywords."""
    adj = _build_adjacency(keywords, overlaps, min_overlap)
    visited: set[str] = set()
    clusters: list[list[str]] = []

    for kw in keywords:
        if kw in visited:
            continue
        # BFS
        component: list[str] = []
        queue = [kw]
        visited.add(kw)
        while queue:
            node = queue.pop(0)
            component.append(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        clusters.append(sorted(component))

    return clusters


def cluster_clique(
    keywords: list[str],
    overlaps: dict[tuple[str, str], int],
    min_overlap: int,
) -> list[list[str]]:
    """Clique-based: all members must mutually share >= min_overlap URLs.
    Uses greedy maximal clique detection (Bron-Kerbosch simplified)."""
    adj = _build_adjacency(keywords, overlaps, min_overlap)

    # Find all maximal cliques using a simple greedy approach
    cliques: list[set[str]] = []
    remaining = set(keywords)

    # Sort by degree descending for better greedy results
    degree_sorted = sorted(
        keywords, key=lambda k: len(adj.get(k, set())), reverse=True
    )

    assigned: set[str] = set()
    for seed in degree_sorted:
        if seed in assigned:
            continue
        # Grow clique from seed
        clique = {seed}
        candidates = adj.get(seed, set()) - assigned
        for candidate in sorted(candidates, key=lambda c: len(adj.get(c, set())), reverse=True):
            # Check if candidate is connected to all current clique members
            if all(candidate in adj.get(member, set()) for member in clique):
                clique.add(candidate)

        if len(clique) >= 2:
            cliques.append(clique)
            assigned.update(clique)
        else:
            # Singleton -- remains orphan unless assigned elsewhere
            pass

    # Add singletons as individual clusters
    for kw in keywords:
        if kw not in assigned:
            cliques.append({kw})

    return [sorted(c) for c in cliques]


def cluster_core_threshold(
    keywords: list[str],
    overlaps: dict[tuple[str, str], int],
    min_overlap: int,
    keyword_urls: dict[str, list[str]],
) -> list[list[str]]:
    """Core-based: seed from highest-overlap pairs, expand by core URL overlap."""
    adj = _build_adjacency(keywords, overlaps, min_overlap)

    # Sort edges by overlap count descending
    edges = sorted(
        [(kw_a, kw_b, count) for (kw_a, kw_b), count in overlaps.items() if count >= min_overlap],
        key=lambda x: x[2],
        reverse=True,
    )

    assigned: set[str] = set()
    clusters: list[list[str]] = []

    for kw_a, kw_b, _ in edges:
        if kw_a in assigned and kw_b in assigned:
            continue

        # Seed cluster
        cluster_kws: set[str] = set()
        if kw_a not in assigned:
            cluster_kws.add(kw_a)
        if kw_b not in assigned:
            cluster_kws.add(kw_b)

        # Find core URLs (shared by the seed pair)
        core_urls = set(keyword_urls.get(kw_a, [])) & set(keyword_urls.get(kw_b, []))

        # Expand: add unassigned keywords that overlap with core URLs
        for kw in keywords:
            if kw in assigned or kw in cluster_kws:
                continue
            kw_url_set = set(keyword_urls.get(kw, []))
            overlap_with_core = len(kw_url_set & core_urls)
            if overlap_with_core >= min_overlap:
                cluster_kws.add(kw)

        assigned.update(cluster_kws)
        clusters.append(sorted(cluster_kws))

    # Add orphans
    for kw in keywords:
        if kw not in assigned:
            clusters.append([kw])

    return clusters


# ---------------------------------------------------------------------------
# Hub URL identification
# ---------------------------------------------------------------------------

def find_hub_urls(
    cluster: list[str], keyword_urls: dict[str, list[str]]
) -> list[tuple[str, int]]:
    """Find URLs that appear most frequently across cluster keywords.
    Returns [(url, count), ...] sorted by count descending."""
    url_counts: dict[str, int] = defaultdict(int)
    for kw in cluster:
        for url in keyword_urls.get(kw, []):
            url_counts[url] += 1
    return sorted(url_counts.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Cluster coherence scoring
# ---------------------------------------------------------------------------

def cluster_coherence(
    cluster: list[str], keyword_urls: dict[str, list[str]]
) -> float:
    """Average pairwise Jaccard similarity within a cluster."""
    if len(cluster) < 2:
        return 1.0
    kw_sets = {kw: set(keyword_urls.get(kw, [])) for kw in cluster}
    pairs = list(combinations(cluster, 2))
    if not pairs:
        return 1.0
    total = sum(jaccard(kw_sets[a], kw_sets[b]) for a, b in pairs)
    return total / len(pairs)


def coherence_label(score: float) -> str:
    """Human-readable coherence label."""
    if score >= 0.50:
        return "tight"
    elif score >= 0.30:
        return "moderate"
    elif score >= 0.15:
        return "loose"
    else:
        return "weak"


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_clustering(
    input_path: str,
    top_n: int = 10,
    min_overlap: int = 3,
    algorithm: str = "connected",
    output_path: str = "serp-clusters.json",
) -> dict:
    """Run full SERP clustering pipeline and return results dict."""

    # Step 1: Parse
    keyword_urls = parse_serp_csv(input_path, top_n=top_n)
    keywords = sorted(keyword_urls.keys())
    print(f"Parsed {len(keywords)} keywords from {input_path}")

    if len(keywords) == 0:
        print("No keywords found. Check CSV format.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Overlap matrix
    overlaps = build_overlap_matrix(keyword_urls)
    edges_above_threshold = sum(1 for c in overlaps.values() if c >= min_overlap)
    print(f"Built overlap matrix: {len(overlaps)} pairs, {edges_above_threshold} above threshold ({min_overlap})")

    # Step 3: Cluster
    if algorithm == "connected":
        clusters = cluster_connected_components(keywords, overlaps, min_overlap)
    elif algorithm == "clique":
        clusters = cluster_clique(keywords, overlaps, min_overlap)
    elif algorithm == "core":
        clusters = cluster_core_threshold(keywords, overlaps, min_overlap, keyword_urls)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Use: connected, clique, core")

    # Separate real clusters from orphans
    real_clusters = [c for c in clusters if len(c) >= 2]
    orphans = [c[0] for c in clusters if len(c) == 1]

    print(f"Formed {len(real_clusters)} clusters, {len(orphans)} orphans")

    # Step 4 & 5: Score coherence and find hub URLs
    cluster_results = []
    for idx, cluster_kws in enumerate(
        sorted(real_clusters, key=len, reverse=True), start=1
    ):
        avg_jaccard = cluster_coherence(cluster_kws, keyword_urls)
        hub_urls = find_hub_urls(cluster_kws, keyword_urls)
        hub_url = hub_urls[0][0] if hub_urls else None
        hub_freq = hub_urls[0][1] if hub_urls else 0

        # Build shared URLs table
        shared_urls = {}
        for url, count in hub_urls:
            if count >= 2:  # Only URLs appearing in 2+ keywords
                shared_urls[url] = count

        cluster_results.append({
            "id": idx,
            "primary_keyword": cluster_kws[0],  # alphabetically first
            "keywords": cluster_kws,
            "keyword_count": len(cluster_kws),
            "hub_url": hub_url,
            "hub_url_frequency": hub_freq,
            "avg_jaccard": round(avg_jaccard, 4),
            "coherence": coherence_label(avg_jaccard),
            "shared_urls": shared_urls,
            "top_hub_urls": [
                {"url": url, "keyword_count": count}
                for url, count in hub_urls[:10]
            ],
        })

    # Build output
    result = {
        "meta": {
            "total_keywords": len(keywords),
            "total_clusters": len(real_clusters),
            "orphan_keywords": len(orphans),
            "algorithm": algorithm,
            "min_overlap": min_overlap,
            "top_n": top_n,
            "avg_cluster_size": round(
                sum(len(c) for c in real_clusters) / len(real_clusters), 1
            ) if real_clusters else 0,
            "avg_jaccard": round(
                sum(c["avg_jaccard"] for c in cluster_results) / len(cluster_results), 4
            ) if cluster_results else 0,
        },
        "clusters": cluster_results,
        "orphans": orphans,
    }

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"Results written to {output_path}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cluster keywords by shared SERP URLs"
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to SERP data CSV"
    )
    parser.add_argument(
        "--output", "-o", default="serp-clusters.json",
        help="Output JSON path (default: serp-clusters.json)",
    )
    parser.add_argument(
        "--top-n", type=int, default=10,
        help="Top N results per keyword to consider (default: 10)",
    )
    parser.add_argument(
        "--min-overlap", type=int, default=3,
        help="Minimum shared URLs to connect keywords (default: 3)",
    )
    parser.add_argument(
        "--algorithm", choices=["connected", "clique", "core"],
        default="connected",
        help="Clustering algorithm (default: connected)",
    )
    args = parser.parse_args()

    run_clustering(
        input_path=args.input,
        top_n=args.top_n,
        min_overlap=args.min_overlap,
        algorithm=args.algorithm,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
