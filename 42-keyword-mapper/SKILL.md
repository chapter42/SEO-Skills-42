---
name: 42-keyword-mapper
description: >
  Map keywords naar pagina's op basis van Screaming Frog embeddings + GSC data.
  Vindt content gaps (keywords zonder pagina), cannibalisatie (meerdere pagina's op
  zelfde keyword), en quick wins (hoge impressies, lage CTR). Use when user says
  "keyword mapping", "keyword pagina match", "content gap", "zoekwoord toewijzing",
  "welke pagina rankt voor", "GSC analyse", "keyword gap analysis".
version: 1.0.0
tags: [seo, keywords, embeddings, gsc, content-gaps, cannibalization, mapping]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*embedding*"
    - "**/*gsc*"
    - "**/*keyword*"
    - "**/*search*console*"
  bashPattern:
    - "keyword.map"
    - "content.gap"
    - "gsc"
---

# Keyword→Page Mapper — Embeddings + GSC

## Purpose

Verbindt zoekwoorden met pagina's op basis van semantische similarity (embeddings uit Screaming Frog) en zoekprestaties (Google Search Console). Vindt:

1. **Mapping:** Welk keyword past het best bij welke pagina?
2. **Content gaps:** Keywords met zoekvolume maar geen goede pagina
3. **Cannibalisatie:** Meerdere pagina's die voor hetzelfde keyword concurreren
4. **Quick wins:** Hoge impressies + lage CTR = pagina rankt maar converteert niet

---

## Commands

```
/42:keyword-mapper <sf-embeddings.csv> <gsc-export.csv>
/42:keyword-mapper <sf-embeddings.csv> --keywords custom-keywords.csv
/42:keyword-mapper <sf-embeddings.csv> <gsc-export.csv> --threshold 0.75
/42:keyword-mapper <sf-embeddings.csv> <gsc-export.csv> --top 5
```

---

## Input Bestanden

### 1. Screaming Frog Embedding Export (verplicht)

Genereer in SF v22+:
1. `Config > API Access > AI` → kies provider (Gemini)
2. `Config > Content > Embeddings` → activeer
3. Crawl uitvoeren
4. `Bulk Export > Content > Embeddings` → CSV

**Verwacht formaat:**

```csv
Address,Embeddings
https://example.com/,[-0.0123,0.0456,-0.0789,...]
https://example.com/about,[-0.0234,0.0567,-0.0891,...]
```

Kolommen:
- `Address` — URL van de pagina
- `Embeddings` — Vector als JSON array (dimensie afhankelijk van model, typisch 1536 of 3072)

### 2. Google Search Console Export (aanbevolen)

Exporteer uit GSC → Performance → Pages:
1. Filter op gewenste periode (laatste 3 maanden aanbevolen)
2. Klik "Export" → CSV

**Verwacht formaat:**

```csv
Top queries,Clicks,Impressions,CTR,Position
seo audit tool,1250,45000,2.78%,4.2
technical seo checklist,890,32000,2.78%,6.1
```

Of het uitgebreide formaat met URL-kolom (Pages tab):

```csv
Top queries,Page,Clicks,Impressions,CTR,Position
seo audit tool,https://example.com/seo-audit,450,12000,3.75%,3.8
```

### 3. Custom Keyword CSV (alternatief)

Als je geen GSC hebt, lever een eigen keyword-lijst:

```csv
keyword,volume,intent
seo audit tool,12000,commercial
technical seo checklist,8500,informational
```

---

## Workflow

### Stap 1: Data Laden

```bash
python3 references/similarity/sf_parser.py \
    --embeddings sf-embeddings.csv \
    --output parsed-embeddings.npz
```

Parsed de SF embedding CSV naar een numpy matrix + URL index.

### Stap 2: Keywords Embedden

Keywords moeten met **dezelfde provider en hetzelfde model** geëmbed worden als de SF crawl gebruikte. Verschillende embedding modellen produceren incompatibele vectoren.

```bash
python3 references/similarity/keyword_embedder.py \
    --keywords gsc-export.csv \
    --provider gemini \
    --model text-embedding-3-small \
    --output keyword-embeddings.npz
```

**Provider moet matchen met SF configuratie:**

Gebruikt Gemini `text-embedding-004` — hetzelfde model als Screaming Frog. Configureer `GOOGLE_API_KEY` in `.env`.

### Stap 3: Similarity Berekenen

```bash
python3 references/similarity/similarity.py \
    --mode keyword-mapping \
    --pages parsed-embeddings.npz \
    --keywords keyword-embeddings.npz \
    --threshold 0.70 \
    --top 5 \
    --url-boost 0.05 \
    --log-file keyword-mapping.log \
    --output keyword-map.json
```

Berekent cosine similarity tussen elke keyword-vector en elke pagina-vector. Op schaal van 10k×25k is dit een matrix multiply (~3 sec met numpy).

**URL Slug Boost (`--url-boost`):** Voegt een klein secundair signaal toe wanneer keyword-woorden voorkomen in het URL-pad. Bijvoorbeeld: keyword "playground equipment" + URL `/commercial-playground-equipment/` → +0.05 boost. De embedding similarity blijft het primaire signaal; de URL boost breekt ties en verbetert precisie voor pagina's met keyword-rijke URLs maar dunne content. Zet op 0 om te disablen.

**Log File (`--log-file`):** Schrijft alle voortgang en resultaten ook naar een logbestand voor post-hoc debugging. Logs gaan altijd naar stderr; het logbestand is een kopie.

### Stap 4: GSC Data Joinen

```bash
python3 references/similarity/gsc_joiner.py \
    --map keyword-map.json \
    --gsc gsc-export.csv \
    --output KEYWORD-MAP.md
```

Voegt clicks, impressies, CTR en positie toe aan de similarity mapping.

### Of: alles in één commando

```bash
python3 references/similarity/keyword_mapper_pipeline.py \
    --embeddings sf-embeddings.csv \
    --gsc gsc-export.csv \
    --provider gemini \
    --model text-embedding-3-small \
    --threshold 0.70 \
    --top 5 \
    --output KEYWORD-MAP.md
```

---

## Thresholds (configureerbaar)

| Cosine Similarity | Classificatie | Betekenis |
|-------------------|--------------|-----------|
| ≥ 0.85 | **Sterke match** | Pagina is primair over dit keyword |
| 0.70 – 0.84 | **Matige match** | Pagina is gerelateerd, niet primair |
| 0.55 – 0.69 | **Zwakke match** | Marginaal gerelateerd |
| < 0.55 | **Geen match** | Content gap — keyword heeft geen pagina |

Defaults zijn configureerbaar via `--threshold` flag.

---

## Cannibalisatie Detectie

Twee of meer pagina's met similarity ≥ 0.70 voor hetzelfde keyword = cannibalisatie.

**Severity berekening:**

```
severity = overlap_count × avg_impressions × (1 / position_gap)
```

Waar:
- `overlap_count` = aantal pagina's dat concurreert
- `avg_impressions` = gemiddeld maandelijks zoekvolume
- `position_gap` = verschil in ranking positie (klein verschil = erger)

**Aanbevelingen per severity:**

| Severity | Actie |
|----------|-------|
| Hoog (>100) | **MERGE** — combineer content in één pagina, redirect de andere |
| Medium (30-100) | **DIFFERENTIATE** — pas titels/H1s aan om intent te scheiden |
| Laag (<30) | **CANONICAL** — stel canonical in naar de sterkste pagina |

---

## Quick Wins Detectie

Pagina's met hoog potentieel maar lage prestatie:

```
quick_win_score = impressions × (1 - CTR) × (1 / position)
```

**Criteria:**
- Impressies > 1000/maand
- CTR < 3%
- Positie 4-20 (rankt, maar niet top 3)

**Aanbeveling:** Optimaliseer title tag en meta description voor hogere CTR, of upgrade content voor hogere ranking.

---

## Output Format

### KEYWORD-MAP.md

```markdown
# Keyword→Page Mapping — [Domain]
Date: [Date]
Pages: [Count] | Keywords: [Count] | Provider: [Model]

## Summary

| Metric | Count |
|--------|-------|
| Keywords met sterke match (≥0.85) | [X] |
| Keywords met matige match (0.70-0.84) | [X] |
| Content gaps (geen match <0.55) | [X] |
| Cannibalisatie waarschuwingen | [X] |
| Quick wins gedetecteerd | [X] |

---

## Top Keyword Mappings

| Keyword | Best Match URL | Similarity | Impressies | Clicks | CTR | Positie |
|---------|---------------|-----------|-----------|--------|-----|---------|
| [kw] | [url] | 0.92 | 12,000 | 450 | 3.8% | 4.2 |

---

## Content Gaps (keywords zonder goede pagina)

| Keyword | Impressies | Best Match | Similarity | Actie |
|---------|-----------|-----------|-----------|-------|
| [kw] | 8,500 | [url] | 0.48 | Nieuwe pagina aanmaken |

---

## Cannibalisatie

| Keyword | Impressies | Pagina 1 | Score 1 | Pagina 2 | Score 2 | Severity | Actie |
|---------|-----------|----------|---------|----------|---------|----------|-------|
| [kw] | 12,000 | [url1] | 0.89 | [url2] | 0.86 | Hoog | MERGE |

---

## Quick Wins

| Keyword | URL | Impressies | CTR | Positie | Potentieel | Actie |
|---------|-----|-----------|-----|---------|-----------|-------|
| [kw] | [url] | 15,000 | 1.2% | 8.3 | Hoog | Title + meta optimaliseren |

---

## Volledige Mapping (alle keywords)

[Volledige tabel, gesorteerd op impressies aflopend]

---

## Hub Pages (pagina's → keywords) — Reverse View

Pagina's die de meeste keywords aantrekken. Nuttig voor internal linking strategie:
de hub pages zijn je sterkste thematische ankers.

| URL | Keywords | Top Keywords |
|-----|----------|-------------|
| [url] | 23 keywords | seo audit, website crawler, technical seo, ... |
| [url] | 18 keywords | content marketing, blog strategy, ... |
| [url] | 12 keywords | ... |

**Gebruik:** Pagina's met 5+ keywords zijn hub pages. Link andere pagina's in hun
topic cluster naar deze hubs. Pagina's met 1-2 keywords zijn supporting pages —
zij moeten linken NAAR de hub, niet andersom.
```

---

## Integratie met 42: Suite

| Skill | Hoe keyword-mapper helpt |
|-------|------------------------|
| **42:screaming-frog** | Levert de embedding CSV als input |
| **42:cannibalization** | Keyword-mapper vindt cannibalisatie via embeddings (semantisch); cannibalization skill doet het via tekst-matching (complementair) |
| **42:content** | Content gaps uit keyword-mapper → input voor content planning |
| **42:seo-plan** | Gaps en cannibalisatie → strategische planning input |
| **42:page-analysis** | Quick wins → diepe analyse van specifieke pagina's |
| **42:audit** | Keyword mapping als onderdeel van full audit |

---

## Cross-References

- Voor **Screaming Frog crawl + embedding generatie** → `/42:screaming-frog crawl <url>` (met embedding profiel)
- Voor **tekst-based cannibalisatie detectie** → `/42:cannibalization` (complementair)
- Voor **content gap planning** → `/42:seo-plan`
- Voor **near-duplicate detectie** → `/42:near-duplicates`
- Voor **keyword research** → `/42:seo-agi` (DataForSEO SERP data)
