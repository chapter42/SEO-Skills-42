---
name: 42-structured-data
description: >
  Unified Schema.org structured data skill — detect, validate, score, and generate
  JSON-LD markup for SEO rich results AND AI entity recognition. Combines traditional
  schema audit with GEO sameAs strategy, speakable properties, and blog-specific
  @graph generation. Use when user says "schema", "structured data", "rich results",
  "JSON-LD", "markup", "blog schema", "sameAs", or "entity graph".
version: 1.0.0
tags: [seo, geo, schema, structured-data, json-ld, entity-recognition, ai-discoverability, rich-results]
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
metadata:
  filePattern:
    - "**/schema*"
    - "**/structured-data*"
    - "**/json-ld*"
    - "**/jsonld*"
  bashPattern:
    - "schema"
    - "structured.data"
    - "json-ld"
---

# Unified Schema & Structured Data — Audit, Score & Generate

## Purpose

Structured data serves two distinct but complementary purposes:

1. **SEO (Google Rich Results):** Schema markup earns rich snippets, knowledge panels, and enhanced SERP features. Google validates against specific required/recommended properties per type.
2. **GEO (AI Entity Recognition):** Schema markup is how AI models (ChatGPT, Perplexity, Gemini, Claude) understand WHAT an entity is, trust it, and cite it. The `sameAs` property builds the cross-platform entity graph that AI systems use for verification.

This skill covers both. Default output includes both perspectives.

---

## Commands

```
/42:structured-data <url>                    # Full audit + generation (both SEO and GEO)
/42:structured-data <url> --seo              # SEO focus: rich results, Google requirements
/42:structured-data <url> --geo              # GEO focus: sameAs, speakable, entity graph
/42:structured-data --blog <file-or-url>     # Blog mode: generate @graph for a blog post
/42:structured-data --generate <page-type>   # Generate template for page type
```

---

## Mode Behavior

| Mode | Detection | Validation | sameAs Audit | Scoring | Generation | speakable |
|------|:---------:|:----------:|:------------:|:-------:|:----------:|:---------:|
| Default | Yes | Yes (both) | Yes | GEO rubric (0-100) | Yes | Yes |
| `--seo` | Yes | Google focus | Minimal | Pass/Fail per type | Yes | No |
| `--geo` | Yes | Entity focus | Full (14 platforms) | GEO rubric (0-100) | Yes | Yes |
| `--blog` | N/A | Blog types | Minimal | N/A | Yes (@graph) | No |

---

## Part 1: Detection

### Step 1: Scan for JSON-LD
Look for `<script type="application/ld+json">` blocks in the HTML. Parse each block as JSON. A page may contain multiple JSON-LD blocks — collect all of them.

### Step 2: Scan for Microdata
Look for elements with `itemscope`, `itemtype`, and `itemprop` attributes. Map the hierarchy of nested items.

### Step 3: Scan for RDFa
Look for elements with `typeof`, `property`, and `vocab` attributes.

### Priority
JSON-LD is the **strongly recommended format** for both Google and AI platforms. If the site uses Microdata or RDFa exclusively, flag as **high-priority migration** to JSON-LD.

> **JavaScript rendering warning:** Per Google's December 2025 JS SEO guidance, structured data injected via JavaScript may face delayed processing. For time-sensitive markup (especially Product, Offer), include JSON-LD in the initial server-rendered HTML. AI crawlers do NOT execute JavaScript — JS-injected schema is invisible to AI platforms.

---

## Part 2: Validation

For each detected schema block, validate:

1. **Valid JSON**: Syntactically valid? Trailing commas, unquoted keys, malformed strings.
2. **Valid @context**: Must be `"https://schema.org"`.
3. **Valid @type**: Matches a recognized Schema.org type. Check against current status list (see Part 3).
4. **Required Properties**: All required properties for the type present? (See per-type specs below.)
5. **Recommended Properties**: Recommended properties that increase discoverability present?
6. **sameAs Links** (GEO): Does the schema include `sameAs` properties? How many platforms?
7. **URL Validity**: All URLs absolute (not relative). All resolve (not 404)?
8. **Nesting**: Properly nested (author inside Article, address inside Organization)?
9. **Rendering Method**: In server-rendered HTML or JavaScript-injected?
10. **Data Types**: Correct types (ISO 8601 dates, numbers as numbers, etc.)
11. **Placeholder Detection**: Flag obvious placeholders (`[Company Name]`, `example.com`, `XXX`)

---

## Part 3: Schema Type Status (as of March 2026)

### ACTIVE — recommend freely

Organization, LocalBusiness, SoftwareApplication, WebApplication, Product (with Certification markup as of April 2025), ProductGroup, Offer, Service, Article, BlogPosting, NewsArticle, Review, AggregateRating, BreadcrumbList, WebSite, WebPage, Person, ProfilePage, ContactPage, VideoObject, ImageObject, Event, JobPosting, Course, DiscussionForumPosting, BroadcastEvent, Clip, SeekToAction, SoftwareSourceCode

### RESTRICTED — only for specific sites

- **FAQPage**: ONLY earns Google rich results for government and healthcare authority sites (restricted Aug 2023). **However**, FAQPage schema still serves GEO purposes — AI platforms parse FAQ structured data for question-answer extraction. Implement for AI readability even if rich results won't appear.

### DEPRECATED — never recommend

| Schema | Deprecated | Note |
|--------|-----------|------|
| HowTo | Sep 2023 | Rich results removed. Still useful for AI parsing — do NOT promise rich results |
| SpecialAnnouncement | Jul 2025 | Was for COVID; remove if still present |
| CourseInfo, EstimatedSalary, LearningVideo | Jun 2025 | Retired |
| ClaimReview | Jun 2025 | Retired from rich results |
| VehicleListing | Jun 2025 | Retired from rich results |
| Practice Problem | Late 2025 | Retired |
| Dataset | Late 2025 | Retired for general use |
| Q&A | Jan 2026 | Distinct from FAQPage — deprecated |
| Sitelinks Search Box | 2025 | Deprecated |

Flag any deprecated schemas found and recommend replacements.

---

## Part 4: Schema Types — Required & Recommended Properties

### Organization (CRITICAL — every business site)

**Required:** `@type`, `name`, `url`, `logo`

**Recommended (SEO):**
- `contactPoint` (ContactPoint with telephone, contactType)
- `sameAs` (social profiles — 3+ links)
- `address` (PostalAddress)

**Recommended (GEO — entity graph signals):**
- `sameAs`: Array of ALL platform URLs (see sameAs Strategy, Part 6)
- `description`: 1-2 sentence description
- `foundingDate`: ISO 8601
- `founder`: Person schema
- `numberOfEmployees`: QuantitativeValue
- `industry`: Text or DefinedTerm
- `award`: Array of awards
- `knowsAbout`: Array of expertise topics (strong GEO signal)

**Template:**
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://example.com/logo.png",
    "width": 600,
    "height": 60
  },
  "description": "Concise description of what the company does.",
  "foundingDate": "2020-01-15",
  "founder": {
    "@type": "Person",
    "name": "Founder Name",
    "sameAs": "https://www.linkedin.com/in/founder"
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "State",
    "postalCode": "12345",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-555-5555",
    "contactType": "customer service",
    "email": "support@example.com"
  },
  "sameAs": [
    "https://en.wikipedia.org/wiki/Company_Name",
    "https://www.wikidata.org/wiki/Q12345",
    "https://www.linkedin.com/company/company-name",
    "https://www.youtube.com/@companyname",
    "https://twitter.com/companyname",
    "https://github.com/companyname",
    "https://www.crunchbase.com/organization/company-name"
  ],
  "knowsAbout": [
    "Topic 1",
    "Topic 2",
    "Topic 3"
  ]
}
```

### LocalBusiness (physical locations)

Extends Organization.

**Additional required:** `address` (PostalAddress), `telephone`, `openingHoursSpecification`

**Recommended (SEO):** `geo` (GeoCoordinates), `priceRange`

**Recommended (GEO):** `aggregateRating`, `review` (array), `hasMap` (Google Maps URL)

**Template:**
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "https://example.com/#business",
  "name": "Business Name",
  "url": "https://example.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "State",
    "postalCode": "12345",
    "addressCountry": "US"
  },
  "telephone": "+1-555-555-5555",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
      "opens": "09:00",
      "closes": "17:00"
    }
  ],
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "40.7128",
    "longitude": "-74.0060"
  },
  "priceRange": "$$"
}
```

### Article / BlogPosting / NewsArticle

**Required:** `@type`, `headline`, `datePublished`, `author`, `publisher`, `image`

**Recommended (SEO):** `dateModified`, `description`, `mainEntityOfPage`

**Recommended (GEO):** `speakable` (see Part 7), `wordCount`, `articleBody` (excerpt)

**Author (Person) — required for GEO credibility:**
- `name`, `url` (author page)
- `sameAs`: LinkedIn, Twitter, Google Scholar, ORCID, personal site
- `jobTitle`, `worksFor` (Organization), `knowsAbout` (expertise areas)
- `alumniOf`, `award`

**Template:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "@id": "https://example.com/blog/post-slug#article",
  "headline": "Article Title (max 110 chars)",
  "description": "Meta description (150-160 chars)",
  "datePublished": "2026-03-15",
  "dateModified": "2026-03-20",
  "author": {
    "@type": "Person",
    "@id": "https://example.com/author/name#person",
    "name": "Author Name",
    "jobTitle": "Role",
    "url": "https://example.com/author/name",
    "sameAs": [
      "https://linkedin.com/in/author",
      "https://twitter.com/author"
    ],
    "worksFor": { "@id": "https://example.com/#organization" },
    "knowsAbout": ["Topic 1", "Topic 2"]
  },
  "publisher": { "@id": "https://example.com/#organization" },
  "image": { "@id": "https://example.com/blog/post-slug#primaryimage" },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/blog/post-slug"
  },
  "wordCount": 2400
}
```

### Product (e-commerce)

**Required:** `name`, `description`, `image`, `offers` (Offer with price, priceCurrency, availability), `brand`, `sku` or `gtin`/`mpn`

**Recommended (GEO):** `aggregateRating`, `review` (array), `category`, `material`, `weight`

### SoftwareApplication (SaaS)

**Required:** `name`, `description`, `applicationCategory`, `operatingSystem`, `offers`

**Recommended (GEO):** `aggregateRating`, `featureList` (strong citation signal), `screenshot`, `softwareVersion`, `releaseNotes`

### WebSite + SearchAction (sitelinks search box)

```json
{
  "@type": "WebSite",
  "@id": "https://example.com/#website",
  "name": "Site Name",
  "url": "https://example.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

### BreadcrumbList (any inner page)

```json
{
  "@type": "BreadcrumbList",
  "@id": "https://example.com/blog/post-slug#breadcrumb",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://example.com/blog" },
    { "@type": "ListItem", "position": 3, "name": "Post Title", "item": "https://example.com/blog/post-slug" }
  ]
}
```

### FAQPage (AI extraction value)

```json
{
  "@type": "FAQPage",
  "@id": "https://example.com/page#faq",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the question?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Complete answer text (40-60 words with statistic)."
      }
    }
  ]
}
```

> Google restricts FAQ rich results to gov/health sites since Aug 2023. Still valuable for AI extraction — AI platforms parse FAQ schema for Q&A citation.

### Person (standalone — authors, thought leaders)

**Required:** `name`, `url`

**Recommended (GEO):** `sameAs`, `jobTitle`, `worksFor`, `knowsAbout`, `alumniOf`, `award`, `description`, `image`

### ImageObject

```json
{
  "@type": "ImageObject",
  "@id": "https://example.com/blog/post-slug#primaryimage",
  "url": "https://example.com/images/hero.jpg",
  "width": 1200,
  "height": 630,
  "caption": "Descriptive caption matching alt text"
}
```

Image requirements: publicly accessible URL, actual dimensions, caption aligned with alt text. Preferred: 1200x630 (OG-compatible) or 1920x1080.

---

## Part 5: Blog Mode (`--blog`)

When invoked with `--blog`, read a blog post and generate a complete `@graph` JSON-LD block.

### Workflow

1. **Read content** — extract: title, author (name, job title, social links), dates (published, modified), description, FAQ pairs, images (cover URL, dimensions, alt), organization info, word count, tags/categories, slug
2. **Generate 6 schema types** in `@graph`:
   - BlogPosting (headline, dates, author ref, publisher ref, image ref, wordCount)
   - Person (author with sameAs, jobTitle, worksFor)
   - Organization (publisher with logo, sameAs)
   - BreadcrumbList (Home → Category → Post)
   - FAQPage (if FAQ section exists, min 2 questions)
   - ImageObject (cover image with dimensions, caption)
3. **Validate** — @id refs resolve within graph, dateModified >= datePublished, headline <110 chars, description 50-160 chars, URLs absolute, positions sequential
4. **Output** — single `<script type="application/ld+json">` tag with `@graph` array

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "BlogPosting", "@id": "{siteUrl}/blog/{slug}#article", ... },
    { "@type": "Person", "@id": "{siteUrl}/author/{author-slug}#person", ... },
    { "@type": "Organization", "@id": "{siteUrl}#organization", ... },
    { "@type": "BreadcrumbList", "@id": "{siteUrl}/blog/{slug}#breadcrumb", ... },
    { "@type": "FAQPage", "@id": "{siteUrl}/blog/{slug}#faq", ... },
    { "@type": "ImageObject", "@id": "{siteUrl}/blog/{slug}#primaryimage", ... }
  ]
}
</script>
```

**@graph benefits:** Single script tag, entity linking via @id, Google and AI systems parse correctly, easier maintenance.

> Pages using 3+ schema types have ~13% higher AI citation likelihood. Blog mode generates 6 types by default.

---

## Part 6: sameAs Strategy (CRITICAL for GEO Entity Recognition)

The `sameAs` property is the single most important structured data property for GEO. It tells AI systems: "This entity on my website is the SAME entity as these profiles elsewhere."

### Recommended sameAs Links (priority order)

| # | Platform | Why | Example URL |
|---|----------|-----|-------------|
| 1 | Wikipedia | Highest authority entity link | `https://en.wikipedia.org/wiki/Company` |
| 2 | Wikidata | Machine-readable entity ID | `https://www.wikidata.org/wiki/Q12345` |
| 3 | LinkedIn | Company/personal profile | `https://www.linkedin.com/company/name` |
| 4 | YouTube | Channel URL | `https://www.youtube.com/@name` |
| 5 | Twitter/X | Profile URL | `https://twitter.com/name` |
| 6 | Facebook | Page URL | `https://www.facebook.com/name` |
| 7 | Crunchbase | Company profile (startups/tech) | `https://www.crunchbase.com/organization/name` |
| 8 | GitHub | Org or personal (tech) | `https://github.com/name` |
| 9 | Google Scholar | Author profile (research) | `https://scholar.google.com/citations?user=ID` |
| 10 | ORCID | Researcher ID (academics) | `https://orcid.org/0000-0000-0000-0000` |
| 11 | Instagram | Profile URL | `https://www.instagram.com/name` |
| 12 | App Store / Play Store | App listings (software) | Store URL |
| 13 | BBB | Business Bureau (US) | BBB listing URL |
| 14 | Industry directories | Vertical-specific | Directory listing URL |

### sameAs Audit Process

1. Collect all known web presences for the entity
2. Check each URL resolves (not 404 or redirected to different entity)
3. Verify Organization/Person schema includes ALL of them
4. Check consistency across platforms (name, description, founding date match)
5. Flag platforms where entity SHOULD have presence but does not

---

## Part 7: speakable Property (GEO — voice/AI assistants)

The `speakable` property marks content sections as suitable for voice and AI assistant consumption. Add to Article or WebPage schemas.

```json
{
  "@type": "Article",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".article-summary", ".key-takeaway"]
  }
}
```

This signals to AI assistants which passages are best candidates for citation or reading aloud. Target: summary paragraphs, key takeaways, definition paragraphs.

---

## Part 8: Scoring Rubric (0-100)

Used in default and `--geo` mode. In `--seo` mode, output Pass/Fail per schema type instead.

| Criterion | Points | How to Score |
|-----------|--------|-------------|
| Organization/Person schema present and complete | 15 | 15 if full, 10 if basic, 0 if none |
| sameAs links (5+ platforms) | 15 | 3 per valid sameAs link, max 15 |
| Article schema with full author details | 10 | 10 if full author schema, 5 if name only, 0 if none |
| Business-type-specific schema present | 10 | 10 if complete, 5 if partial, 0 if missing |
| WebSite + SearchAction | 5 | 5 if present, 0 if not |
| BreadcrumbList on inner pages | 5 | 5 if present, 0 if not |
| JSON-LD format (not Microdata/RDFa) | 5 | 5 if JSON-LD, 3 if mixed, 0 if only Microdata/RDFa |
| Server-rendered (not JS-injected) | 10 | 10 if in HTML source, 5 if JS but in head, 0 if dynamic JS |
| speakable property on articles | 5 | 5 if present, 0 if not |
| Valid JSON + valid Schema.org types | 10 | 10 if no errors, 5 if minor issues, 0 if major errors |
| knowsAbout on Organization/Person | 5 | 5 if 3+ topics, 0 if missing |
| No deprecated schemas present | 5 | 5 if clean, 0 if deprecated found |

### Score Interpretation

| Score | Rating | Meaning |
|-------|--------|---------|
| 85-100 | Excellent | Strong entity graph, high citation probability |
| 70-84 | Good | Solid foundation, targeted improvements possible |
| 55-69 | Moderate | Gaps reducing AI discoverability |
| 40-54 | Below Average | Significant entity recognition barriers |
| 0-39 | Needs Attention | Minimal structured data, AI systems cannot verify entity |

---

## Part 9: Generation Rules

When generating schema for a page:

1. **Identify page type** from content analysis
2. **Select appropriate schema type(s)** from active list
3. **Generate valid JSON-LD** with all required + recommended properties
4. **Use @graph pattern** for multiple schemas in one block
5. **Include @id properties** for cross-referencing between schemas
6. **Use ISO 8601** for all dates
7. **All URLs absolute** (not relative)
8. **Include speakable** on Article schemas (CSS selectors for key content)
9. **Place in `<head>`** — NOT injected via JavaScript
10. **Include only truthful data** — use clearly marked `[PLACEHOLDER]` for values user must fill
11. **Validate output** before presenting

### Always generate (for any site):

1. Organization or Person (depending on entity type)
2. WebSite with SearchAction (homepage)
3. Business-type-specific schema (Article, Product, LocalBusiness, SoftwareApplication)
4. BreadcrumbList (any page deeper than homepage)

---

## Part 10: Output Format

### Default / `--geo` Mode

Generate **STRUCTURED-DATA-REPORT.md**:

```markdown
# Structured Data Report — [Domain]
Date: [Date]
Mode: [Default / SEO / GEO]

## Schema Score: XX/100

## Detected Schemas
| Page | Schema Type | Format | Rendering | Status | Issues |
|------|------------|--------|-----------|--------|--------|
| / | Organization | JSON-LD | Server | Valid | Missing sameAs |
| /blog/post-1 | Article | JSON-LD | Server | Valid | No author schema |

## Validation Results
[Per schema: pass/fail per property]

## sameAs Audit
| Platform | URL | Status |
|----------|-----|--------|
| Wikipedia | [URL or "Not found"] | Present/Missing |
| Wikidata | [URL or "Not found"] | Present/Missing |
| LinkedIn | [URL] | Present |
[Continue for all 14 recommended platforms]

## Missing Recommended Schemas
[Schemas that should be present based on business type but are not]

## Deprecated Schemas Found
[Any deprecated types with removal recommendations]

## Generated JSON-LD Code
[Ready-to-paste JSON-LD blocks for each missing or incomplete schema]

## Implementation Notes
- Where to place each JSON-LD block
- Server-rendering requirements
- Testing: Google Rich Results Test + Schema.org Validator
```

### `--seo` Mode

Same report structure, but:
- No sameAs audit section
- No speakable assessment
- Scoring: Pass/Fail per schema type (Google requirements only)
- Output file: `SCHEMA-REPORT.md`

### `--blog` Mode

Output: ready-to-paste `<script>` tag with @graph, or standalone JSON for CMS fields.

Save to blog post file or separate schema file as user prefers.

---

## Cross-References

- For **blog post SEO validation** (title, meta, headings, links) → use `/blog-seo-check`
- For **AI citability scoring** of content passages → use `/geo-citability`
- For **AI crawler access** audit → use `/geo-crawlers`
- For **full GEO audit** orchestrating all GEO sub-skills → use `/geo`
- For **full SEO audit** orchestrating all SEO sub-skills → use `/seo`
