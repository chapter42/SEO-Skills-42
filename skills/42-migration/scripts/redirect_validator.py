#!/usr/bin/env python3
"""
Redirect Validator — Website Migration Toolkit
Part of the 42:migration skill suite.

Validates redirect specifications against actual crawl data,
detects redirect chains/loops, and queries the Wayback Machine
CDX API for historical site analysis.

Dependencies: Python 3.8+ standard library only (csv, json, urllib).
Optional: requests (for Wayback Machine queries; falls back to urllib).

Usage:
    python3 redirect_validator.py validate --spec spec.csv --crawl crawl.csv --output results.json
    python3 redirect_validator.py history --domain example.com --years 5 --output history.json
"""

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from io import StringIO
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, unquote, urlencode, parse_qs

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# URL Normalization
# ---------------------------------------------------------------------------

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid",
    "ref", "referrer", "source", "mc_cid", "mc_eid",
    "yclid", "twclid", "li_fat_id", "igshid", "s_kwcid",
}


def normalize_url(url: str, force_https: bool = True, strip_www: Optional[bool] = None) -> str:
    """
    Normalize a URL for comparison purposes.

    - Lowercase scheme and host
    - Force https (optional)
    - Strip trailing slash (unless root path)
    - Remove default ports (:80, :443)
    - Decode safe percent-encoded characters
    - Remove fragment identifiers
    - Remove tracking query parameters
    - Optionally strip or add www
    """
    if not url:
        return ""

    url = url.strip()

    # Add scheme if missing
    if not url.startswith(("http://", "https://", "//")):
        url = "https://" + url

    # Decode percent-encoded characters
    url = unquote(url)

    parsed = urlparse(url)

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    if force_https:
        scheme = "https"

    netloc = parsed.hostname.lower() if parsed.hostname else ""

    # Remove default ports
    if parsed.port and parsed.port not in (80, 443):
        netloc = f"{netloc}:{parsed.port}"

    # Handle www normalization
    if strip_www is True:
        netloc = netloc.removeprefix("www.")
    elif strip_www is False and not netloc.startswith("www."):
        netloc = "www." + netloc

    # Normalize path — strip trailing slash unless root
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if not path:
        path = "/"

    # Remove tracking query parameters, sort remaining
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {
            k: v for k, v in params.items()
            if k.lower() not in TRACKING_PARAMS
        }
        if filtered:
            # Sort parameters for consistent comparison
            query = urlencode(sorted(filtered.items()), doseq=True)
        else:
            query = ""
    else:
        query = ""

    # Drop fragment
    return urlunparse((scheme, netloc, path, "", query, ""))


# ---------------------------------------------------------------------------
# CSV Parsing
# ---------------------------------------------------------------------------

def detect_column(headers: List[str], candidates: List[str]) -> Optional[str]:
    """Find the first matching column name (case-insensitive)."""
    headers_lower = {h.lower().strip(): h for h in headers}
    for candidate in candidates:
        if candidate.lower() in headers_lower:
            return headers_lower[candidate.lower()]
    return None


def parse_spec_csv(filepath: str) -> List[Dict[str, str]]:
    """
    Parse a redirect specification CSV.
    Returns list of dicts with keys: old_url, new_url, type.
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        old_col = detect_column(headers, ["old_url", "source", "from", "old url", "source url", "from url", "address"])
        new_col = detect_column(headers, ["new_url", "destination", "to", "new url", "target", "target url", "destination url"])
        type_col = detect_column(headers, ["type", "status", "status code", "redirect type", "code"])

        if not old_col:
            raise ValueError(f"Cannot find old URL column. Headers: {headers}")
        if not new_col:
            raise ValueError(f"Cannot find new URL column. Headers: {headers}")

        results = []
        for row in reader:
            old_url = row.get(old_col, "").strip()
            new_url = row.get(new_col, "").strip()
            rtype = row.get(type_col, "301").strip() if type_col else "301"

            if old_url and new_url:
                results.append({
                    "old_url": old_url,
                    "old_url_normalized": normalize_url(old_url),
                    "new_url": new_url,
                    "new_url_normalized": normalize_url(new_url),
                    "type": rtype,
                })
        return results


def parse_crawl_csv(filepath: str) -> List[Dict[str, str]]:
    """
    Parse a Screaming Frog crawl CSV or generic crawl export.
    Returns list of dicts with keys: url, status_code, redirect_url, title, h1, word_count, etc.
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        url_col = detect_column(headers, ["address", "url", "source url", "page url"])
        status_col = detect_column(headers, ["status code", "status", "http status", "response code"])
        redirect_col = detect_column(headers, ["redirect url", "redirect uri", "redirect destination", "redirect to", "location"])
        title_col = detect_column(headers, ["title 1", "title", "page title"])
        h1_col = detect_column(headers, ["h1-1", "h1", "heading 1"])
        wc_col = detect_column(headers, ["word count", "wordcount", "words"])
        meta_col = detect_column(headers, ["meta description 1", "meta description", "description"])
        index_col = detect_column(headers, ["indexability", "indexable"])
        canonical_col = detect_column(headers, ["canonical link element 1", "canonical", "canonical url"])

        if not url_col:
            raise ValueError(f"Cannot find URL column. Headers: {headers}")

        results = []
        for row in reader:
            url = row.get(url_col, "").strip()
            if not url:
                continue

            entry = {
                "url": url,
                "url_normalized": normalize_url(url),
                "status_code": row.get(status_col, "").strip() if status_col else "",
                "redirect_url": row.get(redirect_col, "").strip() if redirect_col else "",
                "redirect_url_normalized": normalize_url(row.get(redirect_col, "").strip()) if redirect_col and row.get(redirect_col, "").strip() else "",
                "title": row.get(title_col, "").strip() if title_col else "",
                "h1": row.get(h1_col, "").strip() if h1_col else "",
                "word_count": row.get(wc_col, "0").strip() if wc_col else "0",
                "meta_description": row.get(meta_col, "").strip() if meta_col else "",
                "indexability": row.get(index_col, "").strip() if index_col else "",
                "canonical": row.get(canonical_col, "").strip() if canonical_col else "",
            }

            # Parse word count to int
            try:
                entry["word_count_int"] = int(entry["word_count"].replace(",", ""))
            except (ValueError, AttributeError):
                entry["word_count_int"] = 0

            results.append(entry)
        return results


# ---------------------------------------------------------------------------
# Redirect Validation
# ---------------------------------------------------------------------------

def build_redirect_map(crawl_data: List[Dict]) -> Dict[str, Dict]:
    """Build a lookup from normalized URL to crawl entry."""
    url_map = {}
    for entry in crawl_data:
        norm = entry["url_normalized"]
        if norm and norm not in url_map:
            url_map[norm] = entry
    return url_map


def detect_chain(start_url: str, redirect_map: Dict[str, Dict], max_hops: int = 10) -> Tuple[List[str], bool]:
    """
    Follow redirects from start_url to detect chains and loops.
    Returns (chain_path, is_loop).
    """
    visited = []
    current = start_url

    for _ in range(max_hops):
        if current in visited:
            visited.append(current)
            return visited, True  # Loop detected

        visited.append(current)

        entry = redirect_map.get(current)
        if not entry:
            break

        status = entry.get("status_code", "")
        if not status.startswith("3"):
            break

        next_url = entry.get("redirect_url_normalized", "")
        if not next_url:
            break

        current = next_url

    return visited, False


def validate_redirects(spec: List[Dict], crawl_data: List[Dict]) -> Dict:
    """
    Validate redirect spec against actual crawl data.
    Returns categorized results with scoring.
    """
    redirect_map = build_redirect_map(crawl_data)

    # Also build a set of all redirecting URLs from crawl for EXTRA detection
    crawl_redirects = set()
    for entry in crawl_data:
        if entry.get("status_code", "").startswith("3") and entry.get("redirect_url_normalized"):
            crawl_redirects.add(entry["url_normalized"])

    spec_sources = set()
    results = {
        "match": [],
        "wrong_dest": [],
        "wrong_type": [],
        "missing": [],
        "chain": [],
        "loop": [],
        "extra": [],
        "summary": {},
    }

    for rule in spec:
        old_norm = rule["old_url_normalized"]
        new_norm = rule["new_url_normalized"]
        expected_type = rule["type"]
        spec_sources.add(old_norm)

        entry = redirect_map.get(old_norm)

        if not entry:
            # URL not found in crawl at all
            results["missing"].append({
                "old_url": rule["old_url"],
                "expected_destination": rule["new_url"],
                "actual_status": "NOT_IN_CRAWL",
                "notes": "URL not found in crawl data",
            })
            continue

        actual_status = entry.get("status_code", "")
        actual_dest = entry.get("redirect_url_normalized", "")

        # Check if it's actually redirecting
        if not actual_status.startswith("3"):
            results["missing"].append({
                "old_url": rule["old_url"],
                "expected_destination": rule["new_url"],
                "actual_status": actual_status,
                "notes": f"Returns {actual_status} instead of redirect",
            })
            continue

        # Check chain/loop
        chain_path, is_loop = detect_chain(old_norm, redirect_map)

        if is_loop:
            results["loop"].append({
                "old_url": rule["old_url"],
                "expected_destination": rule["new_url"],
                "chain": [redirect_map.get(u, {}).get("url", u) for u in chain_path],
                "notes": "Redirect loop detected",
            })
            continue

        if len(chain_path) > 2:
            # Chain detected — but check if final destination is correct
            final_dest = normalize_url(chain_path[-1]) if chain_path else ""
            chain_entry = {
                "old_url": rule["old_url"],
                "expected_destination": rule["new_url"],
                "chain": [redirect_map.get(u, {}).get("url", u) for u in chain_path],
                "hops": len(chain_path) - 1,
                "final_destination": final_dest,
                "correct_final": final_dest == new_norm,
            }
            results["chain"].append(chain_entry)
            # Don't continue — also check if direct destination is correct
            # for the match/wrong_dest categorization

        # Check destination match
        if actual_dest == new_norm:
            # Check type
            if expected_type and actual_status != expected_type:
                results["wrong_type"].append({
                    "old_url": rule["old_url"],
                    "destination": rule["new_url"],
                    "expected_type": expected_type,
                    "actual_type": actual_status,
                })
            else:
                results["match"].append({
                    "old_url": rule["old_url"],
                    "destination": rule["new_url"],
                    "status": actual_status,
                })
        else:
            results["wrong_dest"].append({
                "old_url": rule["old_url"],
                "expected_destination": rule["new_url"],
                "actual_destination": entry.get("redirect_url", actual_dest),
                "actual_status": actual_status,
            })

    # Detect EXTRA redirects (in crawl but not in spec)
    for norm_url in crawl_redirects:
        if norm_url not in spec_sources:
            entry = redirect_map.get(norm_url, {})
            results["extra"].append({
                "url": entry.get("url", norm_url),
                "destination": entry.get("redirect_url", ""),
                "status": entry.get("status_code", ""),
            })

    # Summary
    total = len(spec)
    match_count = len(results["match"])
    results["summary"] = {
        "total_spec_rules": total,
        "match": match_count,
        "wrong_dest": len(results["wrong_dest"]),
        "wrong_type": len(results["wrong_type"]),
        "missing": len(results["missing"]),
        "chain": len(results["chain"]),
        "loop": len(results["loop"]),
        "extra": len(results["extra"]),
        "score_percent": round((match_count / total) * 100, 1) if total > 0 else 0,
    }

    return results


# ---------------------------------------------------------------------------
# Content Change Detection
# ---------------------------------------------------------------------------

def compare_crawls(old_data: List[Dict], new_data: List[Dict]) -> Dict:
    """
    Compare two crawl datasets to detect content changes.
    """
    old_map = {}
    for entry in old_data:
        norm = entry["url_normalized"]
        if norm:
            old_map[norm] = entry

    new_map = {}
    for entry in new_data:
        norm = entry["url_normalized"]
        if norm:
            new_map[norm] = entry

    old_urls = set(old_map.keys())
    new_urls = set(new_map.keys())

    matched_urls = old_urls & new_urls
    removed_urls = old_urls - new_urls
    new_only_urls = new_urls - old_urls

    changes = {
        "title_changes": [],
        "h1_changes": [],
        "status_changes": [],
        "word_count_changes": [],
        "indexability_changes": [],
        "canonical_changes": [],
        "meta_description_changes": [],
    }

    for url in sorted(matched_urls):
        old = old_map[url]
        new = new_map[url]

        if old["title"] and new["title"] and old["title"] != new["title"]:
            changes["title_changes"].append({
                "url": old["url"],
                "old_title": old["title"],
                "new_title": new["title"],
            })

        if old["h1"] and new["h1"] and old["h1"] != new["h1"]:
            changes["h1_changes"].append({
                "url": old["url"],
                "old_h1": old["h1"],
                "new_h1": new["h1"],
            })

        if old["status_code"] and new["status_code"] and old["status_code"] != new["status_code"]:
            changes["status_changes"].append({
                "url": old["url"],
                "old_status": old["status_code"],
                "new_status": new["status_code"],
                "critical": old["status_code"] == "200" and new["status_code"].startswith(("4", "5")),
            })

        old_wc = old["word_count_int"]
        new_wc = new["word_count_int"]
        if old_wc > 0 and new_wc > 0:
            change_pct = ((new_wc - old_wc) / old_wc) * 100
            if abs(change_pct) >= 20:
                changes["word_count_changes"].append({
                    "url": old["url"],
                    "old_word_count": old_wc,
                    "new_word_count": new_wc,
                    "change_percent": round(change_pct, 1),
                    "significant_drop": change_pct <= -30,
                })

        old_idx = old.get("indexability", "").lower()
        new_idx = new.get("indexability", "").lower()
        if old_idx and new_idx and old_idx != new_idx:
            changes["indexability_changes"].append({
                "url": old["url"],
                "old_indexability": old["indexability"],
                "new_indexability": new["indexability"],
                "critical": "indexable" in old_idx and "non" in new_idx,
            })

        old_canon = normalize_url(old.get("canonical", "")) if old.get("canonical") else ""
        new_canon = normalize_url(new.get("canonical", "")) if new.get("canonical") else ""
        if old_canon and new_canon and old_canon != new_canon:
            changes["canonical_changes"].append({
                "url": old["url"],
                "old_canonical": old.get("canonical", ""),
                "new_canonical": new.get("canonical", ""),
            })

    # Removed and new pages
    removed_pages = []
    for url in sorted(removed_urls):
        entry = old_map[url]
        removed_pages.append({
            "url": entry["url"],
            "title": entry["title"],
            "word_count": entry["word_count_int"],
            "status_code": entry["status_code"],
            "high_risk": entry["word_count_int"] > 500,
        })

    new_pages = []
    for url in sorted(new_only_urls):
        entry = new_map[url]
        if not entry.get("status_code", "").startswith("3"):
            new_pages.append({
                "url": entry["url"],
                "title": entry["title"],
                "word_count": entry["word_count_int"],
                "status_code": entry["status_code"],
            })

    return {
        "summary": {
            "old_total": len(old_data),
            "new_total": len(new_data),
            "matched": len(matched_urls),
            "removed": len(removed_urls),
            "new_pages": len(new_only_urls),
            "title_changes": len(changes["title_changes"]),
            "h1_changes": len(changes["h1_changes"]),
            "status_changes": len(changes["status_changes"]),
            "word_count_changes": len(changes["word_count_changes"]),
            "indexability_changes": len(changes["indexability_changes"]),
            "canonical_changes": len(changes["canonical_changes"]),
        },
        "changes": changes,
        "removed_pages": removed_pages,
        "new_pages": new_pages,
    }


# ---------------------------------------------------------------------------
# Wayback Machine CDX API
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 30) -> str:
    """HTTP GET using requests or urllib fallback."""
    if HAS_REQUESTS:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "42-migration-validator/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")


def query_wayback_cdx(domain: str, years: int = 5, limit: int = 10000) -> Dict:
    """
    Query the Wayback Machine CDX API for historical snapshots.
    Returns structured data about site evolution.
    """
    # Clean domain
    domain = domain.strip().lower()
    domain = domain.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    domain = domain.rstrip("/")

    # Calculate date range
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    from_ts = start_date.strftime("%Y%m%d")
    to_ts = end_date.strftime("%Y%m%d")

    # Query all pages
    cdx_url = (
        f"https://web.archive.org/cdx/search/cdx"
        f"?url={domain}/*"
        f"&output=json"
        f"&fl=timestamp,original,statuscode,mimetype"
        f"&collapse=urlkey"
        f"&from={from_ts}"
        f"&to={to_ts}"
        f"&limit={limit}"
    )

    print(f"Querying Wayback CDX API for {domain}...", file=sys.stderr)

    try:
        raw = _http_get(cdx_url, timeout=60)
        rows = json.loads(raw)
    except Exception as e:
        return {"error": f"CDX API query failed: {str(e)}", "domain": domain}

    if not rows or len(rows) < 2:
        return {"error": "No snapshots found", "domain": domain, "snapshots": []}

    # First row is headers
    headers = rows[0]
    snapshots = []
    for row in rows[1:]:
        entry = dict(zip(headers, row))
        snapshots.append(entry)

    # Group by year-month
    by_period = defaultdict(set)
    for snap in snapshots:
        ts = snap.get("timestamp", "")
        if len(ts) >= 6:
            period = f"{ts[:4]}-{ts[4:6]}"
            by_period[period].add(snap.get("original", ""))

    timeline = []
    prev_count = 0
    for period in sorted(by_period.keys()):
        count = len(by_period[period])
        change = count - prev_count if prev_count > 0 else 0
        change_pct = round((change / prev_count) * 100, 1) if prev_count > 0 else 0
        timeline.append({
            "period": period,
            "unique_urls": count,
            "change": change,
            "change_percent": change_pct,
        })
        prev_count = count

    # Query robots.txt history
    robots_url = (
        f"https://web.archive.org/cdx/search/cdx"
        f"?url={domain}/robots.txt"
        f"&output=json"
        f"&fl=timestamp,statuscode,digest"
        f"&from={from_ts}"
        f"&to={to_ts}"
        f"&collapse=digest"
        f"&limit=50"
    )

    robots_versions = []
    try:
        raw = _http_get(robots_url, timeout=30)
        robots_rows = json.loads(raw)
        if robots_rows and len(robots_rows) > 1:
            r_headers = robots_rows[0]
            for row in robots_rows[1:]:
                entry = dict(zip(r_headers, row))
                ts = entry.get("timestamp", "")
                robots_versions.append({
                    "timestamp": ts,
                    "date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts,
                    "status_code": entry.get("statuscode", ""),
                    "digest": entry.get("digest", ""),
                    "wayback_url": f"https://web.archive.org/web/{ts}/https://{domain}/robots.txt",
                })
    except Exception:
        pass  # robots.txt history is optional

    # Detect URL pattern changes by year
    by_year = defaultdict(set)
    for snap in snapshots:
        ts = snap.get("timestamp", "")
        if len(ts) >= 4:
            year = ts[:4]
            original = snap.get("original", "")
            parsed = urlparse(original)
            # Extract path pattern (first two segments)
            parts = [p for p in parsed.path.split("/") if p]
            pattern = "/" + "/".join(parts[:2]) + "/..." if len(parts) >= 2 else parsed.path
            by_year[year].add(pattern)

    structural_changes = []
    years_sorted = sorted(by_year.keys())
    for i in range(1, len(years_sorted)):
        prev_year = years_sorted[i - 1]
        curr_year = years_sorted[i]
        new_patterns = by_year[curr_year] - by_year[prev_year]
        removed_patterns = by_year[prev_year] - by_year[curr_year]
        if new_patterns or removed_patterns:
            structural_changes.append({
                "year": curr_year,
                "new_patterns": sorted(list(new_patterns))[:20],
                "removed_patterns": sorted(list(removed_patterns))[:20],
            })

    return {
        "domain": domain,
        "period": f"{from_ts[:4]}-{to_ts[:4]}",
        "total_snapshots": len(snapshots),
        "timeline": timeline,
        "robots_versions": robots_versions,
        "structural_changes": structural_changes,
    }


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def cmd_validate(args):
    """Run redirect validation."""
    print(f"Parsing spec: {args.spec}", file=sys.stderr)
    spec = parse_spec_csv(args.spec)
    print(f"  Found {len(spec)} redirect rules", file=sys.stderr)

    print(f"Parsing crawl: {args.crawl}", file=sys.stderr)
    crawl = parse_crawl_csv(args.crawl)
    print(f"  Found {len(crawl)} crawled URLs", file=sys.stderr)

    results = validate_redirects(spec, crawl)

    print(f"\nResults:", file=sys.stderr)
    print(f"  Score: {results['summary']['score_percent']}%", file=sys.stderr)
    print(f"  Match: {results['summary']['match']}", file=sys.stderr)
    print(f"  Wrong dest: {results['summary']['wrong_dest']}", file=sys.stderr)
    print(f"  Missing: {results['summary']['missing']}", file=sys.stderr)
    print(f"  Chain: {results['summary']['chain']}", file=sys.stderr)
    print(f"  Loop: {results['summary']['loop']}", file=sys.stderr)
    print(f"  Extra: {results['summary']['extra']}", file=sys.stderr)

    output = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nResults written to {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_compare(args):
    """Run content change detection."""
    print(f"Parsing old crawl: {args.old}", file=sys.stderr)
    old_data = parse_crawl_csv(args.old)
    print(f"  Found {len(old_data)} pages", file=sys.stderr)

    print(f"Parsing new crawl: {args.new}", file=sys.stderr)
    new_data = parse_crawl_csv(args.new)
    print(f"  Found {len(new_data)} pages", file=sys.stderr)

    results = compare_crawls(old_data, new_data)

    print(f"\nResults:", file=sys.stderr)
    print(f"  Matched pages: {results['summary']['matched']}", file=sys.stderr)
    print(f"  Removed pages: {results['summary']['removed']}", file=sys.stderr)
    print(f"  New pages: {results['summary']['new_pages']}", file=sys.stderr)
    print(f"  Title changes: {results['summary']['title_changes']}", file=sys.stderr)
    print(f"  Word count changes: {results['summary']['word_count_changes']}", file=sys.stderr)

    output = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nResults written to {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_history(args):
    """Query Wayback Machine for historical analysis."""
    results = query_wayback_cdx(args.domain, years=args.years)

    if "error" in results:
        print(f"Error: {results['error']}", file=sys.stderr)

    output = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nResults written to {args.output}", file=sys.stderr)
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Website Migration Redirect Validator (42:migration)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s validate --spec redirects.csv --crawl crawl.csv --output results.json
  %(prog)s compare --old old-crawl.csv --new new-crawl.csv --output changes.json
  %(prog)s history --domain example.com --years 5 --output history.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate redirect spec vs crawl data")
    p_validate.add_argument("--spec", required=True, help="Redirect specification CSV")
    p_validate.add_argument("--crawl", required=True, help="Actual crawl data CSV")
    p_validate.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare old and new crawl data")
    p_compare.add_argument("--old", required=True, help="Old site crawl CSV")
    p_compare.add_argument("--new", required=True, help="New site crawl CSV")
    p_compare.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    # history
    p_history = subparsers.add_parser("history", help="Wayback Machine historical analysis")
    p_history.add_argument("--domain", required=True, help="Domain to analyze")
    p_history.add_argument("--years", type=int, default=5, help="Years of history (default: 5)")
    p_history.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "validate": cmd_validate,
        "compare": cmd_compare,
        "history": cmd_history,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
