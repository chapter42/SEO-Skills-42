---
name: 42-passage-analyzer
description: >
  Passage-level content analyse voor AI/RAG readiness. Segmenteert pagina-content in
  passages (heading-boundary splitting), scoort elke passage op AI-extractability,
  en identificeert welke passages optimaal zijn voor citatie en welke herwerkt moeten.
  Optioneel AI-powered gap analyse per passage. Use when user says "passage analyse",
  "passage scoring", "chunk analyse", "RAG readiness", "AI extractability", "passage
  segmentatie", "content chunking".
version: 1.0.0
tags: [seo, geo, passages, citability, rag, chunking, ai-readiness, content-analysis]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - WebFetch
metadata:
  filePattern:
    - "**/*passage*"
    - "**/*chunk*"
    - "**/*citab*"
  bashPattern:
    - "passage"
    - "chunk"
    - "rag.ready"
---

# Passage-Level Content Analyzer

## Purpose

AI-zoekmachines citeren niet hele pagina's — ze citeren **passages**. Een passage van 134-167 woorden met een duidelijke claim, data, en zelfstandige context heeft de hoogste kans op citatie door ChatGPT, Perplexity en Google AI Overviews.

Deze skill segmenteert pagina-content in passages en scoort elke passage individueel op AI-extractability. Waar `42:citability` op **pagina-niveau** scoort, werkt deze skill op **passage-niveau** — binnen een pagina.

---

## Commands

```
# Heuristic modus (geen API nodig)
/42:passage-analyzer <url>                           # Analyseer enkele pagina
/42:passage-analyzer <sf-text-export-dir>            # Bulk analyse van SF text export
/42:passage-analyzer <url> --ai                      # Met AI gap-analyse per passage

# Embedding modus (echte cosine similarity vs target queries)
/42:passage-analyzer <url> --embeddings --queries gsc.csv --provider gemini
/42:passage-analyzer <sf-text-dir> --embeddings --queries keywords.csv --provider gemini
/42:passage-analyzer <sf-text-dir> --embeddings --queries gsc.csv --provider gemini --sf-embeddings sf-emb.csv
```

### Twee scoring-modi

| Modus | Flag | Wat het meet | API nodig? |
|-------|------|-------------|-----------|
| **Heuristic** (default) | — | 6-dimensie score op basis van tekstpatronen (lengte, zelfstandigheid, data, structuur) | Nee |
| **Embeddings** | `--embeddings` | Echte cosine similarity: passage-vector × query-vector | Ja (Gemini) |

**Heuristic** is snel en gratis — goed voor structurele analyse ("is deze passage goed opgebouwd?").
**Embeddings** meet echte retrieval-kans — "voor welke queries zou een AI-zoekmachine deze passage citeren?"

In embedding-modus worden **beide scores** berekend: de heuristic score EN de retrieval score. Samen geven ze het volledige beeld: een passage kan structureel perfect zijn (hoge heuristic) maar irrelevant voor je target queries (lage retrieval), of andersom.

---

## Input

### Optie 1: URL (live fetch)
Pagina wordt opgehaald via WebFetch. Content wordt geëxtraheerd uit de HTML body (nav/header/footer/sidebar verwijderd).

### Optie 2: Screaming Frog Text Export (aanbevolen voor bulk)
- `Bulk Export > Web > All Page Text` in SF
- Produceert één .txt bestand per pagina
- Schone body text, geen HTML parsing nodig

### Optie 3: SF Internal:HTML Export + Content
- `Internal:HTML` CSV met URL, Title, H1, Meta Description
- Gecombineerd met `All Page Text` voor body content

---

## Workflow

### Stap 1: Content Extractie

**Uit HTML (live fetch):**
1. Verwijder: `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, `.sidebar`, `.ads`, `.menu`, `.cookie`
2. Behoud: `<article>`, `<main>`, `<section>`, `<p>`, `<li>`, `<blockquote>`, `<h1>`-`<h6>`, `<table>`
3. Extraheer tekst per element met HTML-tag type

**Uit SF Text Export:**
1. Lees .txt bestand per URL
2. Detecteer heading-patronen (regels in ALL CAPS of korte regels gevolgd door langere tekst)

### Stap 2: Passage Segmentatie

Splits content in passages met deze regels:

**Heading-boundary splitting:**
- Elke H1/H2/H3 start een nieuwe passage
- De tekst tussen twee headings = één passage

**Lengte-management:**
- Als een passage >250 woorden is: splits op zin-grenzen
- Als een passage <50 woorden is: merge met volgende passage (tenzij het een heading-only sectie is)
- **Target lengte:** 134-167 woorden (optimale AI-citatie lengte)

**Sliding window overlap:**
- Bij splits: neem de laatste 30 woorden van de vorige passage mee als context-overlap
- Dit voorkomt dat zinnen uit context worden gerukt

**Sectie-tracking:**
- Elke passage krijgt een sectie-label (de heading erboven)
- Passages zonder heading = "Introduction" (voor eerste heading) of "Continuation"

### Stap 3: Passage Scoring (0-100)

Elke passage wordt gescoord op 6 dimensies:

| Dimensie | Gewicht | Wat het meet | Scoring |
|----------|---------|-------------|---------|
| **Lengte proximity** | 25% | Afstand tot optimale 134-167 woorden | 25 als in range, -1 per woord afwijking, min 0 |
| **Zelfstandigheid** | 20% | Maakt de passage zin als standalone excerpt? | Begint met claim (niet "This", "It", "However" zonder context), bevat subject+verb |
| **Data dichtheid** | 20% | Bevat cijfers, percentages, statistieken, jaartallen | +5 per datapunt, max 20 |
| **Structurele kwaliteit** | 15% | Zinstructuur: 2-5 zinnen, lead-with-claim | 15 als 2-5 zinnen met sterke eerste zin, aflopend |
| **Lexicale diversiteit** | 10% | Unieke woorden / totaal woorden | ratio × 10, sweet spot 0.6-0.8 |
| **Vraag-antwoord formaat** | 10% | Beantwoordt de passage een impliciete vraag? | +10 als heading een vraag is en passage direct antwoordt |

### Score Interpretatie

| Score | Rating | Betekenis |
|-------|--------|-----------|
| 80-100 | **Excellent** | Hoge kans op AI-citatie. Niet aanpassen. |
| 60-79 | **Good** | Goede basis. Kleine optimalisaties mogelijk. |
| 40-59 | **Needs Work** | Structurele aanpassingen nodig voor citatie-kans. |
| 20-39 | **Poor** | Passage is niet zelfstandig extractbaar. Herschrijven. |
| 0-19 | **Critical** | Te kort, te lang, of onsamenhangend. Fundamenteel herstructureren. |

### Stap 4: Sectie-Analyse

Per sectie (H2-groep):
- Gemiddelde passage score
- Beste passage (meest citeerbaar)
- Slechtste passage (meest verbetering nodig)
- Passage count (te veel = sectie te lang, te weinig = te oppervlakkig)

### Stap 5: AI Gap-Analyse (optioneel, `--ai` flag)

Stuur passage-metadata (niet volledige tekst) naar OpenAI/Anthropic:

**Prompt structuur:**
```
Analyseer deze pagina-passages voor AI-citatie optimalisatie:

[Per passage: id, sectie, woord-count, score, eerste 200 karakters]

Geef per passage:
1. Welke claim of feit een AI-systeem zou extraheren
2. Wat er ontbreekt voor een complete citatie (data? context? specificiteit?)
3. Concrete herschrijf-suggestie (max 2 zinnen)

Geef ook:
- Welke passages gemerged moeten worden (te kort, zelfde onderwerp)
- Welke passages gesplit moeten worden (te lang, meerdere onderwerpen)
- Welke secties een citation capsule missen (40-60 woord definitive statement)
```

---

## Passage Semantische Gewichten

Passages erven een gewicht van hun HTML-context:

| Element | Gewicht | Reden |
|---------|---------|-------|
| `<article>`, `<main>` | 2.5 | Primaire content area |
| `<h1>` context | 3.0 | Hoofdonderwerp |
| `<h2>` context | 2.5 | Kernthema |
| `<h3>` context | 2.0 | Subthema |
| `<section>` | 2.0 | Semantische groepering |
| `<blockquote>` | 1.8 | Citaat/expertise signaal |
| `<p>` | 1.0 | Standaard |
| `<li>` | 0.8 | Lijst-item (vaak minder zelfstandig) |
| `<table>` | 1.5 | Gestructureerde data (hoog citeerbaar) |
| `<div>` | 0.6 | Generiek container |
| `<aside>` | 0.3 | Secundaire content |

Gewicht wordt meegenomen als multiplier op de kwaliteitsscore voor prioritering, niet voor de score zelf.

---

## Output Format

### PASSAGE-ANALYSIS.md

```markdown
# Passage Analysis — [URL/Domain]
Date: [Date]
Pages Analyzed: [Count]
Total Passages: [Count]

## Summary

| Metric | Waarde |
|--------|--------|
| Gemiddelde passage score | XX/100 |
| Passages ≥80 (excellent) | XX (XX%) |
| Passages 60-79 (good) | XX (XX%) |
| Passages 40-59 (needs work) | XX (XX%) |
| Passages <40 (poor/critical) | XX (XX%) |
| Gemiddelde passage lengte | XX woorden |
| Passages in optimaal bereik (134-167w) | XX (XX%) |

---

## Page: [URL]

### Passage Map

| # | Sectie | Woorden | Score | Lengte | Zelfst. | Data | Structuur | Lexicaal | Q&A | Preview |
|---|--------|---------|-------|--------|---------|------|-----------|----------|-----|---------|
| P01 | Introduction | 145 | 82 | 25 | 18 | 15 | 12 | 7 | 5 | "Screaming Frog SEO Spider is..." |
| P02 | How It Works | 178 | 71 | 20 | 16 | 10 | 13 | 8 | 4 | "The crawler starts by..." |
| P03 | How It Works | 92 | 38 | 8 | 10 | 5 | 8 | 5 | 2 | "It also checks for..." |

### Sectie Scores

| Sectie | Passages | Gem. Score | Beste | Slechtste |
|--------|----------|-----------|-------|-----------|
| Introduction | 1 | 82 | P01 (82) | P01 (82) |
| How It Works | 3 | 58 | P02 (71) | P03 (38) |

### Top Passages (meest citeerbaar)
1. **P01** (82/100) — "Screaming Frog SEO Spider is..." → Sterk: optimale lengte, data, zelfstandig
2. **P02** (71/100) — "The crawler starts by..." → Goed: iets te lang, weinig data

### Passages die Aandacht Nodig Hebben
1. **P03** (38/100) — "It also checks for..." → Probleem: te kort (92w), begint met "It also" (niet zelfstandig), geen data
   **Suggestie:** Merge met P02 of uitbreiden met specifieke voorbeelden en cijfers.

---

## AI Gap-Analyse (indien --ai)

### Merge Aanbevelingen
- P03 + P04: Zelfde onderwerp ("crawling process"), samen 188 woorden → optimaal als één passage

### Split Aanbevelingen
- P07 (312 woorden): Bevat twee onderwerpen ("indexability" en "canonicals") → splits op zin na "canonical tags"

### Ontbrekende Citation Capsules
- Sectie "Benefits": Geen enkele passage bevat een definitive 40-60 woord statement. Voeg toe na H2.
- Sectie "Pricing": Mist concrete prijsinformatie in citeerbaar formaat.

### Per-Passage Herschrijf-Suggesties
| Passage | Huidige Opening | Suggestie |
|---------|----------------|-----------|
| P03 | "It also checks for..." | "Screaming Frog validates 15 technical SEO elements including..." |
| P05 | "This is important because..." | "Sites with broken canonical tags lose an average of 23% organic traffic..." |
```

---

## Embedding Modus — Retrieval Scoring

### Wat het doet

In embedding-modus wordt elke passage als vector geëmbed (via Gemini) en vergeleken met target queries via cosine similarity. Dit geeft een **echte retrieval score**: hoe waarschijnlijk is het dat een AI-zoekmachine deze passage citeert als antwoord op een specifieke query?

### Input voor embedding-modus

| Input | Verplicht? | Bron |
|-------|-----------|------|
| Content (tekst/HTML/SF export) | Ja | Zelfde als heuristic modus |
| `--queries` CSV | Ja | GSC export (query kolom) of custom keyword CSV |
| `--model` | Optioneel | Gemini model, default `text-embedding-004` (moet matchen met SF) |
| `--model` | Optioneel | Default: `text-embedding-004` |
| `--sf-embeddings` | Optioneel | SF embedding export CSV (pagina-niveau, als fallback) |

### Workflow

```bash
# 1. Segmenteer passages (zelfde als heuristic)
# 2. Embed elke passage-tekst via API
python3 scripts/passage_analyzer.py \
    --sf-text-dir ./sf-text-export/ \
    --embeddings \
    --queries gsc-performance-export.csv \
    --provider gemini \
    --model text-embedding-004 \
    --output analysis.json
```

### Retrieval Score Interpretatie

| Score | Rating | Betekenis |
|-------|--------|-----------|
| ≥80 | **Excellent** | Passage is een sterk antwoord op minstens één target query |
| 65-79 | **Good** | Passage is relevant voor meerdere queries |
| 50-64 | **Moderate** | Passage raakt het onderwerp maar is niet het beste antwoord |
| 35-49 | **Weak** | Marginale relevantie — passage mist focus |
| <35 | **No match** | Passage matcht geen enkele target query |

### Output Voorbeeld (embedding modus)

Per passage worden beide scores gerapporteerd:

```markdown
| # | Sectie | Woorden | Heuristic | Retrieval | Best Match Query | Similarity |
|---|--------|---------|-----------|-----------|-----------------|-----------|
| P01 | Introduction | 145 | 82/100 | 87/100 | "seo audit tool" | 0.87 |
| P02 | How It Works | 178 | 71/100 | 42/100 | "website crawler" | 0.42 |
| P03 | Pricing | 92 | 38/100 | 91/100 | "screaming frog price" | 0.91 |
```

**Insight uit het voorbeeld:**
- P01: Hoog op beide → perfecte passage, niet aanpassen
- P02: Goede structuur maar lage retrieval → structureel goed geschreven maar beantwoordt geen target query. Herformuleer richting een specifiek keyword.
- P03: Lage structuur maar hoge retrieval → slordig geschreven maar AI's willen het citeren. Investeer in betere structuur.

### Kosten Schatting

| Schaal | Passages | Queries | API Calls | Kosten (Gemini) |
|--------|----------|---------|-----------|----------------|
| 1 pagina | ~10 | 50 | 60 | ~$0.001 |
| 100 pagina's | ~1,000 | 500 | 1,500 | ~$0.03 |
| 1,000 pagina's | ~10,000 | 1,000 | 11,000 | ~$0.22 |

Kosten zijn minimaal — Gemini `text-embedding-004` heeft een gratis tier en kost daarna ~$0.075 per 1M tokens.

### Vergelijking: Heuristic vs Embedding

| Aspect | Heuristic | Embedding |
|--------|-----------|-----------|
| Kosten | Gratis | Gemini free tier of ~$0.01/1000 passages |
| Snelheid | Instant | ~1 sec per batch van 2048 |
| Meet structurele kwaliteit | Ja (primair) | Nee |
| Meet query-relevantie | Nee | Ja (primair) |
| Meet zelfstandigheid | Ja | Indirect |
| Synoniemen/vertalingen | Nee | Ja |
| Aanbevolen gebruik | Structurele audit | Retrieval optimalisatie |
| **Best samen** | **Ja** | **Ja** |

---

## Integratie met 42: Suite

| Skill | Relatie |
|-------|--------|
| **42:citability** | Complementair: citability scoort pagina-niveau, passage-analyzer scoort passage-niveau |
| **42:genai-optimizer** | Passage-analyzer identificeert zwakke passages → genai-optimizer herschrijft ze |
| **42:content** | Content scoort E-E-A-T + readability → passage-analyzer gaat dieper in de passage-structuur |
| **42:near-duplicates** | Near-duplicates vergelijkt pagina's → passage-analyzer kan passage-level duplicatie vinden |
| **42:screaming-frog** | SF levert text export als input |
| **42:blog-geo** | Blog-geo doet blog-specifieke citability → passage-analyzer doet het voor elke pagina |

---

## Cross-References

- Voor **pagina-niveau citability scoring** → `/42:citability`
- Voor **passage herschrijving** → `/42:genai-optimizer`
- Voor **content quality + E-E-A-T** → `/42:content`
- Voor **Screaming Frog text export** → `/42:screaming-frog export <url> --tab "Content:All"`
- Voor **blog-specifieke citability** → `/42:blog-geo`
