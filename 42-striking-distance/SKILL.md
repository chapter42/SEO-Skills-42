---
name: 42-striking-distance
description: >
  Find pages ranking position 4-20 where the target keyword is missing from
  title, H1, meta description, or URL. These are quick wins — a small on-page
  optimization can push them into the top 3. Combines GSC performance data with
  optional Screaming Frog crawl data for title/H1/meta analysis. Scores each
  opportunity by impressions, CTR gap, and position. Use when user says
  "striking distance", "quick wins", "low hanging fruit", "position 4-20",
  "almost ranking", "easy wins SEO", "keyword missing from title",
  "optimize existing rankings".
version: 1.0.0
tags: [seo, gsc, striking-distance, quick-wins, on-page, title-optimization, ctr]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*gsc*"
    - "**/*search*console*"
    - "**/*striking*"
    - "**/*quick*win*"
    - "**/*internal*html*"
  bashPattern:
    - "striking.distance"
    - "quick.win"
    - "gsc"
---

# Striking Distance Keyword Finder

## Purpose

Find pages that rank in positions 4-20 where the target keyword is missing from key on-page elements (title, H1, meta description, URL). These represent the highest-ROI SEO opportunities: the page already ranks, so adding the keyword to the right element can push it into the top 3 where the majority of clicks happen.

**Why positions 4-20 matter:**
- Position 1 gets ~27% CTR, position 4 gets ~7%, position 10 gets ~2%
- Moving from position 8 to position 3 can 3-5x traffic for that keyword
- On-page keyword placement is one of the easiest ranking factors to fix

---

## Commands

```
/42:striking-distance <gsc-export.csv>
/42:striking-distance <gsc-export.csv> --sf-crawl internal.csv
/42:striking-distance <gsc-export.csv> --sf-crawl internal.csv --min-impressions 200
/42:striking-distance <gsc-export.csv> --positions 5-15
/42:striking-distance <gsc-export.csv> --sf-crawl internal.csv --min-impressions 100 --positions 4-20
```

---

## Input Files

### 1. GSC Performance Export (required)

Export from Google Search Console > Performance > Search Results.
Select dimensions: Query + Page. Export as CSV.

**Expected format:**

```csv
Top queries,Top pages,Clicks,Impressions,CTR,Position
seo audit tool,https://example.com/seo-audit,450,12000,3.75%,4.2
technical seo,https://example.com/technical-guide,120,8500,1.41%,8.7
```

Supported column name variations:
- Query: `Top queries`, `Query`, `query`, `Queries`, `Search Query`
- Page: `Top pages`, `Page`, `page`, `Pages`, `URL`, `Landing Page`
- Clicks: `Clicks`, `clicks`
- Impressions: `Impressions`, `impressions`
- CTR: `CTR`, `ctr`, `Click Through Rate`
- Position: `Position`, `position`, `Avg. Position`, `Average Position`

### 2. Screaming Frog Internal:HTML Export (optional)

Export from Screaming Frog: `Internal` tab > Filter: `HTML` > Export.

**Expected format:**

```csv
Address,Title 1,H1-1,Meta Description 1,Status Code
https://example.com/seo-audit,SEO Audit Tool - Complete Guide,SEO Audit Tool,Learn how to perform a complete SEO audit,200
```

When provided, enables checking whether the GSC query appears in:
- Title tag
- H1 heading
- Meta description

Without SF data, only URL-path matching is performed.

---

## Workflow

### Step 1: Parse and Filter GSC Data

```bash
python3 scripts/striking_distance.py \
    --gsc gsc-export.csv \
    --min-impressions 100 \
    --min-position 4 \
    --max-position 20
```

1. Load GSC CSV, normalize column names
2. Filter to position range (default 4-20)
3. Filter by minimum impressions (default 100)
4. Remove branded queries if domain name detected

### Step 2: Join Screaming Frog Data (if provided)

```bash
python3 scripts/striking_distance.py \
    --gsc gsc-export.csv \
    --sf-crawl internal.csv \
    --min-impressions 100
```

1. Load SF Internal:HTML CSV
2. Match GSC pages to SF rows by URL (normalized, trailing slash agnostic)
3. Extract title, H1, meta description for each page

### Step 3: Keyword Presence Check

For each query x page pair, check keyword presence in:

| Element | Check Method | Impact |
|---------|-------------|--------|
| **Title tag** | Case-insensitive, word boundary aware | Highest |
| **H1 heading** | Case-insensitive, word boundary aware | High |
| **Meta description** | Case-insensitive, substring match | Medium |
| **URL path** | Case-insensitive, hyphen-as-space | Medium |

Word boundary matching ensures "seo" matches in "SEO Audit Tool" but not in "museum of art".

### Step 4: Opportunity Scoring

```
opportunity_score = impressions × (1 - CTR) × (1 / position)
```

Where:
- `impressions` = monthly search impressions from GSC
- `CTR` = current click-through rate (decimal, e.g. 0.0375)
- `position` = average ranking position

Higher score = more untapped potential. A page with 10,000 impressions, 2% CTR, at position 8 has a score of: 10000 x 0.98 x 0.125 = 1225.

### Step 5: Classification

Each opportunity is classified by what is missing:

| Classification | Condition | Priority |
|---------------|-----------|----------|
| **TITLE_MISSING** | Keyword not in title tag | Highest — fix first |
| **H1_MISSING** | Keyword not in H1 heading | High |
| **BOTH_MISSING** | Missing from both title and H1 | Critical — biggest gap |
| **META_MISSING** | Keyword not in meta description | Medium — CTR impact |
| **URL_ONLY** | Keyword only in URL, nowhere else | High |
| **PRESENT_ALL** | Keyword found everywhere — other factors at play | Low — investigate further |

### Step 6: Estimated Traffic Uplift

For each opportunity, estimate the traffic gain from moving up:

```
estimated_uplift = impressions × (target_ctr - current_ctr)
```

Where `target_ctr` is the expected CTR for position 3 (~8.5%) or position 1 (~27%), depending on how much improvement is realistic.

---

## Thresholds (configurable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--min-impressions` | 100 | Minimum monthly impressions to include |
| `--positions` | 4-20 | Position range (format: min-max) |
| `--min-opportunity` | 50 | Minimum opportunity score to report |

---

## Output Format

### STRIKING-DISTANCE.md

```markdown
# Striking Distance Opportunities — [Domain]
Date: [Date]
Source: GSC Performance Export + Screaming Frog Internal:HTML
Position range: [min]-[max] | Min impressions: [threshold]

## Summary

| Metric | Count |
|--------|-------|
| Total query×page pairs analyzed | [X] |
| Pairs in striking distance (pos 4-20) | [X] |
| Keyword missing from title | [X] |
| Keyword missing from H1 | [X] |
| Keyword missing from both title + H1 | [X] |
| Keyword missing from meta description | [X] |
| Estimated total traffic uplift | [X] clicks/month |

---

## Top Opportunities (sorted by opportunity score)

| # | Query | Page | Pos | Impr | CTR | Score | Missing From | Est. Uplift |
|---|-------|------|-----|------|-----|-------|-------------|-------------|
| 1 | [query] | [url] | 6.2 | 8,500 | 1.8% | 1,342 | TITLE + H1 | +561 clicks |
| 2 | [query] | [url] | 4.8 | 12,000 | 3.1% | 1,198 | TITLE | +648 clicks |

---

## Fix Priority: Title Tag Updates

Pages where adding the keyword to the title has the highest impact.

| Query | Current Title | Suggested Title | Page | Impressions |
|-------|--------------|----------------|------|------------|
| [query] | [current] | [suggested with keyword] | [url] | [X] |

---

## Fix Priority: H1 Updates

| Query | Current H1 | Suggested H1 | Page | Impressions |
|-------|-----------|-------------|------|------------|
| [query] | [current] | [suggested] | [url] | [X] |

---

## Fix Priority: Meta Description Updates

| Query | Page | Impressions | CTR | Suggestion |
|-------|------|------------|-----|-----------|
| [query] | [url] | [X] | [X]% | Include "[query]" in meta description for CTR boost |

---

## Pages with Multiple Striking Distance Keywords

Pages that appear multiple times — these benefit most from a content refresh.

| Page | # Keywords in Range | Top Keywords | Avg Position | Total Impressions |
|------|-------------------|-------------|-------------|-------------------|
| [url] | [X] | [kw1], [kw2], [kw3] | [X] | [X] |

---

## Estimated Impact Summary

| Action | Pages Affected | Est. Traffic Gain |
|--------|---------------|------------------|
| Add keyword to title | [X] | +[X] clicks/month |
| Add keyword to H1 | [X] | +[X] clicks/month |
| Update meta descriptions | [X] | +[X] clicks/month |
| **Total estimated uplift** | | **+[X] clicks/month** |
```

---

## Integration with 42: Suite

| Skill | How striking-distance connects |
|-------|-------------------------------|
| **42:keyword-mapper** | Keyword-mapper provides the GSC data + semantic mapping; striking-distance focuses on position 4-20 on-page gaps |
| **42:page-analysis** | Deep-dive individual pages flagged as striking distance opportunities |
| **42:meta-optimizer** | Bulk-generate improved title tags and meta descriptions for flagged pages |
| **42:cannibalization** | Check if striking distance pages compete with other pages for the same keyword |
| **42:content** | Content refresh recommendations for pages with multiple striking distance keywords |
| **42:audit** | Striking distance analysis as part of full site audit |

---

## Cross-References

- For **keyword-to-page mapping with embeddings** → `/42:keyword-mapper`
- For **deep single-page analysis** → `/42:page-analysis <url>`
- For **bulk meta tag optimization** → `/42:meta-optimizer`
- For **cannibalization detection** → `/42:cannibalization`
- For **Screaming Frog crawl setup** → `/42:screaming-frog crawl <url>`
