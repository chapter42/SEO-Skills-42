---
name: 42-readability
description: "Bulk readability scoring across entire site. Calculates Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog Index, SMOG Index, and Reading Time per page from Screaming Frog text export or sitemap crawl. Flags outliers by audience type. Use when user says readability, reading level, flesch, gunning fog, smog, reading ease, grade level, content readability, readability audit, readability score, 42-readability."
user-invokable: true
argument-hint: "<sf-text-export-dir or sitemap-url> [--min-words 100] [--limit 500]"
version: "1.0.0"
tags:
  - seo
  - readability
  - content-quality
  - flesch
  - gunning-fog
  - smog
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
metadata:
  filePattern: "**/*readability*,**/*flesch*,**/*reading*"
  bashPattern: "python*readability*,pip*textstat*"
---

# 42 Readability Scorer

Bulk readability scoring across an entire site. Calculates 5 readability metrics per page and aggregates site-wide statistics. Identifies outlier pages that are too difficult or too easy for the target audience.

---

## Why Readability Matters for SEO

Readability directly impacts user engagement metrics that Google uses as ranking signals:
- **Bounce rate** increases 50-100% when content exceeds the audience's reading level.
- **Time on page** drops when readers cannot parse complex sentences.
- **AI citation probability** decreases with overly complex text -- AI models prefer clear, extractable passages.
- **Featured snippet eligibility** favors concise, well-structured answers (Flesch-Kincaid grade 6-10).

Google's Helpful Content Update (2023-2024) explicitly rewards content written for humans, and readability is the most measurable proxy for human-friendliness.

---

## Commands

```
/42:readability <sf-text-export-dir> [--min-words 100] [--audience b2c|b2b|academic] [--output READABILITY-REPORT.md]
/42:readability <sitemap-url> [--limit 500] [--min-words 100] [--audience b2c|b2b|academic]
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `sf-text-export-dir` or `sitemap-url` | Yes | -- | Path to Screaming Frog "All Page Text" export directory, OR a sitemap URL for live fetching |
| `--min-words` | No | `100` | Minimum word count to include a page (pages below this are skipped as too thin for reliable scoring) |
| `--limit` | No | `500` | Maximum pages to process from sitemap (rate limiting for live fetching) |
| `--audience` | No | `b2c` | Target audience type for threshold scoring: `b2c` (grade 6-8), `b2b` (grade 8-12), `academic` (grade 12-16) |
| `--delay` | No | `1.0` | Seconds between requests when fetching from sitemap |
| `--output` | No | `READABILITY-REPORT.md` | Output filename |

---

## Metrics Calculated

### 1. Flesch Reading Ease (FRE)

**Formula:** 206.835 - 1.015 * (total words / total sentences) - 84.6 * (total syllables / total words)

| Score | Grade Level | Audience |
|---|---|---|
| 90-100 | 5th grade | Very easy, understood by 11-year-olds |
| 80-89 | 6th grade | Easy, conversational English |
| 70-79 | 7th grade | Fairly easy |
| 60-69 | 8th-9th grade | Standard, understood by 13-15-year-olds |
| 50-59 | 10th-12th grade | Fairly difficult |
| 30-49 | College | Difficult |
| 0-29 | College graduate+ | Very difficult, academic/legal |

### 2. Flesch-Kincaid Grade Level (FKGL)

**Formula:** 0.39 * (total words / total sentences) + 11.8 * (total syllables / total words) - 15.59

Returns a U.S. school grade level number. Grade 8 means an 8th grader can understand it. Most web content should target grade 6-10.

### 3. Gunning Fog Index (GFI)

**Formula:** 0.4 * ((total words / total sentences) + 100 * (complex words / total words))

"Complex words" = words with 3+ syllables (excluding common suffixes like -ed, -es, -ing). Designed for business writing. Scores above 12 indicate content that is too complex for general audiences.

### 4. SMOG Index

**Formula:** 3 + sqrt(number of polysyllabic words * (30 / number of sentences))

"Polysyllabic words" = words with 3+ syllables. Considered the most accurate readability formula for health and technical content. Requires at least 30 sentences for reliable results.

### 5. Reading Time

**Formula:** total words / 238 (average adult reading speed in WPM)

Returns estimated minutes to read. Useful for UX and content planning. Pages over 10 minutes may benefit from a table of contents or summary.

---

## Workflow

### Step 1: Load Text Per Page

**From Screaming Frog export:**
1. Read the export directory. Screaming Frog's "All Page Text" export produces one `.txt` file per URL.
2. Each filename encodes the URL (typically URL-encoded or slugified).
3. Read each file as plain text.
4. Associate text with its source URL (decoded from filename).

**From sitemap URL:**
1. Fetch the sitemap XML.
2. Extract all `<loc>` URLs.
3. Respect `--limit` to cap the number of pages.
4. For each URL, fetch the page HTML with rate limiting (`--delay`).
5. Extract main content text using BeautifulSoup (strip nav, header, footer, sidebar, script, style).
6. Store text with its source URL.

### Step 2: Filter by Minimum Word Count

- Count words in each page's text.
- Skip pages with fewer than `--min-words` words (default: 100).
- Log skipped pages with reason.
- Short pages produce unreliable readability scores and are typically navigation or thin content pages.

### Step 3: Calculate All 5 Metrics

For each page that passes the word count filter, calculate:
1. Flesch Reading Ease
2. Flesch-Kincaid Grade Level
3. Gunning Fog Index
4. SMOG Index
5. Reading Time (minutes)

Uses the `textstat` Python library for all calculations.

### Step 4: Aggregate Statistics

Calculate site-wide statistics for each metric:
- **Mean** -- average across all pages.
- **Median** -- middle value (less affected by outliers).
- **Standard deviation** -- spread of values.
- **P10 / P90** -- 10th and 90th percentile (defines the "normal range").
- **Min / Max** -- extreme values.
- **Distribution** -- count of pages in each difficulty band.

### Step 5: Flag Outliers

Based on `--audience` type, flag pages outside the target range:

| Audience | Target FKGL | Too Hard | Too Easy |
|---|---|---|---|
| B2C | 6-8 | > grade 10 | < grade 4 |
| B2B | 8-12 | > grade 14 | < grade 6 |
| Academic | 12-16 | > grade 18 | < grade 10 |

Outlier categories:
- **TOO HARD:** Pages with Flesch-Kincaid grade level above the upper threshold. These pages likely lose readers.
- **TOO EASY:** Pages with grade level below the lower threshold. For B2B content, overly simple writing may undermine authority.
- **EXTREME OUTLIERS:** Pages more than 2 standard deviations from the site mean.

---

## Output Format: READABILITY-REPORT.md

```markdown
# Readability Report

**Source:** [directory path or sitemap URL]
**Pages analyzed:** [count]
**Pages skipped (below min words):** [count]
**Target audience:** [B2C / B2B / Academic]
**Generated:** [date]

---

## Site-Wide Summary

| Metric | Mean | Median | P10 | P90 | Min | Max |
|--------|------|--------|-----|-----|-----|-----|
| Flesch Reading Ease | 62.3 | 64.1 | 48.2 | 78.5 | 22.1 | 91.4 |
| Flesch-Kincaid Grade | 8.2 | 7.8 | 5.1 | 12.3 | 3.2 | 18.7 |
| Gunning Fog Index | 10.5 | 9.8 | 7.2 | 14.1 | 4.3 | 21.2 |
| SMOG Index | 9.8 | 9.2 | 6.8 | 13.5 | 4.1 | 19.3 |
| Reading Time (min) | 4.2 | 3.8 | 1.2 | 8.5 | 0.4 | 22.1 |

---

## Grade Level Distribution

| Grade Level | Pages | % |
|-------------|-------|---|
| Grade 1-4 | 3 | 2% |
| Grade 5-6 | 22 | 15% |
| Grade 7-8 | 58 | 39% |
| Grade 9-10 | 41 | 28% |
| Grade 11-12 | 16 | 11% |
| Grade 13+ | 8 | 5% |

---

## Outliers: Too Hard (> Grade [threshold])

| URL | FKGL | FRE | Fog | SMOG | Words | Issue |
|-----|------|-----|-----|------|-------|-------|
| /legal/terms-of-service/ | 16.2 | 28.3 | 19.1 | 15.8 | 3,200 | Dense legal language |
| /technical/api-reference/ | 14.8 | 32.1 | 17.4 | 14.2 | 5,100 | Technical jargon |

## Outliers: Too Easy (< Grade [threshold])

| URL | FKGL | FRE | Fog | SMOG | Words | Issue |
|-----|------|-----|-----|------|-------|-------|
| /about/ | 3.8 | 89.2 | 5.1 | 4.2 | 120 | Very short, simple content |

---

## Per-Page Scores

| URL | Words | FRE | FKGL | Fog | SMOG | Read Time | Status |
|-----|-------|-----|------|-----|------|-----------|--------|
| /blog/seo-guide/ | 2,400 | 64.2 | 7.8 | 9.2 | 8.8 | 10.1 min | OK |
| /blog/technical-seo/ | 1,800 | 52.1 | 10.2 | 12.8 | 11.2 | 7.6 min | HARD |
| /services/ | 450 | 72.8 | 6.2 | 7.8 | 7.1 | 1.9 min | OK |

---

## Recommendations

1. **Site average is [above/below/within] target range for [audience] audience.**
2. **[N] pages flagged as too hard** -- consider simplifying sentence structure, replacing jargon with plain language, breaking long sentences.
3. **[N] pages flagged as too easy** -- may lack depth for the target audience; consider adding more substantive analysis.
4. **Reading time distribution:** [N]% of pages exceed 8 minutes -- consider adding summaries, tables of contents, or TL;DR sections.
```

---

## Script Location

```
scripts/readability_scorer.py
```

### Dependencies

```bash
pip install textstat requests beautifulsoup4 lxml
```

### Direct Usage

```bash
# From Screaming Frog export
python scripts/readability_scorer.py /path/to/sf-text-export/ --audience b2b --min-words 100

# From sitemap
python scripts/readability_scorer.py https://example.com/sitemap.xml --limit 200 --audience b2c

# Custom output
python scripts/readability_scorer.py /path/to/export/ --output my-report.md --audience academic
```

---

## Audience Thresholds Reference

### B2C (Consumer Content)
- **Target:** Flesch-Kincaid Grade 6-8 (Flesch Reading Ease 60-80)
- **Rationale:** Average American reads at 7th-8th grade level. Consumer content should be immediately accessible.
- **Examples:** Blog posts, product descriptions, landing pages, how-to guides.

### B2B (Business Content)
- **Target:** Flesch-Kincaid Grade 8-12 (Flesch Reading Ease 40-60)
- **Rationale:** Business professionals expect more sophisticated language but still value clarity.
- **Examples:** Whitepapers, case studies, industry analysis, technical documentation.

### Academic (Research/Technical)
- **Target:** Flesch-Kincaid Grade 12-16 (Flesch Reading Ease 20-40)
- **Rationale:** Academic audiences expect precise terminology and complex argumentation.
- **Examples:** Research papers, medical content, legal documents, scientific publications.

---

## Cross-References

- **42:content** -- Readability is a core content quality signal; include in content audits.
- **42:audit** -- Readability scoring feeds into the overall site audit as a content quality dimension.
- **42:seo-agi** -- Content briefs should specify target readability range for the audience.
- **42:blog-geo** -- AI-citable content should target Flesch-Kincaid grade 6-10 for maximum extractability.
- **42:genai-optimizer** -- Readability affects AI citability; simpler text is more likely to be cited verbatim.
