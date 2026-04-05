---
name: 42-keyword-assign
description: >
  MECE keyword→URL toewijzing met intent classificatie en conflict review.
  Mini-orchestrator: kan zelf upstream skills aanroepen (keyword-discovery,
  keyword-mapper, serp-cluster) of werken met bestaande data.
  Produceert keyword-assignments.json met {url: [keywords]} formaat.
  Use when user says "keyword toewijzen", "keyword assignment", "welke keywords
  op welke pagina", "MECE mapping", "cornerstone keywords", "keyword→URL",
  "zoekwoord verdeling", "keyword assignment json".
version: 1.0.0
tags: [seo, keywords, assignment, mece, mapping, intent, cornerstone, orchestrator]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*assignment*"
    - "**/*assign*"
    - "**/*keyword-map*"
    - "**/*keyword*assign*"
  bashPattern:
    - "keyword.assign"
    - "assign.py"
    - "mece"
---

# Keyword Assignment — MECE URL→Keywords Mapping

## Purpose

Wijs elk keyword toe aan exact 1 URL (MECE-principe). Combineert output van keyword-discovery, keyword-mapper en serp-cluster tot een definitieve toewijzing. Produceert `keyword-assignments.json` — het formaat dat interne link planning en cornerstone strategie nodig heeft.

**Dit is de ontbrekende schakel tussen keyword research en implementatie.**

```
keyword-discovery → serp-cluster → keyword-mapper → [DEZE SKILL] → interne links
   (intent)          (clusters)     (similarity)    (MECE assign)    (cornerstone)
```

---

## Commands

```
/42-keyword-assign <sf-embeddings.csv> <gsc-export.csv>
/42-keyword-assign --auto                               # gebruikt bestaande output bestanden
/42-keyword-assign <sf-embeddings.csv> <gsc-export.csv> --seeds "seo audit, keyword research"
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sf-embeddings.csv` | -- | Screaming Frog embedding export (verplicht) |
| `gsc-export.csv` | -- | GSC Performance export met queries (verplicht) |
| `--seeds` | -- | Seed keywords voor discovery (als nog niet gedaan) |
| `--clusters` | `serp-clusters.json` | Eerder gegenereerde SERP clusters |
| `--discovery` | `keyword-discovery.csv` | Eerder gegenereerde keyword discovery |
| `--mapper` | `keyword-map.json` | Eerder gegenereerde keyword mapping |
| `--threshold` | `0.70` | Minimum similarity voor toewijzing |
| `--auto` | `false` | Gebruik automatisch alle bestaande output bestanden |
| `--output` | `keyword-assignments.json` | JSON output bestand |
| `--max-per-page` | geen limiet | Maximaal keywords per pagina |

---

## Workflow

### Stap 1: CHECK — Inventariseer beschikbare data

Zoek in de huidige directory naar bestaande output van eerdere skills:

| Bestand | Skill | Wat het bevat |
|---------|-------|---------------|
| `keyword-discovery.csv` | 42-keyword-discovery | Keywords + intent + volume |
| `keyword-discovery.json` | 42-keyword-discovery | Idem, gestructureerd |
| `serp-clusters.json` | 42-serp-cluster | Keyword clusters + hub URLs |
| `KEYWORD-MAP.md` | 42-keyword-mapper | Similarity mappings |
| `keyword-map.json` | 42-keyword-mapper | Idem, gestructureerd |

Meld aan de gebruiker wat gevonden is en wat ontbreekt.

### Stap 2: ORCHESTRATE — Run ontbrekende stappen (indien nodig)

Als essentiële data ontbreekt, roep de juiste skills aan:

```
SF embeddings + GSC export beschikbaar, maar geen keyword-mapper output?
  → Run /42-keyword-mapper <sf-embeddings.csv> <gsc-export.csv>

Seeds opgegeven maar geen keyword-discovery output?
  → Run /42-keyword-discovery <seeds>

Geen serp-clusters? → OPTIONEEL, ga door zonder (DataForSEO kost geld)
```

**Minimale input:** SF embeddings CSV + GSC export CSV. Alles andere kan de skill zelf genereren of overslaan.

### Stap 3: MERGE — Bouw keyword registry

Combineer alle bronnen tot een unified registry:

```python
{
    "seo audit tool": {
        "intent": "commercial",           # uit keyword-discovery
        "volume": 12000,                  # uit keyword-discovery of GSC impressions
        "difficulty": 45,                 # uit keyword-discovery
        "candidate_urls": [
            {
                "url": "https://example.com/seo-audit",
                "similarity": 0.92,       # uit keyword-mapper
                "position": 4.2,          # uit GSC
                "clicks": 450,            # uit GSC
                "impressions": 12000,     # uit GSC
                "is_hub": false           # uit serp-cluster
            },
            {
                "url": "https://example.com/seo-tools",
                "similarity": 0.78,
                "position": 12.1,
                "clicks": 85,
                "impressions": 3200,
                "is_hub": true
            }
        ]
    }
}
```

**Intent classificatie:**
- Als keyword-discovery beschikbaar → gebruik die intent
- Als alleen GSC data → classificeer op basis van keyword patronen:
  - `kopen`, `prijs`, `bestellen`, `goedkoop` → transactional
  - `beste`, `top`, `vergelijk`, `review` → commercial
  - `wat is`, `hoe`, `waarom`, `gids`, `tutorial` → informational
  - Merknaam, bedrijfsnaam, URL → navigational

### Stap 4: ASSIGN — Greedy MECE toewijzing

Algoritme:

```
1. Sorteer alle (keyword, url) paren op similarity DESCENDING
2. Voor elk paar (hoogste similarity first):
   a. Als keyword nog niet toegewezen EN url nog beschikbaar:
      → Wijs toe (direct match)
   b. Als keyword al toegewezen:
      → Skip (MECE: al bezet)
   c. Als keyword niet toegewezen maar meerdere kandidaten:
      → CONFLICT — markeer voor review
3. Na greedy pass: keywords zonder match (similarity < threshold) → orphan
```

**Tiebreak regels bij conflicten (meerdere kandidaten ≥ threshold):**

| Prioriteit | Regel | Rationale |
|------------|-------|-----------|
| 1 | Hoogste similarity wint | Semantisch beste match |
| 2 | Hub URL uit serp-cluster wint (bij gelijke similarity ±0.03) | Al bewezen als authority |
| 3 | Beste GSC positie wint (bij gelijke similarity ±0.03) | Al bewezen in rankings |
| 4 | Meeste impressions wint | Hoogste zoekvolume signaal |

### Stap 5: REVIEW — Presenteer conflicten

Toon conflicten in een review tabel:

```markdown
## Conflicten ({N} gevonden)

Onderstaande keywords hebben meerdere goede kandidaat-pagina's.
De aanbeveling is automatisch bepaald. Geef overrides of accepteer defaults.

| # | Keyword | Intent | Volume | Kandidaat A | Sim A | Pos A | Kandidaat B | Sim B | Pos B | Aanbeveling |
|---|---------|--------|--------|-------------|-------|-------|-------------|-------|-------|-------------|
| 1 | "seo audit" | commercial | 12K | /seo-audit | 0.91 | 3.2 | /seo-tools | 0.87 | 8.1 | → /seo-audit |
| 2 | "keyword tool" | commercial | 5K | /tools | 0.82 | 5.0 | /keyword-research | 0.80 | 4.1 | → /keyword-research |
| 3 | "backlink checker" | commercial | 8K | /seo-tools | 0.85 | 6.2 | /backlinks | 0.84 | 7.0 | → /seo-tools |

**Overrides:** Typ het conflict-nummer en de gewenste URL, bijv. "2 → /tools".
Of typ "ok" om alle aanbevelingen te accepteren.
```

Wacht op gebruiker input. Pas toewijzingen aan op basis van overrides.

### Stap 6: VALIDATE — MECE check

```
✓ 115 keywords toegewezen aan 34 URLs
✓ 0 keywords met dubbele toewijzing (MECE ok)
✓ 12 orphan keywords (content gaps)
✓ 3 conflicten gereviewed en opgelost
```

### Stap 7: OUTPUT — Genereer bestanden

Schrijf twee bestanden:

1. **`keyword-assignments.json`** — Machine-readable (voor Python scripts)
2. **`KEYWORD-ASSIGNMENTS.md`** — Leesbaar rapport

---

## Output Formaat

### keyword-assignments.json

```json
{
  "domain": "example.com",
  "generated": "2026-04-05",
  "mece_validated": true,
  "conflicts_reviewed": 3,
  "config": {
    "threshold": 0.70,
    "sources": ["keyword-mapper", "gsc", "keyword-discovery"]
  },
  "mapping": {
    "https://example.com/seo-audit": {
      "primary_keyword": "seo audit tool",
      "intent": "commercial",
      "keyword_count": 5,
      "total_volume": 32500,
      "keywords": [
        {
          "keyword": "seo audit tool",
          "intent": "commercial",
          "volume": 12000,
          "difficulty": 45,
          "similarity": 0.92,
          "position": 4.2,
          "impressions": 12000,
          "clicks": 450,
          "assignment_reason": "highest_similarity"
        },
        {
          "keyword": "website seo checker",
          "intent": "commercial",
          "volume": 8500,
          "difficulty": 42,
          "similarity": 0.88,
          "position": 6.5,
          "impressions": 8200,
          "clicks": 320,
          "assignment_reason": "highest_similarity"
        }
      ]
    }
  },
  "orphans": [
    {
      "keyword": "seo tools voor webshops",
      "intent": "commercial",
      "volume": 2100,
      "best_candidate": "https://example.com/seo-tools",
      "best_similarity": 0.48,
      "reason": "below_threshold"
    }
  ],
  "conflicts_log": [
    {
      "keyword": "seo audit",
      "candidates": [
        {"url": "/seo-audit", "similarity": 0.91, "position": 3.2},
        {"url": "/seo-tools", "similarity": 0.87, "position": 8.1}
      ],
      "assigned_to": "/seo-audit",
      "reason": "highest_similarity",
      "user_override": false
    }
  ],
  "stats": {
    "total_keywords": 127,
    "assigned": 115,
    "orphans": 12,
    "urls_with_keywords": 34,
    "avg_keywords_per_url": 3.4,
    "conflicts_found": 3,
    "conflicts_overridden": 0,
    "intents": {
      "commercial": 45,
      "informational": 52,
      "transactional": 15,
      "navigational": 3
    }
  }
}
```

### KEYWORD-ASSIGNMENTS.md

```markdown
# Keyword Assignments — [Domain]

Gegenereerd: [Date] | Keywords: [N] | URLs: [N] | MECE: Gevalideerd

## Samenvatting

| Metric | Waarde |
|--------|--------|
| Totaal keywords | 127 |
| Toegewezen | 115 (91%) |
| Orphans (content gaps) | 12 (9%) |
| URLs met keywords | 34 |
| Conflicten gereviewed | 3 |
| Gemiddeld per URL | 3.4 keywords |

### Intent verdeling

| Intent | Count | % |
|--------|-------|---|
| Commercial | 45 | 39% |
| Informational | 52 | 45% |
| Transactional | 15 | 13% |
| Navigational | 3 | 3% |

---

## Cornerstone Pages (meeste keywords)

De top-10 pagina's met de meeste keywords. Dit zijn je cornerstone/hub pages
voor interne link strategie.

| # | URL | Keywords | Totaal volume | Dominant intent | Primary keyword |
|---|-----|----------|---------------|-----------------|-----------------|
| 1 | /seo-audit | 8 | 52,300 | commercial | seo audit tool |
| 2 | /keyword-research | 6 | 38,100 | informational | keyword research |
| ... |

---

## Alle Toewijzingen (per URL)

### /seo-audit (8 keywords, commercial)

**Primary:** seo audit tool (vol: 12K, sim: 0.92, pos: 4.2)

| Keyword | Intent | Volume | Similarity | Positie |
|---------|--------|--------|-----------|---------|
| seo audit tool | commercial | 12,000 | 0.92 | 4.2 |
| website seo checker | commercial | 8,500 | 0.88 | 6.5 |
| ...

[herhaal voor elke URL]

---

## Orphans — Content Gaps

Keywords zonder goede pagina. Overweeg nieuwe content te maken.

| Keyword | Intent | Volume | Beste kandidaat | Similarity | Actie |
|---------|--------|--------|----------------|-----------|-------|
| seo tools voor webshops | commercial | 2,100 | /seo-tools | 0.48 | Nieuwe pagina |

---

## Conflict Log

| # | Keyword | Gekozen URL | Afgewezen URL | Reden | Override? |
|---|---------|-------------|---------------|-------|----------|
| 1 | seo audit | /seo-audit (0.91) | /seo-tools (0.87) | Hoogste similarity | Nee |
```

---

## Python Script

Het assignment script kan ook standalone gedraaid worden:

```bash
python3 scripts/assign.py \
    --sf sf-embeddings.csv \
    --gsc gsc-export.csv \
    [--discovery keyword-discovery.csv] \
    [--clusters serp-clusters.json] \
    [--mapper keyword-map.json] \
    [--threshold 0.70] \
    [--output keyword-assignments.json]
```

Het script:
1. Parsed alle input bronnen (CSV/JSON)
2. Bouwt keyword registry met candidate URLs
3. Runt greedy MECE assignment
4. Schrijft JSON output
5. Print conflicten naar stdout voor review

---

## Integratie met 42: Suite

### Als onderdeel van seo-project orchestrator

Past in **Phase 5: STRATEGIZE** — na discovery, mapping en diagnostiek:

```
Phase 3: DISCOVER
  → /42-keyword-discovery <seeds>
  → /42-serp-cluster <keywords.csv>

Phase 4: DIAGNOSE
  → /42-keyword-mapper <sf-embeddings> <gsc.csv>
  → /42-cannibalization

Phase 5: STRATEGIZE
  → /42-keyword-assign <sf-embeddings> <gsc.csv>  ← DEZE SKILL
  → Output: keyword-assignments.json
  → Feeds into: internal link planning, content briefs
```

### Downstream consumers

| Skill / Tool | Hoe het assignments.json gebruikt |
|---|---|
| Intern link script | URL→keywords bepaalt anchor text en link targets |
| /42-seo-plan | Prioriteer URLs op basis van keyword volume |
| /42-content | Content briefs met toegewezen keywords |
| /42-striking-distance | Focus op URLs met hoog-volume assigned keywords |

---

## Cross-References

- Voor **keyword research** → `/42-keyword-discovery`
- Voor **embedding-based mapping** → `/42-keyword-mapper`
- Voor **SERP clustering** → `/42-serp-cluster`
- Voor **cannibalisatie detectie** → `/42-cannibalization`
- Voor **interne link strategie** → gebruik `keyword-assignments.json` als input
