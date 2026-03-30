---
name: 42-qrg
description: >
  Performs a deep, thorough Search Quality Rater Guidelines (SQRG) assessment for a given URL, enriched with live SEO keyword data and competitive benchmarking. Use this skill whenever a user asks to assess, audit, rate, or evaluate a webpage using Google's Search Quality Rater Guidelines. Trigger on phrases like "assess this URL", "SQRG audit", "quality rater assessment", "E-E-A-T audit", "page quality rating", "needs met analysis", "rate this page like Google", "quality rater report", "competitor gap analysis", or any request to evaluate a webpage's trustworthiness, expertise, authority, information satisfaction, or Needs Met score. Also trigger when a user provides a URL and asks about its SEO quality, content quality, trustworthiness, or how it compares to competitors. Produces a Markdown report with frontmatter, a convincing management summary, full SQRG ratings, competitive keyword gap analysis, and a numbered practical task list.
---

# SQRG URL Assessor

Produces a thorough SQRG assessment enriched with live DataForSEO keyword data and competitive benchmarking. Output is a `.md` file with YAML frontmatter.

---

## Assessment Workflow

Run all data-gathering steps **before** writing a single line of the report. Gather everything first, then write.

---

### Step 1 — Fetch the page

Use `web_fetch` on the URL. Capture:
- Page title, H1, meta description
- Main Content (MC): what directly fulfills the page's purpose
- Supplementary Content (SC): navigation, sidebars, related links
- Ads/Monetization: any commercial elements
- Page purpose and intended audience
- Content creator identity (individual, company, anonymous)
- Website type (corporate, e-commerce, publisher, forum, YMYL, etc.)
- Contact/About page: fetch it if linked, note completeness

Run `web_search` for `[domain.com -site:domain.com]` and `[domain.com reviews]` to surface independent reputation signals.

---

### Step 2 — DataForSEO keyword pull (top 25 organic keywords)

Use `bash_tool` to call the DataForSEO **Domain Organic Keywords** endpoint. Ask the user for their DataForSEO credentials if not already provided, or check if they are set as environment variables (`DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`).

```bash
# Pull top 25 organic keywords for the domain
curl -s --user "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" \
  https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live \
  -X POST \
  -H "Content-Type: application/json" \
  -d '[{
    "target": "DOMAIN_HERE",
    "language_code": "nl",
    "location_code": 2528,
    "limit": 25,
    "order_by": ["keyword_data.keyword_info.search_volume,desc"]
  }]'
```

Replace `2528` with the appropriate location code (2528 = Netherlands, 2276 = Germany, 2056 = Belgium, 2826 = UK, 2840 = US). If the site is international, use the dominant market's code.

From the response, extract for each keyword: `keyword`, `search_volume`, `cpc`, `competition`, `ranked_serp_element.serp_item.rank_group` (= current position), `keyword_data.keyword_info.keyword_difficulty`.

Build a mental table of the top 25: keyword | volume | position | difficulty.

**If DataForSEO credentials are unavailable:** skip Steps 2 and 3, note this clearly in the report. Do not invent keyword data.

---

### Step 3 — Identify the 5 brand-core keywords

From the 25 keywords, select the 5 that are most strategically central to the page's brand positioning — not just highest volume, but highest relevance to what the page is actually about and trying to be known for. These are the keywords that define the page's competitive identity.

For each of the 5 brand-core keywords, fetch the current SERP top 5 using DataForSEO SERP API:

```bash
curl -s --user "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" \
  https://api.dataforseo.com/v3/serp/google/organic/live/advanced \
  -X POST \
  -H "Content-Type: application/json" \
  -d '[{
    "keyword": "KEYWORD_HERE",
    "language_code": "nl",
    "location_code": 2528,
    "depth": 5
  }]'
```

For each competitor URL in the SERP results, get Domain Authority via DataForSEO Backlinks Summary:

```bash
curl -s --user "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" \
  https://api.dataforseo.com/v3/backlinks/domain_pages_summary/live \
  -X POST \
  -H "Content-Type: application/json" \
  -d '[{"target": "COMPETITOR_DOMAIN_HERE", "limit": 1}]'
```

Extract: `domain_rank`, `backlinks` count, `referring_domains` count.

Also use `web_fetch` to briefly inspect the top 1–2 competitor pages per keyword: note their content depth, structure, trust signals, and E-E-A-T indicators. This takes 2–3 minutes but produces the most valuable recommendations.

Build a comparison matrix per brand-core keyword: assessed URL position + competitors ranked 1–5 with their domain rank, backlink count, and a brief quality observation.

---

### Step 4 — YMYL classification

| Category | Examples |
|---|---|
| **Clear YMYL** | Medical, financial advice, legal info, elections, safety instructions |
| **Possibly YMYL** | Fitness, significant product purchases, nutrition |
| **Not YMYL** | Entertainment, hobbies, B2B specialist topics, lifestyle |

Note the classification and its implications for the scrutiny level applied throughout.

---

### Step 5 — Main Content quality

Rate MC on four axes (score 1–10 each):

- **Effort** — Did a human actively work to create this? Is there curation, editing, depth?
- **Originality** — Unique content, or paraphrased/copied/auto-generated?
- **Talent/Skill** — Does the creator demonstrate skill appropriate to the topic?
- **Accuracy** — Consistent with well-established expert consensus? (Critical for YMYL.)

Watch for: filler before the main answer, clickbait titles, AI content without human editing, copied/scraped material, shallow paraphrasing.

---

### Step 6 — Full E-E-A-T assessment

Rate each dimension: **Lowest / Low / Medium / High / Highest**

**TRUST (most important)** — Accurate, honest, safe, reliable? Deceptive design? Obstructed MC? Signs of scam or phishing?

**EXPERIENCE** — First-hand, lived experience with the topic? Product reviews from actual users? On-the-ground knowledge?

**EXPERTISE** — Formal credentials (YMYL) or demonstrable technical skill visible in the content? Peer validation, citations?

**AUTHORITATIVENESS** — Official source? Cited by experts? Awards, notable press mentions? Go-to source in the niche?

---

### Step 7 — Reputation research

Search independently for: news articles, Wikipedia, industry awards, customer reviews, expert citations, fraud reports, controversy. Note the quality of About/Contact information.

Rate: **Very Negative / Negative / Neutral / Positive / Very Positive**

---

### Step 8 — Information Satisfaction (1–10)

Does the MC fully answer what a user would want to know? Is the best content prominently placed? Is there filler or padding? Is the content fresh? Is media used effectively?

---

### Step 9 — Needs Met Rating

| Rating | Description |
|---|---|
| **Fully Meets (FullyM)** | Exact target page for a specific, unambiguous query. Very rare. |
| **Highly Meets (HM)** | Very helpful for any reasonable intent. Accurate, trustworthy, satisfying. |
| **Moderately Meets (MM)** | Helpful but limited: slightly outdated, less comprehensive, or a minor intent only. |
| **Slightly Meets (SM)** | Less helpful, off-topic, outdated, or only tangentially related. |
| **Fails to Meet (FailsM)** | Unhelpful or harmful for all or almost all users. |

---

### Step 10 — Overall Page Quality Rating

**Lowest → Lowest+ → Low → Low+ → Medium → Medium+ → High → High+ → Highest**

- **Lowest**: Harmful, deceptive, spammy, harmfully misleading, hacked/scraped, lowest E-E-A-T
- **Low**: Lacking E-E-A-T, low quality MC, distracting Ads/SC, mildly negative reputation
- **Medium**: Adequate MC, adequate E-E-A-T, achieves its purpose
- **High**: At least one of: high quality MC, positive reputation, high E-E-A-T
- **Highest**: Outstanding MC and/or very positive reputation and/or very high E-E-A-T

---

## Report Format

Output as a **Markdown file** (`.md`) saved to `/mnt/user-data/outputs/`. Use `present_files` to share it.

File naming: `[domain]-sqrg-[YYYY-MM-DD].md`

---

### YAML Frontmatter

```yaml
---
title: "SQRG Assessment – [Domain]"
url: "[full URL assessed]"
author: "Chapter42 / Roy Huiskes"
date: "[DD MMMM YYYY]"
page_quality_rating: "[e.g. High]"
needs_met_rating: "[e.g. HM]"
eeat_overall: "[e.g. High]"
ymyl: "[Yes / No / Possibly]"
keywords_analysed: [number or 0 if no DataForSEO]
competitors_benchmarked: [number]
dataforseo: "[yes / no]"
---
```

---

### Report Structure (in order)

---

#### 0. Management Summary

This section comes first. Written for a decision-maker who has 90 seconds. Three parts:

**Wat gaat goed** — 2–3 sentences on genuine strengths. Specific, not vague. Name what actually works.

**Wat moet beter** — 2–3 sentences on the most important problems. Honest and direct. Name the gaps that matter most.

**Oordeel** — One sentence stating the PQ rating with justification.

Then immediately the **Takenlijst** — every concrete action item from the full report in priority order. This is what a client actually needs. Format exactly as:

```
### Takenlijst

**🔴 Kritiek — direct aanpakken**
1. [Specific action — what exactly, where on the page, why it matters]
2. …

**🟠 Hoog — binnen 4 weken**
3. …

**🟡 Middel — komend kwartaal**
6. …

**🟢 Laag — nice to have**
9. …
```

Tasks must be specific and actionable.  
Bad: "Improve content quality."  
Good: "Voeg een introductieblok van 150–200 woorden toe boven het productgrid op de homepage. Beschrijf hierin: doelgroep (professionele hulpdiensten), kernpropositie (realistisch trainen), en de top-3 USPs. Dit is het eerste dat Google en een bezoeker lezen."

Include tasks from the competitive analysis here — these are often the highest-ROI items.

---

#### 1. Page Overview

```
URL:              
Paginatitel:      
Paginatype:       
Doel:             [1 sentence]
Content creator:  
YMYL-status:      [classification + 1-sentence rationale]
Talen:            
```

---

#### 2. Keyword Profiel

*(Omit this section entirely if DataForSEO was unavailable.)*

**Top 25 organische keywords**

| # | Keyword | Volume/mnd | Positie | Moeilijkheid |
|---|---|---|---|---|

**Top 5 brand-core keywords**

2–3 sentences explaining why these 5 were chosen as the page's competitive identity.

---

#### 3. Competitieve Benchmark

*(Omit this section entirely if DataForSEO was unavailable.)*

For each brand-core keyword, a table:

**Keyword: [keyword] — volume [X]/mnd**

| Positie | Domein | Domain Rank | Verw. domeinen | Kwaliteitsignalen |
|---|---|---|---|---|
| [assessed position] | [assessed domain] | … | … | … |
| 1 | [competitor] | … | … | … |
| 2 | … | … | … | … |

After all 5 keyword tables, write 3–5 sentences of competitive analysis: where are the authority gaps? What content or trust patterns do top competitors use that the assessed URL does not? What is realistically achievable within 6 months?

**Gap-aanbevelingen**

3–5 specific actions derived directly from the competitive analysis. For each: *Wat* the competitor does better → *Wat* is missing on the assessed URL → *Concrete stap* to close the gap. These actions should also appear in the Takenlijst (Section 0).

---

#### 4. Main Content Beoordeling

Introductory paragraph, then:

| Dimensie | Score | Bevindingen |
|---|---|---|
| Inspanning (Effort) | X/10 | … |
| Originaliteit | X/10 | … |
| Vakmanschap / Skill | X/10 | … |
| Nauwkeurigheid | X/10 | … |

---

#### 5. E-E-A-T Beoordeling

Introductory paragraph, then:

| Dimensie | Beoordeling | Bewijs | Hiaten |
|---|---|---|---|
| 🔒 Trust | Lowest–Highest | … | … |
| 🧑 Experience | … | … | … |
| 🎓 Expertise | … | … | … |
| 🏆 Authoritativeness | … | … | … |
| **Overall E-E-A-T** | … | … | … |

---

#### 6. Reputatie

| Signal | Bevinding |
|---|---|
| Over / Contactpagina | … |
| Onafhankelijke reviews | … |
| Pers / Awards | … |
| Expertherkenning | … |
| Rode vlaggen | … |
| **Samenvatting** | Very Negative / … / Very Positive |

---

#### 7. Informatiesatisfactie

**Score: X/10**

Prose paragraph covering: content depth, structure, freshness, filler, comprehensiveness, media use, answer prominence.

---

#### 8. Needs Met Rating

**Rating: [FullyM / HM / MM / SM / FailsM]**

2–3 sentences justifying the rating for a typical query leading to this page.

---

#### 9. Overall Page Quality Rating

**Rating: [e.g. High+]**

A paragraph covering how all evidence leads to this rating. State specifically what is preventing a higher rating.

---

#### 10. Verbeterprioritering (volledig)

The full improvement reference table — separate from the Takenlijst (which is the quick action list). This section provides full reasoning for each item.

| Prioriteit | Gebied | Probleem | Concrete aanbeveling |
|---|---|---|---|
| 🔴 Kritiek | … | … | … |
| 🟠 Hoog | … | … | … |
| 🟡 Middel | … | … | … |
| 🟢 Laag | … | … | … |

8–12 rows. Include the SEO/competitive gap actions from Section 3 here as well, so this is the single complete reference.

For every recommendation: name the specific location on the page, the specific change to make, and a concrete example or target (word count, number of reviews, etc.).

---

## Formatting Rules

- Output is `.md` — clean Markdown, no HTML tags
- Sentences start with a capital letter
- Dutch number formatting: 1.000 / 1.000,00
- Scores are plain integers
- Ratings (E-E-A-T, PQ, NM) are **bold**
- Tables for all structured data; prose paragraphs for narrative sections
- No bullet lists in narrative prose — use natural language
- The Takenlijst in Section 0 is the exception: numbered list is required

---

## Important Notes

- **Trust overrides all other E-E-A-T dimensions**
- **YMYL = higher bar** — extra skepticism on health, financial, safety, civic
- **Needs Met ≠ Page Quality** — a great page can still Fail to Meet
- **No reputation data = neutral** — not negative
- **DataForSEO is optional** — if unavailable, skip Sections 2 and 3 entirely, note it in frontmatter, and note it briefly in the Management Summary. Never invent keyword data.
- **Competitive analysis drives the highest-ROI recommendations** — invest time here

---

## Reference: E-E-A-T Quick Guide

| Rating | Trust | Experience | Expertise | Authoritativeness |
|---|---|---|---|---|
| **Lowest** | Active deception, harmful, scam | None / fabricated | None / harmful misinfo | Very negative reputation |
| **Low** | Multiple inaccuracies, vague sourcing | Claimed but unverifiable | Superficial / off-topic | Unknown or mildly negative |
| **Medium** | Generally reliable, minor issues | Some personal context | Adequate for topic | Recognised but not prominent |
| **High** | Reliable, verifiable, honest | Clear first-hand experience | Demonstrable expertise | Go-to source in niche |
| **Highest** | Exceptional trustworthiness | Extensive lived experience | Leading expert / official source | Uniquely authoritative |

---

## Reference: Page Quality by Level

| Level | MC Quality | Reputation | E-E-A-T |
|---|---|---|---|
| **Highest** | Outstanding, very high effort/originality | Very positive | Very high — at least one dimension exceptional |
| **High** | High effort, original, accurate | Positive | High — at least one clearly high |
| **Medium** | Adequate, achieves purpose | Neutral | Adequate |
| **Low** | Low effort or mild inaccuracies | Mildly negative | Inadequate — any one Low criterion is enough |
| **Lowest** | Harmful, deceptive, spammy, gibberish | Extremely negative | Lowest — any one Lowest criterion is enough |
