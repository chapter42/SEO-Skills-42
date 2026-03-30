---
name: 42-audit
description: >
  Unified SEO + GEO audit orchestrator. Performs full website audits combining
  traditional SEO analysis (crawlability, indexability, Core Web Vitals with INP,
  content quality, schema markup, images, sitemaps) with Generative Engine
  Optimization (AI citability, brand authority, E-E-A-T, AI crawler access,
  llms.txt, platform-specific optimization). Crawls up to 500 pages (SEO mode)
  or 50 pages (GEO mode), detects business type (SaaS, Local, E-commerce,
  Publisher, Agency), delegates to parallel subagents, produces dual scores
  (SEO Health Score 0-100, GEO Score 0-100), and generates a prioritized
  action plan. Triggers on: "audit", "full SEO check", "full GEO check",
  "analyze my site", "website health check", "site audit", "SEO audit",
  "GEO audit", "AI visibility audit".
version: 1.0.0
tags: [seo, geo, audit, orchestrator, health-score, geo-score, eeat, citability, technical, schema, crawl, ai-visibility]
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/robots.txt"
    - "**/sitemap*.xml"
    - "**/llms.txt"
    - "**/.htaccess"
    - "**/next.config*"
    - "**/vercel.json"
  bashPattern:
    - "audit"
    - "seo.audit"
    - "geo.audit"
    - "site.check"
---

# 42-audit — Unified SEO + GEO Audit Orchestrator

> Comprehensive website audit combining traditional SEO analysis with Generative
> Engine Optimization. One command, dual scores, parallel execution.

---

## Quick Reference

| Command | What It Does |
|---------|-------------|
| `/42:audit <url>` | Full dual audit (SEO + GEO) |
| `/42:audit <url> --seo` | SEO-only audit (up to 500 pages) |
| `/42:audit <url> --geo` | GEO-only audit (up to 50 pages) |
| `/42:audit page <url>` | Deep single-page dual analysis |
| `/42:audit technical <url>` | Technical SEO + GEO infrastructure |
| `/42:audit content <url>` | Content quality, E-E-A-T, citability |
| `/42:audit schema <url>` | Structured data detection and validation |
| `/42:audit sitemap <url>` | Sitemap analysis and quality gates |
| `/42:audit images <url>` | Image optimization analysis |
| `/42:audit crawlers <url>` | AI crawler access (robots.txt, meta tags, headers) |
| `/42:audit llmstxt <url>` | llms.txt analysis or generation |
| `/42:audit brands <url>` | Brand mention scanning across AI-cited platforms |
| `/42:audit platforms <url>` | Platform-specific AI search optimization |
| `/42:audit citability <url>` | Passage-level AI citation readiness scoring |
| `/42:audit seo-geo <url>` | AI Overviews / GEO optimization |
| `/42:audit plan <type>` | Strategic SEO planning by business type |

---

## Market Context — Why Dual Auditing Matters

| Metric | Value | Source |
|--------|-------|--------|
| GEO services market (2025) | $850M-$886M | Yahoo Finance / Superlines |
| Projected GEO market (2031) | $7.3B (34% CAGR) | Industry analysts |
| AI-referred sessions growth | +527% (Jan-May 2025) | SparkToro |
| AI traffic conversion vs organic | 4.4x higher | Industry data |
| Google AI Overviews reach | 1.5B users/month, 200+ countries | Google |
| ChatGPT weekly active users | 900M+ | OpenAI |
| Perplexity monthly queries | 500M+ | Perplexity |
| Gartner: search traffic drop by 2028 | -50% | Gartner |
| Marketers investing in GEO | Only 23% | Industry surveys |
| Brand mentions vs backlinks for AI | 3x stronger correlation | Ahrefs (Dec 2025) |

Traditional SEO alone is no longer sufficient. Sites need to be optimized for both
Google's ranking algorithms AND for AI systems that extract, cite, and recommend
content. This orchestrator audits both dimensions in a single pass.

---

## Orchestration Logic

### Mode Selection

| Mode | Flag | Crawl Limit | Scores Produced | Subagents Launched |
|------|------|-------------|-----------------|-------------------|
| **Full (default)** | none | 50 pages | SEO + GEO | All 11 |
| **SEO-only** | `--seo` | 500 pages | SEO only | 6 SEO-focused |
| **GEO-only** | `--geo` | 50 pages | GEO only | 7 GEO-focused |

### Phase 1: Discovery (Sequential)

**Step 1: Fetch Homepage and Detect Business Type**

1. Use WebFetch or curl to retrieve the homepage at the provided URL.
2. Extract signals for business type classification:
   - Page title, meta description, H1 heading
   - Navigation menu items (site structure)
   - Footer content (business info, location, legal pages)
   - Schema.org markup on homepage
   - Key page indicators (pricing, products, blog, case studies, address)
3. Classify the business type (see Business Type Detection below).

**Step 2: Crawl Sitemap and Internal Links**

1. Attempt to fetch `/sitemap.xml` and `/sitemap_index.xml`.
2. If sitemap exists, extract unique page URLs prioritized by:
   - Homepage (always include)
   - Top-level navigation pages
   - High-value pages (pricing, about, contact, key service/product pages)
   - Blog posts (sample 5-10 most recent)
   - Category/landing pages
3. If no sitemap exists, crawl internal links from the homepage:
   - Extract all `<a href>` links pointing to the same domain
   - Follow up to 2 levels deep
   - Prioritize pages linked from main navigation
4. Enforce crawl limits per mode (see Crawl Configuration below).
5. Always respect `robots.txt` directives.

**Step 3: Collect Page-Level Data**

For each page in the crawl set, record:
- URL, title, meta description, canonical URL
- H1-H6 heading structure
- Word count of main content
- Schema.org types present
- Internal/external link counts
- Images with/without alt text
- Open Graph and Twitter Card meta tags
- HTTP status code
- Whether the page has structured data
- Response headers (security, cache, server-side rendering indicators)

### Phase 2: Parallel Subagent Delegation

Launch subagents in parallel based on the selected mode. Each subagent operates
on the collected page data and produces a category score (0-100) plus findings.

#### Full Mode (default) — All 11 Subagents

| # | Subagent | Skill Reference | SEO | GEO | Responsibility |
|---|----------|----------------|-----|-----|---------------|
| 1 | Technical | `42:technical` | Y | Y | Crawlability, indexability, security, CWV, SSR, AI crawler access |
| 2 | Content | `42:content` | Y | Y | E-E-A-T, readability, thin content, AI citation readiness |
| 3 | Structured Data | `42:structured-data` | Y | Y | Schema detection, validation, generation, AI discoverability |
| 4 | Sitemap | `42:sitemap` | Y | — | Structure analysis, coverage, quality gates, missing pages |
| 5 | Images | `42:images` | Y | — | Alt text, file sizes, formats, responsive, lazy loading |
| 6 | SEO-GEO | `42:seo-geo` | Y | — | AI Overviews, ChatGPT citations, Perplexity optimization |
| 7 | Crawlers | `42:crawlers` | — | Y | robots.txt AI directives, meta tags, HTTP headers |
| 8 | LLMs.txt | `42:llmstxt` | — | Y | llms.txt presence, completeness, standard compliance |
| 9 | Brand Mentions | `42:brand-mentions` | — | Y | Brand presence on YouTube, Reddit, Wikipedia, LinkedIn |
| 10 | Platform Optimizer | `42:platform-optimizer` | — | Y | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |
| 11 | Citability | `42:citability` | — | Y | Passage-level quotability, answer block quality, statistical density |

#### SEO-Only Mode (`--seo`) — 6 Subagents

Subagents 1-6 from the table above. Optionally also launch `42:dataforseo` if
DataForSEO MCP tools are available.

#### GEO-Only Mode (`--geo`) — 7 Subagents

Subagents 1-3 (technical, content, structured-data) plus subagents 7-11
(crawlers, llmstxt, brand-mentions, platform-optimizer, citability).

### Phase 3: Score Aggregation and Report Generation

1. Collect all subagent reports and category scores.
2. Calculate composite scores based on mode (see Scoring Methodology below).
3. Classify all issues by severity (Critical, High, Medium, Low).
4. Generate prioritized action plan.
5. Output `AUDIT-REPORT.md` with complete findings.

---

## Business Type Detection

Analyze homepage for these patterns and classify accordingly:

| Type | Detection Signals |
|------|-------------------|
| **SaaS** | Pricing page, "Sign up" / "Free trial" CTAs, `/features`, `/integrations`, `/docs`, `app.domain.com` subdomain, feature comparison tables, API docs |
| **Local Service** | Physical address on homepage, phone number, Google Maps embed, "Near me" content, service area pages, LocalBusiness schema, "serving [city]" |
| **E-commerce** | Product listings, `/products`, `/collections`, `/cart`, "Add to cart" buttons, product schema, price elements, category pages |
| **Publisher** | Blog-heavy navigation, `/blog`, `/articles`, `/topics`, article schema, author pages, publication dates, date-based archives, RSS feeds |
| **Agency** | Portfolio, case studies, `/case-studies`, "Our Work" section, team page, client logos, service descriptions, `/industries` |
| **Hybrid** | Combination of above signals -- classify by dominant pattern |

### Business-Type-Specific Audit Adjustments

#### SaaS Sites
- Extra weight on: Feature comparison tables (high citability), integration pages, documentation quality
- Check for: API documentation structure, changelog pages, knowledge base organization
- Key schema: SoftwareApplication, FAQPage, HowTo (note: HowTo deprecated Sept 2023)
- GEO priority: Comparison content for AI recommendations, technical docs for AI citation

#### Local Businesses
- Extra weight on: NAP consistency, Google Business Profile signals, local schema
- Check for: Service area pages, location-specific content, review markup
- Key schema: LocalBusiness, GeoCoordinates, OpeningHoursSpecification
- GEO priority: Local entity recognition, review aggregation for AI answers

#### E-commerce Sites
- Extra weight on: Product descriptions (citability), comparison content, buying guides
- Check for: Product schema completeness, review aggregation, FAQ sections on product pages
- Key schema: Product, AggregateRating, Offer, BreadcrumbList
- GEO priority: Product recommendation citability, buyer guide extraction

#### Publishers
- Extra weight on: Article quality, author credentials, source citation practices
- Check for: Article schema, author pages, publication date freshness, original research
- Key schema: Article, NewsArticle, Person (author), ClaimReview
- GEO priority: Expert content for AI citation, statistical claims, original data

#### Agency/Services
- Extra weight on: Case studies (citability), expertise demonstration, thought leadership
- Check for: Portfolio schema, team credentials, industry-specific expertise signals
- Key schema: Organization, Service, Person (team), Review
- GEO priority: Case study citability, industry expertise signals for AI recommendations

---

## Crawl Configuration

| Setting | SEO Mode | GEO Mode | Full Mode |
|---------|----------|----------|-----------|
| Max pages | 500 | 50 | 50 |
| Respect robots.txt | Yes | Yes | Yes |
| Follow redirects | Yes (max 3 hops) | Yes (max 3 hops) | Yes (max 3 hops) |
| Timeout per page | 30 seconds | 30 seconds | 30 seconds |
| Concurrent requests | 5 | 5 | 5 |
| Delay between requests | 1 second | 1 second | 1 second |
| Duplicate detection | Skip >80% similarity | Skip >80% similarity | Skip >80% similarity |
| Content types | HTML only | HTML only | HTML only |
| URL canonicalization | Yes (HTTP/HTTPS, www/non-www, trailing slashes) | Yes | Yes |

**Error handling:** Log failed fetches but continue the audit. Report fetch
failures in the appendix. Skip PDFs, images, and other binary content.

---

## Scoring Methodology

### SEO Health Score (0-100)

Weighted aggregate of all SEO categories:

| Category | Weight | Measured By |
|----------|--------|-------------|
| Technical SEO | 22% | Crawlability, indexability, security, URL structure, mobile, server config |
| Content Quality | 23% | E-E-A-T framework, readability, thin content detection, freshness |
| On-Page SEO | 20% | Title tags, meta descriptions, heading structure, internal linking |
| Schema / Structured Data | 10% | Schema completeness, JSON-LD validation, rich result eligibility |
| Performance (CWV) | 10% | LCP, INP, CLS measurements (never FID -- deprecated) |
| AI Search Readiness | 10% | Citability score, AI crawler access, structural improvements |
| Images | 5% | Alt text, file sizes, formats, responsive, lazy loading |

**Formula:**
```
SEO_Score = (Technical * 0.22) + (Content * 0.23) + (OnPage * 0.20) + (Schema * 0.10) + (CWV * 0.10) + (AIReady * 0.10) + (Images * 0.05)
```

### GEO Score (0-100)

Weighted aggregate of all GEO categories:

| Category | Weight | Measured By |
|----------|--------|-------------|
| AI Citability | 25% | Passage scoring, answer block quality, statistical density, AI crawler access |
| Brand Authority | 20% | Mentions on Reddit, YouTube, Wikipedia, LinkedIn; entity presence |
| Content E-E-A-T | 20% | Expertise signals, original data, author credentials, source citations |
| Technical GEO | 15% | SSR, Core Web Vitals, crawlability, mobile, security, AI crawler directives |
| Schema & Structured Data | 10% | Schema completeness, JSON-LD validation, AI-critical schema types |
| Platform Optimization | 10% | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |

**Formula:**
```
GEO_Score = (Citability * 0.25) + (Brand * 0.20) + (EEAT * 0.20) + (Technical * 0.15) + (Schema * 0.10) + (Platform * 0.10)
```

### Score Interpretation

| Score Range | Rating | SEO Interpretation | GEO Interpretation |
|-------------|--------|-------------------|-------------------|
| 90-100 | Excellent | Top-tier SEO; well-optimized for rankings | Highly likely to be cited by AI systems |
| 75-89 | Good | Strong SEO foundation with room to improve | Strong GEO foundation, some gaps |
| 60-74 | Fair | Moderate SEO presence; significant opportunities | Moderate AI presence; optimization opportunities exist |
| 40-59 | Poor | Weak SEO signals; rankings at risk | Weak GEO signals; AI systems may struggle to cite |
| 0-39 | Critical | Major SEO issues; likely de-indexed or penalized | Largely invisible to AI systems |

---

## Issue Severity Classification

Every issue found during the audit is classified by severity. Definitions are
consistent across both SEO and GEO dimensions.

### Critical (Fix Immediately)
- Site returns 5xx errors on key pages
- Domain-level noindex directive
- All AI crawlers blocked in robots.txt
- No indexable content (JavaScript-rendered only with no SSR)
- Complete absence of any structured data
- Brand not recognized as an entity by any AI system
- Homepage not indexable
- robots.txt blocks Googlebot entirely
- Sitewide canonical loop or chain

### High (Fix Within 1 Week)
- Key AI crawlers (GPTBot, ClaudeBot, PerplexityBot) blocked
- No llms.txt file present
- Zero question-answering content blocks on key pages
- Missing Organization or LocalBusiness schema
- No author attribution on content pages
- All content behind login/paywall with no preview
- Critical Core Web Vitals failures (LCP > 4s, INP > 500ms, CLS > 0.25)
- Missing or duplicate title tags on important pages
- Broken internal links on navigation pages
- No XML sitemap

### Medium (Fix Within 1 Month)
- Partial AI crawler blocking (some allowed, some blocked)
- llms.txt exists but is incomplete or malformed
- Content blocks average under 50 citability score
- Missing FAQ schema on pages with FAQ content
- Thin author bios without credentials
- No Wikipedia or Reddit brand presence
- Core Web Vitals in "needs improvement" range
- Images over 500KB without optimization
- Missing meta descriptions on secondary pages
- Heading hierarchy issues (skipped levels)

### Low (Optimize When Possible)
- Minor schema validation errors
- Some images missing alt text
- Content freshness issues on non-critical pages
- Missing Open Graph tags
- Suboptimal heading hierarchy on some pages
- LinkedIn company page exists but is incomplete
- Minor title tag length issues
- Non-critical pages missing canonical tags

---

## Quality Gates

### Content Quality Gates

| Page Type | Min Words | Unique Content % | Notes |
|-----------|-----------|-----------------|-------|
| Homepage | 500 | 100% | Must clearly communicate value proposition |
| Service / Feature Page | 800 | 100% | Detailed explanation of offering |
| Location (Primary) | 600 | 60%+ | City headquarters or main service area |
| Location (Secondary) | 500 | 40%+ | Satellite locations |
| Blog Post | 1,500 | 100% | In-depth, valuable content |
| Product Page | 400 | 80%+ | Unique descriptions, specs |
| Category Page | 400 | 100% | Unique intro, not just product listings |
| About Page | 400 | 100% | Company story, team, values |
| Landing Page | 600 | 100% | Focused conversion content |
| FAQ Page | 800 | 100% | Comprehensive Q&A |

### Location Page Thresholds

- **WARNING** at 30+ location pages: Enforce 60%+ unique content per page.
  Content must include unique local information (landmarks, neighborhoods),
  location-specific services, local team info, genuine local testimonials.
- **HARD STOP** at 50+ location pages: Require explicit user justification.
  Must demonstrate legitimate business presence, unique content strategy,
  local signals (Google Business Profile, local reviews).

### Schema Quality Gates

- Never recommend HowTo schema (deprecated Sept 2023).
- FAQ schema for Google rich results: only government and healthcare sites
  (Aug 2023 restriction). Existing FAQPage on commercial sites: flag as Info
  priority (not Critical), noting AI/LLM citation benefit. Adding new FAQPage
  to commercial sites: not recommended for Google benefit, but may help AI
  citation.
- All Core Web Vitals references must use INP, never FID (deprecated March 2024).

### Crawl Quality Gates

- Never crawl more than the mode-specific page limit.
- Prioritize high-value pages when limit is reached.
- Always check and respect robots.txt before crawling.
- Note any AI-specific directives in robots.txt.
- Wait at least 1 second between page fetches.
- Log failed fetches but continue the audit.
- Only analyze HTML pages; skip binary content.
- Canonicalize URLs before crawling to avoid duplicates.

---

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, spawn the `42:dataforseo` agent alongside
existing subagents to enrich the SEO audit with live data:

- Real SERP positions and visibility
- Backlink profiles with spam scores
- On-page analysis (Lighthouse data)
- Business listings verification
- AI visibility checks (ChatGPT scraper, LLM mentions)
- Keyword rankings and search volume data

This agent is launched only in SEO mode (`--seo`) or full mode. It runs in
parallel with other subagents and its findings are integrated into the final
report under a "Live Data Enrichment" section.

---

## Subagent Delegation Map

### Subagent Reference

| Subagent | Skill | Source Skills Merged | Scope |
|----------|-------|---------------------|-------|
| Technical | `42:technical` | seo-technical + geo-technical | Crawlability, indexability, security, CWV, SSR, mobile, AI crawler access |
| Content | `42:content` | seo-content + geo-content | E-E-A-T, readability, thin content, citability, topical authority |
| Structured Data | `42:structured-data` | seo-schema + geo-schema | Schema detection, validation, generation, AI discoverability |
| Sitemap | `42:sitemap` | seo-sitemap | XML sitemap analysis, generation, quality gates |
| Images | `42:images` | seo-images | Alt text, file sizes, formats, responsive, lazy loading |
| SEO-GEO | `42:seo-geo` | seo-geo | AI Overviews, ChatGPT citations, Perplexity optimization |
| Crawlers | `42:crawlers` | geo-crawlers | AI bot robots.txt, meta tags, HTTP headers |
| LLMs.txt | `42:llmstxt` | geo-llmstxt | llms.txt standard analysis and generation |
| Brand Mentions | `42:brand-mentions` | geo-brand-mentions | Brand presence on AI-cited platforms |
| Platform Optimizer | `42:platform-optimizer` | geo-platform-optimizer | Platform-specific AI search optimization |
| Citability | `42:citability` | geo-citability | Passage-level AI citation readiness |

### Delegation Instructions for Each Subagent

When delegating to a subagent, pass the following context:
1. **URL** — the target site URL
2. **Business type** — the detected business type
3. **Page list** — the crawled page URLs with basic metadata
4. **Mode** — whether this is SEO, GEO, or full audit
5. **Instructions** — "Analyze the provided pages, produce a category score (0-100), and return structured findings with severity classification."

Each subagent returns:
- Category score (0-100)
- List of issues with severity (Critical/High/Medium/Low)
- Specific page URLs affected
- Recommended fixes with expected impact
- Quick wins identified

---

## Output Format

Generate a file called `AUDIT-REPORT.md` with the following structure:

```markdown
# Audit Report: [Site Name]

**Audit Date:** [Date]
**URL:** [URL]
**Mode:** [Full / SEO-Only / GEO-Only]
**Business Type:** [Detected Type]
**Pages Analyzed:** [Count]

---

## Executive Summary

### SEO Health Score: [X]/100 ([Rating])
### GEO Score: [X]/100 ([Rating])

[2-3 sentence summary of the site's overall health, biggest strengths, and most
critical gaps across both SEO and GEO dimensions.]

### SEO Score Breakdown

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Technical SEO | [X]/100 | 22% | [X] |
| Content Quality | [X]/100 | 23% | [X] |
| On-Page SEO | [X]/100 | 20% | [X] |
| Schema / Structured Data | [X]/100 | 10% | [X] |
| Performance (CWV) | [X]/100 | 10% | [X] |
| AI Search Readiness | [X]/100 | 10% | [X] |
| Images | [X]/100 | 5% | [X] |
| **SEO Health Score** | | | **[X]/100** |

### GEO Score Breakdown

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| AI Citability | [X]/100 | 25% | [X] |
| Brand Authority | [X]/100 | 20% | [X] |
| Content E-E-A-T | [X]/100 | 20% | [X] |
| Technical GEO | [X]/100 | 15% | [X] |
| Schema & Structured Data | [X]/100 | 10% | [X] |
| Platform Optimization | [X]/100 | 10% | [X] |
| **GEO Score** | | | **[X]/100** |

---

## Critical Issues (Fix Immediately)

[List each critical issue with specific page URLs, the affected score category,
and a recommended fix with expected impact.]

## High Priority Issues (Fix Within 1 Week)

[List each high-priority issue with details.]

## Medium Priority Issues (Fix Within 1 Month)

[List each medium-priority issue.]

## Low Priority Issues (Backlog)

[List each low-priority issue.]

---

## SEO Deep Dive

### Technical SEO ([X]/100)
[Crawlability, indexability, security, URL structure, mobile, server config findings.]

### Content Quality ([X]/100)
[E-E-A-T assessment, thin content pages, duplicate content, readability scores.]

### On-Page SEO ([X]/100)
[Title tags, meta descriptions, heading structure, internal linking gaps.]

### Schema & Structured Data ([X]/100)
[Current implementation, validation errors, missing opportunities.]

### Performance / Core Web Vitals ([X]/100)
[LCP, INP, CLS scores, resource optimization, third-party script impact.]

### Images ([X]/100)
[Missing alt text, oversized images, format recommendations.]

### AI Search Readiness ([X]/100)
[Citability score, structural improvements, authority signals.]

---

## GEO Deep Dive

### AI Citability ([X]/100)
[Passage scoring, answer block quality, rewrite suggestions for key pages.]

### Brand Authority ([X]/100)
[Platform presence map (YouTube, Reddit, Wikipedia, LinkedIn), mention volume, sentiment.]

### Content E-E-A-T ([X]/100)
[Author quality, source citations, freshness, depth, original research.]

### Technical GEO ([X]/100)
[AI crawler access, llms.txt status, SSR, rendering, security headers.]

### Schema & Structured Data ([X]/100)
[GEO-critical schema types, AI discoverability, rich result eligibility.]

### Platform Optimization ([X]/100)
[Google AIO readiness, ChatGPT citation readiness, Perplexity optimization.]

---

## Quick Wins (Implement This Week)

1. [Specific, actionable quick win with expected impact]
2. [Another quick win]
3. [Another quick win]
4. [Another quick win]
5. [Another quick win]

## 30-Day Action Plan

### Week 1: [Theme — e.g., Critical Fixes & Technical Foundation]
- [ ] Action item 1
- [ ] Action item 2

### Week 2: [Theme — e.g., Content & E-E-A-T Improvements]
- [ ] Action item 1
- [ ] Action item 2

### Week 3: [Theme — e.g., Schema & Structured Data]
- [ ] Action item 1
- [ ] Action item 2

### Week 4: [Theme — e.g., GEO Optimization & AI Visibility]
- [ ] Action item 1
- [ ] Action item 2

---

## Appendix A: Pages Analyzed

| # | URL | Title | Status | SEO Issues | GEO Issues |
|---|-----|-------|--------|------------|------------|
| 1 | [url] | [title] | [code] | [count] | [count] |

## Appendix B: Schema Inventory

| Page | Schema Types Found | Valid | Issues |
|------|--------------------|-------|--------|
| [url] | [types] | [Y/N] | [issues] |

## Appendix C: AI Crawler Access Matrix

| Crawler | User-Agent | robots.txt | Meta Tags | Access |
|---------|-----------|------------|-----------|--------|
| Googlebot | Googlebot | [Allow/Block] | [index/noindex] | [Y/N] |
| GPTBot | GPTBot | [Allow/Block] | — | [Y/N] |
| ClaudeBot | ClaudeBot | [Allow/Block] | — | [Y/N] |
| PerplexityBot | PerplexityBot | [Allow/Block] | — | [Y/N] |
| Google-Extended | Google-Extended | [Allow/Block] | — | [Y/N] |

## Appendix D: DataForSEO Enrichment (if available)

[Live SERP data, backlink profile summary, keyword rankings.]

## Appendix E: Methodology

### SEO Health Score
Weighted aggregate of 7 categories. Each category scored 0-100 by specialized
subagent analysis. Weights reflect relative impact on Google search rankings
based on current algorithm signals (Dec 2025 Core Update, E-E-A-T extended to
all competitive queries).

### GEO Score
Weighted aggregate of 6 categories. Each category scored 0-100 by specialized
subagent analysis. Weights reflect relative impact on AI system citation
probability based on research from Georgia Tech / Princeton / IIT Delhi (2024)
and industry data from Ahrefs, SparkToro, and platform-specific studies.

### Issue Severity
- **Critical**: Blocks indexing, causes penalties, or makes site invisible to AI
- **High**: Significantly impacts rankings or AI citation probability
- **Medium**: Optimization opportunity with measurable impact
- **Low**: Nice-to-have improvement
```

---

## Cross-References to 42: Sub-Skills

This orchestrator delegates to the following consolidated 42: skills. Each can
also be invoked independently:

| Skill | Independent Command | Purpose |
|-------|-------------------|---------|
| `42:technical` | `/42:technical <url>` | Technical SEO + GEO infrastructure audit |
| `42:content` | `/42:content <url>` | Content quality, E-E-A-T, citability analysis |
| `42:structured-data` | `/42:structured-data <url>` | Schema detection, validation, generation |
| `42:sitemap` | `/42:sitemap <url>` | XML sitemap analysis and generation |
| `42:images` | `/42:images <url>` | Image optimization analysis |
| `42:seo-geo` | `/42:seo-geo <url>` | AI Overviews and GEO optimization |
| `42:crawlers` | `/42:crawlers <url>` | AI crawler access analysis |
| `42:llmstxt` | `/42:llmstxt <url>` | llms.txt analysis and generation |
| `42:brand-mentions` | `/42:brand-mentions <url>` | Brand presence on AI-cited platforms |
| `42:platform-optimizer` | `/42:platform-optimizer <url>` | Platform-specific AI search optimization |
| `42:citability` | `/42:citability <url>` | Passage-level AI citation scoring |

---

## Reference Files

Load these on-demand as needed -- do NOT load all at startup:

| Reference | Path | Purpose |
|-----------|------|---------|
| CWV Thresholds | `references/cwv-thresholds.md` | Current Core Web Vitals thresholds (INP, not FID) |
| Schema Types | `references/schema-types.md` | Supported schema types with deprecation status |
| E-E-A-T Framework | `references/eeat-framework.md` | E-E-A-T evaluation criteria (Sept 2025 QRG update) |
| E-E-A-T Scoring Rubric | `references/eeat-scoring-rubric.md` | 100-point rubric (4 x 25 points) for content scoring |
| Quality Gates | `references/quality-gates.md` | Content length minimums, uniqueness thresholds |

---

## Quick Start Examples

```bash
# Full dual audit (SEO + GEO) — default 50 pages
/42:audit https://example.com

# SEO-only audit — up to 500 pages
/42:audit https://example.com --seo

# GEO-only audit — up to 50 pages
/42:audit https://example.com --geo

# Deep single-page analysis
/42:audit page https://example.com/pricing

# Just check technical SEO + AI crawlers
/42:audit technical https://example.com

# Score content for AI citability
/42:audit citability https://example.com/blog/best-article

# Check if AI bots can access your site
/42:audit crawlers https://example.com

# Analyze structured data
/42:audit schema https://example.com
```
