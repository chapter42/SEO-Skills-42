---
name: 42-content-decay
description: >
  Detect pages where traffic is declining vs their historical peak. Combines
  decay detection (current vs peak), anomaly detection (sudden drops), and
  Google algorithm update correlation. Classifies decay as gradual, sudden,
  seasonal, or recovering. Prioritizes content refresh candidates by decay
  severity and traffic impact. Use when user says "content decay", "traffic
  decline", "losing rankings", "traffic drop", "pages declining", "content
  refresh", "algorithm update impact", "historical performance", "peak traffic".
version: 1.0.0
tags: [seo, gsc, content-decay, traffic-decline, algorithm-updates, content-refresh, anomaly-detection]
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
    - "**/*decay*"
    - "**/*traffic*"
    - "**/*performance*"
  bashPattern:
    - "content.decay"
    - "traffic.decline"
    - "gsc"
---

# Content Decay Detector

## Purpose

Detect pages where organic traffic is declining compared to their historical peak. Content decay is one of the most common and preventable causes of traffic loss. This skill combines three analysis methods:

1. **Decay detection** — Compare current traffic to peak traffic for each page
2. **Anomaly detection** — Find sudden drops using rolling average analysis
3. **Algorithm update correlation** — Match traffic drops to known Google core updates

**Why content decay matters:**
- 50-60% of pages lose traffic within 12 months of publishing without updates
- Content that once ranked can lose positions as competitors publish fresher content
- Google's Helpful Content system actively demotes stale, outdated content
- Early detection enables proactive refresh before rankings collapse

---

## Commands

```
/42:content-decay <gsc-export.csv>
/42:content-decay <gsc-export.csv> --period 12m
/42:content-decay <gsc-export.csv> --decay-threshold 30
/42:content-decay <gsc-export.csv> --min-peak-clicks 50
/42:content-decay <gsc-export.csv> --period 18m --decay-threshold 20 --min-peak-clicks 100
```

---

## Input Files

### GSC Performance Export with Date Dimension (required)

Export from Google Search Console > Performance > Search Results.
Select dimensions: Page + Date. Set date range to at least 6 months (12+ months recommended).
Export as CSV.

**Expected format (monthly):**

```csv
Page,Date,Clicks,Impressions,CTR,Position
https://example.com/seo-guide,2025-01,450,12000,3.75%,4.2
https://example.com/seo-guide,2025-02,380,11500,3.30%,5.1
https://example.com/seo-guide,2025-03,290,10000,2.90%,6.8
```

**Expected format (daily/weekly — will be aggregated to monthly):**

```csv
Page,Date,Clicks,Impressions,CTR,Position
https://example.com/seo-guide,2025-01-01,15,400,3.75%,4.2
https://example.com/seo-guide,2025-01-02,18,420,4.29%,3.9
```

Supported date formats:
- `2025-01` (monthly)
- `2025-01-15` (daily, ISO)
- `01/15/2025` (daily, US)
- `15/01/2025` (daily, EU)
- `Jan 2025` (monthly, text)

Supported column name variations:
- Page: `Page`, `Top pages`, `URL`, `Landing Page`, `Address`
- Date: `Date`, `date`, `Month`, `Period`
- Clicks: `Clicks`, `clicks`
- Impressions: `Impressions`, `impressions`
- CTR: `CTR`, `ctr`, `Click Through Rate`
- Position: `Position`, `position`, `Avg. Position`

---

## Workflow

### Step 1: Parse and Aggregate

```bash
python3 scripts/content_decay.py \
    --gsc gsc-export.csv \
    --period 12m
```

1. Load GSC CSV with date handling (auto-detect format)
2. Aggregate daily data to monthly per page
3. Build time series: page -> [{month, clicks, impressions, position}, ...]
4. Filter to the specified analysis period (default: last 12 months)

### Step 2: Peak Detection

For each page:
1. Find the month with the highest clicks (peak month)
2. Record peak clicks, impressions, and position
3. Identify the current month (or most recent month in data)
4. Record current clicks, impressions, and position

### Step 3: Decay Calculation

```
decay_percentage = (peak_clicks - current_clicks) / peak_clicks x 100
```

Flag pages where `decay_percentage > threshold` (default: 30%).

**Decay severity levels:**

| Decay % | Severity | Urgency |
|---------|----------|---------|
| 80-100% | Critical | Immediate — content may be deindexed or severely penalized |
| 50-79% | High | This week — significant traffic loss, refresh urgently |
| 30-49% | Medium | This month — declining trend, schedule refresh |
| 10-29% | Low | Monitor — early signs of decay, add to watch list |
| < 10% | Stable | No action — normal fluctuation |

### Step 4: Anomaly Detection

For each page with sufficient data (6+ months):
1. Calculate a 3-month rolling average of clicks
2. Compute month-over-month delta from the rolling average
3. Flag months where the delta exceeds -2 standard deviations (sudden drop)
4. Record the anomaly month and magnitude

**Rolling average formula:**
```
rolling_avg[month] = (clicks[month-2] + clicks[month-1] + clicks[month]) / 3
delta[month] = clicks[month] - rolling_avg[month-1]
```

### Step 5: Algorithm Update Correlation

Match detected anomalies and decay onset to known Google algorithm updates:

| Update | Date | Impact Type |
|--------|------|-------------|
| March 2024 Core Update | 2024-03-05 | Broad core ranking changes |
| August 2024 Core Update | 2024-08-15 | Broad core ranking changes |
| November 2024 Core Update | 2024-11-11 | Broad core ranking changes |
| December 2024 Spam Update | 2024-12-19 | Link spam, thin content |
| March 2025 Core Update | 2025-03-13 | Broad core ranking changes |
| June 2025 Core Update | 2025-06-10 | Broad core ranking changes (estimated) |
| September 2025 Core Update | 2025-09-15 | Broad core ranking changes (estimated) |
| December 2025 Core Update | 2025-12-01 | Helpful content refinement (estimated) |
| March 2026 Core Update | 2026-03-10 | Broad core ranking changes (estimated) |

A traffic drop within 4 weeks of an update is flagged as "likely correlated".

### Step 6: Classification

Each decaying page is classified into one of four patterns:

| Pattern | Description | Criteria |
|---------|------------|----------|
| **Gradual Decay** | Slow, steady decline over multiple months | No single month drop > 25%, trend is consistently down |
| **Sudden Drop** | Sharp decline in a single month | One month shows > 40% drop from rolling average |
| **Seasonal** | Traffic follows a predictable yearly cycle | Similar pattern visible across multiple years, or known seasonal industry |
| **Recovering** | Traffic dropped but is now trending back up | Current month > previous 2 months, but still below peak |

---

## Thresholds (configurable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--period` | 12m | Analysis period (6m, 12m, 18m, 24m) |
| `--decay-threshold` | 30 | Minimum decay % to flag (0-100) |
| `--min-peak-clicks` | 50 | Minimum peak clicks to include page |
| `--rolling-window` | 3 | Rolling average window in months |
| `--anomaly-std` | 2.0 | Standard deviations for anomaly detection |

---

## Output Format

### CONTENT-DECAY.md

```markdown
# Content Decay Report — [Domain]
Date: [Date]
Period analyzed: [Start] to [End]
Decay threshold: [X]% | Min peak clicks: [X]

## Summary

| Metric | Count |
|--------|-------|
| Total pages analyzed | [X] |
| Pages with decay > threshold | [X] |
| Critical decay (80-100%) | [X] |
| High decay (50-79%) | [X] |
| Medium decay (30-49%) | [X] |
| Anomalies detected (sudden drops) | [X] |
| Drops correlated with algorithm updates | [X] |
| Total traffic lost vs peak | [X] clicks/month |

---

## Decay Table (sorted by traffic loss)

| # | Page | Peak Month | Peak Clicks | Current Clicks | Decay % | Severity | Pattern | Update Correlation |
|---|------|-----------|-------------|----------------|---------|----------|---------|-------------------|
| 1 | [url] | [month] | [X] | [X] | [X]% | Critical | Sudden Drop | March 2025 Core |
| 2 | [url] | [month] | [X] | [X] | [X]% | High | Gradual | None |

---

## Anomaly Timeline

Visual timeline of detected traffic anomalies overlaid with Google algorithm updates.

| Date | Page | Event | Magnitude | Algorithm Update |
|------|------|-------|-----------|-----------------|
| [date] | [url] | Sudden drop: -[X]% | -[X] clicks | [update or "None"] |
| [date] | [url] | Decay onset | -[X]% from peak | [update or "None"] |

---

## Algorithm Update Impact

| Update | Date | Pages Affected | Avg Decay % | Most Impacted Page |
|--------|------|---------------|-------------|-------------------|
| March 2025 Core | 2025-03-13 | [X] | [X]% | [url] |
| November 2024 Core | 2024-11-11 | [X] | [X]% | [url] |

---

## Content Refresh Priorities

Sorted by potential traffic recovery (peak clicks - current clicks).

| Priority | Page | Decay % | Traffic Lost | Peak Position | Current Position | Recommended Action |
|----------|------|---------|-------------|--------------|-----------------|-------------------|
| 1 | [url] | [X]% | [X] clicks | [X] | [X] | Full rewrite — content outdated |
| 2 | [url] | [X]% | [X] clicks | [X] | [X] | Refresh stats + add new sections |
| 3 | [url] | [X]% | [X] clicks | [X] | [X] | Update title + meta, add internal links |

### Refresh Action Guidelines

| Decay Pattern | Recommended Action |
|--------------|-------------------|
| **Gradual Decay** | Content refresh: update statistics, add new sections, improve depth |
| **Sudden Drop (update correlated)** | Audit against update guidelines, check for manual actions, review SERP changes |
| **Sudden Drop (no correlation)** | Check for technical issues (broken links, redirects, canonical), competitor analysis |
| **Seasonal** | Pre-season refresh: update content 1-2 months before expected peak |
| **Recovering** | Monitor weekly, consider light optimization to accelerate recovery |

---

## Pages Gaining Traffic (for context)

| Page | 3 Months Ago | Current | Growth % |
|------|-------------|---------|----------|
| [url] | [X] | [X] | +[X]% |

---

## Monthly Traffic Trend (all analyzed pages)

| Month | Total Clicks | vs Previous Month | vs Peak Month |
|-------|-------------|------------------|--------------|
| [month] | [X] | [+/-X]% | [-X]% |
```

---

## Integration with 42: Suite

| Skill | How content-decay connects |
|-------|--------------------------|
| **42:content** | Content quality assessment for pages flagged for refresh |
| **42:audit** | Content decay as part of full site audit workflow |
| **42:page-analysis** | Deep-dive individual decaying pages for optimization opportunities |
| **42:geo-compare** | Compare decay patterns across geographic markets |
| **42:keyword-mapper** | Check if decaying pages have keyword mapping issues |
| **42:cannibalization** | Verify if decay is caused by newer pages cannibalizing older ones |
| **42:striking-distance** | Cross-reference decaying pages that still have striking distance keywords |

---

## Cross-References

- For **content quality assessment** → `/42:content <url>`
- For **full site audit** → `/42:audit <domain>`
- For **single page deep-dive** → `/42:page-analysis <url>`
- For **geographic comparison** → `/42:geo-compare`
- For **striking distance opportunities on decaying pages** → `/42:striking-distance`
