#!/usr/bin/env python3
"""
Internal Link Graph — Visualization, Analysis & Revenue Optimization.

Mode 1 — visualize:  Build NetworkX graph, calculate PageRank/centrality,
                      identify orphans/hubs/authorities/bridges.
Mode 2 — anchors:    Audit anchor text diversity and relevance.
Mode 3 — revenue:    Cross-analyze internal links with transaction data.

Output: JSON to stdout for Claude to process into LINK-GRAPH.md.
"""

import sys
import json
import csv
import re
import argparse
from collections import Counter, defaultdict
from typing import Optional
from urllib.parse import urlparse

try:
    import networkx as nx
except ImportError:
    nx = None


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

INLINK_COLUMN_MAP = {
    "source": ["source", "from", "source url", "source address",
                "bron", "van"],
    "destination": ["destination", "target", "to", "destination url",
                     "target url", "dest", "bestemming", "naar",
                     "address"],
    "type": ["type", "link type", "type of link"],
    "anchor": ["anchor", "anchor text", "link text", "ankertekst",
               "alt text"],
    "follow": ["follow", "nofollow", "rel", "status code"],
}

TRANSACTION_COLUMN_MAP = {
    "page": ["page", "landing page", "page path", "url", "address",
             "page path + query string", "pagina"],
    "transactions": ["transactions", "conversions", "purchases",
                      "ecommerce purchases", "transacties", "aankopen"],
    "revenue": ["revenue", "purchase revenue", "total revenue",
                "omzet", "opbrengst", "transaction revenue",
                "item revenue"],
}


def normalize_columns(headers: list[str], column_map: dict) -> dict:
    """Map actual CSV headers to canonical field names."""
    mapping = {}
    lower_headers = [h.strip().lower() for h in headers]
    for canonical, variants in column_map.items():
        for variant in variants:
            if variant in lower_headers:
                idx = lower_headers.index(variant)
                mapping[canonical] = headers[idx]
                break
    return mapping


def read_csv(filepath: str) -> list[dict]:
    """Read CSV with flexible encoding detection."""
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                reader = csv.DictReader(f, dialect=dialect)
                rows = list(reader)
                if rows:
                    return rows
        except (UnicodeDecodeError, csv.Error):
            continue
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)


def normalize_url(url: str) -> str:
    """Normalize URL for matching: lowercase, strip trailing slash, remove fragment."""
    url = url.strip().lower()
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    if parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    return path


# ---------------------------------------------------------------------------
# Generic anchors to flag
# ---------------------------------------------------------------------------

GENERIC_ANCHORS = {
    "click here", "read more", "learn more", "here", "this", "link",
    "more", "lees meer", "bekijk", "klik hier", "meer info", "meer",
    "see more", "view", "details", "info", "ga naar", "bekijk meer",
    "meer informatie", "lees verder", "verder lezen",
}


# ---------------------------------------------------------------------------
# Mode 1: Link Graph Visualization
# ---------------------------------------------------------------------------

def build_link_graph(
    filepath: str,
    min_links: int = 0,
    export_gexf: Optional[str] = None,
) -> dict:
    """Build NetworkX graph and calculate metrics."""
    if nx is None:
        return {"error": "NetworkX not installed. Run: pip install networkx"}

    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), INLINK_COLUMN_MAP)

    source_col = col_map.get("source")
    dest_col = col_map.get("destination")
    type_col = col_map.get("type")

    if not source_col:
        return {"error": f"No source column found. Available: {list(rows[0].keys())}"}
    if not dest_col:
        return {"error": f"No destination column found. Available: {list(rows[0].keys())}"}

    # Build graph — filter to hyperlinks only
    G = nx.DiGraph()
    total_links = 0
    skipped = 0

    for row in rows:
        source = normalize_url(row.get(source_col, ""))
        dest = normalize_url(row.get(dest_col, ""))
        link_type = row.get(type_col, "").strip().lower() if type_col else ""

        if not source or not dest:
            skipped += 1
            continue

        # Skip non-hyperlinks if type column exists
        if type_col and link_type and "hyperlink" not in link_type and "ahref" not in link_type:
            skipped += 1
            continue

        # Skip self-links
        if source == dest:
            skipped += 1
            continue

        if G.has_edge(source, dest):
            G[source][dest]["weight"] += 1
        else:
            G.add_edge(source, dest, weight=1)
        total_links += 1

    if G.number_of_nodes() == 0:
        return {"error": "Graph has no nodes. Check column mapping."}

    # Calculate metrics
    pagerank = nx.pagerank(G, alpha=0.85)
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())

    # Betweenness centrality (can be slow for large graphs)
    if G.number_of_nodes() <= 10000:
        betweenness = nx.betweenness_centrality(G, normalized=True)
    else:
        # Sample-based approximation for large graphs
        betweenness = nx.betweenness_centrality(G, normalized=True, k=min(500, G.number_of_nodes()))

    # Classify pages
    all_pages = []
    for node in G.nodes():
        ind = in_degree.get(node, 0)
        outd = out_degree.get(node, 0)
        pr = pagerank.get(node, 0)
        bc = betweenness.get(node, 0)

        classifications = []
        if ind == 0:
            classifications.append("orphan")
        if outd == 0:
            classifications.append("dead_end")

        all_pages.append({
            "url": node,
            "pagerank": round(pr, 6),
            "in_degree": ind,
            "out_degree": outd,
            "betweenness": round(bc, 6),
            "classifications": classifications,
        })

    # Sort by PageRank
    all_pages.sort(key=lambda x: x["pagerank"], reverse=True)

    # Compute thresholds for hub/authority/bridge classification
    pr_values = [p["pagerank"] for p in all_pages]
    in_values = [p["in_degree"] for p in all_pages]
    out_values = [p["out_degree"] for p in all_pages]
    bc_values = [p["betweenness"] for p in all_pages]

    pr_p75 = sorted(pr_values)[int(len(pr_values) * 0.75)] if pr_values else 0
    in_p75 = sorted(in_values)[int(len(in_values) * 0.75)] if in_values else 0
    out_p75 = sorted(out_values)[int(len(out_values) * 0.75)] if out_values else 0
    bc_p75 = sorted(bc_values)[int(len(bc_values) * 0.75)] if bc_values else 0

    for page in all_pages:
        if page["out_degree"] >= out_p75 and page["out_degree"] > 5:
            page["classifications"].append("hub")
        if page["in_degree"] >= in_p75 and page["pagerank"] >= pr_p75:
            page["classifications"].append("authority")
        if page["betweenness"] >= bc_p75 and page["betweenness"] > 0.001:
            page["classifications"].append("bridge")

    # Filter by min_links if specified
    if min_links > 0:
        filtered_pages = [p for p in all_pages if p["in_degree"] >= min_links or p["out_degree"] >= min_links or "orphan" in p["classifications"]]
    else:
        filtered_pages = all_pages

    # Separate classified pages
    orphans = [p for p in all_pages if "orphan" in p["classifications"]]
    hubs = [p for p in all_pages if "hub" in p["classifications"]]
    authorities = [p for p in all_pages if "authority" in p["classifications"]]
    bridges = [p for p in all_pages if "bridge" in p["classifications"]]
    dead_ends = [p for p in all_pages if "dead_end" in p["classifications"]]

    # Export GEXF if requested
    if export_gexf:
        # Add attributes to nodes for Gephi
        for node in G.nodes():
            G.nodes[node]["pagerank"] = pagerank.get(node, 0)
            G.nodes[node]["in_degree"] = in_degree.get(node, 0)
            G.nodes[node]["out_degree"] = out_degree.get(node, 0)
            G.nodes[node]["betweenness"] = betweenness.get(node, 0)
        nx.write_gexf(G, export_gexf)

    return {
        "mode": "visualize",
        "summary": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "total_links_parsed": total_links,
            "skipped_links": skipped,
            "orphan_pages": len(orphans),
            "hub_pages": len(hubs),
            "authority_pages": len(authorities),
            "bridge_pages": len(bridges),
            "dead_end_pages": len(dead_ends),
            "avg_in_degree": round(sum(in_values) / len(in_values), 1) if in_values else 0,
            "avg_out_degree": round(sum(out_values) / len(out_values), 1) if out_values else 0,
            "max_pagerank": round(max(pr_values), 6) if pr_values else 0,
            "gexf_exported": export_gexf if export_gexf else None,
        },
        "top_pages_by_pagerank": filtered_pages[:30],
        "orphan_pages": orphans[:50],
        "hub_pages": sorted(hubs, key=lambda x: x["out_degree"], reverse=True)[:20],
        "authority_pages": sorted(authorities, key=lambda x: x["pagerank"], reverse=True)[:20],
        "bridge_pages": sorted(bridges, key=lambda x: x["betweenness"], reverse=True)[:20],
        "dead_end_pages": dead_ends[:30],
    }


# ---------------------------------------------------------------------------
# Mode 2: Anchor Text Analysis
# ---------------------------------------------------------------------------

def analyze_anchors(filepath: str) -> dict:
    """Audit anchor text diversity and quality."""
    rows = read_csv(filepath)
    if not rows:
        return {"error": "No rows found in CSV"}

    col_map = normalize_columns(list(rows[0].keys()), INLINK_COLUMN_MAP)

    dest_col = col_map.get("destination")
    anchor_col = col_map.get("anchor")
    type_col = col_map.get("type")

    if not dest_col:
        return {"error": f"No destination column found. Available: {list(rows[0].keys())}"}
    if not anchor_col:
        return {"error": f"No anchor column found. Available: {list(rows[0].keys())}"}

    # Group anchors by target URL
    anchors_by_target = defaultdict(list)

    for row in rows:
        dest = normalize_url(row.get(dest_col, ""))
        anchor = row.get(anchor_col, "").strip()
        link_type = row.get(type_col, "").strip().lower() if type_col else ""

        if not dest:
            continue

        # Skip non-hyperlinks
        if type_col and link_type and "hyperlink" not in link_type:
            continue

        anchors_by_target[dest].append(anchor)

    # Analyze each target
    target_analysis = []
    generic_issues = Counter()
    empty_anchor_targets = []
    duplicate_anchor_targets = defaultdict(list)  # anchor -> [different target URLs]

    # Track anchor→targets for duplicate detection
    anchor_to_targets = defaultdict(set)
    for target, anchors in anchors_by_target.items():
        for a in anchors:
            if a:
                anchor_to_targets[a.lower()].add(target)

    for target, anchors in anchors_by_target.items():
        total = len(anchors)
        non_empty = [a for a in anchors if a]
        empty_count = total - len(non_empty)

        unique_anchors = set(a.lower() for a in non_empty)
        diversity = round(len(unique_anchors) / total, 3) if total > 0 else 0

        # Count generic anchors
        generic_count = 0
        anchor_counter = Counter(a.lower() for a in non_empty)
        for anchor_text in unique_anchors:
            if anchor_text in GENERIC_ANCHORS:
                generic_count += anchor_counter[anchor_text]
                generic_issues[anchor_text] += anchor_counter[anchor_text]

        # Check relevance: does anchor relate to URL path?
        path_words = set(re.findall(r"[a-z]+", urlparse(target).path.lower()))
        relevant_count = 0
        for anchor_text in non_empty:
            anchor_words = set(re.findall(r"[a-z]+", anchor_text.lower()))
            if anchor_words & path_words:
                relevant_count += 1

        relevance = round(relevant_count / total, 3) if total > 0 else 0

        issues = []
        if diversity < 0.15 and total > 3:
            issues.append("over_optimized")
        if generic_count > total * 0.3:
            issues.append("too_many_generic")
        if empty_count > total * 0.5:
            issues.append("many_empty_anchors")
        if relevance < 0.3 and total > 3:
            issues.append("low_relevance")

        if empty_count > 0:
            empty_anchor_targets.append({"url": target, "empty_count": empty_count, "total": total})

        target_analysis.append({
            "url": target,
            "total_links": total,
            "unique_anchors": len(unique_anchors),
            "diversity_score": diversity,
            "relevance_score": relevance,
            "generic_count": generic_count,
            "empty_count": empty_count,
            "top_anchors": [
                {"text": text, "count": count}
                for text, count in anchor_counter.most_common(5)
            ],
            "issues": issues,
        })

    # Sort by issues (most problematic first)
    target_analysis.sort(key=lambda x: (len(x["issues"]), -x["diversity_score"]), reverse=True)

    # Duplicate anchors pointing to different targets
    duplicate_anchors = []
    for anchor_text, targets in anchor_to_targets.items():
        if len(targets) > 1 and anchor_text not in GENERIC_ANCHORS:
            duplicate_anchors.append({
                "anchor": anchor_text,
                "targets": sorted(targets)[:5],
                "target_count": len(targets),
            })
    duplicate_anchors.sort(key=lambda x: x["target_count"], reverse=True)

    # Summary
    all_diversities = [t["diversity_score"] for t in target_analysis if t["total_links"] > 2]

    return {
        "mode": "anchors",
        "summary": {
            "total_targets": len(target_analysis),
            "total_links_analyzed": sum(t["total_links"] for t in target_analysis),
            "targets_with_issues": len([t for t in target_analysis if t["issues"]]),
            "avg_diversity": round(sum(all_diversities) / len(all_diversities), 3) if all_diversities else 0,
            "total_generic_anchors": sum(generic_issues.values()),
            "total_empty_anchors": sum(t["empty_count"] for t in target_analysis),
        },
        "targets_with_issues": [t for t in target_analysis if t["issues"]][:50],
        "all_targets": target_analysis[:100],
        "generic_anchor_summary": [
            {"anchor": text, "count": count}
            for text, count in generic_issues.most_common(20)
        ],
        "duplicate_anchors": duplicate_anchors[:30],
        "empty_anchor_targets": sorted(empty_anchor_targets, key=lambda x: x["empty_count"], reverse=True)[:20],
    }


# ---------------------------------------------------------------------------
# Mode 3: Revenue vs Links
# ---------------------------------------------------------------------------

def analyze_revenue_links(
    inlinks_file: str,
    transactions_file: str,
) -> dict:
    """Cross-analyze internal link counts with transaction data."""
    # Count internal links per page (in-degree)
    link_rows = read_csv(inlinks_file)
    if not link_rows:
        return {"error": f"No rows found in {inlinks_file}"}

    link_col_map = normalize_columns(list(link_rows[0].keys()), INLINK_COLUMN_MAP)
    dest_col = link_col_map.get("destination")
    type_col = link_col_map.get("type")

    if not dest_col:
        return {"error": f"No destination column. Available: {list(link_rows[0].keys())}"}

    link_counts = Counter()
    for row in link_rows:
        dest = normalize_url(row.get(dest_col, ""))
        link_type = row.get(type_col, "").strip().lower() if type_col else ""

        if not dest:
            continue
        if type_col and link_type and "hyperlink" not in link_type:
            continue

        link_counts[dest] += 1

    # Parse transaction data
    tx_rows = read_csv(transactions_file)
    if not tx_rows:
        return {"error": f"No rows found in {transactions_file}"}

    tx_col_map = normalize_columns(list(tx_rows[0].keys()), TRANSACTION_COLUMN_MAP)
    page_col = tx_col_map.get("page")
    tx_count_col = tx_col_map.get("transactions")
    revenue_col = tx_col_map.get("revenue")

    if not page_col:
        return {"error": f"No page column in transactions file. Available: {list(tx_rows[0].keys())}"}

    # Build revenue data
    revenue_data = {}
    for row in tx_rows:
        page = normalize_url(row.get(page_col, ""))
        if not page:
            continue

        transactions = 0
        revenue = 0.0

        if tx_count_col:
            try:
                val = row.get(tx_count_col, "0").replace(",", "").replace(".", "")
                transactions = int(val) if val else 0
            except (ValueError, TypeError):
                transactions = 0

        if revenue_col:
            try:
                val = row.get(revenue_col, "0")
                val = re.sub(r"[^\d.,\-]", "", val)
                # Handle European number format (1.234,56)
                if "," in val and "." in val:
                    if val.rindex(",") > val.rindex("."):
                        val = val.replace(".", "").replace(",", ".")
                    else:
                        val = val.replace(",", "")
                elif "," in val:
                    val = val.replace(",", ".")
                revenue = float(val) if val else 0.0
            except (ValueError, TypeError):
                revenue = 0.0

        revenue_data[page] = {
            "transactions": transactions,
            "revenue": revenue,
        }

    # Join datasets
    all_urls = set(link_counts.keys()) | set(revenue_data.keys())
    joined = []

    for url in all_urls:
        links = link_counts.get(url, 0)
        rev_info = revenue_data.get(url, {"transactions": 0, "revenue": 0.0})
        revenue = rev_info["revenue"]
        transactions = rev_info["transactions"]

        revenue_per_link = round(revenue / links, 2) if links > 0 else 0

        joined.append({
            "url": url,
            "internal_links": links,
            "transactions": transactions,
            "revenue": round(revenue, 2),
            "revenue_per_link": revenue_per_link,
        })

    # Classify
    high_revenue_few_links = sorted(
        [j for j in joined if j["revenue"] > 0 and j["internal_links"] < 10],
        key=lambda x: x["revenue"],
        reverse=True,
    )

    many_links_no_revenue = sorted(
        [j for j in joined if j["revenue"] == 0 and j["internal_links"] > 10],
        key=lambda x: x["internal_links"],
        reverse=True,
    )

    # Efficiency ranking (best revenue per link)
    efficient = sorted(
        [j for j in joined if j["revenue"] > 0 and j["internal_links"] > 0],
        key=lambda x: x["revenue_per_link"],
        reverse=True,
    )

    total_revenue = sum(j["revenue"] for j in joined)
    total_links = sum(j["internal_links"] for j in joined)

    return {
        "mode": "revenue",
        "summary": {
            "total_pages_joined": len(joined),
            "pages_with_revenue": len([j for j in joined if j["revenue"] > 0]),
            "pages_with_links": len([j for j in joined if j["internal_links"] > 0]),
            "total_revenue": round(total_revenue, 2),
            "total_internal_links": total_links,
            "high_revenue_few_links_count": len(high_revenue_few_links),
            "many_links_no_revenue_count": len(many_links_no_revenue),
        },
        "high_revenue_few_links": high_revenue_few_links[:30],
        "many_links_no_revenue": many_links_no_revenue[:30],
        "most_efficient": efficient[:20],
        "least_efficient": sorted(
            [j for j in joined if j["revenue"] > 0 and j["internal_links"] > 0],
            key=lambda x: x["revenue_per_link"],
        )[:20],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Internal Link Graph — Visualization, Analysis & Revenue"
    )
    subparsers = parser.add_subparsers(dest="command", help="Mode to run")

    # Visualize
    viz = subparsers.add_parser("visualize", help="Build and analyze link graph")
    viz.add_argument("csv_file", help="Screaming Frog Inlinks:All CSV")
    viz.add_argument("--min-links", type=int, default=0,
                     help="Minimum links to include in output (default: 0)")
    viz.add_argument("--export-gexf", default=None,
                     help="Export GEXF file for Gephi (e.g., graph.gexf)")

    # Anchors
    anc = subparsers.add_parser("anchors", help="Anchor text analysis")
    anc.add_argument("csv_file", help="Screaming Frog Inlinks:All CSV")

    # Revenue
    rev = subparsers.add_parser("revenue", help="Revenue vs internal links")
    rev.add_argument("inlinks_file", help="Screaming Frog Inlinks:All CSV")
    rev.add_argument("transactions_file", help="GA transactions CSV")

    args = parser.parse_args()

    if args.command == "visualize":
        result = build_link_graph(
            filepath=args.csv_file,
            min_links=args.min_links,
            export_gexf=args.export_gexf,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "anchors":
        result = analyze_anchors(args.csv_file)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "revenue":
        result = analyze_revenue_links(args.inlinks_file, args.transactions_file)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
