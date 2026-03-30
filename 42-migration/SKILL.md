---
name: 42-migration
description: >
  Website migration toolkit: redirect validation (spec vs actual crawl), content
  change detection (old site vs new site crawl comparison), and Wayback Machine
  historical analysis. Validates redirect specs against crawl data, detects
  content changes between site versions, and analyzes historical site evolution.
  Use when user says "migration", "redirect validation", "redirect check",
  "site migration", "domain migration", "replatform", "content comparison",
  "old vs new", "wayback", "redirect spec", "redirect map", "301 audit",
  "migration audit", "pre-migration", "post-migration".
version: 1.0.0
tags: [seo, migration, redirects, content-change, wayback, technical-seo, replatform]
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/redirect*.csv"
    - "**/migration*.csv"
    - "**/*_redirect*"
    - "**/*_migration*"
    - "**/MIGRATION-REPORT.md"
  bashPattern:
    - "redirect"
    - "migration"
    - "wayback"
    - "replatform"
---

# Migration — Website Migration Toolkit

## Purpose

End-to-end website migration validation covering three critical phases:
1. **Redirect validation** — Does the redirect spec match what's actually live?
2. **Content change detection** — What content changed between old and new site?
3. **Wayback Machine analysis** — How has the site evolved historically?

Uses the Python script at `scripts/redirect_validator.py` for URL normalization,
redirect matching, chain detection, and Wayback CDX API queries. Claude handles
analysis, reporting, and recommendations.

---

## Commands

```
/42:migration validate <spec.csv> <crawl.csv>                  # Redirect spec vs actual
/42:migration compare <old-crawl.csv> <new-crawl.csv>          # Content changes old vs new
/42:migration history <domain> [--years 5]                     # Wayback Machine analysis
/42:migration full <spec.csv> <old-crawl.csv> <new-crawl.csv>  # All three combined
```

---

## Input Formats

### Redirect Specification CSV (`spec.csv`)
Required columns:
- `old_url` or `Source` or `From` — the original URL
- `new_url` or `Destination` or `To` — the target URL
- `type` or `Status` (optional) — redirect type (301, 302, etc.), defaults to 301

### Crawl Data CSV (`crawl.csv`, `old-crawl.csv`, `new-crawl.csv`)
Screaming Frog Internal:All or Internal:HTML export with columns:
- `Address` — the URL
- `Status Code` — HTTP status
- `Redirect URL` — where the URL redirects to (if applicable)
- `Title 1` — page title
- `H1-1` — primary heading
- `Word Count` — content word count
- `Meta Description 1` — meta description
- `Indexability` — indexable / non-indexable
- `Canonical Link Element 1` — canonical URL

### Domain (for history command)
A bare domain (e.g., `example.com`) or full URL (`https://example.com`).

---

## Workflow

### Command: `validate`

#### Step 1: Parse Redirect Specification

1. Read the spec CSV with the Read tool.
2. Identify column mapping (old_url, new_url, type).
3. Normalize all URLs using these rules:
   - Lowercase the entire URL
   - Strip trailing slashes (unless root `/`)
   - Force `https://` protocol
   - Normalize `www` vs non-`www` (match spec convention)
   - Remove default ports (`:80`, `:443`)
   - Decode percent-encoded characters where safe
   - Remove fragment identifiers (`#section`)
   - Sort and remove tracking query parameters (`utm_*`, `ref`, `fbclid`)
4. Count total redirect rules in spec.

#### Step 2: Parse Actual Crawl Data

1. Read the crawl CSV.
2. Filter to URLs with 3xx status codes.
3. Extract: source URL, status code, redirect destination URL.
4. Normalize all URLs with the same rules as Step 1.

#### Step 3: Match and Categorize

For each redirect in the spec, check against actual crawl data:

| Category | Definition | Severity |
|----------|-----------|----------|
| **MATCH** | Spec source redirects to spec destination with correct type | None (correct) |
| **WRONG_DEST** | Source redirects, but to a different destination than spec | High |
| **WRONG_TYPE** | Correct destination, but wrong redirect type (e.g., 302 instead of 301) | Medium |
| **MISSING** | Source URL returns 200 or 404 — no redirect implemented | Critical |
| **CHAIN** | Redirect works but goes through intermediate hops (A -> B -> C) | Medium |
| **LOOP** | Redirect creates a circular loop | Critical |
| **EXTRA** | Redirect exists in crawl but not in spec (unexpected redirect) | Low |

#### Step 4: Chain Detection

For each redirect destination, check if it also redirects:
- Follow up to 10 hops
- Flag chains of 2+ hops
- Flag any loops (URL appears twice in chain)
- Record the full chain path (A -> B -> C -> D)

#### Step 5: Scoring

Calculate implementation score:
```
Score = (MATCH count / total spec rules) x 100
```

Additional metrics:
- Missing rate: critical redirects not implemented
- Chain rate: redirects requiring extra hops
- Wrong destination rate: redirects going to wrong pages

#### Step 6: Run Python Validator (optional)

If the dataset is large (100+ redirects), use the Python script for faster
processing:

```bash
python3 scripts/redirect_validator.py validate \
  --spec spec.csv \
  --crawl crawl.csv \
  --output results.json
```

---

### Command: `compare`

#### Step 1: Parse Both Crawls

1. Read old-crawl.csv and new-crawl.csv.
2. Extract for each URL: address, title, H1, word count, meta description,
   status code, indexability, canonical.
3. Normalize all URLs for matching.

#### Step 2: Match Pages

Match pages between old and new crawl:
1. **Exact URL match** — same normalized URL exists in both crawls
2. **Slug match** — same URL path/slug with different domain
3. **Title match** — same or very similar title (for replatforms that changed URL structure)
4. **Unmatched** — pages that exist in only one crawl

#### Step 3: Detect Changes

For each matched page pair, detect:

| Change Type | Detection | Impact |
|-------------|-----------|--------|
| **Title changed** | Old title != new title | Medium — affects rankings |
| **H1 changed** | Old H1 != new H1 | Medium — affects relevance |
| **Meta description changed** | Old != new description | Low — affects CTR |
| **Word count drop** | New word count < old * 0.7 (30%+ decrease) | High — thin content risk |
| **Word count spike** | New word count > old * 2.0 (100%+ increase) | Low — review quality |
| **Status code changed** | Different HTTP status | High if 200 -> 4xx/5xx |
| **Indexability lost** | Was indexable, now non-indexable | Critical |
| **Canonical changed** | Different canonical URL | High — may lose rankings |

#### Step 4: Flag Critical Losses

Flag pages that meet ANY of these criteria:
- Status changed from 200 to 404/410/5xx
- Indexability changed from indexable to non-indexable
- Word count dropped by more than 50%
- Page existed in old crawl but is completely missing from new crawl
- Canonical now points to a different page

#### Step 5: New and Removed Pages

- **New pages**: URLs in new crawl not in old crawl (exclude redirects)
- **Removed pages**: URLs in old crawl not in new crawl and not redirected
- Flag removed pages that had significant word count (>500 words) as potential
  content loss

---

### Command: `history`

#### Step 1: Query Wayback Machine CDX API

Use the Wayback Machine CDX API to retrieve historical snapshots:

```
https://web.archive.org/cdx/search/cdx?url=<domain>/*&output=json&fl=timestamp,original,statuscode,mimetype&collapse=urlkey&limit=10000
```

Parameters:
- `url`: domain with `/*` wildcard for all pages
- `collapse=urlkey`: deduplicate by URL
- `limit`: cap results (default 10000)
- `from` / `to`: date range based on `--years` flag

If using the Python script:
```bash
python3 scripts/redirect_validator.py history \
  --domain example.com \
  --years 5 \
  --output history.json
```

#### Step 2: Analyze Site Size Over Time

Group snapshots by year-month:
- Count unique URLs per period
- Identify growth phases (significant URL count increases)
- Identify shrink phases (URL count decreases — possible migrations or pruning)
- Plot trend: `[year]: [url_count] URLs [+/-change]`

#### Step 3: Compare robots.txt Versions

Fetch historical robots.txt snapshots:
```
https://web.archive.org/cdx/search/cdx?url=<domain>/robots.txt&output=json&fl=timestamp,statuscode&limit=100
```

For each unique robots.txt version:
- Fetch the content from Wayback: `https://web.archive.org/web/<timestamp>/<domain>/robots.txt`
- Compare with previous version
- Flag changes that could cause deindexing:
  - New `Disallow: /` rules
  - Removed `Allow:` rules
  - Changed `Sitemap:` directives
  - New `User-agent: *` blocks

#### Step 4: Identify Major Structural Changes

From the URL data, detect:
- **URL pattern changes**: e.g., `/blog/post` changed to `/articles/post`
- **Subdomain changes**: content moved between www and subdomains
- **Technology indicators**: URL patterns suggesting platform changes
  (e.g., `.php` -> clean URLs = CMS migration)
- **New sections**: large batches of new URL patterns appearing
- **Removed sections**: URL patterns disappearing

---

## Output Format

Write to `MIGRATION-REPORT.md` in the current working directory.

```markdown
# Migration Report

**Generated**: [date]
**Domain**: [domain]
**Analysis type**: [validate / compare / history / full]

---

## 1. Redirect Validation

**Spec file**: [filename]
**Crawl file**: [filename]
**Total rules in spec**: [N]
**Implementation score**: [X]%

### Results Summary

| Category | Count | % of Total |
|----------|-------|-----------|
| MATCH (correct) | [N] | [%] |
| WRONG_DEST | [N] | [%] |
| WRONG_TYPE | [N] | [%] |
| MISSING | [N] | [%] |
| CHAIN | [N] | [%] |
| LOOP | [N] | [%] |
| EXTRA (not in spec) | [N] | — |

### Critical Issues (MISSING redirects)

| # | Old URL | Expected Destination | Actual Status |
|---|---------|---------------------|---------------|
| 1 | /old-page | /new-page | 404 |
| 2 | /product-x | /products/x | 200 (no redirect) |

### Wrong Destinations

| # | Old URL | Expected | Actual | Status |
|---|---------|----------|--------|--------|
| 1 | /page-a | /page-b | /page-c | 301 |

### Redirect Chains

| # | Chain Path | Hops | Final Destination |
|---|-----------|------|-------------------|
| 1 | /a -> /b -> /c | 2 | /c |

---

## 2. Content Change Detection

**Old crawl**: [filename] ([N] pages)
**New crawl**: [filename] ([N] pages)

### Page Inventory

| Metric | Count |
|--------|-------|
| Matched pages | [N] |
| New pages (added) | [N] |
| Removed pages (missing) | [N] |
| Redirected pages | [N] |

### Critical Changes

| # | URL | Change | Old Value | New Value | Impact |
|---|-----|--------|-----------|-----------|--------|
| 1 | /page | Status 200 -> 404 | 200 | 404 | Critical |
| 2 | /blog/post | Word count -65% | 2,400 | 840 | High |
| 3 | /service | Indexability lost | Indexable | Non-indexable | Critical |

### Title Changes

| # | URL | Old Title | New Title |
|---|-----|-----------|-----------|
| 1 | /page | "Old Title Here" | "New Title Here" |

### Content Volume Changes

| Category | Count | Avg Word Count Change |
|----------|-------|----------------------|
| Significant decrease (>30%) | [N] | -[X]% |
| Minor decrease (10-30%) | [N] | -[X]% |
| Stable (within 10%) | [N] | [X]% |
| Increase | [N] | +[X]% |

### Removed Pages (not redirected)

| # | URL | Old Title | Word Count | Risk |
|---|-----|-----------|------------|------|
| 1 | /old-page | "Title" | 2,500 | High — substantial content lost |

---

## 3. Wayback Machine Analysis

**Domain**: [domain]
**Period**: [start year] - [end year]
**Total snapshots analyzed**: [N]

### Site Size Over Time

| Year | Unique URLs | Change | Notes |
|------|------------|--------|-------|
| 2021 | 450 | — | Baseline |
| 2022 | 620 | +38% | Blog expansion |
| 2023 | 580 | -6% | Minor pruning |
| 2024 | 1,200 | +107% | Major expansion / new sections |
| 2025 | 950 | -21% | Migration — content consolidation |

### robots.txt Changes

| Date | Change | Risk |
|------|--------|------|
| 2023-06 | Added `Disallow: /staging/` | Low — correct |
| 2024-11 | Added `Disallow: /blog/` | Critical — blog deindexed |
| 2025-01 | Removed `Disallow: /blog/` | Recovery — blog re-allowed |

### Structural Changes Detected

- **2023**: URL pattern shift from `/blog/YYYY/MM/slug` to `/blog/slug`
- **2024**: New `/resources/` section appeared (120+ URLs)
- **2025**: Migration from `.php` URLs to clean URLs (platform change)

---

## 4. Recommendations

### Immediate Actions (pre/during migration)
1. [Fix N missing redirects — see Critical Issues table]
2. [Resolve N redirect chains to single-hop 301s]
3. [Investigate N pages with wrong redirect destinations]

### Post-Migration Monitoring
1. Monitor Google Search Console for coverage errors (daily for 2 weeks)
2. Check crawl stats for spike in 404s
3. Re-crawl with Screaming Frog after 1 week to verify all redirects
4. Compare organic traffic week-over-week for 4 weeks
5. Submit updated sitemap.xml to Google Search Console

### Content Recovery
1. [N pages removed without redirects — evaluate for restoration or redirect]
2. [N pages with significant content reduction — review for quality]
```

---

## Cross-References

| Skill | When to use together |
|-------|---------------------|
| `42:technical` | Full technical SEO audit after migration completes |
| `42:audit` | Comprehensive site audit to catch post-migration issues |
| `42:screaming-frog` | Generate the crawl CSVs needed as input for this skill |
| `42:sitemap` | Validate sitemap after migration (new URLs, removed old URLs) |
| `42:meta-optimizer` | Optimize meta descriptions on the new site post-migration |

---

## Tips

- **Pre-migration**: Run `validate` with your redirect spec against a staging
  crawl before going live. Fix all MISSING and WRONG_DEST issues first.
- **Post-migration**: Run `compare` immediately after launch, then again at
  1 week and 4 weeks to catch delayed issues.
- **Large migrations**: For 10,000+ redirects, use the Python script for faster
  processing. Claude analyzes the JSON output.
- **Redirect chains**: Every chain adds latency and dilutes PageRank. Resolve
  all chains to single-hop 301s before migration.
- **Content freeze**: Avoid content changes during migration week — it makes
  the `compare` results noisy and harder to audit.
