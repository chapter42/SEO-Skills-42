#!/usr/bin/env python3
"""
42-keyword-discovery: Seed keyword expansion with DataForSEO.

Modes:
  --live     Use DataForSEO API for real volume/difficulty data (default if creds available)
  --mock     Generate keyword ideas via LLM-friendly patterns without API calls

Usage:
  python3 discover.py "seed keyword" [--location 2840] [--language en] [--limit 50] [--mock]
  python3 discover.py seeds.csv [--location 2840] [--language en] [--limit 50]
"""

import argparse
import csv
import io
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.dataforseo import DataForSEOClient


# --- Location codes for common markets ---
LOCATIONS = {
    "us": 2840, "nl": 2528, "be": 2056, "de": 2276,
    "uk": 2826, "fr": 2250, "es": 2724, "it": 2380,
    "au": 2036, "ca": 2124, "br": 2076, "in": 2356,
}

# --- Intent classification signals ---
INTENT_SIGNALS = {
    "transactional": [
        "buy", "kopen", "price", "prijs", "discount", "korting",
        "order", "bestellen", "deal", "cheap", "goedkoop", "shop",
        "purchase", "coupon", "subscribe", "abonnement",
    ],
    "commercial": [
        "best", "beste", "review", "vs", "versus", "compare",
        "vergelijk", "top", "alternative", "alternatief",
        "recommended", "aanbevolen", "which", "welke",
    ],
    "informational": [
        "what", "wat", "how", "hoe", "why", "waarom", "when", "wanneer",
        "who", "wie", "guide", "gids", "tutorial", "learn", "leren",
        "example", "voorbeeld", "meaning", "betekenis", "definition",
    ],
    "navigational": [],  # Detected by brand name presence, not signal words
}

INTENT_VALUES = {
    "transactional": 3,
    "commercial": 2,
    "informational": 1,
    "navigational": 1,
}


def load_credentials() -> Optional[tuple[str, str]]:
    """Load DataForSEO credentials from env or config file."""
    login = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")

    if login and password:
        return login, password

    # Try seo-agi config
    env_file = Path.home() / ".config" / "seo-agi" / ".env"
    if env_file.exists():
        env = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
        login = env.get("DATAFORSEO_LOGIN", "")
        password = env.get("DATAFORSEO_PASSWORD", "")
        if login and password:
            return login, password

    # Try seo-project .env
    for env_path in Path(".").glob(".seo-project/**/.env"):
        env = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
        login = env.get("DATAFORSEO_LOGIN", "")
        password = env.get("DATAFORSEO_PASSWORD", "")
        if login and password:
            return login, password

    return None


def classify_intent(keyword: str) -> str:
    """Classify search intent based on signal words."""
    kw_lower = keyword.lower()
    for intent, signals in INTENT_SIGNALS.items():
        if any(s in kw_lower for s in signals):
            return intent
    return "informational"  # default


def calculate_opportunity(volume: int, difficulty: int, intent: str) -> float:
    """Opportunity = (Volume x Intent Value) / max(Difficulty, 1)."""
    intent_value = INTENT_VALUES.get(intent, 1)
    return round((volume * intent_value) / max(difficulty, 1), 1)


def parse_seeds(input_arg: str) -> list[str]:
    """Parse seed keywords from string or CSV file."""
    path = Path(input_arg)
    if path.exists() and path.suffix.lower() in (".csv", ".txt"):
        seeds = []
        with open(path) as f:
            if path.suffix.lower() == ".csv":
                reader = csv.DictReader(f)
                # Try common column names
                for row in reader:
                    for col in ["keyword", "Keyword", "query", "Query", "seed"]:
                        if col in row and row[col].strip():
                            seeds.append(row[col].strip())
                            break
                    else:
                        # Single column CSV
                        vals = list(row.values())
                        if vals and vals[0].strip():
                            seeds.append(vals[0].strip())
            else:
                for line in f:
                    line = line.strip()
                    if line:
                        seeds.append(line)
        return seeds if seeds else [input_arg]
    return [input_arg]


def discover_live(
    seeds: list[str],
    client: DataForSEOClient,
    location_code: int,
    language_code: str,
    limit: int,
) -> dict:
    """Run keyword discovery using DataForSEO API."""
    all_suggestions = []
    all_related = []

    for seed in seeds:
        print(f"  Fetching suggestions for: {seed}", file=sys.stderr)
        try:
            suggestions = client.keyword_suggestions(
                seed, location_code, language_code, limit
            )
            all_suggestions.extend(suggestions)
        except RuntimeError as e:
            print(f"  Warning: suggestions failed for '{seed}': {e}", file=sys.stderr)

        print(f"  Fetching related keywords for: {seed}", file=sys.stderr)
        try:
            related = client.related_keywords(
                seed, location_code, language_code, limit
            )
            all_related.extend(related)
        except RuntimeError as e:
            print(f"  Warning: related failed for '{seed}': {e}", file=sys.stderr)

    # Deduplicate by keyword
    seen = set()
    unique = []
    for kw in all_suggestions + all_related:
        k = kw["keyword"].lower().strip()
        if k not in seen:
            seen.add(k)
            kw["intent"] = classify_intent(kw["keyword"])
            kw["opportunity"] = calculate_opportunity(
                kw.get("volume", 0) or 0,
                kw.get("difficulty", 0) or 0,
                kw["intent"],
            )
            unique.append(kw)

    # Sort by opportunity score
    unique.sort(key=lambda x: x["opportunity"], reverse=True)

    # Group by intent
    by_intent = {}
    for kw in unique:
        intent = kw["intent"]
        by_intent.setdefault(intent, []).append(kw)

    # Quick wins: high volume, low difficulty
    quick_wins = [
        kw for kw in unique
        if (kw.get("volume", 0) or 0) >= 100
        and (kw.get("difficulty", 0) or 0) <= 40
    ][:20]

    # GEO opportunities: informational questions likely to get AI citations
    geo_opportunities = [
        kw for kw in unique
        if kw["intent"] == "informational"
        and any(
            kw["keyword"].lower().startswith(q)
            for q in ["what", "how", "why", "wat", "hoe", "waarom", "when", "wanneer"]
        )
    ][:20]

    return {
        "seeds": seeds,
        "total_keywords": len(unique),
        "keywords": unique,
        "by_intent": by_intent,
        "quick_wins": quick_wins,
        "geo_opportunities": geo_opportunities,
        "mode": "live",
    }


def format_markdown(result: dict, seeds: list[str]) -> str:
    """Format results as markdown report."""
    lines = []
    lines.append(f"# Keyword Discovery Report")
    lines.append(f"")
    lines.append(f"**Seeds:** {', '.join(seeds)}")
    lines.append(f"**Mode:** {'DataForSEO (live data)' if result['mode'] == 'live' else 'LLM patterns (no API)'}")
    lines.append(f"**Total keywords found:** {result['total_keywords']}")
    lines.append(f"")

    # Quick wins
    if result.get("quick_wins"):
        lines.append("## Quick Wins (high volume, low difficulty)")
        lines.append("")
        lines.append("| Keyword | Volume | Difficulty | Intent | Opportunity |")
        lines.append("|---------|--------|------------|--------|-------------|")
        for kw in result["quick_wins"]:
            lines.append(
                f"| {kw['keyword']} | {kw.get('volume', '-')} | "
                f"{kw.get('difficulty', '-')} | {kw['intent']} | "
                f"{kw.get('opportunity', '-')} |"
            )
        lines.append("")

    # GEO opportunities
    if result.get("geo_opportunities"):
        lines.append("## GEO Opportunities (question keywords for AI citations)")
        lines.append("")
        lines.append("| Keyword | Volume | Difficulty | Opportunity |")
        lines.append("|---------|--------|------------|-------------|")
        for kw in result["geo_opportunities"]:
            lines.append(
                f"| {kw['keyword']} | {kw.get('volume', '-')} | "
                f"{kw.get('difficulty', '-')} | {kw.get('opportunity', '-')} |"
            )
        lines.append("")

    # By intent
    for intent in ["transactional", "commercial", "informational"]:
        kws = result.get("by_intent", {}).get(intent, [])
        if not kws:
            continue
        lines.append(f"## {intent.title()} Keywords ({len(kws)})")
        lines.append("")
        lines.append("| Keyword | Volume | Difficulty | CPC | Opportunity |")
        lines.append("|---------|--------|------------|-----|-------------|")
        for kw in kws[:30]:
            lines.append(
                f"| {kw['keyword']} | {kw.get('volume', '-')} | "
                f"{kw.get('difficulty', '-')} | "
                f"${kw.get('cpc', 0):.2f} | {kw.get('opportunity', '-')} |"
            )
        if len(kws) > 30:
            lines.append(f"| *... +{len(kws) - 30} more* | | | | |")
        lines.append("")

    # Next steps
    lines.append("---")
    lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("")
    lines.append("Use these skills to action the keyword data:")
    lines.append("")
    lines.append("| Step | Skill | What it does with this data |")
    lines.append("|------|-------|---------------------------|")
    lines.append("| 1 | `/42:serp-cluster <keywords.csv>` | Group keywords by SERP overlap into topic clusters |")
    lines.append("| 2 | `/42:topical-map <keywords.csv>` | Build pillar/cluster content architecture |")
    lines.append("| 3 | `/42:paa-scraper <seed>` | Expand question keywords into full PAA trees |")
    lines.append("| 4 | `/42:audience-angles <niche>` | Generate 50 content angles across 10 psychological dimensions |")
    lines.append("| 5 | `/42:keyword-mapper <sf-emb.csv> <gsc.csv>` | Map keywords to existing pages, find gaps |")
    lines.append("| 6 | `/42:striking-distance <gsc.csv>` | Find keywords in position 5-20 for quick wins |")
    lines.append("| 7 | `/42:cannibalization` | Detect pages competing for the same keywords |")
    lines.append("| 8 | `/seo-agi <keyword>` | Write GEO-optimized content for top opportunities |")
    lines.append("")

    return "\n".join(lines)


def format_csv(keywords: list[dict]) -> str:
    """Format keywords as CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["keyword", "volume", "difficulty", "cpc", "competition", "intent", "opportunity"],
    )
    writer.writeheader()
    for kw in keywords:
        writer.writerow({
            "keyword": kw.get("keyword", ""),
            "volume": kw.get("volume", 0) or 0,
            "difficulty": kw.get("difficulty", 0) or 0,
            "cpc": kw.get("cpc", 0) or 0,
            "competition": kw.get("competition", 0) or 0,
            "intent": kw.get("intent", ""),
            "opportunity": kw.get("opportunity", 0),
        })
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description="42-keyword-discovery")
    parser.add_argument("seed", help="Seed keyword or path to CSV/TXT file")
    parser.add_argument("--location", default="nl", help="Location code or country (default: nl)")
    parser.add_argument("--language", default="nl", help="Language code (default: nl)")
    parser.add_argument("--limit", type=int, default=50, help="Max results per API call (default: 50)")
    parser.add_argument("--mock", action="store_true", help="Skip API, output seed expansion patterns")
    parser.add_argument("--output", default="keyword-discovery.md", help="Output file (default: keyword-discovery.md)")
    parser.add_argument("--csv", default="keyword-discovery.csv", help="CSV output file")
    parser.add_argument("--json", action="store_true", help="Also output JSON")

    args = parser.parse_args()

    # Resolve location
    location_code = LOCATIONS.get(args.location.lower(), None)
    if location_code is None:
        try:
            location_code = int(args.location)
        except ValueError:
            print(f"Unknown location: {args.location}. Use country code (nl, us, de) or numeric code.", file=sys.stderr)
            sys.exit(1)

    seeds = parse_seeds(args.seed)
    print(f"Seeds: {seeds}", file=sys.stderr)

    if args.mock:
        print("Mock mode: generating keyword patterns without API calls.", file=sys.stderr)
        # In mock mode, just output the seeds with expansion patterns
        result = {
            "seeds": seeds,
            "total_keywords": 0,
            "keywords": [],
            "by_intent": {},
            "quick_wins": [],
            "geo_opportunities": [],
            "mode": "mock",
        }
    else:
        creds = load_credentials()
        if not creds:
            print(
                "No DataForSEO credentials found. Checked:\n"
                "  - DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD env vars\n"
                "  - ~/.config/seo-agi/.env\n"
                "  - .seo-project/*/.env\n"
                "\nUse --mock for pattern-based discovery without API.",
                file=sys.stderr,
            )
            sys.exit(1)

        client = DataForSEOClient(creds[0], creds[1])
        result = discover_live(seeds, client, location_code, args.language, args.limit)

    # Write markdown report
    md = format_markdown(result, seeds)
    with open(args.output, "w") as f:
        f.write(md)
    print(f"Report: {args.output}", file=sys.stderr)

    # Write CSV
    if result["keywords"]:
        csv_data = format_csv(result["keywords"])
        with open(args.csv, "w") as f:
            f.write(csv_data)
        print(f"CSV: {args.csv}", file=sys.stderr)

    # Write JSON if requested
    if args.json and result["keywords"]:
        json_file = args.output.replace(".md", ".json")
        with open(json_file, "w") as f:
            json.dump(result["keywords"], f, indent=2)
        print(f"JSON: {json_file}", file=sys.stderr)

    # Also print markdown to stdout for Claude to read
    print(md)


if __name__ == "__main__":
    main()
