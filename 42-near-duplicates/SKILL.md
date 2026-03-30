---
name: 42-near-duplicates
description: >
  Detecteer near-duplicate en semantisch vergelijkbare pagina's met drie lagen:
  SF MinHash (tekst-overlap), SF Semantic Similarity (embedding cosine), en gewogen
  component-analyse (title/H1/meta/body apart). Use when user says "near duplicates",
  "duplicate content", "thin content", "vergelijkbare pagina's", "content overlap",
  "pagina similarity", "duplicate detectie", "cannibalisatie".
version: 1.0.0
tags: [seo, duplicates, similarity, embeddings, minhash, content-quality]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*duplicate*"
    - "**/*similar*"
    - "**/*near_dup*"
  bashPattern:
    - "duplicate"
    - "near.dup"
    - "similarity"
---

# Near-Duplicate & Similarity Detection

## Purpose

Detecteert pagina's die te veel op elkaar lijken — van exacte kopieën tot semantisch vergelijkbare content. Combineert drie complementaire methoden uit Screaming Frog met eigen analyse:

| Laag | Methode | Bron | Wat het vindt |
|------|---------|------|--------------|
| 1 | **Exact Duplicates** (MD5) | SF export | Letterlijk identieke pagina's |
| 2 | **Near Duplicates** (MinHash) | SF export | Tekst-overlap >90% (woordvolgorde) |
| 3 | **Semantic Similarity** (Embeddings) | SF export | Zelfde onderwerp, andere woording |
| 4 | **Component Analysis** (gewogen) | Eigen berekening | Title+H1 gelijk maar body verschilt (of omgekeerd) |

Laag 4 is de toegevoegde waarde boven SF: het scoort componenten **apart**, zodat je ziet dat twee pagina's dezelfde title/H1 hebben maar totaal andere body text (of andersom).

---

## Commands

```
/42:near-duplicates <sf-export-dir>                      # Analyseer SF exports
/42:near-duplicates <sf-export-dir> --threshold 0.85     # Custom similarity threshold
/42:near-duplicates <sf-export-dir> --component-weights   # Toon component breakdown
/42:near-duplicates --embeddings-only <sf-embeddings.csv> # Alleen embedding-based analyse
```

---

## Input Bestanden

Alle input komt uit Screaming Frog exports. Geen HTML parsing nodig.

### Vereiste SF Exports

Genereer deze exports na een SF crawl:

| Export | Hoe te genereren | Wat het bevat |
|--------|-----------------|--------------|
| **Internal:HTML** | `Bulk Export > Internal > HTML` | URL, title, H1, meta description, word count |
| **Near Duplicates** | `Bulk Export > Content > Near Duplicates` | URL, closest match, similarity %, hash |
| **Exact Duplicates** | `Bulk Export > Content > Exact Duplicates` | URL, hash (identieke hashes = exacte dupes) |

### Optionele SF Exports (v22+)

| Export | Hoe te genereren | Wat het bevat |
|--------|-----------------|--------------|
| **Semantically Similar** | `Bulk Export > Content > Semantically Similar` | URL, closest semantic match, score 0-1 |
| **Embeddings** | `Bulk Export > Content > Embeddings` | URL, embedding vector (voor eigen analyse) |
| **All Page Text** | `Bulk Export > Web > All Page Text` | Volledige body text per pagina |

---

## Hoe SF Near-Duplicates Berekent

Screaming Frog gebruikt **MinHash** (Minimum Hashing):

1. **Tekst extractie:** Haalt body text uit de pagina (exclusief nav, footer, boilerplate). Configureerbaar via `Config > Content > Area`.
2. **Shingling:** Breekt tekst op in overlappende n-grams (woordgroepen).
3. **Hashing:** Genereert een compact fingerprint (MinHash signature) van elke pagina.
4. **Vergelijking:** Berekent Jaccard similarity tussen fingerprints. Dit is een schatting van de overlap in woordgroepen.
5. **Threshold:** Default 90%. Pagina's met ≥90% similarity worden gemarkeerd.

**Sterkte:** Snel, schaalt goed naar 100k+ pagina's, vindt letterlijke tekst-overlap.
**Zwakte:** Mist semantische duplicaten ("zelfde onderwerp, andere woorden"). Begrijpt geen synoniemen.

## Hoe SF Semantic Similarity Berekent (v22+)

Screaming Frog's semantische analyse:

1. **Embedding generatie:** Stuurt pagina-content naar Gemini API.
2. **Vector opslag:** Slaat embedding vector op per pagina (typisch 1536 of 3072 dimensies).
3. **Cosine similarity:** Berekent cosine distance tussen alle pagina-paren.
4. **Threshold:** Default 0.95 (streng). Configureerbaar via `Config > Content > Embeddings`.
5. **Centroid:** Berekent een gemiddelde vector van de hele site. Pagina's ver van de centroid = outliers.

**Sterkte:** Begrijpt betekenis, vindt semantische duplicaten.
**Zwakte:** Vereist API calls ($), trager, threshold 0.95 is vaak te streng.

---

## Laag 4: Component Analysis (eigen berekening)

De toegevoegde waarde boven SF. Vergelijkt pagina-componenten apart:

```
component_scores = {
    "title":       cosine_similarity(title_a, title_b),
    "h1":          cosine_similarity(h1_a, h1_b),
    "meta":        cosine_similarity(meta_a, meta_b),
    "body":        cosine_similarity(body_a, body_b)
}

weighted_similarity = (
    0.20 × title_score +
    0.15 × h1_score +
    0.10 × meta_score +
    0.55 × body_score
)
```

### Wat component analysis vindt dat SF mist

| Scenario | SF MinHash | SF Semantic | Component Analysis |
|----------|-----------|-------------|-------------------|
| Zelfde title+H1, andere body | Lage overlap | Matige similarity | Hoge title/H1, lage body → **DIFFERENTIATE** |
| Andere title, zelfde body | Hoge overlap | Hoge similarity | Lage title, hoge body → **CANONICAL** |
| Zelfde template, unieke content | Hoge overlap (boilerplate) | Matige similarity | Hoge boilerplate, lage unique → **FALSE POSITIVE** |
| Zelfde onderwerp, andere aanpak | Lage overlap | Hoge similarity | Alle componenten matig → **REVIEW** |

### Input voor Component Analysis

Uit SF `Internal:HTML` export:
- `Address` → URL
- `Title 1` → Title tag
- `H1-1` → Eerste H1
- `Meta Description 1` → Meta description

Uit SF `All Page Text` export of `Embeddings` export:
- Body text of embedding vector per URL

Component similarity wordt berekend met de embeddings uit SF (als beschikbaar) of met TF-IDF als fallback (als alleen tekst beschikbaar is).

---

## Workflow

### Stap 1: SF Data Laden

```bash
python3 references/similarity/sf_parser.py \
    --internal internal_html.csv \
    --near-duplicates near_duplicates.csv \
    --exact-duplicates exact_duplicates.csv \
    --semantic-similar semantically_similar.csv \
    --embeddings embeddings.csv \
    --output parsed-data.json
```

### Stap 2: Component Analysis Uitvoeren

```bash
python3 references/similarity/similarity.py \
    --mode near-duplicates \
    --data parsed-data.json \
    --threshold 0.85 \
    --component-weights "title:0.20,h1:0.15,meta:0.10,body:0.55" \
    --output NEAR-DUPLICATES.md
```

### Of: alles in één commando

```bash
python3 references/similarity/near_duplicates_pipeline.py \
    --sf-dir ./sf-export/ \
    --threshold 0.85 \
    --output NEAR-DUPLICATES.md
```

De pipeline detecteert automatisch welke SF exports beschikbaar zijn en gebruikt de rijkste data.

---

## Classificatie & Aanbevelingen

### Classificatie per Cluster

| Classificatie | Criteria | Actie |
|--------------|---------|-------|
| **EXACT DUPLICATE** | MD5 hash identiek | **Canonical** → behoud beste, redirect rest |
| **NEAR DUPLICATE** | MinHash ≥90% | **Merge of canonical** → combineer content |
| **SEMANTISCH VERGELIJKBAAR** | Embedding cosine ≥0.85 | **Review** → is de overlap gewenst? |
| **TITLE/H1 OVERLAP** | Title sim ≥0.90, body sim <0.60 | **Differentiate** → pas titles aan |
| **BODY OVERLAP** | Body sim ≥0.85, title sim <0.60 | **Canonical** → zelfde content, andere verpakking |
| **TEMPLATE DUPLICATE** | Hoge boilerplate overlap, lage unique content | **Enrich** → voeg unieke content toe |
| **THEMATISCH VERWANT** | Embedding cosine 0.70-0.84 | **OK** — kan topic cluster zijn |

### Aanbevelingen per Actie

| Actie | Wat te doen |
|-------|------------|
| **CANONICAL** | Stel `<link rel="canonical">` in naar de sterkste pagina (meeste backlinks/traffic) |
| **MERGE** | Combineer content van beide pagina's in één, redirect de zwakkere met 301 |
| **DIFFERENTIATE** | Pas title, H1 en meta description aan om unieke zoekintent te targeten |
| **ENRICH** | Voeg minimaal 40% unieke content toe aan template-pagina's |
| **OK** | Geen actie nodig — thematisch verwant is gezond (topic cluster) |

---

## Thresholds (configureerbaar)

### Near-Duplicate Thresholds

| Parameter | Default | Bereik | Beschrijving |
|-----------|---------|--------|-------------|
| `--threshold` | 0.85 | 0.50-1.00 | Minimum similarity voor flagging |
| `--exact-threshold` | 1.00 | — | MD5 match (niet configureerbaar) |
| `--semantic-threshold` | 0.85 | 0.60-0.99 | Embedding cosine drempel |
| `--title-threshold` | 0.90 | 0.70-1.00 | Title overlap drempel |

### Component Gewichten

| Component | Default gewicht | Aanpasbaar |
|-----------|----------------|-----------|
| Title | 0.20 | Ja (`--component-weights`) |
| H1 | 0.15 | Ja |
| Meta Description | 0.10 | Ja |
| Body Text | 0.55 | Ja |

---

## Output Format

### NEAR-DUPLICATES.md

```markdown
# Near-Duplicate Analysis — [Domain]
Date: [Date]
Pages Analyzed: [Count]
Clusters Found: [Count]

## Summary

| Type | Count | Actie Nodig |
|------|-------|-------------|
| Exact Duplicates | [X] | Canonical/redirect |
| Near Duplicates (MinHash ≥90%) | [X] | Merge of canonical |
| Semantisch Vergelijkbaar (≥0.85) | [X] | Review |
| Title/H1 Overlap | [X] | Differentiate |
| Body Overlap | [X] | Canonical |
| Template Duplicates | [X] | Enrich |
| Thematisch Verwant (0.70-0.84) | [X] | OK (topic cluster) |

---

## Cluster Details

### Cluster 1: [Label]
**Classificatie:** NEAR DUPLICATE
**Aanbeveling:** MERGE

| URL | Title | MinHash% | Semantic | Component |
|-----|-------|----------|----------|-----------|
| [url1] | [title1] | 94% | 0.92 | T:0.95 H1:0.98 M:0.88 B:0.91 |
| [url2] | [title2] | 94% | 0.92 | T:0.95 H1:0.98 M:0.88 B:0.91 |

**Waarom:** Pagina's delen 94% tekst en 0.92 semantische similarity.
Alle componenten scoren hoog. Dit is dezelfde content.

**Actie:** Behoud [url1] (meer backlinks/traffic), redirect [url2] → [url1] met 301.

---

### Cluster 2: [Label]
**Classificatie:** TITLE/H1 OVERLAP
**Aanbeveling:** DIFFERENTIATE

| URL | Title | MinHash% | Semantic | Component |
|-----|-------|----------|----------|-----------|
| [url1] | [title1] | 45% | 0.71 | T:0.95 H1:0.92 M:0.80 B:0.42 |
| [url2] | [title2] | 45% | 0.71 | T:0.95 H1:0.92 M:0.80 B:0.42 |

**Waarom:** Title en H1 zijn bijna identiek (0.95/0.92), maar body text
verschilt sterk (0.42). Deze pagina's concurreren in SERP door gelijke
titles maar bieden verschillende content.

**Actie:** Hernoem [url2] title en H1 om unieke zoekintent te targeten.

---

## Prioritized Actions

### Critical (fix immediately)
[Exact duplicates en near-duplicates met hoge traffic]

### High (fix within 1 week)
[Title/H1 overlap op pagina's met zoekverkeer]

### Medium (fix within 1 month)
[Semantisch vergelijkbare pagina's die cannibaliseren]

### Low (backlog)
[Template duplicates met lage traffic]
```

---

## Integratie met 42: Suite

| Skill | Relatie |
|-------|--------|
| **42:screaming-frog** | Levert alle input (MinHash, semantic, embeddings, page text) |
| **42:keyword-mapper** | Near-duplicates die voor zelfde keywords ranken → dubbele actie nodig |
| **42:cannibalization** | Complementair: cannibalization kijkt vanuit keywords, near-duplicates vanuit content |
| **42:content** | Thin content pagina's die ook near-duplicate zijn → sterkere merge-case |
| **42:technical** | Canonical issues uit near-duplicate analyse → technische fixes |
| **42:audit** | Near-duplicate rapport als onderdeel van full audit |

---

## Cross-References

- Voor **Screaming Frog exports genereren** → `/42:screaming-frog export <url> --tab "Content:Near Duplicates"`
- Voor **keyword-based cannibalisatie** → `/42:cannibalization`
- Voor **keyword→pagina mapping** → `/42:keyword-mapper`
- Voor **canonical issue detectie** → `/42:technical`
- Voor **content quality per pagina** → `/42:content`
