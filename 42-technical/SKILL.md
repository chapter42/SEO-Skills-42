---
name: 42-technical
description: >
  Unified technical SEO & GEO audit across 10 categories: crawlability, indexability,
  security, URL structure, mobile, Core Web Vitals, server-side rendering, page speed,
  structured data, and IndexNow. Dual scoring: SEO (Google ranking signals) and GEO
  (AI crawler visibility). Use when user says "technical SEO", "crawl issues",
  "robots.txt", "Core Web Vitals", "site speed", "security headers", "SSR", or
  "AI crawlers".
version: 1.0.0
tags: [seo, geo, technical, crawlability, core-web-vitals, ssr, security, performance, ai-crawlers]
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
    - "**/.htaccess"
    - "**/next.config*"
    - "**/vercel.json"
    - "**/vercel.ts"
    - "**/nginx.conf"
  bashPattern:
    - "technical.seo"
    - "core.web.vitals"
    - "lighthouse"
    - "robots"
    - "crawl"
---

# Unified Technical SEO & GEO Audit

## Purpose

Technical SEO forms the foundation of both traditional search visibility and AI search citation. A technically broken site cannot be crawled, indexed, or cited by any platform. This skill audits **10 categories** of technical health with dual scoring:

- **SEO lens:** Google ranking signals, crawl efficiency, rich result eligibility
- **GEO lens:** AI crawler accessibility, server-side rendering (AI crawlers do NOT execute JavaScript), and platform-specific visibility

Default mode reports both scores.

---

## Commands

```
/42:technical <url>          # Full audit — both SEO and GEO scoring
/42:technical <url> --seo    # SEO focus — Google ranking signals
/42:technical <url> --geo    # GEO focus — AI crawler visibility, SSR critical
```

---

## Mode Behavior

| Aspect | Default | `--seo` | `--geo` |
|--------|---------|---------|---------|
| All 10 categories audited | Yes | Yes | Yes |
| SSR weight | 10/100 | 5/100 (nice-to-have) | **15/100 (CRITICAL)** |
| AI crawler scoring | Detailed | Basic (present/absent) | Detailed + platform impact |
| Scoring model | Dual (both) | Per-category XX/100 | Weighted total /100 |
| Output | Both score tables | SEO score table | GEO score table |
| DataForSEO integration | If available | If available | Not used |
| IndexNow GEO framing | Yes | Minimal | Full (ChatGPT via Bing) |

---

## How to Use This Skill

1. Collect the target URL (homepage + 2-3 key inner pages)
2. Fetch each page using curl/WebFetch to get raw HTML and HTTP headers
3. Run through each of the 10 audit categories below
4. Score each category using the mode-appropriate rubric
5. Generate output report

---

## Category 1: Crawlability

### SEO weight: important | GEO weight: 15/100

### 1.1 robots.txt Validity

- Fetch `https://[domain]/robots.txt`
- Check syntactic validity: proper `User-agent`, `Allow`, `Disallow` directives
- Check for common errors: missing User-agent, wildcards blocking important paths, `Disallow: /` blocking entire site
- Verify XML sitemap is referenced: `Sitemap: https://[domain]/sitemap.xml`

### 1.2 AI Crawler Management (CRITICAL for GEO)

Check robots.txt for directives targeting these AI crawlers:

#### Tier 1 — Critical (block = major GEO impact)

| Crawler | User-Agent | Platform | Purpose |
|---------|-----------|----------|---------|
| GPTBot | `GPTBot` | ChatGPT / OpenAI | Model training + search |
| ChatGPT-User | `ChatGPT-User` | ChatGPT | Real-time browsing |
| Googlebot | `Googlebot` | Google Search + AI Overviews | Search + AIO |
| Bingbot | `bingbot` | Bing + Copilot + ChatGPT (via Bing) | Search + AI |

#### Tier 2 — Important (block = reduced GEO visibility)

| Crawler | User-Agent | Platform | Purpose |
|---------|-----------|----------|---------|
| PerplexityBot | `PerplexityBot` | Perplexity AI | Search index + training |
| Google-Extended | `Google-Extended` | Gemini training | AI training (NOT search) |
| ClaudeBot | `ClaudeBot` | Anthropic Claude | Model training |
| Applebot-Extended | `Applebot-Extended` | Apple Intelligence | AI features |

#### Tier 3 — Training-only (block = minimal search impact)

| Crawler | User-Agent | Platform | Purpose |
|---------|-----------|----------|---------|
| Bytespider | `Bytespider` | ByteDance / TikTok AI | Model training |
| CCBot | `CCBot` | Common Crawl | Open dataset (used by many AI) |
| FacebookBot | `FacebookExternalHit` | Meta AI | Social + AI training |
| Amazonbot | `Amazonbot` | Amazon / Alexa AI | AI features |

**Key distinctions:**
- Blocking `Google-Extended` prevents Gemini training but does NOT affect Google Search indexing or AI Overviews (those use `Googlebot`). However, blocking may reduce presence in AI Overviews.
- Blocking `GPTBot` prevents OpenAI training but does NOT prevent ChatGPT from citing your content via browsing (`ChatGPT-User`)
- ~3-5% of websites now use AI-specific robots.txt rules

**AI Crawler Scoring (GEO mode):**

| Scenario | Points (of 5) |
|----------|---------------|
| All major AI crawlers allowed | 5 |
| Some blocked but Googlebot + Bingbot allowed | 3 |
| GPTBot or PerplexityBot blocked | 1 (significant GEO impact) |
| Googlebot blocked | 0 (fatal for all search) |

**Example — selective AI crawler blocking:**
```
# Allow search indexing, block AI training crawlers
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: Bytespider
Disallow: /

# Allow all other crawlers (including Googlebot for search)
User-agent: *
Allow: /
```

**Recommendation:** Consider your AI visibility strategy before blocking. Being cited by AI systems drives brand awareness and referral traffic. Cross-reference the `42:structured-data` skill for entity recognition, and `/geo-crawlers` for the full 14+ crawler reference with per-crawler recommendations.

### 1.3 XML Sitemaps

- Fetch sitemap (check robots.txt for location, or try `/sitemap.xml`, `/sitemap_index.xml`)
- Validate XML syntax
- Check for `<lastmod>` dates (should be present and accurate)
- Count URLs — compare to expected number of indexable pages
- Check for sitemap index if large site (50,000+ URLs per sitemap max)
- Verify all sitemap URLs return 200 status codes (sample check)

### 1.4 Crawl Depth

- Homepage = depth 0. All important pages reachable within **3 clicks** (depth 3)
- Pages at depth 4+ receive significantly less crawl budget and are less likely to be cited by AI
- Check internal linking: are key content pages linked from homepage or main navigation?

### 1.5 Crawl Budget (large sites >10k pages)

- Assess whether thin, duplicate, or parameter pages waste crawl budget
- Check for unnecessary URLs in sitemap (paginated, filtered, sorted variations)
- Evaluate robots.txt efficiency: are non-content resources (CSS, JS, images) correctly handled?
- Flag if indexed pages significantly exceed valuable content pages

### 1.6 Noindex Management

- Check for `<meta name="robots" content="noindex">` on pages that SHOULD be indexed
- Check for `X-Robots-Tag: noindex` HTTP headers
- Common mistakes: noindex on paginated pages, category pages, or key landing pages

**GEO Scoring:**

| Check | Points |
|-------|--------|
| robots.txt valid and complete | 3 |
| AI crawlers allowed | 5 |
| XML sitemap present and valid | 3 |
| Crawl depth within 3 clicks | 2 |
| No erroneous noindex directives | 2 |
| **Total** | **15** |

---

## Category 2: Indexability

### SEO weight: important | GEO weight: 12/100

### 2.1 Canonical Tags

- Every indexable page must have `<link rel="canonical" href="...">`
- Canonical must self-reference for the authoritative version
- Check for conflicting canonicals (HTML vs HTTP header)
- Check for canonical chains (A→B→C should be A→C directly)

**JavaScript caveat (Dec 2025):** If a canonical tag in raw HTML differs from one injected by JavaScript, Google may use EITHER one. Ensure canonical tags are identical between server-rendered HTML and JS-rendered output.

### 2.2 Duplicate Content

- www vs non-www: both resolve, one redirects
- HTTP vs HTTPS: HTTP must redirect to HTTPS
- Trailing slash consistency: pick one pattern, redirect the other
- Parameter-based duplicates (`?sort=price` creating duplicate pages)

### 2.3 Pagination

- Check for `rel="next"` / `rel="prev"` (Google ignores since 2019; Bing still uses)
- Preferred: `rel="canonical"` on paginated pages pointing to view-all or first page
- Ensure paginated pages not noindexed if they contain unique content

### 2.4 Hreflang (international sites)

- Check for `<link rel="alternate" hreflang="xx">` tags
- Validate reciprocal hreflang (A→B means B must→A)
- Validate x-default fallback exists
- Check language/region code validity (ISO 639-1 / ISO 3166-1)

### 2.5 Index Bloat

- Estimate indexed pages (sitemap count, `site:domain.com`)
- Compare indexed vs actual valuable content pages
- Flag if indexed pages significantly exceed content pages

**GEO Scoring:**

| Check | Points |
|-------|--------|
| Canonical tags correct on all pages | 3 |
| No duplicate content issues | 3 |
| Pagination handled correctly | 2 |
| Hreflang correct (if applicable) | 2 |
| No index bloat | 2 |
| **Total** | **12** |

---

## Category 3: Security

### SEO weight: important | GEO weight: 10/100

### 3.1 HTTPS Enforcement

- Site loads over HTTPS
- HTTP redirects to HTTPS (301)
- No mixed content warnings (HTTP resources on HTTPS pages)
- SSL/TLS certificate valid and not expired

### 3.2 Security Headers

| Header | Required Value | Purpose |
|--------|---------------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Forces HTTPS |
| `Content-Security-Policy` | Appropriate policy | Prevents XSS |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Prevents clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` or stricter | Controls referrer |
| `Permissions-Policy` | Appropriate restrictions | Controls browser features |

### 3.3 HSTS Preload

- For high-security sites: check HSTS preload list inclusion
- Requires: `includeSubDomains` and `preload` directives in HSTS header

**GEO Scoring:**

| Check | Points |
|-------|--------|
| HTTPS enforced with valid cert | 4 |
| HSTS header present | 2 |
| X-Content-Type-Options | 1 |
| X-Frame-Options | 1 |
| Referrer-Policy | 1 |
| Content-Security-Policy | 1 |
| **Total** | **10** |

---

## Category 4: URL Structure

### SEO weight: moderate | GEO weight: 8/100

### 4.1 Clean URLs

- Human-readable: `/blog/seo-guide` not `/blog?id=12345`
- No session IDs in URLs
- Lowercase only (no mixed case)
- Hyphens for word separation (not underscores)
- No special characters or encoded spaces

### 4.2 Logical Hierarchy

- URL path reflects site architecture: `/category/subcategory/page`
- Flat where appropriate — avoid unnecessarily deep nesting
- Consistent pattern across the site

### 4.3 Redirect Chains

- No redirect chains (A→B→C)
- Maximum 1 hop recommended (A→C directly)
- No redirect loops
- All redirects 301 (permanent), not 302, unless intentionally temporary

### 4.4 Parameter Handling

- URL parameters must not create duplicate indexable pages
- Use canonical tags or `robots.txt Disallow` for parameter variations
- Configure parameter handling in Google Search Console and Bing Webmaster Tools

### 4.5 URL Length

- Flag URLs >100 characters
- Shorter URLs correlate with better click-through rates and easier sharing

### 4.6 Trailing Slash Consistency

- Pick one pattern (with or without trailing slash)
- Redirect the other pattern to the canonical version
- Inconsistency creates duplicate content signals

**GEO Scoring:**

| Check | Points |
|-------|--------|
| Clean, readable URLs | 2 |
| Logical hierarchy | 2 |
| No redirect chains (max 1 hop) | 2 |
| Parameter handling configured | 2 |
| **Total** | **8** |

---

## Category 5: Mobile Optimization

### SEO weight: critical | GEO weight: 10/100

### Critical Context

As of **July 2024**, Google crawls ALL sites exclusively with mobile Googlebot. There is no desktop crawling. **Mobile-first indexing is 100% complete.** If your site does not work on mobile, it does not work for Google. Period.

### 5.1 Responsive Design

- Check for `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Content must not require horizontal scrolling on mobile
- No fixed-width layouts wider than viewport

### 5.2 Tap Targets

- Interactive elements (buttons, links) at least **48x48 CSS pixels**
- Minimum **8px spacing** between tap targets
- Navigation usable on mobile

### 5.3 Font Sizes

- Base font size at least **16px**
- No text requiring zoom to read
- Sufficient contrast ratio (WCAG AA: 4.5:1 normal text, 3:1 large text)

### 5.4 Mobile Content Parity

- All desktop-visible content also visible on mobile
- No hidden content behind "read more" toggles that crawlers cannot expand (Google improved at expanding these as of 2025, but AI crawlers cannot)
- Images and media load on mobile

**GEO Scoring:**

| Check | Points |
|-------|--------|
| Viewport meta tag correct | 3 |
| Responsive layout (no horizontal scroll) | 3 |
| Tap targets appropriately sized | 2 |
| Font sizes legible | 2 |
| **Total** | **10** |

---

## Category 6: Core Web Vitals

### SEO weight: ranking signal | GEO weight: 15/100

### 2026 Metrics and Thresholds

Core Web Vitals use the **75th percentile** of real user data (field data). Lab data is useful for debugging but field data determines the ranking signal.

| Metric | Good | Needs Improvement | Poor | Notes |
|--------|------|-------------------|------|-------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s - 4.0s | > 4.0s | Loading — time until largest visible element renders |
| **INP** (Interaction to Next Paint) | < 200ms | 200ms - 500ms | > 500ms | Replaced FID March 2024. Measures ALL interactions |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 - 0.25 | > 0.25 | Visual stability — unexpected layout movements |

> **FID is dead.** INP replaced FID on March 12, 2024. FID was fully removed from all Chrome tools (CrUX API, PageSpeed Insights, Lighthouse) on September 9, 2024. Do NOT reference FID anywhere.

### How to Assess Without CrUX Data

When real user data is unavailable, estimate from page characteristics:
- **LCP**: Check largest above-fold element. Image (check size/format)? Text (check web font loading)? Server response time (TTFB)?
- **INP**: Check for heavy JavaScript. Long tasks (>50ms) block interactivity. Third-party scripts?
- **CLS**: Images without explicit width/height? Dynamically inserted content above fold? Web fonts causing layout shift (FOUT/FOIT)?

### Common LCP Fixes

1. Optimize hero images: **WebP/AVIF** format, correct sizing, preload with `<link rel="preload">`
2. Reduce server response time (**TTFB < 800ms**)
3. Eliminate render-blocking CSS/JS
4. Preconnect to critical third-party origins: `<link rel="preconnect" href="...">`
5. Use `fetchpriority="high"` on LCP element

### Common INP Fixes

1. Break up long tasks (>50ms) into smaller chunks using `requestIdleCallback` or `scheduler.yield()`
2. Reduce third-party JavaScript
3. Use `content-visibility: auto` for off-screen content
4. Debounce/throttle event handlers
5. Defer non-critical JavaScript with `defer` attribute

### Common CLS Fixes

1. Always include `width` and `height` attributes on images and videos
2. Reserve space for ads and embeds with CSS `aspect-ratio` or explicit dimensions
3. Use `font-display: swap` with size-adjusted fallback fonts
4. Avoid inserting content above existing content after page load
5. Use `min-height` on dynamic containers

**GEO Scoring:**

| Check | Points |
|-------|--------|
| LCP < 2.5s | 5 |
| INP < 200ms | 5 |
| CLS < 0.1 | 5 |
| **Total** | **15** |

---

## Category 7: Server-Side Rendering & JavaScript SEO

### SEO weight: moderate (5/100) | GEO weight: CRITICAL (15/100)

### Why SSR Matters

**For GEO (CRITICAL):** AI crawlers (GPTBot, PerplexityBot, ClaudeBot, etc.) do **NOT execute JavaScript**. They fetch raw HTML and parse it. If content is rendered client-side by React, Vue, Angular, or any JavaScript framework, AI crawlers see an empty page.

**For SEO (important):** Even Googlebot, which does execute JavaScript, deprioritizes JS-rendered content. Google processes JS rendering in a separate "rendering queue" that can delay indexing by days or weeks.

### 7.1 SSR Detection Method

1. Fetch the page with curl (no JavaScript execution): `curl -s [URL]`
2. Compare raw HTML to rendered DOM (via browser)
3. If key content (headings, paragraphs, product info, article text) is MISSING from the curl output, the site relies on client-side rendering

### 7.2 What to Check in Raw HTML

| Element | In raw HTML? | Impact if missing |
|---------|:------------:|------------------|
| Main content text (article body, product description) | Required | AI crawlers see empty page |
| Headings (H1, H2, H3) | Required | No semantic structure for AI |
| Navigation / internal links | Required | Crawlability broken for all crawlers |
| Structured data (JSON-LD) | Required | No entity recognition |
| Meta tags (title, description, canonical, OG) | Required | No SEO signals |
| Images with alt text | Recommended | Missing media context |

### 7.3 JavaScript SEO — Canonical & Indexing Guidance (December 2025)

Google updated JavaScript SEO documentation in December 2025 with critical clarifications:

1. **Canonical conflicts:** If canonical in raw HTML differs from one injected by JavaScript, Google may use EITHER one. Ensure canonical tags are identical between server-rendered and JS-rendered output.
2. **noindex with JavaScript:** If raw HTML contains `<meta name="robots" content="noindex">` but JavaScript removes it, Google MAY still honor the raw HTML noindex. Serve correct robots directives in initial HTML.
3. **Non-200 status codes:** Google does NOT render JavaScript on pages returning non-200 HTTP status codes. JS-injected content on error pages is invisible to Googlebot.
4. **Structured data in JavaScript:** Product, Article, and other structured data injected via JS may face delayed processing. For time-sensitive structured data, include in server-rendered HTML.

**Best practice:** Serve ALL critical SEO elements (canonical, meta robots, structured data, title, meta description) in initial server-rendered HTML. Never rely on JavaScript injection for these.

### 7.4 SSR Solutions by Framework

| Framework | SSR Solution | Notes |
|-----------|-------------|-------|
| React | **Next.js** (SSR/SSG/ISR) | Recommended. Turbopack default bundler in v16 |
| React | Remix | Full SSR, nested routing |
| React | Gatsby | SSG-focused |
| Vue | **Nuxt.js** (SSR/SSG) | Recommended |
| Angular | Angular Universal | SSR support |
| Svelte | **SvelteKit** | SSR/SSG built-in |
| Generic | Prerender.io | Prerendering service (not true SSR) |
| Generic | Rendertron | Google's prerendering solution |

### 7.5 SPA Framework Detection

Flag these client-side frameworks if detected without SSR:
- React (`react-dom`, `__NEXT_DATA__` absent = no Next.js)
- Vue (`__vue__`, `__NUXT__` absent = no Nuxt)
- Angular (`ng-version`, universal markers absent)
- Svelte (check for SvelteKit markers)

**GEO Scoring:**

| Check | Points |
|-------|--------|
| Main content in raw HTML | 8 |
| Meta tags + structured data in raw HTML | 4 |
| Internal links in raw HTML | 3 |
| **Total** | **15** |

**SEO Scoring:** Same checks, but total weight is 5/100 (SSR is nice-to-have, not critical).

---

## Category 8: Page Speed & Server Performance

### SEO weight: moderate | GEO weight: 15/100

### 8.1 Time to First Byte (TTFB)

- Target: **< 800ms** (ideally < 200ms)
- Measure with curl: `curl -o /dev/null -s -w 'TTFB: %{time_starttransfer}s\n' [URL]`
- If TTFB > 800ms: check server location, caching, database queries, CDN usage

### 8.2 Resource Optimization

- Total page weight target: **< 2MB** (critical pages < 1MB)
- Check for uncompressed resources (gzip/brotli compression must be enabled)
- Check for unminified CSS and JavaScript
- Check for unused CSS/JS (can represent 50%+ of downloaded bytes)

### 8.3 Image Optimization

- Check image formats: **WebP or AVIF** preferred over JPEG/PNG
- Check for oversized images (images larger than display size)
- Check for lazy loading: below-fold images should have `loading="lazy"`
- Check for explicit dimensions (`width`/`height` attributes prevent CLS)
- Above-fold images should **NOT** be lazy loaded (harms LCP)
- LCP image should have `fetchpriority="high"` and `<link rel="preload">`

### 8.4 Code Splitting and Lazy Loading

- JavaScript should be code-split so each page only loads what it needs
- Check for large JavaScript bundles:
  - **Warning:** > 200KB compressed
  - **Critical:** > 500KB compressed
- Third-party scripts should load asynchronously (`async` or `defer`)
- Check for render-blocking resources in `<head>`

### 8.5 Caching

- Check `Cache-Control` headers on static resources (images, CSS, JS)
- Static assets: `max-age=31536000` (1 year) with content-hashed filenames
- HTML pages: shorter cache or `no-cache` with validation (`ETag` / `Last-Modified`)

### 8.6 CDN Usage

- Check if static resources served from CDN (different domain or CDN headers)
- CDN-specific headers to detect:
  - `CF-Ray` → Cloudflare
  - `X-Cache` → AWS CloudFront
  - `X-Served-By` → Fastly
  - `X-Vercel-Cache` → Vercel
- For global audience, CDN is critical for consistent performance

**GEO Scoring:**

| Check | Points |
|-------|--------|
| TTFB < 800ms | 3 |
| Page weight < 2MB | 2 |
| Images optimized (format, size, lazy) | 3 |
| JS bundles reasonable (< 200KB compressed) | 2 |
| Compression enabled (gzip/brotli) | 2 |
| Cache headers on static resources | 2 |
| CDN in use | 1 |
| **Total** | **15** |

---

## Category 9: Structured Data

### SEO weight: moderate | GEO weight: included in schema skill

This category provides a quick check. For full schema audit, use `42:structured-data`.

### Quick Checks

- JSON-LD detected? (preferred format)
- Microdata or RDFa only? → flag for migration
- Organization/Person schema present? (entity recognition)
- Article schema with author details? (E-E-A-T signal)
- sameAs properties present? (entity graph for AI)
- Server-rendered or JavaScript-injected?

### Action

If schema issues found, recommend: "Run `/42:structured-data` for full schema audit, scoring, and code generation."

---

## Category 10: IndexNow Protocol

### SEO weight: low-moderate | GEO weight: significant for AI visibility

### What It Is

IndexNow is an open protocol allowing websites to notify search engines instantly when content is created, updated, or deleted. Supported by **Bing, Yandex, Seznam, and Naver**. Google does NOT support IndexNow but monitors the protocol.

### Why It Matters for GEO

ChatGPT uses **Bing's index**. Bing Copilot uses **Bing's index**. Faster Bing indexing means faster AI visibility on two major AI platforms. Implementing IndexNow can reduce the time from content publication to AI citation from weeks to hours.

### Implementation Check

1. Check for IndexNow key file: `https://[domain]/.well-known/indexnow-key.txt` or similar
2. Check if CMS has IndexNow plugin:
   - WordPress: IndexNow plugin (official)
   - Many modern CMS platforms support natively
   - Next.js: can implement via API route
3. If not implemented, recommend adding with instructions

### Implementation Example

```
POST https://api.indexnow.org/IndexNow HTTP/1.1
Content-Type: application/json

{
  "host": "example.com",
  "key": "your-indexnow-key",
  "urlList": [
    "https://example.com/new-page",
    "https://example.com/updated-page"
  ]
}
```

---

## Scoring

### GEO Mode — Weighted Total (100 points)

| Category | Max Points | Weight | Focus |
|----------|-----------|--------|-------|
| Crawlability | 15 | Core foundation | AI crawler access critical |
| Indexability | 12 | Core foundation | Canonical, deduplication |
| Security | 10 | Trust signal | HTTPS + headers |
| URL Structure | 8 | Crawl efficiency | Clean, logical URLs |
| Mobile Optimization | 10 | Google requirement | Mobile-first indexing |
| Core Web Vitals | 15 | Ranking signal + UX | LCP, INP, CLS |
| Server-Side Rendering | **15** | **GEO CRITICAL** | AI crawlers cannot execute JS |
| Page Speed & Server | 15 | Performance | TTFB, resources, CDN |
| **Total** | **100** | | |

### SEO Mode — Per-Category Scoring

Each category scored independently (XX/100). No weighted total — each stands alone with status indicator.

| Category | Status Thresholds |
|----------|------------------|
| All categories | Pass: 80%+ | Warn: 50-79% | Fail: <50% |

### Score Interpretation (GEO mode)

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | Excellent | Technically sound for both traditional SEO and GEO |
| 70-89 | Good | Minor issues, fundamentally solid |
| 50-69 | Needs Work | Significant technical debt impacting visibility |
| 30-49 | Poor | Major issues blocking crawling, indexing, or AI visibility |
| 0-29 | Critical | Fundamental technical failures requiring immediate attention |

---

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, enhance the audit with live data:

| Tool | Purpose | Category |
|------|---------|----------|
| `on_page_instant_pages` | Real page analysis: status codes, timing, broken links | Crawlability, URL Structure |
| `on_page_lighthouse` | Lighthouse audit: performance, accessibility, SEO scores | CWV, Page Speed |
| `domain_analytics_technologies_domain_technologies` | Technology stack detection | SSR/JS detection |

These are optional enrichments — the audit works fully without them using curl/WebFetch.

---

## Output Format

### Default Mode — Dual Report

Generate **TECHNICAL-AUDIT.md**:

```markdown
# Technical SEO & GEO Audit — [Domain]
Date: [Date]
Mode: Default (SEO + GEO)
Pages analyzed: [List of URLs]

---

## GEO Technical Score: XX/100

| Category | Score | Status | Key Finding |
|----------|-------|--------|-------------|
| Crawlability | XX/15 | Pass/Warn/Fail | [One-line] |
| Indexability | XX/12 | Pass/Warn/Fail | [One-line] |
| Security | XX/10 | Pass/Warn/Fail | [One-line] |
| URL Structure | XX/8 | Pass/Warn/Fail | [One-line] |
| Mobile Optimization | XX/10 | Pass/Warn/Fail | [One-line] |
| Core Web Vitals | XX/15 | Pass/Warn/Fail | [One-line] |
| Server-Side Rendering | XX/15 | Pass/Warn/Fail | [One-line] |
| Page Speed & Server | XX/15 | Pass/Warn/Fail | [One-line] |

Status: Pass = 80%+ of category points, Warn = 50-79%, Fail = <50%

---

## SEO Technical Scores

| Category | Score | Status |
|----------|-------|--------|
| Crawlability | XX/100 | Pass/Warn/Fail |
| Indexability | XX/100 | Pass/Warn/Fail |
| Security | XX/100 | Pass/Warn/Fail |
| URL Structure | XX/100 | Pass/Warn/Fail |
| Mobile Optimization | XX/100 | Pass/Warn/Fail |
| Core Web Vitals | XX/100 | Pass/Warn/Fail |
| JS Rendering & SSR | XX/100 | Pass/Warn/Fail |
| Page Speed | XX/100 | Pass/Warn/Fail |
| Structured Data | XX/100 | Pass/Warn/Fail |
| IndexNow | XX/100 | Pass/Warn/Fail |

---

## AI Crawler Access

| Crawler | User-Agent | Tier | Status | Recommendation |
|---------|-----------|------|--------|----------------|
| GPTBot | GPTBot | 1 | Allowed/Blocked | [Action] |
| ChatGPT-User | ChatGPT-User | 1 | Allowed/Blocked | [Action] |
| Googlebot | Googlebot | 1 | Allowed/Blocked | [Action] |
| Bingbot | bingbot | 1 | Allowed/Blocked | [Action] |
| PerplexityBot | PerplexityBot | 2 | Allowed/Blocked | [Action] |
| Google-Extended | Google-Extended | 2 | Allowed/Blocked | [Action] |
| ClaudeBot | ClaudeBot | 2 | Allowed/Blocked | [Action] |
| Applebot-Extended | Applebot-Extended | 2 | Allowed/Blocked | [Action] |
[Continue for all crawlers]

---

## Server-Side Rendering Assessment

| Element | In Raw HTML | Status |
|---------|:-----------:|--------|
| Main content text | Yes/No | [Impact] |
| Headings (H1-H3) | Yes/No | [Impact] |
| Navigation links | Yes/No | [Impact] |
| Structured data (JSON-LD) | Yes/No | [Impact] |
| Meta tags (title, desc, canonical) | Yes/No | [Impact] |

[If CSR detected]: "Your site uses client-side rendering, which means AI crawlers
see an empty page. This is the single most impactful technical issue for AI search
visibility. Recommended: migrate to [SSR solution based on detected framework]."

---

## Core Web Vitals

| Metric | Value | Rating | Fix Priority |
|--------|-------|--------|-------------|
| LCP | X.Xs | Good/Needs Work/Poor | [Specific fix] |
| INP | Xms | Good/Needs Work/Poor | [Specific fix] |
| CLS | X.XX | Good/Needs Work/Poor | [Specific fix] |

---

## Critical Issues (fix immediately)
[List with specific page URLs and what is wrong]

## High Priority (fix within 1 week)
[List with details]

## Medium Priority (fix within 1 month)
[List with details]

## Low Priority (backlog)
[List with details]

---

## Detailed Findings
[Per-category breakdown with evidence]
```

### `--seo` Mode

Same report but:
- No GEO weighted score table
- SEO per-category scores only
- AI crawler section simplified (present/absent)
- SSR section briefer (not flagged as CRITICAL)

### `--geo` Mode

Same report but:
- No SEO per-category score table
- GEO weighted score only
- SSR section prominently flagged as CRITICAL
- IndexNow includes GEO framing (ChatGPT/Copilot via Bing)
- No DataForSEO integration

---

## Cross-References

- For **full schema audit** → use `/42:structured-data`
- For **detailed AI crawler reference** (14+ crawlers) → use `/geo-crawlers`
- For **content quality & E-E-A-T** → use `/seo-content` (SEO lens) or `/geo-content` (GEO lens)
- For **image optimization** → use `/seo-images`
- For **full SEO audit** orchestrating all sub-skills → use `/seo`
- For **full GEO audit** orchestrating all sub-skills → use `/geo`
