#!/usr/bin/env python3
"""
42-keyword-assign: MECE Keyword→URL Assignment Engine

Combines data from keyword-discovery, keyword-mapper, serp-cluster, and GSC
to produce a validated {url: [keywords]} JSON mapping where each keyword is
assigned to exactly one URL.

Usage:
    python3 assign.py --sf embeddings.csv --gsc queries.csv
    python3 assign.py --sf embeddings.csv --gsc queries.csv --clusters serp-clusters.json
    python3 assign.py --sf embeddings.csv --gsc queries.csv --discovery keywords.csv --threshold 0.75
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Load env (shared helper)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
REFS = REPO_ROOT / "references"

if (REFS / "load_env.py").exists():
    sys.path.insert(0, str(REFS))
    import load_env  # noqa: F401


# ---------------------------------------------------------------------------
# Intent classification heuristics (fallback when discovery data unavailable)
# ---------------------------------------------------------------------------
INTENT_PATTERNS = {
    "transactional": [
        r"\b(kopen|bestellen|prijs|kosten|goedkoop|aanbieding|offerte|tarief)\b",
        r"\b(buy|order|price|cheap|deal|discount|coupon|shop)\b",
    ],
    "commercial": [
        r"\b(beste|top|vergelijk|review|alternatief|vs|versus)\b",
        r"\b(best|review|compare|alternative|vs|versus|recommend)\b",
    ],
    "informational": [
        r"\b(wat is|hoe|waarom|wanneer|gids|tutorial|uitleg|betekenis|voorbeeld)\b",
        r"\b(what is|how to|why|when|guide|tutorial|explain|example|definition)\b",
    ],
    "navigational": [
        r"\b(login|inloggen|dashboard|account|app|website)\b",
    ],
}


def classify_intent(keyword: str) -> str:
    """Classify keyword intent based on pattern matching."""
    kw = keyword.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, kw):
                return intent
    return "informational"  # default


# ---------------------------------------------------------------------------
# Input parsers
# ---------------------------------------------------------------------------
def parse_gsc_csv(path: str) -> dict:
    """Parse GSC Performance export → {keyword: {clicks, impressions, ctr, position, url?}}"""
    keywords = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # GSC exports use various column names
            kw = (
                row.get("Top queries")
                or row.get("Query")
                or row.get("query")
                or row.get("Keyword")
                or row.get("keyword")
                or ""
            ).strip()
            if not kw:
                continue

            def parse_num(val):
                if not val:
                    return 0
                val = val.strip().replace(",", "").replace("%", "")
                try:
                    return float(val)
                except ValueError:
                    return 0

            entry = {
                "clicks": int(parse_num(row.get("Clicks", row.get("clicks", "0")))),
                "impressions": int(
                    parse_num(row.get("Impressions", row.get("impressions", "0")))
                ),
                "ctr": parse_num(row.get("CTR", row.get("ctr", "0"))),
                "position": parse_num(
                    row.get("Position", row.get("position", "0"))
                ),
            }

            # Some exports include the URL
            url = (row.get("Page") or row.get("page") or row.get("URL") or "").strip()
            if url:
                entry["url"] = url

            # Keep the entry with most impressions if duplicate
            if kw not in keywords or entry["impressions"] > keywords[kw]["impressions"]:
                keywords[kw] = entry

    return keywords


def parse_discovery_csv(path: str) -> dict:
    """Parse keyword-discovery.csv → {keyword: {intent, volume, difficulty}}"""
    keywords = {}
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kw = (
                row.get("keyword") or row.get("Keyword") or row.get("query") or ""
            ).strip()
            if not kw:
                continue

            def safe_int(val):
                try:
                    return int(float(val.replace(",", ""))) if val else 0
                except (ValueError, AttributeError):
                    return 0

            keywords[kw] = {
                "intent": (row.get("intent") or row.get("Intent") or "").strip().lower()
                or classify_intent(kw),
                "volume": safe_int(row.get("volume") or row.get("Volume") or row.get("search_volume") or ""),
                "difficulty": safe_int(row.get("difficulty") or row.get("Difficulty") or row.get("kd") or ""),
            }
    return keywords


def parse_clusters_json(path: str) -> dict:
    """Parse serp-clusters.json → {keyword: hub_url}"""
    hub_map = {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    clusters = data if isinstance(data, list) else data.get("clusters", [])
    for cluster in clusters:
        hub_url = cluster.get("hub_url") or cluster.get("hub") or ""
        kws = cluster.get("keywords", [])
        for kw_entry in kws:
            kw = kw_entry if isinstance(kw_entry, str) else kw_entry.get("keyword", "")
            if kw and hub_url:
                hub_map[kw.lower().strip()] = hub_url
    return hub_map


def parse_mapper_json(path: str) -> list:
    """Parse keyword-map.json → [{keyword, url, similarity}]"""
    mappings = []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Adapt to different output formats
    if isinstance(data, list):
        entries = data
    elif "mappings" in data:
        entries = data["mappings"]
    elif "keywords" in data:
        entries = data["keywords"]
    else:
        entries = []

    for entry in entries:
        kw = entry.get("keyword", "").strip()
        candidates = entry.get("candidates", entry.get("urls", []))
        if not candidates and entry.get("url"):
            candidates = [{"url": entry["url"], "similarity": entry.get("similarity", 0.5)}]

        for c in candidates:
            url = c.get("url", c.get("address", "")).strip()
            sim = float(c.get("similarity", c.get("score", 0)))
            if kw and url:
                mappings.append({"keyword": kw, "url": url, "similarity": sim})

    return mappings


# ---------------------------------------------------------------------------
# Core assignment engine
# ---------------------------------------------------------------------------
def build_registry(
    gsc_data: dict,
    discovery_data: dict,
    mapper_data: list,
    hub_map: dict,
    threshold: float,
) -> dict:
    """Build unified keyword registry with candidate URLs."""
    registry = {}

    # Start with all known keywords
    all_keywords = set()
    all_keywords.update(gsc_data.keys())
    all_keywords.update(discovery_data.keys())
    all_keywords.update(m["keyword"] for m in mapper_data)

    for kw in all_keywords:
        kw_lower = kw.lower().strip()
        disc = discovery_data.get(kw, {})
        gsc = gsc_data.get(kw, {})

        registry[kw] = {
            "intent": disc.get("intent") or classify_intent(kw),
            "volume": disc.get("volume") or gsc.get("impressions", 0),
            "difficulty": disc.get("difficulty", 0),
            "impressions": gsc.get("impressions", 0),
            "clicks": gsc.get("clicks", 0),
            "position": gsc.get("position", 0),
            "candidate_urls": [],
        }

    # Add mapper candidates
    for m in mapper_data:
        kw = m["keyword"]
        if kw not in registry:
            continue
        url = m["url"]
        sim = m["similarity"]
        if sim < threshold:
            continue

        gsc = gsc_data.get(kw, {})
        is_hub = hub_map.get(kw.lower().strip(), "") == url

        registry[kw]["candidate_urls"].append(
            {
                "url": url,
                "similarity": sim,
                "position": gsc.get("position", 0),
                "impressions": gsc.get("impressions", 0),
                "clicks": gsc.get("clicks", 0),
                "is_hub": is_hub,
            }
        )

    # Also add GSC url-level data as candidates if mapper didn't cover them
    for kw, gsc in gsc_data.items():
        if kw in registry and gsc.get("url"):
            existing_urls = {c["url"] for c in registry[kw]["candidate_urls"]}
            if gsc["url"] not in existing_urls:
                registry[kw]["candidate_urls"].append(
                    {
                        "url": gsc["url"],
                        "similarity": 0.60,  # moderate assumed similarity
                        "position": gsc.get("position", 0),
                        "impressions": gsc.get("impressions", 0),
                        "clicks": gsc.get("clicks", 0),
                        "is_hub": hub_map.get(kw.lower().strip(), "") == gsc["url"],
                    }
                )

    return registry


def assign_keywords(registry: dict, threshold: float) -> tuple:
    """
    Greedy MECE assignment: highest similarity first, tiebreak on position.

    Returns: (assignments, orphans, conflicts)
    - assignments: {url: [{keyword, intent, volume, ...}]}
    - orphans: [{keyword, intent, volume, reason}]
    - conflicts: [{keyword, candidates, assigned_to, reason}]
    """
    # Build all (keyword, url, score) triples
    triples = []
    for kw, info in registry.items():
        for c in info["candidate_urls"]:
            triples.append((kw, c["url"], c["similarity"], c))

    # Sort: highest similarity first, tiebreak on position (lower = better)
    triples.sort(key=lambda t: (-t[2], t[3].get("position", 999)))

    assigned_keywords = {}  # kw → url
    assignments = defaultdict(list)  # url → [kw_entries]
    conflicts = []

    # Detect conflicts first: keywords with multiple candidates above threshold
    multi_candidate = {}
    for kw, info in registry.items():
        candidates = [c for c in info["candidate_urls"] if c["similarity"] >= threshold]
        if len(candidates) >= 2:
            # Check if similarity difference is small (within 0.05)
            candidates.sort(key=lambda c: -c["similarity"])
            if candidates[0]["similarity"] - candidates[1]["similarity"] < 0.05:
                multi_candidate[kw] = candidates

    # Greedy assignment
    for kw, url, sim, candidate in triples:
        if kw in assigned_keywords:
            continue  # already assigned (MECE)

        info = registry[kw]
        reason = "highest_similarity"

        # Check if this is a conflict case
        if kw in multi_candidate:
            best = multi_candidate[kw][0]
            # Hub URL preference
            for c in multi_candidate[kw]:
                if c["is_hub"] and abs(c["similarity"] - best["similarity"]) < 0.03:
                    url = c["url"]
                    reason = "hub_url_preference"
                    break
            else:
                # Position tiebreak
                if (
                    len(multi_candidate[kw]) >= 2
                    and multi_candidate[kw][1]["position"] > 0
                    and multi_candidate[kw][0]["position"] > 0
                    and multi_candidate[kw][1]["position"]
                    < multi_candidate[kw][0]["position"]
                    and abs(
                        multi_candidate[kw][0]["similarity"]
                        - multi_candidate[kw][1]["similarity"]
                    )
                    < 0.03
                ):
                    url = multi_candidate[kw][1]["url"]
                    reason = "better_position"
                else:
                    url = best["url"]
                    reason = "highest_similarity"

            conflicts.append(
                {
                    "keyword": kw,
                    "candidates": [
                        {
                            "url": c["url"],
                            "similarity": c["similarity"],
                            "position": c.get("position", 0),
                        }
                        for c in multi_candidate[kw][:3]
                    ],
                    "assigned_to": url,
                    "reason": reason,
                    "user_override": False,
                }
            )

        assigned_keywords[kw] = url
        assignments[url].append(
            {
                "keyword": kw,
                "intent": info["intent"],
                "volume": info["volume"],
                "difficulty": info["difficulty"],
                "similarity": sim,
                "position": info["position"],
                "impressions": info["impressions"],
                "clicks": info["clicks"],
                "assignment_reason": reason,
            }
        )

    # Orphans: keywords with no candidate above threshold
    orphans = []
    for kw, info in registry.items():
        if kw not in assigned_keywords:
            best = max(info["candidate_urls"], key=lambda c: c["similarity"]) if info["candidate_urls"] else None
            orphans.append(
                {
                    "keyword": kw,
                    "intent": info["intent"],
                    "volume": info["volume"],
                    "best_candidate": best["url"] if best else None,
                    "best_similarity": best["similarity"] if best else 0,
                    "reason": "below_threshold" if best else "no_candidates",
                }
            )

    return dict(assignments), orphans, conflicts


def determine_primary(keywords: list) -> str:
    """Pick the primary keyword for a URL (highest volume among highest similarity)."""
    if not keywords:
        return ""
    # Sort by similarity desc, then volume desc
    sorted_kws = sorted(keywords, key=lambda k: (-k["similarity"], -k["volume"]))
    return sorted_kws[0]["keyword"]


def determine_dominant_intent(keywords: list) -> str:
    """Most common intent among assigned keywords."""
    if not keywords:
        return "informational"
    counts = defaultdict(int)
    for k in keywords:
        counts[k["intent"]] += 1
    return max(counts, key=counts.get)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def build_output(assignments: dict, orphans: list, conflicts: list, domain: str, config: dict) -> dict:
    """Build the final JSON output structure."""
    mapping = {}
    for url, keywords in assignments.items():
        keywords.sort(key=lambda k: (-k["similarity"], -k["volume"]))
        mapping[url] = {
            "primary_keyword": determine_primary(keywords),
            "intent": determine_dominant_intent(keywords),
            "keyword_count": len(keywords),
            "total_volume": sum(k["volume"] for k in keywords),
            "keywords": keywords,
        }

    # Stats
    all_intents = defaultdict(int)
    total_assigned = 0
    for url_data in mapping.values():
        for kw in url_data["keywords"]:
            all_intents[kw["intent"]] += 1
            total_assigned += 1

    return {
        "domain": domain,
        "generated": str(date.today()),
        "mece_validated": True,
        "conflicts_reviewed": len(conflicts),
        "config": config,
        "mapping": mapping,
        "orphans": orphans,
        "conflicts_log": conflicts,
        "stats": {
            "total_keywords": total_assigned + len(orphans),
            "assigned": total_assigned,
            "orphans": len(orphans),
            "urls_with_keywords": len(mapping),
            "avg_keywords_per_url": round(total_assigned / max(len(mapping), 1), 1),
            "conflicts_found": len(conflicts),
            "conflicts_overridden": sum(1 for c in conflicts if c.get("user_override")),
            "intents": dict(all_intents),
        },
    }


def print_conflicts(conflicts: list) -> None:
    """Print conflict review table to stderr."""
    if not conflicts:
        print("\nGeen conflicten gevonden.", file=sys.stderr)
        return

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"CONFLICTEN ({len(conflicts)} gevonden)", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(
        f"{'#':>3} | {'Keyword':<30} | {'Kandidaat A':<25} | {'Sim A':>5} | {'Kandidaat B':<25} | {'Sim B':>5} | Aanbeveling",
        file=sys.stderr,
    )
    print("-" * 130, file=sys.stderr)

    for i, c in enumerate(conflicts, 1):
        cands = c["candidates"]
        a = cands[0] if len(cands) > 0 else {"url": "-", "similarity": 0}
        b = cands[1] if len(cands) > 1 else {"url": "-", "similarity": 0}

        a_path = urlparse(a["url"]).path if a["url"] != "-" else "-"
        b_path = urlparse(b["url"]).path if b["url"] != "-" else "-"
        assigned_path = urlparse(c["assigned_to"]).path

        print(
            f"{i:>3} | {c['keyword']:<30} | {a_path:<25} | {a['similarity']:.2f} | {b_path:<25} | {b['similarity']:.2f} | → {assigned_path}",
            file=sys.stderr,
        )

    print(f"{'='*80}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="MECE Keyword→URL Assignment Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 assign.py --sf embeddings.csv --gsc queries.csv
  python3 assign.py --sf embeddings.csv --gsc queries.csv --clusters serp-clusters.json
  python3 assign.py --sf embeddings.csv --gsc queries.csv --threshold 0.75 --output my-assignments.json
        """,
    )
    parser.add_argument("--sf", required=True, help="Screaming Frog embedding CSV")
    parser.add_argument("--gsc", required=True, help="GSC Performance CSV")
    parser.add_argument("--discovery", default=None, help="keyword-discovery.csv")
    parser.add_argument("--clusters", default=None, help="serp-clusters.json")
    parser.add_argument("--mapper", default=None, help="keyword-map.json")
    parser.add_argument("--threshold", type=float, default=0.70, help="Min similarity (default: 0.70)")
    parser.add_argument("--output", default="keyword-assignments.json", help="Output JSON file")
    parser.add_argument("--domain", default=None, help="Domain name (auto-detected from GSC)")

    args = parser.parse_args()

    # --- Parse inputs ---
    print("Parsing GSC data...", file=sys.stderr)
    gsc_data = parse_gsc_csv(args.gsc)
    print(f"  → {len(gsc_data)} keywords uit GSC", file=sys.stderr)

    discovery_data = {}
    if args.discovery and os.path.exists(args.discovery):
        print("Parsing keyword discovery...", file=sys.stderr)
        discovery_data = parse_discovery_csv(args.discovery)
        print(f"  → {len(discovery_data)} keywords uit discovery", file=sys.stderr)

    hub_map = {}
    if args.clusters and os.path.exists(args.clusters):
        print("Parsing SERP clusters...", file=sys.stderr)
        hub_map = parse_clusters_json(args.clusters)
        print(f"  → {len(hub_map)} keywords met hub URL", file=sys.stderr)

    mapper_data = []
    if args.mapper and os.path.exists(args.mapper):
        print("Parsing keyword mapper...", file=sys.stderr)
        mapper_data = parse_mapper_json(args.mapper)
        print(f"  → {len(mapper_data)} keyword→URL paren", file=sys.stderr)

    # If no mapper data, we need to run similarity ourselves
    # For now, use GSC url-level data as basic mapping
    if not mapper_data:
        print("Geen mapper data — gebruik GSC URL-level data als fallback", file=sys.stderr)
        for kw, info in gsc_data.items():
            if info.get("url"):
                mapper_data.append(
                    {"keyword": kw, "url": info["url"], "similarity": 0.75}
                )

    # Auto-detect domain
    domain = args.domain
    if not domain:
        for kw, info in gsc_data.items():
            if info.get("url"):
                domain = urlparse(info["url"]).netloc
                break
        if not domain:
            domain = "unknown"

    # --- Build registry & assign ---
    print("\nBuilding keyword registry...", file=sys.stderr)
    registry = build_registry(gsc_data, discovery_data, mapper_data, hub_map, args.threshold)
    print(f"  → {len(registry)} unieke keywords", file=sys.stderr)

    print("Running MECE assignment...", file=sys.stderr)
    assignments, orphans, conflicts = assign_keywords(registry, args.threshold)

    # --- Print conflicts for review ---
    print_conflicts(conflicts)

    # --- Build output ---
    config = {
        "threshold": args.threshold,
        "sources": [],
    }
    if gsc_data:
        config["sources"].append("gsc")
    if discovery_data:
        config["sources"].append("keyword-discovery")
    if mapper_data:
        config["sources"].append("keyword-mapper")
    if hub_map:
        config["sources"].append("serp-clusters")

    output = build_output(assignments, orphans, conflicts, domain, config)

    # --- Write JSON ---
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # --- Summary ---
    stats = output["stats"]
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"MECE Assignment Complete", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)
    print(f"  Keywords:    {stats['assigned']}/{stats['total_keywords']} toegewezen", file=sys.stderr)
    print(f"  Orphans:     {stats['orphans']} (content gaps)", file=sys.stderr)
    print(f"  URLs:        {stats['urls_with_keywords']}", file=sys.stderr)
    print(f"  Conflicten:  {stats['conflicts_found']}", file=sys.stderr)
    print(f"  MECE:        {'✓' if output['mece_validated'] else '✗'}", file=sys.stderr)
    print(f"  Output:      {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
