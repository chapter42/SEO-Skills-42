---
name: 42-internal-links
description: >
  Competitive internal link analysis for e-commerce category pages. Crawls competitor pages with Playwright,
  maps every internal link into named blocks (breadcrumb, facet-filters, A-Z index, FAQ, product cards, etc.),
  checks crawlability (real <a> vs JS-only), audits canonical tags and Google rankings, then generates
  prioritized improvement stories in SCQA format. Use when user says "internal link analysis",
  "interne link analyse", "link vergelijking", "categorie pagina analyse", "competitor link audit",
  "concurrent analyse links", "linkblokken vergelijken", or wants to compare how competitors structure
  internal links on category pages. Also use when analyzing hub vs lister page architectures.
---

# 42 Internal Link Analysis

Competitive analysis of internal links on e-commerce category pages. Focus is exclusively on internal links — not UX, content quality, or conversion.

## When to use

- Comparing internal link structures across competitor category pages
- Auditing a client's category page internal linking vs competitors
- Understanding hub vs lister page link architecture
- Finding internal link opportunities based on competitor patterns

## Core Principle

**Only internal links matter.** Every observation, comparison, and recommendation must be about:
- Which internal links exist (anchor text + destination URL)
- Where they sit on the page (which block/section)
- Whether they are crawlable (`<a href>` vs JavaScript-only controls)
- How many there are compared to competitors
- What's missing vs what competitors do

Never drift into UX recommendations, content quality assessments, or conversion optimization.

---

## Phase 1: Page Discovery

For each competitor and the client, identify **both** page types per category:

| Page Type | What it is | How to find |
|-----------|-----------|-------------|
| **Hub** | Editorial/navigation page without product listings | Often at clean URLs like `/laptops`, `/sf/laptops/`, `/specials/laptops` |
| **Lister** | Product listing page with filters and product cards | Often at `/laptops/filter`, `/category/laptops-433.html`, `/l/laptops/4770/` |

Steps:
1. Start with the obvious category URL (e.g., `coolblue.nl/laptops`)
2. Check if it's a hub (no products) or a lister (has products with filters)
3. Find the counterpart — hubs usually link to their lister via "Alle [category]" CTA
4. Use WebSearch `site:domain.com [category]` to find both variants
5. Record both URLs per competitor

**Important:** Some retailers combine hub + lister on one URL. Note this.

---

## Phase 2: Canonical & Ranking Check

For each discovered page, collect:

### Canonical tag
Use Playwright `browser_evaluate`:
```javascript
() => { const link = document.querySelector('link[rel="canonical"]'); return link ? link.href : 'No canonical found'; }
```

### Google ranking
Use WebSearch for key category terms (e.g., "laptops kopen", "televisies") and note which URL from each competitor appears.

Produce a summary table:

```markdown
| Zoekterm | Competitor A | Competitor B | Client |
|----------|-------------|-------------|--------|
| "[category] kopen" | URL (hub/lister) | URL | URL |
| "[category]" | URL | URL | URL |
```

---

## Phase 3: Browser Analysis with Playwright

For each page:

1. **Navigate** to the URL with `browser_navigate`
2. **Accept cookies** — try `browser_evaluate` with button detection:
   ```javascript
   () => {
     const buttons = document.querySelectorAll('button');
     for (const btn of buttons) {
       const text = btn.textContent.toLowerCase();
       if (text.includes('accepte') || text.includes('akkoord') || text.includes('alle cookies')) {
         btn.click();
         return 'Clicked: ' + btn.textContent.trim();
       }
     }
     return 'No cookie button found';
   }
   ```
3. **Take full-page screenshot** saved as `[competitor]-[category]-[hub|lister].png`
4. **Save accessibility snapshot** to `[competitor]-[category]-[hub|lister]-snapshot.md`
5. **Read the entire snapshot** — this is the raw data for link extraction

**Parallelize** using subagents: launch one agent per page (up to 6 at once for 3 competitors × 2 page types).

---

## Phase 4: Link Block Identification

Read each snapshot and categorize ALL internal links into these named blocks:

### Link Block Taxonomy

| # | Block Name | What to look for | Crawlability check |
|---|-----------|-----------------|-------------------|
| 1 | **Breadcrumb** | `navigation "Broodkruimels"` or breadcrumb list | Usually `<a>` ✅ |
| 2 | **Horizontal sub-nav** | Scrollable bar below header with subcategory/brand links | Check if `<a>` or `<button>` |
| 3 | **Hero tiles / CTA** | Large visual tiles at top linking to subcategories | Usually `<a>` ✅ |
| 4 | **Brand logos** | Brand logo images linking to brand-filtered pages | Usually `<a>` ✅ |
| 5 | **Type/use-case blocks** | Tiles like "Gaming laptops", "Laptops voor studie" | Usually `<a>` ✅ |
| 6 | **Spec/technology blocks** | Tiles like "OLED", "QLED", "Mini-LED" | Usually `<a>` ✅ |
| 7 | **Quick links** | "Navigeer snel naar" or similar compact link lists | Usually `<a>` ✅ |
| 8 | **Sidebar facet-filters** | Left sidebar with filter options | ⚠️ CHECK: `<a href>` or `<input type="checkbox">`? |
| 9 | **Category chips** | Horizontal pill buttons above product list | Check if `<a>` or `<button>` |
| 10 | **Editorial/advice articles** | Links to buying guides, comparisons, how-to's | Usually `<a>` ✅ |
| 11 | **FAQ** | Accordion questions linking to advice pages | Check if expandable content has `<a>` |
| 12 | **Inspiration carousel** | Visual tabs with lifestyle content | Check if tabs contain `<a>` |
| 13 | **Featured product** | "Product van de week" or similar single product highlight | Usually `<a>` ✅ |
| 14 | **Product carousel** | Horizontal scrollable product recommendations | Usually `<a>` ✅ |
| 15 | **Accessory links** | Cross-category links to related accessories | Usually `<a>` ✅ |
| 16 | **Store visit block** | Links to store locations, appointments | Usually `<a>` ✅ |
| 17 | **Service/USP bar** | "Gratis verzending", "Gratis ruilen" etc. | Usually `<a>` ✅ |
| 18 | **A-Z Index** | Alphabetical list of all subcategories | Usually `<a>` ✅ |
| 19 | **SEO text + inline links** | Body text with embedded internal links | Check actual `<a>` in text |
| 20 | **"See also" pills** | "Bekijk ook eens" related category suggestions | Usually `<a>` ✅ |
| 21 | **Choice helper** | Keuzehulp wizard or CTA | Check if `<a>` or iframe |
| 22 | **Promo banners** | Deal/discount banners with links | Usually `<a>` ✅ |
| 23 | **Mega-menu** | Full site navigation in dropdown | Check if preloaded in DOM |
| 24 | **Sponsored brand** | Sponsored brand carousel in product feed | Usually `<a>` ✅ |
| 25 | **Pagination** | Page 2, 3, etc. navigation | ⚠️ CHECK: `<a href>` or JS click handlers? |
| 26 | **Footer** | Full footer with multiple columns | Usually `<a>` ✅ |
| 27 | **Product cards** | Individual product links in listing | Usually `<a>` ✅, count per page |

For each block found, record:
- **Present:** ✅, ❌, or ⚠️ (present but not crawlable)
- **Count:** Number of unique internal links
- **Destinations:** Type of pages linked to (subcategory, product, advice, service)
- **Crawlable:** Real `<a href>` or JavaScript-only?

---

## Phase 5: Comparison Tables

Create **separate tables for Hub and Lister pages**. Never mix them.

### Hub comparison table format:
```markdown
## Hub [Category] — Internal links comparison

| Link Block | Competitor A | Competitor B | Client | Client missing / note |
|------------|:---:|:---:|:---:|------|
| **Breadcrumb** | ✅ 3 links | ❌ | ❌ | No breadcrumb on hub. Missing parent category link. |
| **A-Z Index** | ✅ ~70 links | ❌ | ❌ | Biggest gap: 70 subcategory links missing. |
...
| **Total estimated links** | **~130** | **~50** | **~65** | |
```

### Lister comparison table format:
Same structure but different blocks are relevant (sidebar filters, pagination, product cards).

### Per-table summary sections:
After each table, add:
- **What's missing at client** — numbered list of gaps
- **What client does better** — numbered list of strengths

---

## Phase 6: Story Generation (SCQA Format)

Generate improvement stories as individual files: `il-001.md`, `il-002.md`, etc.

Each story follows **SCQA** (Situation-Complication-Question-Answer):

```markdown
# IL-XXX: [Title focused on internal links]

**Priority:** X — [Impact] impact, [effort] effort
**Category:** Internal linking | Technical SEO
**Pages:** [Which pages this affects]

---

## Situation
[Current state — what exists, what links are present, how competitors do it]

## Complication
[Why the current state is a problem — missing links, crawlability issues, competitive gap.
Include specific numbers: "Competitor X has 70 links, we have 30."]

## Question
[The specific internal linking question to solve]

## Answer
[Concrete actions — which links to add, where to place them, what to link to.
Reference existing URLs that can be linked to.]
```

**Rules for stories:**
- Every story must be about adding, fixing, or restructuring internal links
- Include specific link counts and URLs where possible
- Reference the comparison data ("Competitor X has this, we don't")
- Prioritize by impact (how many links gained) and effort

### Management Summary

Create `management-summary.md` in SCQA format:
- **Situation:** What was analyzed
- **Complication:** Key gaps found (with numbers)
- **Question:** What to improve
- **Answer:** Prioritized story table with links to individual files

---

## Phase 7: File Organization

All outputs go into an `/analysis/` directory:

```
analysis/
├── categorie-pagina-vergelijking.md    ← Main comparison report
├── stories/
│   ├── management-summary.md           ← SCQA executive summary
│   ├── il-001.md                       ← Individual stories
│   ├── il-002.md
│   └── ...
├── [competitor]-[category]-[type].png           ← Screenshots
└── [competitor]-[category]-[type]-snapshot.md   ← Accessibility snapshots
```

---

## Workflow Summary

```
1. Discover pages (hub + lister per competitor)
2. Check canonicals + Google rankings
3. Crawl with Playwright (screenshot + snapshot) — use parallel agents
4. Extract link blocks from snapshots
5. Build comparison tables (hub SEPARATE from lister)
6. Generate SCQA stories for gaps
7. Write management summary
8. Organize in /analysis/
```

---

## Example Trigger Prompts

- "Vergelijk de interne links op de categoriepagina's van Coolblue, MediaMarkt en Bol.com voor laptops"
- "Doe een internal link analyse van onze categoriepagina vs de concurrentie"
- "Analyseer de linkblokken op de TV pagina's van onze concurrenten"
- "Welke interne links missen wij op onze categoriepagina vergeleken met de concurrent?"
- "Competitor link audit voor de laptop categorie"
