---
name: 42-keyword-discovery
description: >
  Keyword discovery en ideation vanuit seed keywords. Haalt suggestions, related
  keywords, zoekvolume en difficulty op via DataForSEO. Classificeert intent,
  berekent opportunity scores, en identificeert quick wins + GEO-kansen.
  Werkt ook zonder API in mock-modus voor LLM-gestuurde expansie.
  Use when user says "keyword discovery", "keyword ideeën", "zoekwoord suggesties",
  "keyword ideas", "find keywords", "welke zoekwoorden", "waar moet ik over schrijven",
  "keyword research", "seed keywords uitbreiden", "zoekwoord onderzoek".
version: 1.0.0
tags: [seo, keywords, discovery, ideation, dataforseo, intent, opportunity, geo]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - WebFetch
metadata:
  filePattern:
    - "**/*keyword*"
    - "**/*discovery*"
    - "**/*seed*"
  bashPattern:
    - "keyword.discover"
    - "discover.py"
    - "keyword.research"
---

# Keyword Discovery — Seed to Strategy

## Purpose

Transformeer een handvol seed keywords naar een complete, geprioriteerde keyword
lijst met zoekvolume, difficulty scores, intent classificatie en opportunity
ranking. Dit is de "ik heb nog niks, waar begin ik" skill die alle andere
keyword-skills voedt.

**Twee modi:**
1. **Live** (default) -- DataForSEO API voor echte volume/difficulty data
2. **Mock** -- LLM-gestuurde keyword expansie zonder API calls

---

## Commands

```
/42:keyword-discovery <seed>
/42:keyword-discovery <seed> --location nl --language nl
/42:keyword-discovery seeds.csv --limit 100
/42:keyword-discovery <seed> --mock
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `seed` | -- | Seed keyword string of pad naar CSV/TXT bestand |
| `--location` | `nl` | Land (nl, us, de, uk, be, fr, es, it) of DataForSEO location code |
| `--language` | `nl` | Taalcode voor zoekresultaten |
| `--limit` | `50` | Max resultaten per API call |
| `--mock` | `false` | Skip API, gebruik LLM-patronen voor keyword expansie |
| `--output` | `keyword-discovery.md` | Output bestandsnaam |
| `--csv` | `keyword-discovery.csv` | CSV export bestandsnaam |
| `--json` | `false` | Ook JSON output genereren |

---

## API Configuratie

### DataForSEO Credentials

Het script zoekt credentials in deze volgorde:

1. Environment variables: `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD`
2. Bestaande seo-agi config: `~/.config/seo-agi/.env`
3. Project config: `.seo-project/<domain>/.env`

Kosten: ~$0.002 per keyword suggestie API call. Twee calls per seed keyword
(suggestions + related), dus ~$0.004 per seed.

---

## Workflow

### Step 1: Parse Seeds

- **String input:** Gebruik als enkel seed keyword
- **CSV/TXT input:** Lees alle keywords uit bestand
  - CSV: zoekt kolom `keyword`, `query`, of `seed`
  - TXT: een keyword per regel

### Step 2: DataForSEO Calls (live modus)

Per seed keyword twee API calls:
1. **Keyword Suggestions** (`/dataforseo_labs/google/keyword_suggestions/live`)
   -- Brede ideation, ontdekt gerelateerde termen die je niet zou bedenken
2. **Related Keywords** (`/dataforseo_labs/google/related_keywords/live`)
   -- Nauwer gerelateerde varianten met overlap in SERP rankings

Elk resultaat bevat: keyword, zoekvolume, CPC, competition score, difficulty.

### Step 3: Deduplicatie + Verrijking

- Dedupliceer op genormaliseerde keyword string
- Classificeer intent per keyword (transactional/commercial/informational/navigational)
- Bereken opportunity score: `(Volume x Intent Value) / max(Difficulty, 1)`
  - Intent values: transactional=3, commercial=2, informational=1

### Step 4: Segmentatie

Het script produceert vier lijsten:

| Segment | Criteria | Gebruik |
|---------|----------|---------|
| **Quick Wins** | Volume >= 100, Difficulty <= 40 | Direct targetbaar, snel resultaat |
| **GEO Opportunities** | Informational + question format (what/how/why) | AI citatie kansen |
| **Transactional** | Koopintent signaalwoorden | Product/service pagina's |
| **Commercial** | Vergelijkings/review signaalwoorden | Vergelijkingscontent |

### Step 5: Output

Drie bestanden:
1. **keyword-discovery.md** -- Volledig rapport met tabellen en actieplan
2. **keyword-discovery.csv** -- Machine-readable export voor andere skills
3. **keyword-discovery.json** (optioneel) -- Gestructureerde data

---

## Mock Modus (zonder API)

Wanneer `--mock` is opgegeven of geen credentials beschikbaar zijn, genereer
keyword variaties via patronen:

### Expansion Patterns

Pas deze patronen toe op elk seed keyword:

| Patroon | Voorbeeld (seed: "zonnepanelen") |
|---------|----------------------------------|
| best [seed] | beste zonnepanelen |
| [seed] kopen | zonnepanelen kopen |
| [seed] vergelijken | zonnepanelen vergelijken |
| [seed] kosten | zonnepanelen kosten |
| wat is [seed] | wat is zonnepanelen |
| hoe werkt [seed] | hoe werkt zonnepanelen |
| [seed] voor [audience] | zonnepanelen voor huurders |
| [seed] vs [alternatief] | zonnepanelen vs warmtepomp |
| [seed] review | zonnepanelen review |
| [seed] [jaar] | zonnepanelen 2026 |
| voordelen [seed] | voordelen zonnepanelen |
| nadelen [seed] | nadelen zonnepanelen |

**Let op:** Mock modus heeft geen volume/difficulty data. Gebruik het alleen als
startpunt en verifieer met DataForSEO of GSC data.

---

## Output Voorbeeld

```markdown
# Keyword Discovery Report

**Seeds:** zonnepanelen
**Mode:** DataForSEO (live data)
**Total keywords found:** 127

## Quick Wins (high volume, low difficulty)

| Keyword | Volume | Difficulty | Intent | Opportunity |
|---------|--------|------------|--------|-------------|
| zonnepanelen subsidie 2026 | 2400 | 28 | informational | 85.7 |
| zonnepanelen plat dak | 1900 | 22 | informational | 86.4 |
| hoeveel zonnepanelen nodig | 1600 | 18 | informational | 88.9 |

## GEO Opportunities (question keywords for AI citations)

| Keyword | Volume | Difficulty | Opportunity |
|---------|--------|------------|-------------|
| hoeveel zonnepanelen heb ik nodig | 1600 | 18 | 88.9 |
| wat kosten zonnepanelen | 3200 | 35 | 91.4 |
| hoe werken zonnepanelen | 880 | 15 | 58.7 |
```

---

## Concrete Actieplan na Discovery

Na het draaien van deze skill, gebruik de output als input voor andere skills:

### Direct opvolging (data-driven)

| Stap | Skill | Input | Output |
|------|-------|-------|--------|
| 1 | `/42:serp-cluster keyword-discovery.csv` | CSV met alle keywords | Topic clusters op basis van SERP overlap |
| 2 | `/42:topical-map keyword-discovery.csv` | CSV met alle keywords | Pillar/cluster content architectuur |
| 3 | `/42:paa-scraper <top-keyword>` | Top keywords uit Quick Wins | PAA question trees voor FAQ content |
| 4 | `/42:audience-angles <niche>` | Niche/topic van de seeds | 50 content hoeken vanuit gebruikersperspectief |

### Met bestaande site data (vereist SF + GSC)

| Stap | Skill | Input | Output |
|------|-------|-------|--------|
| 5 | `/42:keyword-mapper <sf-emb.csv> keyword-discovery.csv` | Discovery CSV + SF embeddings | Keyword→pagina mapping + content gaps |
| 6 | `/42:striking-distance <gsc.csv>` | GSC performance export | Quick win keywords in positie 5-20 |
| 7 | `/42:cannibalization` | SF crawl data | Pagina's die voor dezelfde keywords concurreren |

### Content creatie (op basis van resultaten)

| Stap | Skill | Input | Output |
|------|-------|-------|--------|
| 8 | `/42:seo-agi <keyword>` | Top opportunity keyword | GEO-geoptimaliseerde pagina |
| 9 | `/42:meta-optimizer <urls.csv>` | Bestaande pagina URLs | Geoptimaliseerde titles en meta descriptions |
| 10 | `/42:title-optimizer <titel>` | Huidige titels | CTR-geoptimaliseerde titels |

### Monitoring (na publicatie)

| Stap | Skill | Input | Output |
|------|-------|-------|--------|
| 11 | `/42:share-of-voice` | Target keywords | Marktaandeel in zoekresultaten |
| 12 | `/42:content-decay` | GSC data over tijd | Pagina's die traffic verliezen |

---

## Integratie met seo-project Orchestrator

Deze skill wordt aanbevolen in **Phase 3 (STRATEGIZE)** van `/seo-project`:
- Na de baseline audit (Phase 1) en diagnose (Phase 2)
- Seeds komen uit de diagnose: underperforming categorieën, missed topics
- Output voedt de implementation waves in Phase 4

Kan ook standalone gebruikt worden zonder actief seo-project.

---

## Skill Afhankelijkheden

| Skill | Relatie |
|-------|---------|
| `42-serp-cluster` | Neemt CSV output als input voor SERP-based clustering |
| `42-topical-map` | Neemt CSV output als input voor topic hiërarchie |
| `42-paa-scraper` | Top keywords als seeds voor PAA tree expansie |
| `42-keyword-mapper` | CSV output als custom keywords input |
| `42-striking-distance` | Complementair: discovery vindt nieuwe keywords, striking-distance vindt bestaande kansen |
| `42-audience-angles` | Complementair: discovery vindt zoektermen, angles vindt content perspectieven |
| `seo-agi` | Top opportunity keywords als input voor pagina creatie |
| `seo-project` | Onderdeel van Phase 3 (Strategize) workflow |
