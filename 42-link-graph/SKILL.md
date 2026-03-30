---
name: 42-link-graph
description: >
  Internal link graph visualization and analysis. Builds a NetworkX directed
  graph from Screaming Frog link data, calculates PageRank/centrality metrics,
  identifies orphan pages, hubs, authorities, and bridges, audits anchor text
  quality, and cross-analyzes revenue vs internal link counts. Use when user
  says "link graph", "internal link graph", "link visualisatie", "link analyse",
  "orphan pages", "anchor text audit", "pagerank analyse", "link equity",
  "revenue links", "hub pages", "authority pages", "gephi export",
  "interne links grafiek", "link netwerk".
version: 1.0.0
tags: [seo, link-graph, networkx, pagerank, anchor-text, orphan-pages, revenue, gephi]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*inlink*"
    - "**/*link*"
    - "**/*anchor*"
    - "**/*transaction*"
    - "**/LINK-GRAPH.md"
  bashPattern:
    - "link.graph"
    - "pagerank"
    - "orphan"
    - "anchor.text"
---

# Internal Link Graph — Visualization, Analysis & Revenue Optimization

## Purpose

Build and analyze the internal link graph of a website using Screaming Frog data. Three complementary analysis modes:

1. **Link Graph Visualization:** Build directed graph, calculate PageRank/centrality, find orphans/hubs/authorities
2. **Anchor Text Analysis:** Audit anchor text diversity and relevance per target URL
3. **Revenue vs Links:** Cross-analyze internal link counts with transaction data to find revenue optimization opportunities

---

## Commands

```
/42:link-graph visualize <sf-inlinks.csv> [--min-links 3]
/42:link-graph anchors <sf-inlinks.csv> [--ai-grade]
/42:link-graph revenue <sf-inlinks.csv> <ga-transactions.csv>
```

---

## Mode 1 — Link Graph Visualization

### Input

Screaming Frog **Inlinks:All** export CSV containing:
- **Source**: source page URL
- **Destination/Target**: target page URL
- **Type**: link type (hyperlink, canonical, etc.)
- **Anchor**: anchor text (optional for this mode)

### Workflow

1. **Parse SF Inlinks:All export** — filter to follow/dofollow hyperlinks only
2. **Build NetworkX directed graph** (source → target)
3. **Calculate graph metrics:**
   - **PageRank:** Algorithmic importance score per page
   - **In-degree:** Number of internal links pointing TO a page
   - **Out-degree:** Number of internal links FROM a page
   - **Betweenness centrality:** How often a page sits on shortest paths between other pages
4. **Classify pages:**
   - **Orphan pages:** 0 in-degree (no internal links pointing to them)
   - **Hub pages:** High out-degree (link out to many pages — navigation hubs)
   - **Authority pages:** High in-degree + high PageRank (most internally linked)
   - **Bridge pages:** High betweenness centrality (critical connectors in the graph)
   - **Dead ends:** 0 out-degree (link to no other internal page)
5. **Generate graph metrics summary**
6. **Export GEXF** for Gephi visualization (optional)

### Key Metrics Table

```
Page Metrics — Top 20 by PageRank:

| URL | PageRank | In-degree | Out-degree | Betweenness | Classification |
|-----|----------|-----------|-----------|-------------|---------------|
| /   | 0.142    | 847       | 156       | 0.312       | Hub + Authority |
| /laptops | 0.038 | 234    | 89        | 0.087       | Authority     |
| /about   | 0.002 | 3       | 12        | 0.001       | Low priority  |
```

### GEXF Export

The script exports a GEXF file that can be opened in Gephi for interactive graph visualization:
- Node size = PageRank
- Node color = classification (hub/authority/orphan/bridge)
- Edge weight = number of links between pages

---

## Mode 2 — Anchor Text Analysis

### Input

Same SF Inlinks:All CSV, but now focused on the **Anchor** column.

### Workflow

1. **Extract all internal anchor texts** from SF data
2. **Group by target URL:**
   - List all anchors pointing to each URL
   - Count total links and unique anchors
3. **Score diversity:** `unique_anchors / total_anchors`
   - 1.0 = every link uses different anchor text (high diversity)
   - 0.1 = almost all links use the same anchor (low diversity)
4. **Score relevance:** Compare anchor texts against target page URL/path
   - Does the anchor text relate to the page topic?
5. **Flag issues:**
   - Generic anchors: "click here", "read more", "lees meer", "bekijk"
   - Duplicate anchors: same anchor text pointing to different pages
   - Empty anchors: image links without alt text
6. **Optional AI grading** (`--ai-grade`):
   - Claude evaluates each anchor as: High / Medium / Fail / Typo
   - Based on relevance to target page topic

### Example Output

```
ANCHOR TEXT AUDIT — Top Issues:

Target: /laptops/gaming
  Total links: 47 | Unique anchors: 4 | Diversity: 0.09 (LOW)
  Anchors: "gaming laptops" (38x), "bekijk" (5x), "click here" (3x), "gaming" (1x)
  Issue: Over-optimized — 81% identical anchor text

Target: /contact
  Total links: 234 | Unique anchors: 2 | Diversity: 0.01 (VERY LOW)
  Anchors: "contact" (230x), "neem contact op" (4x)
  Issue: Acceptable for navigational page
```

---

## Mode 3 — Revenue vs Links

### Input

Two files:
1. **SF Inlinks CSV** — for internal link counts per page
2. **GA Transactions CSV** — Google Analytics/GA4 export with:
   - **page/landing page**: URL
   - **transactions/conversions**: transaction count
   - **revenue**: revenue amount

### Workflow

1. **Count internal links per page** from SF data (in-degree)
2. **Parse GA transaction data** per page
3. **Join datasets** on URL (normalize trailing slashes, protocol)
4. **Identify opportunities:**
   - **High revenue, few links:** Pages generating revenue but underlinked — priority linking targets
   - **Many links, zero revenue:** Pages with high link equity but no commercial value — potential link waste
   - **Balanced:** Pages with proportional links-to-revenue ratio
5. **Calculate efficiency score:** `revenue_per_link = revenue / in_degree`
6. **Rank by opportunity size**

### Example Output

```
REVENUE vs INTERNAL LINKS:

HIGH REVENUE, FEW LINKS (priority linking targets):
| URL | Revenue | Transactions | Internal Links | Revenue/Link |
|-----|---------|-------------|---------------|-------------|
| /product/sony-wh1000xm5 | €45,230 | 312 | 3 | €15,077 |
| /product/iphone-15-pro   | €89,100 | 198 | 5 | €17,820 |

MANY LINKS, ZERO REVENUE (link equity waste):
| URL | Revenue | Internal Links | Classification |
|-----|---------|---------------|---------------|
| /blog/history-of-audio | €0 | 47 | Informational |
| /about/team             | €0 | 34 | Corporate     |
```

---

## Running the Script

```bash
# Link Graph Visualization
python3 scripts/link_graph.py visualize sf-inlinks.csv --min-links 3

# Anchor Text Analysis
python3 scripts/link_graph.py anchors sf-inlinks.csv

# Revenue vs Links
python3 scripts/link_graph.py revenue sf-inlinks.csv ga-transactions.csv

# Export GEXF for Gephi
python3 scripts/link_graph.py visualize sf-inlinks.csv --export-gexf graph.gexf
```

### Dependencies

```bash
pip install networkx
```

The script outputs JSON to stdout. Claude reads the JSON and generates the final LINK-GRAPH.md report.

---

## Output Format — LINK-GRAPH.md

```markdown
# Internal Link Graph Analysis

## Executive Summary
- Total pages: X | Total internal links: Y
- Orphan pages: Z | Hub pages: W | Bridge pages: V
- Top PageRank page: / (score: 0.142)

## Graph Metrics — Top Pages by PageRank
| URL | PageRank | In-degree | Out-degree | Betweenness | Type |
|-----|----------|-----------|-----------|-------------|------|

## Orphan Pages (0 internal links pointing to them)
| URL | Out-degree | Notes |
|-----|-----------|-------|

## Hub Pages (high out-degree)
| URL | Out-degree | In-degree | PageRank |
|-----|-----------|-----------|----------|

## Bridge Pages (high betweenness centrality)
| URL | Betweenness | In-degree | Out-degree |
|-----|------------|-----------|-----------|

## Anchor Text Audit
### Low Diversity Targets
| Target URL | Total Links | Unique Anchors | Diversity | Top Anchor |
|-----------|------------|---------------|-----------|-----------|

### Generic Anchor Issues
| Anchor | Used For | Count |
|--------|---------|-------|

## Revenue Opportunities
### High Revenue, Few Links
| URL | Revenue | Links | Revenue/Link |
|-----|---------|-------|-------------|

### Link Equity Waste
| URL | Revenue | Links | Action |
|-----|---------|-------|--------|

## Recommendations
1. Add internal links to high-revenue orphan/underlinked pages
2. Diversify anchor text for over-optimized targets
3. Reduce link equity to zero-revenue pages
4. Create hub pages for isolated content clusters
```

---

## Cross-references

- **42:internal-links** — Complementary: competitor-focused internal link analysis (this skill = own-site graph)
- **42:technical** — Technical SEO audit includes crawlability checks related to link structure
- **42:audit** — Full site audit incorporates link graph findings
