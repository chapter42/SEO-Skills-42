---
name: 42-serp-cluster
description: >
  Cluster keywords based on shared organic SERP URLs. If two keywords share 3+
  of the same ranking URLs, they belong to the same topic cluster and should be
  targeted by the same page. Uses URL overlap (not embeddings) for real-world
  SERP similarity. Use when user says "SERP clustering", "keyword clustering",
  "topic clusters from SERPs", "group keywords by SERP overlap", "which keywords
  should share a page", "consolidate keywords", "SERP similarity".
version: 1.0.0
tags: [seo, serp, clustering, keywords, topic-clusters, cannibalization, consolidation]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*serp*"
    - "**/*ranking*"
    - "**/*keyword*"
    - "**/*cluster*"
  bashPattern:
    - "serp.cluster"
    - "keyword.cluster"
    - "topic.cluster"
---

# SERP-Based Keyword Clustering

## Purpose

Cluster keywords by analyzing which URLs they share in organic search results. Two keywords that surface the same URLs are effectively competing for the same SERP -- Google treats them as the same topic. This is the most reliable clustering signal because it reflects Google's actual understanding, not semantic similarity guesses.

**Core principle:** If keyword A and keyword B share 3+ of the same top-10 URLs, they belong to the same topic cluster and should be targeted by a single page.

**Use cases:**

1. **Topic consolidation:** Find keywords that should share one landing page
2. **Content planning:** Group hundreds of keywords into actionable clusters
3. **Cannibalization prevention:** Avoid creating separate pages for same-SERP keywords
4. **Hub page identification:** Find the URL that already ranks for the most keywords in a cluster
5. **Orphan detection:** Keywords with unique SERPs that need dedicated pages

---

## Commands

```
/42:serp-cluster <serp-data.csv>
/42:serp-cluster <serp-data.csv> --min-overlap 3
/42:serp-cluster <serp-data.csv> --algorithm connected
/42:serp-cluster <serp-data.csv> --algorithm clique
/42:serp-cluster <serp-data.csv> --algorithm core --min-overlap 4
/42:serp-cluster <serp-data.csv> --top-n 10
/42:serp-cluster <serp-data.csv> --top-n 20 --min-overlap 5
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `<serp-data.csv>` | required | CSV with keyword, rank, url columns |
| `--min-overlap` | `3` | Minimum shared URLs to connect two keywords |
| `--algorithm` | `connected` | Clustering algorithm: `connected`, `clique`, `core` |
| `--top-n` | `10` | Only consider top N results per keyword |

---

## Input Data

### SERP Data CSV (required)

A CSV file with one row per keyword-URL-rank combination. Every keyword should have up to N rows (one per ranking URL).

**Expected format:**

```csv
keyword,rank,url
best running shoes,1,https://www.runnersworld.com/gear/best-running-shoes
best running shoes,2,https://www.nike.com/running-shoes
best running shoes,3,https://www.brooks.com/road-running-shoes
top running shoes 2024,1,https://www.runnersworld.com/gear/best-running-shoes
top running shoes 2024,2,https://www.brooks.com/road-running-shoes
top running shoes 2024,3,https://www.asics.com/running
```

**Flexible column naming:** The script auto-detects common column name variations:

| Column | Accepted names |
|--------|---------------|
| keyword | `keyword`, `query`, `search_term`, `term`, `Keyword` |
| rank | `rank`, `position`, `pos`, `Rank`, `Position` |
| url | `url`, `link`, `result_url`, `URL`, `landing_page`, `result` |

**Data sources:**

| Source | How to export |
|--------|--------------|
| **DataForSEO** | SERP API batch → CSV export |
| **Ahrefs** | Keywords Explorer → SERP Overview → Export |
| **SEMrush** | Keyword Overview → SERP Analysis → Export |
| **SERPApi** | Batch results → JSON→CSV conversion |
| **Manual** | Scrape or compile manually in the format above |

---

## Workflow

### Step 1: Parse SERP Data

```bash
python3 scripts/serp_cluster.py \
    --input serp-data.csv \
    --top-n 10 \
    --output serp-clusters.json
```

Groups URLs per keyword, keeping only the top N results. Normalizes URLs (strips trailing slashes, query params, fragments).

### Step 2: Build Keyword-Pair Overlap Matrix

For every pair of keywords, count shared URLs in their top-N results:

```
keyword_a top-10: {url1, url2, url3, url4, url5, ...}
keyword_b top-10: {url1, url3, url5, url7, url9, ...}
overlap = {url1, url3, url5} → 3 shared URLs
```

### Step 3: Apply Clustering Algorithm

Three algorithms available, each with different strictness:

#### Connected Components (default)

- Any pair with `overlap >= min_overlap` creates an edge
- Keywords connected by any path of edges belong to the same cluster
- **Most inclusive** — produces larger clusters
- Best for: initial exploration, broad topic mapping

#### Clique-Based

- All keywords in a cluster must mutually share `>= min_overlap` URLs with each other
- **Most strict** — produces smaller, tighter clusters
- Best for: identifying exact-match topic groups

#### Core-Based (Threshold)

- Start with keyword pairs above `min_overlap`
- Seed clusters from highest-overlap pairs
- Add keywords that overlap with the cluster's core URLs
- **Balanced** — tighter than connected, looser than clique
- Best for: production-ready clustering with clear boundaries

### Step 4: Score Cluster Coherence

For each cluster, calculate average pairwise Jaccard similarity:

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

| Jaccard Score | Cluster Quality |
|---------------|----------------|
| >= 0.50 | **Tight** — keywords are near-synonyms, definitely same page |
| 0.30 - 0.49 | **Moderate** — same topic, likely same page |
| 0.15 - 0.29 | **Loose** — related topic, consider same page or hub+spoke |
| < 0.15 | **Weak** — may need sub-clustering |

### Step 5: Identify Hub URL Per Cluster

For each cluster, find the URL that appears in the most keywords' SERPs. This is the "hub URL" -- the page Google already associates with this topic group.

- If a hub URL from your own domain exists: optimize that page for the full cluster
- If no hub URL from your domain: content gap -- create a page targeting this cluster
- If multiple hub URLs from your domain: potential cannibalization

### Step 6: Generate Consolidation Recommendations

Based on cluster analysis:

| Situation | Recommendation |
|-----------|---------------|
| Cluster has 1 owned hub URL | Optimize that page for all cluster keywords |
| Cluster has 0 owned URLs | Create new page targeting the cluster |
| Cluster has 2+ owned URLs | Evaluate cannibalization -- consider merging |
| Single-keyword cluster | Unique SERP -- needs dedicated page |

---

## Output Format

### SERP-CLUSTERS.md

```markdown
# SERP-Based Keyword Clusters — [Domain/Project]
Date: [Date]
Keywords: [Count] | Clusters: [Count] | Orphans: [Count]
Algorithm: [connected/clique/core] | Min Overlap: [N] | Top-N: [N]

---

## Summary

| Metric | Value |
|--------|-------|
| Total keywords analyzed | [X] |
| Clusters formed | [X] |
| Avg keywords per cluster | [X] |
| Avg Jaccard similarity | [X] |
| Orphan keywords (no cluster) | [X] |
| Keywords with owned hub URL | [X] |
| Content gap clusters | [X] |

---

## Clusters (sorted by size)

### Cluster 1: [Primary Keyword] (N keywords)

**Hub URL:** [url] (appears in N/N keywords)
**Avg Jaccard:** 0.52 (Tight)
**Recommendation:** Optimize hub page for full cluster

| Keyword | Shared URLs with Hub | Jaccard vs Hub |
|---------|---------------------|----------------|
| [kw1] | 7/10 | 0.58 |
| [kw2] | 5/10 | 0.42 |
| [kw3] | 4/10 | 0.36 |

**Shared URLs across cluster:**

| URL | Keywords Containing |
|-----|-------------------|
| [url1] | 8/8 |
| [url2] | 6/8 |
| [url3] | 5/8 |

---

### Cluster 2: [Primary Keyword] (N keywords)

[Same structure as above]

---

## Content Gap Clusters (no owned hub URL)

| Cluster | Keywords | Avg Jaccard | Top Competitor Hub | Action |
|---------|----------|------------|-------------------|--------|
| [name] | [N] | 0.45 | [competitor-url] | Create new page |

---

## Orphan Keywords (unique SERPs)

| Keyword | Closest Cluster | Max Overlap | Action |
|---------|----------------|-------------|--------|
| [kw] | [cluster-name] | 2 URLs | Dedicated page or raise min_overlap |

---

## Consolidation Opportunities

| Current State | Keywords Affected | Recommendation |
|--------------|-------------------|---------------|
| 2 pages targeting Cluster 3 | [N] | Merge [url1] into [url2], redirect |
| No page for Cluster 7 | [N] | Create new page targeting [primary kw] |
| Thin cluster (Jaccard < 0.15) | [N] | Re-cluster with stricter algorithm |
```

### JSON Output (serp-clusters.json)

Also writes a structured JSON file for programmatic use:

```json
{
  "meta": {
    "total_keywords": 150,
    "total_clusters": 23,
    "orphan_keywords": 12,
    "algorithm": "connected",
    "min_overlap": 3,
    "top_n": 10
  },
  "clusters": [
    {
      "id": 1,
      "primary_keyword": "best running shoes",
      "keywords": ["best running shoes", "top running shoes", ...],
      "hub_url": "https://www.runnersworld.com/...",
      "hub_url_frequency": 8,
      "avg_jaccard": 0.52,
      "coherence": "tight",
      "shared_urls": {"url1": 8, "url2": 6, ...}
    }
  ],
  "orphans": ["unique keyword 1", "unique keyword 2"]
}
```

---

## Integratie met 42: Suite

| Skill | How serp-cluster integrates |
|-------|---------------------------|
| **42:keyword-mapper** | Complementary -- keyword-mapper uses embeddings (semantic), serp-cluster uses SERP overlap (behavioral). Use both for full picture |
| **42:cannibalization** | Clusters with 2+ owned hub URLs feed directly into cannibalization analysis |
| **42:near-duplicates** | Near-duplicate pages may correspond to keywords in the same SERP cluster |
| **42:seo-plan** | Clusters → content strategy: which clusters need pages, which need consolidation |
| **42:content** | Content gap clusters → content creation priorities |
| **42:seo-agi** | DataForSEO SERP data can be direct input for clustering |

---

## Cross-References

- For **semantic keyword clustering** (embeddings-based) → `/42:keyword-mapper`
- For **cannibalization detection** → `/42:cannibalization`
- For **near-duplicate page detection** → `/42:near-duplicates`
- For **content planning from clusters** → `/42:seo-plan`
- For **SERP data collection** → `/42:seo-agi` (DataForSEO integration)
