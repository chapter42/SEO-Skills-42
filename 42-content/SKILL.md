---
name: 42-content
description: >
  Unified content quality analysis — E-E-A-T scoring, keyword optimization, AI citability,
  passage architecture, topical authority, and freshness assessment. Dual perspective:
  SEO (Google ranking) and GEO (AI citation). Use when user says "content quality",
  "E-E-A-T", "content analysis", "readability", "thin content", "content audit",
  "citability", or "topical authority".
version: 1.0.0
tags: [seo, geo, content, eeat, citability, readability, topical-authority, keyword, freshness]
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/blog/**"
    - "**/content/**"
    - "**/posts/**"
    - "**/articles/**"
    - "**/*.mdx"
  bashPattern:
    - "content.quality"
    - "content.audit"
    - "eeat"
    - "readability"
---

# Unified Content Quality & E-E-A-T Analysis

## Purpose

Content quality determines both Google rankings and AI citation likelihood. This skill analyzes content through two complementary lenses:

- **SEO lens:** Keyword optimization, multimedia, linking density, Google ranking signals
- **GEO lens:** Passage architecture for AI extraction, citability, topical authority

Default mode reports both. E-E-A-T is the shared foundation — always scored regardless of mode.

---

## Commands

```
/42:content <url>          # Full analysis — both SEO and GEO
/42:content <url> --seo    # SEO focus — keywords, multimedia, linking
/42:content <url> --geo    # GEO focus — citability, passage structure, topical authority
```

---

## Mode Behavior

| Aspect | Default | `--seo` | `--geo` |
|--------|---------|---------|---------|
| E-E-A-T scoring | Always (core) | Always (core) | Always (core) |
| Keyword optimization | Yes | Yes (prominent) | Included with context note |
| Passage architecture | Yes | Minimal | Yes (prominent) |
| Citability assessment | Yes | Minimal | Yes (prominent) |
| Topical authority | Yes | Minimal | Yes (with modifier) |
| Multimedia assessment | Yes | Yes (prominent) | Minimal |
| External linking | Yes | Yes | Minimal |
| DataForSEO integration | If available | If available | Not used |

---

## How to Use This Skill

1. Fetch the target page(s) — homepage, key blog posts, service/product pages
2. Score E-E-A-T using the canonical rubric (see `references/eeat-scoring-rubric.md`)
3. Run mode-appropriate content quality checks
4. Assess content freshness
5. Assess topical authority (site-wide)
6. Generate output report

---

## Part 1: E-E-A-T Assessment (always — core score)

### Scoring

Read `references/eeat-scoring-rubric.md` for the full scoring rubric with per-signal point tables.

Score each of the 4 dimensions (25 points each, 100 total):

| Dimension | Focus | Max |
|-----------|-------|-----|
| Experience | First-hand knowledge, original data, case studies, process evidence | 25 |
| Expertise | Author credentials, technical depth, methodology, data-backed claims | 25 |
| Authoritativeness | External citations, media mentions, awards, topical coverage, Wikipedia | 25 |
| Trustworthiness | Contact info, privacy policy, HTTPS, editorial standards, accuracy | 25 |

E-E-A-T applies to **ALL competitive queries** as of Google's December 2025 Quality Rater Guidelines update, not just YMYL topics.

---

## Part 2: Content Metrics

### 2.1 Word Count Benchmarks

These are **topical coverage floors, not targets**. Google has confirmed word count is NOT a direct ranking factor. The goal is comprehensive topical coverage — a 500-word page that thoroughly answers the query will outrank a 2,000-word page that doesn't.

| Page Type | Minimum | Ideal Range | Notes |
|-----------|---------|-------------|-------|
| Homepage | 500 | 500-1,500 | Clear value proposition, not wall of text |
| Blog post | 1,500 | 1,500-3,000 | Thorough but focused |
| Pillar content / Ultimate guide | 2,000 | 2,500-5,000 | Comprehensive topic coverage |
| Product page | 300 | 500-1,500 | Descriptions, specs, use cases |
| Service page | 500 | 800-2,000 | What, how, why, for whom |
| About page | 300 | 500-1,000 | Company/person story and credentials |
| FAQ page | 500 | 1,000-2,500 | Thorough answers, not one-liners |
| Location page | 500 | 500-600 | Local relevance, unique per location |

### 2.2 Readability

- **Target Flesch Reading Ease:** 60-70 (8th-9th grade level)
- Average sentence length: 15-20 words ideal
- Average paragraph length: 2-4 sentences
- Passive voice: < 15% of sentences
- Jargon: should be defined when first used

> **Note:** Flesch Reading Ease is a useful proxy for content accessibility but is NOT a direct Google ranking factor. John Mueller has confirmed Google does not use basic readability scores for ranking. Yoast deprioritized Flesch in v19.3. Use as a content quality indicator, not an SEO metric.

> **GEO context:** Readability affects citability — AI platforms prefer content that is clear and unambiguous. Overly academic writing (score < 30) reduces citability for general queries. Overly simple writing (score > 80) may lack expertise depth.

### 2.3 Heading Structure

- **One H1 per page** — the primary topic/title
- **H2 for major sections** — distinct subtopics
- **H3 for subsections** — nested under relevant H2
- **No skipped levels** — do not go H1→H3 without H2
- **Descriptive headings** — "How to Optimize for AI Search" not "Section 2"
- **Question-based headings** where appropriate — these map directly to AI queries and trigger People Also Ask. Target: 60-70% of H2s as questions for informational content.

### 2.4 Paragraph Structure for AI Parsing (GEO)

AI platforms extract content at the paragraph level. Each paragraph should be a self-contained unit of meaning.

**Optimal paragraph structure:**
- **2-4 sentences** per paragraph (1-sentence paragraphs are weak; 5+ are hard to extract)
- **One idea per paragraph** — do not mix topics
- **Lead with the key claim** — first sentence contains the main point
- **Support with evidence** — remaining sentences provide data, examples, or context
- **Quotable standalone** — each paragraph should make sense if extracted in isolation

**Optimal passage length for AI citation:** 134-167 words per passage. Content structured in this range gets significantly more AI citations.

---

## Part 3: Keyword Optimization (SEO add-on)

> **Context:** Keyword optimization has no direct impact on AI citation. AI systems cite based on passage quality, not keyword density. However, keyword optimization improves traditional search visibility, which increases the likelihood of AI platforms encountering and indexing your content. Think of it as the path to discovery, not the reason for citation.

### 3.1 Primary Keyword Placement

- Present in title tag
- Present in H1
- Present in first 100 words
- Present in at least one H2
- Present in meta description
- URL slug contains keyword (or close variant)

### 3.2 Keyword Density

- Natural density: 1-3% (not a target — a ceiling)
- Semantic variations present (LSI keywords)
- No keyword stuffing (repetitive, unnatural usage)
- Related terms and synonyms used throughout

### 3.3 Search Intent Alignment

- Content matches the dominant search intent for the target keyword
- Informational queries → comprehensive answers, how-tos, guides
- Transactional queries → product info, pricing, CTAs
- Navigational queries → clear brand/product identification
- Commercial investigation → comparisons, reviews, alternatives

---

## Part 4: Multimedia Assessment (SEO add-on)

### 4.1 Images

- Relevant images with proper alt text (descriptive, not keyword-stuffed)
- Appropriate file format (WebP/AVIF preferred)
- Sized correctly for display (not oversized)
- Lazy loading below fold, eager above fold

### 4.2 Video

- Embedded video where appropriate (how-tos, demonstrations, interviews)
- Video transcript available (accessibility + indexability)
- VideoObject schema if present

### 4.3 Data Visualization

- Infographics for complex data
- Charts/graphs for statistics
- Tables for comparative data (also helps AI extraction)

---

## Part 5: Linking

### 5.1 Internal Linking

- **3-5 relevant internal links per 1,000 words**
- Descriptive anchor text (not "click here" or "read more")
- Links to related content — build topic cluster structure
- Pillar page linked to/from all related subtopic pages
- **No orphan pages** — pages with zero internal links are rarely crawled and never cited by AI

### 5.2 External Linking (SEO add-on)

- Cite authoritative sources (reinforces expertise and trust)
- Open external links in new tab for user experience
- Reasonable count (2-5 per 1,000 words, not excessive)
- No broken external links
- Avoid linking to low-quality or irrelevant sources

---

## Part 6: AI Content Assessment

### AI-Generated Content Policy

AI-generated content is **acceptable** per Google's guidance (March 2024 clarification) as long as it demonstrates genuine E-E-A-T signals and has human oversight. The concern is not HOW content is created but WHETHER it provides value.

> **Helpful Content System (March 2024):** Merged into Google's core ranking algorithm during the March 2024 core update. No longer a standalone classifier. Helpfulness signals are now weighted within every core update — people-first content, E-E-A-T, satisfying user intent.

### Signs of Low-Quality AI Content (flag these)

| Signal | Description |
|--------|------------|
| Generic phrasing | "In today's fast-paced world...", "It's important to note that...", "At the end of the day..." |
| No original insight | Content only rephrases widely available information |
| Lack of first-hand experience | No personal anecdotes, case studies, or specific examples |
| Perfect but empty structure | Well-formatted headings with shallow content beneath |
| No specific examples | Abstract explanations without concrete instances |
| Repetitive conclusions | Each section ends with a variation of the same point |
| Hedging overload | "Generally speaking", "In most cases", "It depends on various factors" — without specifying which |
| Missing human voice | No opinions, preferences, or professional judgment expressed |
| Filler content | Paragraphs that could be deleted without losing information |
| No data or sources | Claims presented as facts without attribution or evidence |

### Signs of High-Quality Content (regardless of production method)

| Signal | Description |
|--------|------------|
| Original data | Surveys, experiments, benchmarks, proprietary analysis |
| Specific examples | Named products, companies, dates, numbers |
| Contrarian or nuanced views | Disagreement with conventional wisdom, backed by reasoning |
| First-person experience | "When I tested this..." or "Our team found..." |
| Updated information | References to recent events, current data |
| Expert opinion | Clear professional judgment, not just facts |
| Practical recommendations | Specific, actionable advice, not vague guidance |
| Trade-offs acknowledged | "This approach works well for X but not for Y because..." |

---

## Part 7: AI Citation Readiness (GEO add-on)

### Why This Matters

**Google AI Mode** launched publicly in May 2025 as a separate tab in Google Search, available in 180+ countries. Unlike AI Overviews (which appear above organic results), AI Mode provides a fully conversational search experience with **zero organic blue links** — making AI citation the only visibility mechanism.

### Citation Optimization Strategies

- **Structured answers:** Clear question-answer formats, definition patterns, step-by-step instructions that AI systems can extract and cite
- **First-party data:** Original research, statistics, case studies, and unique datasets are highly cited
- **Schema markup:** Article, FAQ (for non-Google AI platforms), and structured content schemas help AI parse and attribute. Use `/42:structured-data` for implementation.
- **Entity clarity:** Brand, authors, and key concepts clearly defined with structured data (Organization, Person schema)
- **Multi-platform tracking:** Monitor visibility across Google AI Overviews, AI Mode, ChatGPT, Perplexity, and Bing Copilot — treat AI citation as standalone KPI

### Citation Capsules

For each major H2 section, content should contain a **citation capsule**: a 40-60 word definitive statement that can be extracted by AI systems as a standalone answer. Characteristics:
- Self-contained (makes sense without surrounding text)
- Contains a specific claim or fact
- Includes attribution or data point
- Written in declarative voice (not hedging)

### Passage-Level Citability Checklist

| Check | Target |
|-------|--------|
| Passages 134-167 words | AI-optimal extraction length |
| Lead sentence contains main claim | AI extracts first sentence preferentially |
| Statistics or data within passage | Increases citation probability |
| No hedging language in key passages | "X is..." not "X might be..." |
| Clear entity references | Named companies, products, people |
| Self-contained paragraphs | Each paragraph works as standalone excerpt |

> For deep passage-level scoring (0-100 with rubric), use `/geo-citability`.
> For blog-specific AI citation audit, use `/blog-geo`.
> For content rewriting to maximize AI extractability, use `/42-genai-optimizer`.

---

## Part 8: Content Freshness

### Publication Dates

- Check for visible `datePublished` and `dateModified` in content AND structured data
- Content without dates is treated as less trustworthy by AI platforms
- Dates should be specific (January 15, 2026) not vague ("recently")

### Freshness Scoring

| Criterion | Score | Assessment |
|-----------|-------|-----------|
| Updated within 3 months | Excellent | Current and relevant |
| Updated within 6 months | Good | Still reasonably current |
| Updated within 12 months | Acceptable | May need refresh |
| Updated 12-24 months ago | Warning | Review for accuracy |
| No date or 24+ months old | Critical | AI platforms may deprioritize |

> **GEO context:** 76.4% of top AI citations are from content updated within 30 days. Freshness is a disproportionately strong signal for AI citation.

### Evergreen Content Exceptions

Flag content as evergreen (freshness less critical) if:
- It covers fundamental concepts that do not change (physics, basic math, legal definitions)
- It is clearly labeled as a reference/guide for lasting concepts
- It does NOT contain time-dependent claims ("the latest", "currently", "in 2024")

---

## Part 9: Topical Authority (GEO add-on)

### What It Is

Topical authority measures whether a site comprehensively covers a topic rather than touching on it superficially. AI platforms prefer citing sites that are recognized authorities on their topics.

### How to Assess

1. **Content breadth:** Does the site have multiple pages covering different aspects of its core topic?
2. **Content depth:** Do individual pages go deep into subtopics?
3. **Topic clustering:** Are pages organized into logical groups with internal linking?
4. **Content gaps:** Are there obvious subtopics the site should cover but does not?
5. **Competitor comparison:** Do competitors cover subtopics this site misses?

### Topical Authority Modifier

| Level | Description | Score Impact |
|-------|-------------|-------------|
| Authority | 20+ pages covering topic comprehensively, strong clustering | +10 bonus |
| Developing | 10-20 pages with some clustering | +5 bonus |
| Emerging | 5-10 pages on topic, limited clustering | +0 |
| Thin | < 5 pages, no clustering | -5 penalty |

This modifier applies to the final GEO Content Score (added after E-E-A-T, capped at 100).

---

## Scoring

### Core Score (always calculated)

**E-E-A-T: XX/100** — from `references/eeat-scoring-rubric.md`

### SEO Add-on Score (default + `--seo`)

| Component | Weight | Max |
|-----------|--------|-----|
| Keyword optimization | 25% | 25 |
| Content structure (headings, word count, readability) | 25% | 25 |
| Multimedia | 15% | 15 |
| Internal linking | 15% | 15 |
| External linking | 10% | 10 |
| Freshness | 10% | 10 |
| **SEO Content Score** | | **100** |

### GEO Add-on Score (default + `--geo`)

| Component | Weight | Max |
|-----------|--------|-----|
| Passage architecture (structure, length, self-containment) | 30% | 30 |
| Citation readiness (capsules, declarative voice, data density) | 25% | 25 |
| Content structure (headings, question-based H2s, readability) | 20% | 20 |
| Freshness (weighted heavier — 76.4% of citations from <30 day content) | 15% | 15 |
| Internal linking (orphan detection, cluster structure) | 10% | 10 |
| **GEO Content Score** | | **100** |
| Topical Authority Modifier | | +10 to -5 |
| **Final GEO Score** | | **Capped at 100** |

### Default Mode

Reports all three: E-E-A-T (core), SEO Content Score (add-on), GEO Content Score (add-on).

---

## DataForSEO Integration (Optional — SEO mode)

If DataForSEO MCP tools are available, enhance the analysis with:

| Tool | Purpose |
|------|---------|
| `kw_data_google_ads_search_volume` | Real keyword volume data |
| `dataforseo_labs_bulk_keyword_difficulty` | Difficulty scores |
| `dataforseo_labs_search_intent` | Intent classification |
| `content_analysis_summary` | Content quality analysis |

These are optional enrichments — the audit works fully without them.

---

## Output Format

### Default Mode — Full Report

Generate **CONTENT-ANALYSIS.md**:

```markdown
# Content Quality Analysis — [Domain]
Date: [Date]
Mode: [Default / SEO / GEO]
Pages analyzed: [URLs]

---

## E-E-A-T Score: XX/100

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Experience | XX/25 | [One-line] |
| Expertise | XX/25 | [One-line] |
| Authoritativeness | XX/25 | [One-line] |
| Trustworthiness | XX/25 | [One-line] |

---

## SEO Content Score: XX/100

| Component | Score | Status |
|-----------|-------|--------|
| Keyword Optimization | XX/25 | [Finding] |
| Content Structure | XX/25 | [Finding] |
| Multimedia | XX/15 | [Finding] |
| Internal Linking | XX/15 | [Finding] |
| External Linking | XX/10 | [Finding] |
| Freshness | XX/10 | [Finding] |

---

## GEO Content Score: XX/100 (+ Topical Authority: [+X/-X])

| Component | Score | Status |
|-----------|-------|--------|
| Passage Architecture | XX/30 | [Finding] |
| Citation Readiness | XX/25 | [Finding] |
| Content Structure | XX/20 | [Finding] |
| Freshness | XX/15 | [Finding] |
| Internal Linking | XX/10 | [Finding] |

Topical Authority Level: [Authority/Developing/Emerging/Thin] ([+10/+5/+0/-5])
**Final GEO Score: XX/100**

---

## Pages Analyzed

| Page | Word Count | Readability | Headings | SEO Score | GEO Citability |
|------|-----------|-------------|----------|-----------|---------------|
| [URL] | [Count] | [Flesch] | [Pass/Warn/Fail] | [XX/100] | [High/Med/Low] |

---

## E-E-A-T Detailed Findings

### Experience
[Specific passages and pages with strong/weak experience signals]

### Expertise
[Author credentials found, technical depth assessment, gaps]

### Authoritativeness
[External validation found, topical authority assessment, gaps]

### Trustworthiness
[Trust signals present/missing, accuracy concerns]

---

## AI Content Assessment
[Low-quality AI patterns detected, with specific examples]
[High-quality content signals present]

---

## Content Freshness

| Page | Published | Last Updated | Status |
|------|----------|-------------|--------|
| [URL] | [Date] | [Date] | [Current/Stale/No Date] |

---

## Citability Assessment (GEO)

### Most Citable Passages
[Top 5 passages AI platforms are most likely to cite, with reasons]

### Least Citable Pages
[Pages with lowest citability, with specific improvement recommendations]

### Citation Capsule Gaps
[H2 sections missing a 40-60 word definitive statement]

---

## Keyword Analysis (SEO)

| Keyword | Volume | Density | In Title | In H1 | In First 100w | Intent |
|---------|--------|---------|----------|-------|---------------|--------|
| [Primary] | [Vol] | [%] | Yes/No | Yes/No | Yes/No | [Type] |
| [Secondary] | [Vol] | [%] | — | — | — | [Type] |

---

## Improvement Recommendations

### Quick Wins
[Specific content changes that can be made immediately]

### Content Gaps
[Topics the site should cover to strengthen topical authority]

### E-E-A-T Improvements
[Specific steps to strengthen each dimension]

### Citability Improvements
[Passage restructuring recommendations for AI extraction]
```

### `--seo` Mode

Same report but:
- GEO Content Score table hidden
- Citability assessment minimal (one-line summary)
- Topical authority minimal
- Passage architecture not assessed
- Keyword analysis prominent

### `--geo` Mode

Same report but:
- SEO Content Score table hidden
- Keyword analysis included with context note ("improves discoverability, not citation")
- Citability assessment prominent
- Passage architecture prominent
- Topical authority with modifier
- Multimedia minimal

---

## Cross-References

- For **E-E-A-T scoring details** → see `references/eeat-scoring-rubric.md`
- For **deep passage-level citability scoring** (0-100 rubric) → use `/geo-citability`
- For **blog-specific AI citation audit** → use `/blog-geo`
- For **content rewriting for AI extractability** → use `/42-genai-optimizer`
- For **schema markup** (Article, Person, Organization) → use `/42:structured-data`
- For **keyword cannibalization detection** → use `/blog-cannibalization`
- For **full SEO audit** → use `/seo`
- For **full GEO audit** → use `/geo`
