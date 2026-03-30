---
name: 42-page-health
description: >
  Samengestelde per-URL gezondheidscore (0-100) die meerdere SEO-risicosignalen
  combineert: thin content, orphan pages, missing on-page elementen, indexability
  problemen, en optioneel traffic decay. Bulk URL triage na Google core updates.
  Use when user says "page health", "URL risk", "HCU audit", "core update impact",
  "slechtste pagina's", "pagina gezondheid", "URL triage", "risico score".
version: 1.0.0
tags: [seo, audit, health-score, hcu, core-update, triage, risk, bulk]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/internal_all*"
    - "**/internal_html*"
    - "**/*health*"
    - "**/*risk*"
  bashPattern:
    - "page.health"
    - "hcu"
    - "core.update"
    - "url.risk"
    - "triage"
---

# Page Health — Samengestelde URL Risico Score

## Purpose

Na een Google core update is de eerste vraag: **"Welke pagina's trekken mijn site omlaag?"**

Deze skill combineert meerdere SEO-signalen per URL tot één Health Score (0-100, hoog = gezond) en sorteert alle pagina's op risico. Input is een Screaming Frog crawl export, optioneel verrijkt met GSC data voor traffic decay.

**Verschil met individuele skills:**
- `42:technical` checkt crawlability/CWV/security — site-breed, niet per-URL gescoord
- `42:content` checkt E-E-A-T/readability — per pagina maar niet als bulk triage
- `42:content-decay` detecteert traffic decline — maar combineert niet met technische signalen
- **`42:page-health` combineert alles in één score per URL voor snelle prioritering**

---

## Commands

```
/42:page-health <sf-internal.csv>                          # Basis: SF Internal export
/42:page-health <sf-internal.csv> --gsc <gsc-export.csv>   # + traffic decay signaal
/42:page-health <sf-internal.csv> --type blog               # Pagina-type specifieke thresholds
/42:page-health <sf-internal.csv> --top 50                  # Toon top 50 risico-URLs
/42:page-health <sf-internal.csv> --weights custom.json     # Custom gewichten
```

---

## Input

### Screaming Frog Internal Export (verplicht)

Genereer via: `Bulk Export > Internal > All` of `Bulk Export > Internal > HTML`

**Gebruikte kolommen:**

| SF Kolom | Wat we meten | Fallback als ontbreekt |
|----------|-------------|----------------------|
| `Address` | URL identifier | Verplicht |
| `Status Code` | HTTP status | Skip URL als ontbreekt |
| `Indexability` | Indexeerbaar? | Aanname: indexable |
| `Indexability Status` | Reden niet-indexeerbaar | Geen detail |
| `Word Count` | Thin content detectie | 0 (flagged als thin) |
| `Title 1` | Title aanwezigheid + lengte | Leeg = flag |
| `H1-1` | H1 aanwezigheid | Leeg = flag |
| `H2-1` | H2 aanwezigheid | Leeg = flag |
| `Meta Description 1` | Meta description aanwezigheid + lengte | Leeg = flag |
| `Canonical Link Element 1` | Canonical aanwezigheid | Leeg = flag |
| `Inlinks` | Orphan detectie | 0 (flagged als orphan) |
| `Outlinks` | Internal linking | 0 |
| `Content Type` | Filter op HTML | Alleen text/html verwerken |
| `Crawl Depth` | Diepte in site-structuur | Geen penalty |

**Taal-ondersteuning:** Engelse en Spaanse SF kolomnamen worden automatisch herkend (alias mapping).

### Google Search Console Export (optioneel)

GSC Performance export met Pages dimensie voor traffic decay signaal:

```csv
Page,Clicks,Impressions,CTR,Position
https://example.com/page-1,450,12000,3.75%,4.2
```

Wanneer GSC data beschikbaar is, wordt traffic decay als extra signaal meegenomen in de health score.

---

## Pre-processing

Voordat scoring begint, worden URLs gefilterd:

1. **Alleen HTML pagina's** — filter op Content Type `text/html` (skip images, CSS, JS, PDF)
2. **Alleen 200 status codes** — skip 3xx redirects, 4xx errors, 5xx server errors
3. **Skip non-indexable met intentionele reden** — pagina's met `noindex` directive worden apart gerapporteerd, niet mee-gescoord (ze zijn al uit de index, ze trekken de site niet omlaag)
4. **URL normalisatie** — lowercase, strip trailing slash, voor deduplicatie

---

## Scoring Model

### Health Score = 100 - Risk Score

De Health Score loopt van **100 (perfect) tot 0 (kritiek)**. Intern berekenen we een Risk Score (hoe meer problemen, hoe hoger) en trekken die af van 100.

### Risk Signalen (7 categorieen, max 100 punten risico)

| # | Signaal | Max Punten | Threshold | Wat het meet |
|---|---------|-----------|-----------|-------------|
| 1 | **Thin Content** | 25 | Pagina-type afhankelijk (zie tabel) | Te weinig content voor adequate topical coverage |
| 2 | **Missing/Bad Canonical** | 15 | Canonical veld leeg of wijst naar andere URL | Indexatie-verwarring, duplicate content risico |
| 3 | **Orphan Page** | 15 | Inlinks < threshold (type-afhankelijk) | Niet intern gelinkt, wordt niet gecrawld/geciteerd |
| 4 | **Poor Structure** | 15 | H1 of (H1+H2) afwezig | Geen semantische structuur voor Google en AI |
| 5 | **Missing Meta** | 10 | Title of meta description afwezig of buiten lengte | Slechte SERP presentatie, lage CTR |
| 6 | **Deep Crawl Depth** | 10 | Crawl depth > 4 | Te ver van homepage, weinig crawl budget |
| 7 | **Traffic Decay** | 10 | Clicks gedaald >50% vs piek (GSC data nodig) | Content verliest relevantie |

**Totaal maximum risico: 100 punten → Health Score = 0**

### Pagina-Type Specifieke Thresholds

| Pagina Type | Thin Threshold | Orphan Threshold | Detectie |
|-------------|---------------|-----------------|----------|
| Blog post | < 800 woorden | < 3 inlinks | URL bevat `/blog/`, `/article/`, `/post/` |
| Product pagina | < 200 woorden | < 2 inlinks | URL bevat `/product/`, `/shop/`, `/item/` |
| Categorie pagina | < 300 woorden | < 5 inlinks | URL bevat `/category/`, `/collection/`, `/tag/` |
| Service pagina | < 500 woorden | < 3 inlinks | URL bevat `/service/`, `/dienst/` |
| Locatie pagina | < 400 woorden | < 2 inlinks | URL bevat `/location/`, `/vestiging/`, `/filiaal/` |
| Homepage | < 300 woorden | N.v.t. (altijd linked) | URL is root `/` |
| **Overig** | < 300 woorden | < 3 inlinks | Default |

Override met `--type <type>` om alle pagina's als één type te behandelen.

### Gedetailleerde Scoring per Signaal

#### 1. Thin Content (0-25 punten)

```
Als word_count < threshold:
  ratio = word_count / threshold
  thin_risk = round((1 - ratio) * 25)
Anders:
  thin_risk = 0
```

Gegradueerd: een pagina met 150 woorden (threshold 300) scoort 12.5 risico, niet de volle 25. Dit is eerlijker dan een binary flag.

#### 2. Missing/Bad Canonical (0-15 punten)

| Situatie | Punten |
|----------|--------|
| Geen canonical tag | 15 |
| Canonical wijst naar andere URL (niet self-referencing) | 10 |
| Self-referencing canonical aanwezig | 0 |

#### 3. Orphan Page (0-15 punten)

```
Als inlinks == 0:
  orphan_risk = 15
Als inlinks < threshold:
  ratio = inlinks / threshold
  orphan_risk = round((1 - ratio) * 15)
Anders:
  orphan_risk = 0
```

#### 4. Poor Structure (0-15 punten)

| Situatie | Punten |
|----------|--------|
| H1 afwezig EN H2 afwezig | 15 |
| H1 afwezig (H2 wel aanwezig) | 10 |
| H1 aanwezig, H2 afwezig | 5 |
| Beide aanwezig | 0 |

#### 5. Missing Meta (0-10 punten)

| Situatie | Punten |
|----------|--------|
| Title afwezig | 5 |
| Title te kort (<30 chars) of te lang (>60 chars) | 2 |
| Meta description afwezig | 5 |
| Meta desc te kort (<70 chars) of te lang (>160 chars) | 2 |

Cumulatief: max 10 als alles ontbreekt.

#### 6. Deep Crawl Depth (0-10 punten)

| Crawl Depth | Punten |
|-------------|--------|
| 0-3 | 0 |
| 4 | 3 |
| 5 | 6 |
| 6+ | 10 |

#### 7. Traffic Decay (0-10 punten, alleen met GSC data)

```
Als GSC data beschikbaar:
  decay_pct = (peak_clicks - current_clicks) / peak_clicks
  Als decay_pct > 0.75: traffic_risk = 10
  Als decay_pct > 0.50: traffic_risk = 7
  Als decay_pct > 0.30: traffic_risk = 4
  Anders: traffic_risk = 0
Anders:
  traffic_risk = 0 (niet meegeteld)
```

---

## Custom Gewichten

Override de default punten per signaal via `--weights custom.json`:

```json
{
  "thin_content": 25,
  "missing_canonical": 15,
  "orphan_page": 15,
  "poor_structure": 15,
  "missing_meta": 10,
  "deep_crawl_depth": 10,
  "traffic_decay": 10
}
```

De tool normaliseert automatisch zodat het totaal altijd max 100 is.

---

## Output Format

### PAGE-HEALTH.md

```markdown
# Page Health Report — [Domain]
Date: [Date]
Pages Analyzed: [Count] (van [Total] gecrawld, [Filtered] gefilterd op status/type)
Data: SF Internal Export [+ GSC Performance]

## Score Distributie

| Range | Count | % | Beoordeling |
|-------|-------|---|------------|
| 90-100 | [X] | [X]% | Uitstekend |
| 70-89 | [X] | [X]% | Gezond |
| 50-69 | [X] | [X]% | Aandacht nodig |
| 30-49 | [X] | [X]% | Risico |
| 0-29 | [X] | [X]% | Kritiek |

## Site-Gemiddelden

| Signaal | Gemiddeld Risico | Pagina's Getroffen |
|---------|-----------------|-------------------|
| Thin Content | [X]/25 | [X] ([X]%) |
| Missing Canonical | [X]/15 | [X] ([X]%) |
| Orphan Page | [X]/15 | [X] ([X]%) |
| Poor Structure | [X]/15 | [X] ([X]%) |
| Missing Meta | [X]/10 | [X] ([X]%) |
| Deep Crawl Depth | [X]/10 | [X] ([X]%) |
| Traffic Decay | [X]/10 | [X] ([X]%) |

## Top [N] Risico-URL's

| # | URL | Health | Thin | Canon. | Orphan | Struct. | Meta | Depth | Decay |
|---|-----|--------|------|--------|--------|---------|------|-------|-------|
| 1 | [url] | 23/100 | 25 | 15 | 12 | 15 | 5 | 6 | — |
| 2 | [url] | 31/100 | 20 | 15 | 10 | 10 | 8 | 6 | — |

## Non-Indexable Pagina's (apart gerapporteerd)

| URL | Reden | Actie |
|-----|-------|-------|
| [url] | noindex tag | Bewust? Zo niet: verwijder noindex |
| [url] | Canonical naar andere URL | Check of canonical correct is |

## Actie Prioriteiten

### Kritiek (Health 0-29) — [X] pagina's
[Lijst met specifieke acties per URL]

### Risico (Health 30-49) — [X] pagina's
[Lijst met patronen: "23 pagina's missen H1+H2, waarvan 18 in /blog/"]

### Aandacht (Health 50-69) — [X] pagina's
[Gegroepeerde aanbevelingen]

## Patronen Gedetecteerd

- **[X] blog posts onder 800 woorden** → Content uitbreiden of consolideren
- **[X] orphan pagina's in /category/** → Internal linking verbeteren
- **[X] pagina's op depth 5+** → Navigatie herstructureren
- **[X] pagina's zonder meta description** → Bulk meta generation (→ 42:meta-optimizer)
```

---

## Workflow

### Stap 1: SF Crawl Export

```bash
# In Screaming Frog:
# Bulk Export > Internal > HTML (aanbevolen) of Internal > All
# Sla op als CSV
```

### Stap 2: Optioneel — GSC Export

```bash
# In Google Search Console:
# Performance > Pages > Export > CSV
# Filter op laatste 3 maanden voor traffic decay detectie
```

### Stap 3: Run Page Health

```bash
python3 scripts/page_health.py \
    --sf-internal internal_html.csv \
    --gsc gsc-pages.csv \
    --top 50 \
    --output PAGE-HEALTH.md \
    --csv page-health-scores.csv \
    --log-file page-health.log
```

### Stap 4: Review + Actie

1. Bekijk top 50 risico-URLs
2. Identificeer patronen (welke sectie, welk pagina-type)
3. Prioriteer: kritieke pagina's eerst
4. Gebruik andere 42: skills voor diepe analyse van specifieke problemen

---

## Integratie met 42: Suite

| Skill | Hoe page-health helpt |
|-------|----------------------|
| **42:content-decay** | Decay detectie als signaal in health score. Draai decay eerst, join met health. |
| **42:striking-distance** | Gecombineerd: pagina's op pos 4-20 met lage health score → prioriteit |
| **42:meta-optimizer** | Health flagged missing meta → meta-optimizer herschrijft ze bulk |
| **42:link-graph** | Health flagged orphans → link-graph identificeert linking targets |
| **42:passage-analyzer** | Health flagged thin content → passage-analyzer toont welke secties zwak zijn |
| **42:content** | Health flagged poor structure → content doet diepe E-E-A-T analyse |
| **42:screaming-frog** | SF levert de input CSV |
| **42:audit** | Page health als onderdeel van full audit rapportage |

---

## Cross-References

- Voor **traffic decline analyse** → `/42:content-decay`
- Voor **meta description verbetering** → `/42:meta-optimizer`
- Voor **orphan page linking** → `/42:link-graph`
- Voor **thin content verbetering** → `/42:passage-analyzer` + `/42:genai-optimizer`
- Voor **quick win identificatie** → `/42:striking-distance`
- Voor **full site audit** → `/42:audit`
