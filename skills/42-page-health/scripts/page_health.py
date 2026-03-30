"""
Page Health — Samengestelde per-URL gezondheidscore (0-100).

Combineert 7 risicosignalen uit Screaming Frog + optioneel GSC traffic decay.
Health Score = 100 - Risk Score. Hoog = gezond, laag = problematisch.

Usage:
    python3 page_health.py --sf-internal internal_html.csv --output PAGE-HEALTH.json
    python3 page_health.py --sf-internal internal.csv --gsc gsc-pages.csv --top 50 --output results.json
    python3 page_health.py --sf-internal internal.csv --type blog --weights custom.json --output results.json
"""

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger("page-health")

# --- Column Alias Mapping (English + Spanish SF exports) ---

ALIASES = {
    "address":        ["Address", "address", "URL", "url", "Dirección", "\ufeffAddress"],
    "status_code":    ["Status Code", "status_code", "Código de Estado"],
    "indexability":   ["Indexability", "indexability", "Indexabilidad"],
    "index_status":   ["Indexability Status", "indexability_status", "Estado de Indexabilidad"],
    "word_count":     ["Word Count", "word_count", "Palabras"],
    "title":          ["Title 1", "title_1", "Title", "Título 1"],
    "h1":             ["H1-1", "h1_1", "H1", "h1"],
    "h2":             ["H2-1", "h2_1", "H2", "h2"],
    "meta_desc":      ["Meta Description 1", "meta_description_1", "Meta Description", "Descripción Meta 1"],
    "canonical":      ["Canonical Link Element 1", "canonical_link_element_1", "Canonical", "Enlace Canónico 1"],
    "inlinks":        ["Inlinks", "inlinks", "Enlaces Entrantes"],
    "outlinks":       ["Outlinks", "outlinks", "Enlaces Salientes"],
    "content_type":   ["Content Type", "content_type", "Tipo de Contenido"],
    "crawl_depth":    ["Crawl Depth", "crawl_depth", "Profundidad de Rastreo"],
}

DEFAULT_WEIGHTS = {
    "thin_content": 25,
    "missing_canonical": 15,
    "orphan_page": 15,
    "poor_structure": 15,
    "missing_meta": 10,
    "deep_crawl_depth": 10,
    "traffic_decay": 10,
}

PAGE_TYPE_THRESHOLDS = {
    "blog":     {"thin": 800, "orphan": 3},
    "product":  {"thin": 200, "orphan": 2},
    "category": {"thin": 300, "orphan": 5},
    "service":  {"thin": 500, "orphan": 3},
    "location": {"thin": 400, "orphan": 2},
    "homepage": {"thin": 300, "orphan": 0},
    "default":  {"thin": 300, "orphan": 3},
}

PAGE_TYPE_PATTERNS = {
    "blog":     re.compile(r"/blog/|/article/|/post/|/nieuws/|/news/|/magazine/", re.I),
    "product":  re.compile(r"/product/|/shop/|/item/|/p/|/artikel/", re.I),
    "category": re.compile(r"/category/|/collection/|/tag/|/categorie/|/c/", re.I),
    "service":  re.compile(r"/service/|/dienst/|/solution/|/oplossing/", re.I),
    "location": re.compile(r"/location/|/vestiging/|/filiaal/|/store/|/winkel/", re.I),
}


# --- CSV Parsing ---

def normalize_columns(fieldnames: list[str]) -> dict[str, str]:
    """Map raw CSV column names to canonical names via alias lookup."""
    mapping = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            for field in fieldnames:
                if field.strip().lower() == alias.lower() or field.strip() == alias:
                    mapping[field] = canonical
                    break
            if canonical in mapping.values():
                break
    return mapping


def parse_sf_internal(filepath: str) -> list[dict]:
    """Parse Screaming Frog Internal export CSV."""
    pages = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Auto-detect delimiter
        sample = f.read(2048)
        f.seek(0)
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","

        reader = csv.DictReader(f, delimiter=delimiter)
        col_map = normalize_columns(reader.fieldnames)

        for row in reader:
            # Remap columns
            page = {}
            for raw_col, val in row.items():
                canonical = col_map.get(raw_col, raw_col)
                page[canonical] = val.strip() if val else ""

            # Filter: only HTML, only 200 status
            content_type = page.get("content_type", "text/html").lower()
            if "text/html" not in content_type:
                continue

            status = page.get("status_code", "200")
            try:
                status_int = int(status)
            except (ValueError, TypeError):
                continue
            if status_int != 200:
                continue

            # Coerce numeric fields
            page["word_count"] = _to_int(page.get("word_count", "0"))
            page["inlinks"] = _to_int(page.get("inlinks", "0"))
            page["outlinks"] = _to_int(page.get("outlinks", "0"))
            page["crawl_depth"] = _to_int(page.get("crawl_depth", "0"))

            pages.append(page)

    log.info(f"Parsed {len(pages)} HTML pages with 200 status from {filepath}")
    return pages


def parse_gsc_pages(filepath: str) -> dict[str, dict]:
    """Parse GSC Performance export (pages level) for traffic data."""
    gsc = {}

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            page_url = ""
            clicks = 0

            for key, val in row.items():
                kl = key.lower().strip()
                if kl in ("page", "pages", "url", "landing page"):
                    page_url = val.strip().rstrip("/").lower()
                elif kl == "clicks":
                    try:
                        clicks = int(val.strip().replace(",", ""))
                    except (ValueError, TypeError):
                        clicks = 0

            if page_url:
                if page_url not in gsc:
                    gsc[page_url] = {"clicks": 0}
                gsc[page_url]["clicks"] += clicks

    log.info(f"Parsed GSC data for {len(gsc)} pages")
    return gsc


def _to_int(val: str) -> int:
    """Safe int conversion."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


# --- Page Type Detection ---

def detect_page_type(url: str, override: str | None = None) -> str:
    """Detect page type from URL patterns."""
    if override:
        return override

    # Homepage
    path = re.sub(r"^https?://[^/]+", "", url)
    if path in ("", "/", "/index.html", "/index.php"):
        return "homepage"

    for ptype, pattern in PAGE_TYPE_PATTERNS.items():
        if pattern.search(url):
            return ptype

    return "default"


# --- Risk Scoring ---

def score_page(page: dict, weights: dict, page_type_override: str | None = None,
               gsc_data: dict | None = None) -> dict:
    """Calculate risk scores for a single page."""
    url = page.get("address", "")
    ptype = detect_page_type(url, page_type_override)
    thresholds = PAGE_TYPE_THRESHOLDS.get(ptype, PAGE_TYPE_THRESHOLDS["default"])

    scores = {}

    # 1. Thin Content (graduated)
    wc = page["word_count"]
    thin_thresh = thresholds["thin"]
    if wc < thin_thresh:
        ratio = wc / max(thin_thresh, 1)
        scores["thin_content"] = round((1 - ratio) * weights["thin_content"])
    else:
        scores["thin_content"] = 0

    # 2. Missing/Bad Canonical
    canonical = page.get("canonical", "")
    if not canonical:
        scores["missing_canonical"] = weights["missing_canonical"]
    elif canonical.rstrip("/").lower() != url.rstrip("/").lower():
        # Canonical points elsewhere — might be intentional, reduced penalty
        scores["missing_canonical"] = round(weights["missing_canonical"] * 0.67)
    else:
        scores["missing_canonical"] = 0

    # 3. Orphan Page (graduated)
    inlinks = page["inlinks"]
    orphan_thresh = thresholds["orphan"]
    if orphan_thresh == 0:  # homepage
        scores["orphan_page"] = 0
    elif inlinks == 0:
        scores["orphan_page"] = weights["orphan_page"]
    elif inlinks < orphan_thresh:
        ratio = inlinks / orphan_thresh
        scores["orphan_page"] = round((1 - ratio) * weights["orphan_page"])
    else:
        scores["orphan_page"] = 0

    # 4. Poor Structure
    has_h1 = bool(page.get("h1", "").strip())
    has_h2 = bool(page.get("h2", "").strip())
    if not has_h1 and not has_h2:
        scores["poor_structure"] = weights["poor_structure"]
    elif not has_h1:
        scores["poor_structure"] = round(weights["poor_structure"] * 0.67)
    elif not has_h2:
        scores["poor_structure"] = round(weights["poor_structure"] * 0.33)
    else:
        scores["poor_structure"] = 0

    # 5. Missing Meta (cumulative)
    meta_risk = 0
    title = page.get("title", "")
    meta_desc = page.get("meta_desc", "")

    if not title:
        meta_risk += 5
    elif len(title) < 30 or len(title) > 60:
        meta_risk += 2

    if not meta_desc:
        meta_risk += 5
    elif len(meta_desc) < 70 or len(meta_desc) > 160:
        meta_risk += 2

    scores["missing_meta"] = min(meta_risk, weights["missing_meta"])

    # 6. Deep Crawl Depth
    depth = page["crawl_depth"]
    if depth <= 3:
        scores["deep_crawl_depth"] = 0
    elif depth == 4:
        scores["deep_crawl_depth"] = round(weights["deep_crawl_depth"] * 0.3)
    elif depth == 5:
        scores["deep_crawl_depth"] = round(weights["deep_crawl_depth"] * 0.6)
    else:
        scores["deep_crawl_depth"] = weights["deep_crawl_depth"]

    # 7. Traffic Decay (only with GSC data)
    scores["traffic_decay"] = 0
    if gsc_data:
        url_normalized = url.rstrip("/").lower()
        gsc_entry = gsc_data.get(url_normalized)
        if gsc_entry:
            # Simple decay: if clicks are very low relative to site average
            # More sophisticated decay detection in 42:content-decay
            clicks = gsc_entry.get("clicks", 0)
            if clicks == 0:
                scores["traffic_decay"] = weights["traffic_decay"]
            # We flag zero-click pages with GSC impressions — they're indexed but not performing

    # Total risk and health
    total_risk = sum(scores.values())
    total_risk = min(100, max(0, total_risk))
    health_score = 100 - total_risk

    return {
        "url": url,
        "page_type": ptype,
        "health_score": health_score,
        "total_risk": total_risk,
        "signals": scores,
        "metadata": {
            "word_count": wc,
            "inlinks": inlinks,
            "crawl_depth": depth,
            "has_h1": has_h1,
            "has_h2": has_h2,
            "has_title": bool(title),
            "has_meta_desc": bool(meta_desc),
            "has_canonical": bool(canonical),
        },
    }


# --- Bulk Analysis ---

def analyze_site(pages: list[dict], weights: dict,
                 page_type_override: str | None = None,
                 gsc_data: dict | None = None) -> dict:
    """Score all pages and produce summary statistics."""
    scored = []
    for page in pages:
        result = score_page(page, weights, page_type_override, gsc_data)
        scored.append(result)

    scored.sort(key=lambda p: p["health_score"])

    # Distribution
    dist = {
        "excellent_90_100": sum(1 for p in scored if p["health_score"] >= 90),
        "healthy_70_89": sum(1 for p in scored if 70 <= p["health_score"] < 90),
        "attention_50_69": sum(1 for p in scored if 50 <= p["health_score"] < 70),
        "risk_30_49": sum(1 for p in scored if 30 <= p["health_score"] < 50),
        "critical_0_29": sum(1 for p in scored if p["health_score"] < 30),
    }

    # Per-signal averages
    signal_names = list(weights.keys())
    signal_stats = {}
    for signal in signal_names:
        values = [p["signals"].get(signal, 0) for p in scored]
        affected = sum(1 for v in values if v > 0)
        signal_stats[signal] = {
            "avg_risk": round(sum(values) / max(len(values), 1), 1),
            "max_points": weights[signal],
            "pages_affected": affected,
            "pct_affected": round(affected / max(len(scored), 1) * 100, 1),
        }

    # Non-indexable pages (reported separately)
    # These would need to be parsed from the original file before filtering

    avg_health = round(sum(p["health_score"] for p in scored) / max(len(scored), 1), 1)

    return {
        "total_pages": len(scored),
        "avg_health_score": avg_health,
        "distribution": dist,
        "signal_stats": signal_stats,
        "pages": scored,
    }


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Page Health — per-URL risk scoring")
    parser.add_argument("--sf-internal", required=True, help="Screaming Frog Internal export CSV")
    parser.add_argument("--gsc", help="GSC Performance export CSV (pages level)")
    parser.add_argument("--type", help="Override page type for all URLs (blog/product/category/service/location)")
    parser.add_argument("--weights", help="Custom weights JSON file")
    parser.add_argument("--top", type=int, default=25, help="Show top N risk URLs (default: 25)")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--csv", help="Also export as CSV (all pages with scores)")
    parser.add_argument("--log-file", help="Write logs to file")
    args = parser.parse_args()

    # Configure logging
    handlers = [logging.StreamHandler(sys.stderr)]
    if args.log_file:
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )

    # Load weights
    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        with open(args.weights) as f:
            custom = json.load(f)
        weights.update(custom)
        # Normalize to sum=100
        total = sum(weights.values())
        if total != 100:
            factor = 100 / total
            weights = {k: round(v * factor) for k, v in weights.items()}
            log.info(f"Weights normalized from {total} to 100")

    # Parse data
    pages = parse_sf_internal(args.sf_internal)
    if not pages:
        log.error("No pages found after filtering. Check the CSV file.")
        sys.exit(1)

    gsc_data = None
    if args.gsc:
        gsc_data = parse_gsc_pages(args.gsc)

    # Analyze
    result = analyze_site(pages, weights, args.type, gsc_data)

    # Print summary
    log.info(f"\n{'='*60}")
    log.info(f"PAGE HEALTH REPORT")
    log.info(f"{'='*60}")
    log.info(f"Pages analyzed: {result['total_pages']}")
    log.info(f"Average health: {result['avg_health_score']}/100")
    log.info(f"")
    log.info(f"Distribution:")
    d = result["distribution"]
    log.info(f"  Excellent (90-100): {d['excellent_90_100']}")
    log.info(f"  Healthy   (70-89):  {d['healthy_70_89']}")
    log.info(f"  Attention (50-69):  {d['attention_50_69']}")
    log.info(f"  Risk      (30-49):  {d['risk_30_49']}")
    log.info(f"  Critical  ( 0-29):  {d['critical_0_29']}")
    log.info(f"")
    log.info(f"Top {args.top} risk URLs:")
    for i, page in enumerate(result["pages"][:args.top]):
        signals = " | ".join(f"{k}:{v}" for k, v in page["signals"].items() if v > 0)
        log.info(f"  {i+1}. [{page['health_score']}/100] {page['url']}")
        if signals:
            log.info(f"     {signals}")

    # Write JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log.info(f"\nJSON saved to {args.output}")

    # Write CSV if requested
    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            header = ["URL", "Health Score", "Page Type", "Word Count", "Inlinks",
                       "Crawl Depth", "Thin", "Canonical", "Orphan", "Structure",
                       "Meta", "Depth", "Decay", "Total Risk"]
            writer.writerow(header)
            for page in result["pages"]:
                s = page["signals"]
                writer.writerow([
                    page["url"],
                    page["health_score"],
                    page["page_type"],
                    page["metadata"]["word_count"],
                    page["metadata"]["inlinks"],
                    page["metadata"]["crawl_depth"],
                    s.get("thin_content", 0),
                    s.get("missing_canonical", 0),
                    s.get("orphan_page", 0),
                    s.get("poor_structure", 0),
                    s.get("missing_meta", 0),
                    s.get("deep_crawl_depth", 0),
                    s.get("traffic_decay", 0),
                    page["total_risk"],
                ])
        log.info(f"CSV saved to {args.csv}")


if __name__ == "__main__":
    main()
