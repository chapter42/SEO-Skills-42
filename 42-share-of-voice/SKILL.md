---
name: 42-share-of-voice
description: >
  Calculate competitive Share of Voice -- what percentage of total search
  visibility does each domain own for a set of keywords? Supports both
  rank-based CTR-adjusted SOV and simple traffic-share mode. Use when user
  says "share of voice", "SOV", "search visibility", "competitive visibility",
  "domain visibility", "who owns the SERP", "competitive share", "market share
  search", "visibility percentage".
version: 1.0.0
tags: [seo, share-of-voice, sov, visibility, competitive, ctr, rankings]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*ranking*"
    - "**/*sov*"
    - "**/*visibility*"
    - "**/*share*voice*"
    - "**/*traffic*domain*"
  bashPattern:
    - "share.of.voice"
    - "sov"
    - "visibility"
---

# Share of Voice — Competitive Search Visibility

## Purpose

Calculate how much of the total search visibility each domain owns for a given set of keywords. SOV is the single best predictor of organic market share.

**Core formula:**

```
Domain SOV = sum(search_volume_i * CTR_at_position_i) / total_visibility * 100%
```

Where total_visibility = sum of all (volume * CTR) across all keywords and all ranking domains.

**Use cases:**

1. **Competitive benchmarking:** How do we compare to competitors in organic search?
2. **Market share estimation:** SOV correlates strongly with actual market share
3. **Campaign tracking:** Monitor SOV changes over time after SEO investments
4. **Gap analysis:** Which keywords contribute most to competitor SOV?
5. **Board reporting:** Simple percentage metric for stakeholder communication

---

## Commands

```
/42:share-of-voice <ranking-data.csv>
/42:share-of-voice <ranking-data.csv> --ctr-model sistrix
/42:share-of-voice <ranking-data.csv> --ctr-model awr --top-n 20
/42:share-of-voice <ranking-data.csv> --ctr-model custom --ctr-file ctr-curve.json
/42:share-of-voice <ahrefs-traffic-by-domain.csv> --simple
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `<ranking-data.csv>` | required | CSV with keyword, volume, domain/url, position |
| `--ctr-model` | `sistrix` | CTR curve model: `sistrix`, `awr`, `conservative`, `backlinko`, `custom` |
| `--top-n` | `10` | Only count positions 1-N (ignore rankings below) |
| `--ctr-file` | - | JSON file with custom CTR curve (required when `--ctr-model custom`) |
| `--simple` | `false` | Simple mode: use traffic estimates directly, skip CTR calculation |
| `--domain` | - | Highlight a specific domain in the output |

---

## Input Data

### Ranking Data CSV (standard mode)

One row per keyword-domain-position combination. If a domain ranks multiple URLs for the same keyword, include the best-ranking one.

**Expected format:**

```csv
keyword,volume,domain,position
best running shoes,22000,runnersworld.com,1
best running shoes,22000,nike.com,2
best running shoes,22000,brooks.com,3
top running shoes,12000,runnersworld.com,2
top running shoes,12000,asics.com,1
top running shoes,12000,nike.com,5
```

**Flexible column naming:**

| Column | Accepted names |
|--------|---------------|
| keyword | `keyword`, `query`, `search_term`, `term`, `Keyword` |
| volume | `volume`, `search_volume`, `sv`, `avg_monthly_searches`, `Volume` |
| domain | `domain`, `url`, `site`, `Domain`, `landing_page`, `result_url` |
| position | `position`, `rank`, `pos`, `Position`, `Rank` |

**Data sources:**

| Source | How to export |
|--------|--------------|
| **Ahrefs** | Keywords Explorer → export with Rank, Volume, URL |
| **SEMrush** | Organic Research → Positions → Export |
| **DataForSEO** | SERP API batch → CSV with position + volume |
| **Sistrix** | Visibility Index → keyword data export |
| **SE Ranking** | Rankings → Export |
| **Manual** | Compile from any rank tracker in format above |

### Ahrefs Traffic by Domain (simple mode)

For `--simple` mode, provide Ahrefs "Traffic by Domain" or similar export:

```csv
domain,traffic,keywords
runnersworld.com,125000,8500
nike.com,89000,5200
brooks.com,45000,3100
```

---

## CTR Models

Four built-in CTR curves, each based on different CTR studies:

### Sistrix (default)

Based on Sistrix 2020 CTR study (80M+ keywords):

| Position | CTR % |
|----------|-------|
| 1 | 28.5 |
| 2 | 15.7 |
| 3 | 11.0 |
| 4 | 8.0 |
| 5 | 7.2 |
| 6 | 5.1 |
| 7 | 4.0 |
| 8 | 3.2 |
| 9 | 2.8 |
| 10 | 2.5 |

### AWR (Advanced Web Ranking)

Based on AWR 2023 CTR study:

| Position | CTR % |
|----------|-------|
| 1 | 31.7 |
| 2 | 24.7 |
| 3 | 18.7 |
| 4 | 13.6 |
| 5 | 9.5 |
| 6 | 6.2 |
| 7 | 4.2 |
| 8 | 3.1 |
| 9 | 2.4 |
| 10 | 1.9 |

### Conservative

Lower estimates accounting for zero-click searches, featured snippets, and ads:

| Position | CTR % |
|----------|-------|
| 1 | 20.0 |
| 2 | 12.0 |
| 3 | 8.0 |
| 4 | 5.5 |
| 5 | 4.0 |
| 6 | 3.0 |
| 7 | 2.2 |
| 8 | 1.8 |
| 9 | 1.5 |
| 10 | 1.2 |

### Backlinko

Based on Backlinko/Semrush 2023 CTR study (4M+ results):

| Position | CTR % |
|----------|-------|
| 1 | 27.6 |
| 2 | 15.8 |
| 3 | 11.0 |
| 4 | 8.4 |
| 5 | 6.3 |
| 6 | 4.9 |
| 7 | 3.9 |
| 8 | 3.3 |
| 9 | 2.7 |
| 10 | 2.4 |

### Custom

Provide a JSON file with your own CTR curve:

```json
{
  "name": "My Industry CTR",
  "curve": {
    "1": 35.0,
    "2": 18.0,
    "3": 12.0,
    "4": 8.0,
    "5": 6.0,
    "6": 4.5,
    "7": 3.5,
    "8": 2.8,
    "9": 2.2,
    "10": 1.8
  }
}
```

---

## Workflow

### Step 1: Parse Ranking Data

```bash
python3 scripts/share_of_voice.py \
    --input ranking-data.csv \
    --output sov-results.json
```

Reads CSV, normalizes domains (strips www., protocol), groups by keyword.

### Step 2: Apply CTR Model

For each keyword-domain-position combination:

```
estimated_clicks = search_volume * (CTR_at_position / 100)
```

Positions beyond the model's range (e.g., position 15 with a top-10 model) get CTR = 0.

### Step 3: Calculate SOV Per Domain

```
domain_visibility = sum of estimated_clicks across all keywords
total_visibility = sum of all domain_visibility values
domain_SOV = domain_visibility / total_visibility * 100
```

### Step 4: Generate Keyword-Level Breakdown

For each domain, show which keywords contribute most to their SOV. This reveals:
- Keywords where you dominate (high rank = high contribution)
- Keywords where competitors dominate
- Keywords with high volume but low rank (opportunities)

### Simple Mode

When `--simple` is used:
- Skip CTR calculation
- Use traffic estimates directly as visibility score
- SOV% = domain_traffic / total_traffic * 100
- Faster, simpler, but less granular

---

## Output Format

### SHARE-OF-VOICE.md

```markdown
# Share of Voice Analysis — [Keyword Set/Industry]
Date: [Date]
Keywords: [Count] | Domains: [Count] | CTR Model: [Model]
Total Search Volume: [Sum] | Total Estimated Clicks: [Sum]

---

## Domain Rankings by SOV

| Rank | Domain | SOV % | Est. Clicks | Keywords Ranked | Avg Position |
|------|--------|-------|-------------|-----------------|-------------|
| 1 | runnersworld.com | 18.4% | 45,200 | 142 | 3.8 |
| 2 | nike.com | 14.2% | 34,800 | 128 | 4.5 |
| 3 | brooks.com | 9.8% | 24,100 | 96 | 5.2 |
| 4 | asics.com | 7.6% | 18,600 | 88 | 6.1 |
| 5 | zappos.com | 5.3% | 13,000 | 72 | 7.3 |
| ... | ... | ... | ... | ... | ... |

---

## SOV Distribution

| SOV Range | Domains | Combined SOV |
|-----------|---------|-------------|
| > 10% | [N] | [X]% |
| 5-10% | [N] | [X]% |
| 2-5% | [N] | [X]% |
| 1-2% | [N] | [X]% |
| < 1% | [N] | [X]% |

---

## Top Keywords by Visibility Impact

| Keyword | Volume | #1 Domain (CTR) | #2 Domain (CTR) | #3 Domain (CTR) |
|---------|--------|-----------------|-----------------|-----------------|
| [kw] | 22,000 | runnersworld.com (28.5%) | nike.com (15.7%) | brooks.com (11.0%) |

---

## Domain Deep Dive: [highlighted domain]

### Keyword Contributions to SOV

| Keyword | Volume | Position | Est. Clicks | % of Domain SOV |
|---------|--------|----------|-------------|----------------|
| [kw1] | 22,000 | 1 | 6,270 | 13.9% |
| [kw2] | 15,000 | 2 | 2,355 | 5.2% |

### Position Distribution

| Position | Keywords | Est. Clicks | % of SOV |
|----------|----------|-------------|----------|
| 1 | [N] | [X] | [X]% |
| 2-3 | [N] | [X] | [X]% |
| 4-10 | [N] | [X] | [X]% |

---

## Opportunities (High Volume, Low Position)

| Keyword | Volume | Your Position | #1 Domain | Gap Clicks |
|---------|--------|--------------|-----------|-----------|
| [kw] | 18,000 | 8 | competitor.com | 4,554 |
```

### JSON Output (sov-results.json)

```json
{
  "meta": {
    "total_keywords": 250,
    "total_domains": 45,
    "ctr_model": "sistrix",
    "top_n": 10,
    "total_search_volume": 1250000,
    "total_estimated_clicks": 485000
  },
  "domains": [
    {
      "domain": "runnersworld.com",
      "sov_percent": 18.4,
      "estimated_clicks": 45200,
      "keywords_ranked": 142,
      "avg_position": 3.8,
      "keyword_breakdown": [
        {
          "keyword": "best running shoes",
          "volume": 22000,
          "position": 1,
          "estimated_clicks": 6270,
          "pct_of_domain_sov": 13.9
        }
      ]
    }
  ]
}
```

---

## Integratie met 42: Suite

| Skill | How share-of-voice integrates |
|-------|------------------------------|
| **42:audit** | SOV as part of full site audit -- competitive positioning overview |
| **42:seo-plan** | SOV gaps inform strategic keyword targeting priorities |
| **42:competitor-pages** | Identify which competitor pages drive their SOV |
| **42:serp-cluster** | Cluster-level SOV -- which topic clusters does each domain own? |
| **42:cannibalization** | Cannibalization may split SOV across your own URLs |
| **42:content** | Content priorities based on SOV gap analysis |

---

## Cross-References

- For **full site audit with SOV context** → `/42:audit`
- For **strategic SEO planning** → `/42:seo-plan`
- For **competitor page analysis** → `/42:competitor-pages`
- For **keyword clustering** → `/42:serp-cluster`
- For **SERP data collection** → `/42:seo-agi` (DataForSEO integration)
