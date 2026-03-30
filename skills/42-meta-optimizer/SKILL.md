---
name: 42-meta-optimizer
description: >
  AI-powered bulk meta description analysis: score quality on 4 criteria (0-40),
  rewrite to length constraints (desktop ≤160 chars, mobile ≤130 chars), and
  generate featured snippet "At a glance" summaries. Accepts single URLs, CSVs
  with URLs, or Screaming Frog Internal:HTML exports. No Python scripts — this
  is fully AI-based analysis and rewriting. Use when user says "meta description",
  "meta optimizer", "meta rewrite", "snippet", "featured snippet", "meta grade",
  "meta score", "meta quality", "SERP snippet", "description optimization",
  "meta bulk", "rewrite descriptions".
version: 1.0.0
tags: [seo, meta-description, copywriting, featured-snippet, serp, ai-rewrite, bulk]
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/meta*.csv"
    - "**/internal_html*.csv"
    - "**/descriptions*.csv"
    - "**/META-OPTIMIZER.md"
  bashPattern:
    - "meta.optim"
    - "meta.desc"
    - "meta.rewrite"
---

# Meta Optimizer — AI-Powered Meta Description Analysis & Rewriting

## Purpose

Analyze, score, rewrite, and optimize meta descriptions at scale using AI. No
external scripts required — Claude performs all grading, rewriting, and snippet
generation directly. Works with single URLs, CSV files, or Screaming Frog
Internal:HTML exports.

---

## Commands

```
/42:meta-optimizer grade <url-or-csv>          # Score meta descriptions (0-40)
/42:meta-optimizer rewrite <url-or-csv>        # AI rewrite to length constraints
/42:meta-optimizer snippet <url-or-csv>        # Generate featured snippet summaries
/42:meta-optimizer full <url-or-csv>           # All three: grade + rewrite + snippet
```

---

## Input Formats

### Single URL
Provide a URL directly. Claude fetches the page with WebFetch and extracts the
existing meta description, title, H1, and page content for context.

### CSV File
A CSV with at minimum a `URL` column. Optional columns:
- `Meta Description` or `Description 1` — existing description text
- `Title 1` or `Title` — page title
- `H1-1` or `H1` — primary heading
- `Word Count` — page word count

### Screaming Frog Internal:HTML Export
Standard SF export with columns: `Address`, `Title 1`, `Meta Description 1`,
`Meta Description 1 Length`, `Meta Description 1 Pixel Width`, `H1-1`,
`Word Count`, `Status Code`. Read the CSV with the Read tool and parse
accordingly.

---

## Workflow

### Step 1: Parse Input

1. **Single URL**: Use WebFetch to retrieve the page. Extract `<title>`,
   `<meta name="description">`, `<h1>`, and the first 500 words of body text.
2. **CSV / SF Export**: Use Read to load the file. Identify column mapping:
   - URL column: `Address` or `URL` or first column containing URLs
   - Description column: `Meta Description 1` or `Meta Description` or `Description`
   - Title column: `Title 1` or `Title`
   - H1 column: `H1-1` or `H1`
3. For CSVs with many rows, process in batches of 25.

### Step 2: Grade Meta Descriptions

Score each meta description on 4 criteria, each 0-10 points, for a total of 0-40.

#### Rubric

| # | Criterion | 0-3 (Weak) | 4-6 (Adequate) | 7-10 (Strong) |
|---|-----------|------------|----------------|---------------|
| 1 | **Emotional hooks** | No power words, flat tone, reads like a dictionary definition | 1-2 mild engagement words, some personality | Strong power words (proven, essential, secret, surprising), creates curiosity or urgency |
| 2 | **Benefit-driven** | Describes what the page is, not what the user gets | Hints at value but buries it | Leads with clear user benefit, answers "what's in it for me?" |
| 3 | **Active voice** | Mostly passive constructions ("is described", "are listed") | Mix of active and passive | Entirely active voice, subject-verb-object, direct and commanding |
| 4 | **CTA / Urgency** | No call to action, no time sensitivity | Weak CTA ("learn more") or generic urgency | Strong CTA (discover, master, unlock, get started) with scarcity or time element |

#### Score Interpretation

| Range | Rating | Action |
|-------|--------|--------|
| 0-10 | Poor | Full rewrite required |
| 11-20 | Below Average | Significant improvements needed |
| 21-30 | Good | Minor tweaks recommended |
| 31-40 | Excellent | No changes needed |

### Step 3: Rewrite Meta Descriptions

For each description scoring below 30, generate optimized rewrites following
these constraints:

#### Desktop Version (primary)
- **Max 160 characters** (hard limit)
- **Target pixel width**: ≤990 pixels (approximate: avg 6.2px per character)
- **Structure**: [Benefit/Hook] + [Core value] + [CTA or closing benefit]
- Must include the primary keyword naturally (infer from title + H1)
- End with a period or CTA verb phrase
- No quotes, no ALL CAPS, no excessive punctuation

#### Mobile Version
- **Max 130 characters** (hard limit)
- Tighter version of desktop — same message, fewer words
- Prioritize the single strongest benefit
- Still includes primary keyword

#### Rewrite Rules
1. **Preserve brand voice**: Match the tone of the existing description and page
   content (formal, casual, technical, friendly)
2. **Primary keyword**: Identify from title + H1 + URL slug. Place in first
   half of description when possible.
3. **No keyword stuffing**: Keyword appears once, maximum twice if natural.
4. **End strong**: Close with a CTA verb (discover, learn, explore, get, try,
   see, find, start) or a concrete benefit statement.
5. **Front-load value**: Most important information in first 80 characters
   (visible in all SERP truncation scenarios).
6. **Avoid cliches**: No "In this article", "Click here to", "Welcome to",
   "Looking for", "Read on to find out".

### Step 4: Generate Featured Snippet Summaries

Create an "At a glance" summary optimized for Google Featured Snippet extraction.

#### Snippet Format
```
**At a glance:**
- [Bullet 1: Key fact or definition]
- [Bullet 2: Core benefit or primary answer]
- [Bullet 3: Supporting detail or statistic]
- [Bullet 4: Secondary benefit or scope] (optional)
- [Bullet 5: Action or next step] (optional)
```

#### Snippet Rules
- **3-5 bullets** per page
- **40-60 words total** (strict range)
- **Factual and declarative**: No hedging ("might", "could", "it depends"),
  no questions, no subjective claims
- **Self-contained**: Each bullet makes sense on its own
- **Front-load answers**: If the page answers a question, the first bullet
  should contain the direct answer
- **Use specific numbers**: Prefer "saves 3 hours per week" over "saves time"
- **No brand fluff**: Focus on information, not marketing
- **Optimized for extraction**: Google's featured snippet algorithm favors
  concise, structured, factual content in list or paragraph format

### Step 5: Generate Report

Compile all results into META-OPTIMIZER.md.

---

## Output Format

Write to `META-OPTIMIZER.md` in the current working directory (or specified output path).

```markdown
# Meta Description Optimization Report

**Generated**: [date]
**Source**: [URL / filename]
**Pages analyzed**: [N]
**Average score**: [X/40]

---

## Grade Summary

| # | URL | Current Description | Score | Emotional | Benefit | Active | CTA | Rating |
|---|-----|-------------------|-------|-----------|---------|--------|-----|--------|
| 1 | /page-1 | "Current meta..." | 24/40 | 6 | 7 | 5 | 6 | Good |
| 2 | /page-2 | "Current meta..." | 12/40 | 3 | 4 | 2 | 3 | Below Avg |
| ... | | | | | | | | |

### Score Distribution
- Excellent (31-40): [N] pages ([%])
- Good (21-30): [N] pages ([%])
- Below Average (11-20): [N] pages ([%])
- Poor (0-10): [N] pages ([%])

---

## Rewrites

### /page-1
**Current** (score: 24/40):
> "Current meta description text here."

**Desktop rewrite** (158 chars):
> "Rewritten meta description with benefit-first structure and strong CTA."

**Mobile rewrite** (127 chars):
> "Shorter version with core benefit and CTA."

**Changes made**: Added power word "proven", led with user benefit, replaced passive "is designed" with active "delivers", added CTA "Get started today."

---

### /page-2
**Current** (score: 12/40):
> "Current weak meta description."

**Desktop rewrite** (155 chars):
> "Optimized description here."

**Mobile rewrite** (128 chars):
> "Mobile version here."

**Changes made**: [specific changes explained]

---

## Featured Snippets

### /page-1
**At a glance:**
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

*Word count: [N] words*

---

### /page-2
**At a glance:**
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]
- [Bullet 4]

*Word count: [N] words*

---

## Implementation Checklist

- [ ] Update meta descriptions in CMS / codebase
- [ ] Verify character counts after CMS rendering (some CMS add suffix)
- [ ] Test SERP preview with Google SERP Simulator
- [ ] Add featured snippet content to page body (above the fold or in FAQ section)
- [ ] Re-crawl with Screaming Frog to verify changes
- [ ] Monitor CTR changes in Google Search Console (2-4 week window)
```

---

## Cross-References

| Skill | When to use together |
|-------|---------------------|
| `42:blog-seo-check` | Run after meta-optimizer to validate full on-page SEO |
| `42:page-analysis` | Deep single-page analysis including meta tag context |
| `42:content` | Content quality scoring — complements meta description quality |
| `42:striking-distance` | Prioritize meta rewrites for pages ranking positions 4-20 |
| `42:screaming-frog` | Export Internal:HTML for bulk meta description input |

---

## Tips

- **Batch processing**: For sites with 100+ pages, prioritize pages with highest
  impressions (from GSC) or those ranking in striking distance (positions 4-20).
- **A/B testing**: Use Google Search Console performance data to measure CTR
  impact of rewritten descriptions after 2-4 weeks.
- **Character vs pixel width**: Google truncates by pixel width (~990px for
  desktop), not character count. 160 chars is a safe proxy, but characters like
  "W" and "M" consume more pixels than "i" and "l".
- **AI provider**: This skill uses Claude's own capabilities for grading and
  rewriting. For alternative providers, pipe the rubric and constraints to
  OpenAI or another API via Bash.
