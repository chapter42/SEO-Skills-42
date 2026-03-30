---
name: 42-entity-extractor
description: "Named Entity Recognition across page content. Extract entities (persons, organizations, locations, products) with frequency counts. Optionally use AI for entity relationship mapping and Wikipedia URL resolution. Use when user says entity extractor, entity extraction, NER, named entities, extract entities, entity analysis, entity graph, entity map, 42-entity."
user-invokable: true
argument-hint: "<url-or-csv> [--model spacy|ai] [--types PER,ORG,LOC,PRODUCT]"
version: "1.0.0"
tags:
  - seo
  - ner
  - entities
  - content-analysis
  - topical-authority
  - knowledge-graph
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
metadata:
  filePattern: "**/*entity*,**/*ner*,**/*entities*"
  bashPattern: "python*entity*,python*spacy*"
---

# 42 Entity Extractor

Named Entity Recognition (NER) across web page content. Extracts persons, organizations, locations, products, and other entity types with frequency counts. Supports two modes: SpaCy for fast local processing, and AI for deeper relationship mapping with Wikipedia URL resolution.

---

## Why Entity Extraction Matters for SEO

Google's Knowledge Graph contains over 500 billion facts about 5 billion entities. Google's understanding of content is fundamentally entity-based, not keyword-based. Entities are how Google connects topics, establishes authority, and determines relevance.

Entity extraction reveals:
- **Topical authority signals** -- which entities does your content cover vs. competitors?
- **Internal linking opportunities** -- entities mentioned across multiple pages should be linked.
- **Content gaps** -- important entities in your niche that your content never mentions.
- **E-E-A-T signals** -- persons mentioned (authors, experts) strengthen Experience and Expertise.
- **AI citation readiness** -- AI models use entity recognition to identify authoritative content.

---

## Commands

```
/42:entity-extractor <url-or-csv> [--model spacy|ai] [--types PER,ORG,LOC,PRODUCT]
/42:entity-extractor <text-file> [--model spacy|ai] [--types PER,ORG,LOC,PRODUCT]
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `url-or-csv` | Yes | -- | Single URL, path to CSV of URLs, path to text file, or Screaming Frog content export directory |
| `--model` | No | `spacy` | NER engine: `spacy` (local, fast) or `ai` (OpenAI/Anthropic, deeper analysis) |
| `--types` | No | all | Comma-separated entity types to extract. Options: `PER`, `ORG`, `LOC`, `PRODUCT`, `EVENT`, `WORK_OF_ART`, `DATE`, `MONEY`, `GPE`, `NORP` |
| `--spacy-model` | No | `en_core_web_sm` | SpaCy model size: `en_core_web_sm` (fast), `en_core_web_md` (balanced), `en_core_web_lg` (accurate) |
| `--relationships` | No | `false` | (AI mode only) Map entity relationships and co-occurrences |
| `--wikipedia` | No | `false` | (AI mode only) Resolve entities to Wikipedia URLs for Knowledge Graph alignment |
| `--min-frequency` | No | `2` | Minimum mention count to include in report |
| `--output` | No | `ENTITY-REPORT.md` | Output filename |

---

## Dependencies

### SpaCy Mode

```bash
pip install spacy beautifulsoup4 requests
python -m spacy download en_core_web_sm    # 12MB, fast
python -m spacy download en_core_web_md    # 40MB, balanced (includes word vectors)
python -m spacy download en_core_web_lg    # 560MB, most accurate
```

### AI Mode

Requires one of:
- `OPENAI_API_KEY` environment variable (for GPT-4)
- `ANTHROPIC_API_KEY` environment variable (for Claude)

---

## Workflow: SpaCy Mode

### Step 1: Extract Text from Input

Determine input type and extract plain text:
- **URL:** Fetch the page with requests/BeautifulSoup. Strip navigation, footer, sidebar. Extract main content text.
- **CSV of URLs:** Read URLs from CSV (column named `url` or first column). Fetch each page.
- **Text file:** Read the file directly as plain text.
- **Screaming Frog export directory:** Read `.txt` files from the directory. Each file represents one page's extracted text. Filename typically contains the URL slug.

### Step 2: Run SpaCy NER

For each text input:
1. Load the SpaCy model (`en_core_web_sm` by default).
2. Process the text through the NER pipeline.
3. Extract entities with their labels (PER, ORG, LOC, GPE, etc.).
4. Filter by requested `--types` if specified.
5. Store: entity text, entity label, source URL/file, sentence context.

### Step 3: Group by Entity Type

Organize extracted entities into groups:
- **PERSON** (PER) -- People, including fictional characters.
- **ORG** -- Organizations, companies, agencies, institutions.
- **GPE** -- Geopolitical entities (countries, cities, states).
- **LOC** -- Non-GPE locations (mountain ranges, bodies of water).
- **PRODUCT** -- Objects, vehicles, foods, software (not services).
- **EVENT** -- Named events (battles, wars, sports events).
- **WORK_OF_ART** -- Titles of books, songs, films.
- **DATE** -- Absolute or relative dates/periods.
- **MONEY** -- Monetary values.
- **NORP** -- Nationalities, religious or political groups.

### Step 4: Count Frequency

For each unique entity (normalized: case-insensitive dedup with most common casing preserved):
- Total mention count across all pages.
- Per-page mention count.
- Pages where entity appears (for internal linking).
- Average position in text (early mentions signal higher importance).

### Step 5: Identify Key Entities

Rank entities by:
1. **Frequency** -- most mentioned entities.
2. **Spread** -- entities appearing across the most pages (cross-page authority signals).
3. **Prominence** -- entities appearing earliest in content (title, first paragraph).

---

## Workflow: AI Mode

### Step 1: Extract Text from Input

Same as SpaCy mode Step 1.

### Step 2: Send Text to AI Model

Construct a prompt for the AI model:

```
Analyze the following text and extract all named entities. For each entity, provide:
1. Entity name (canonical form)
2. Entity type (PERSON, ORG, LOCATION, PRODUCT, EVENT, CONCEPT)
3. Wikipedia URL (if the entity has a Wikipedia page)
4. Brief description (1 sentence)
5. Confidence score (0.0-1.0)

Also identify relationships between entities:
- Entity A → relationship → Entity B
- Example: "Google → owns → YouTube"

Text:
[content]
```

### Step 3: Extract Entities and Relationships

Parse the AI response to extract:
- Structured entity list with types, Wikipedia URLs, descriptions.
- Entity relationship pairs.
- Confidence scores for each extraction.

### Step 4: Build Entity Graph

From the relationships, build a graph:
- Nodes = entities (with type, frequency, Wikipedia URL).
- Edges = relationships (with label: "owns", "founded by", "located in", etc.).
- Identify clusters of related entities (topic clusters).

### Step 5: Cross-Reference with Content

Map entities back to content:
- Which pages mention which entities?
- Which entities co-occur on the same page? (Internal linking candidates.)
- Which entities appear in competitor content but not yours? (Content gaps.)

---

## Output Format: ENTITY-REPORT.md

```markdown
# Entity Extraction Report

**Source:** [URL/file/directory]
**Model:** [spacy en_core_web_sm | AI (GPT-4)]
**Pages analyzed:** [count]
**Total entities found:** [count]
**Unique entities:** [count]
**Generated:** [date]

---

## Top Entities by Frequency

| # | Entity | Type | Mentions | Pages | Avg Position |
|---|--------|------|----------|-------|-------------|
| 1 | Google | ORG | 47 | 12 | 0.15 |
| 2 | John Smith | PER | 23 | 5 | 0.08 |
| 3 | New York | GPE | 19 | 8 | 0.32 |

---

## Entities by Type

### PERSON
| Entity | Mentions | Pages | Context |
|--------|----------|-------|---------|
| John Smith | 23 | 5 | "CEO John Smith announced..." |

### ORG
| Entity | Mentions | Pages | Context |
|--------|----------|-------|---------|
| Google | 47 | 12 | "Google's algorithm update..." |

### GPE (Geopolitical)
| Entity | Mentions | Pages | Context |
|--------|----------|-------|---------|
| New York | 19 | 8 | "headquartered in New York..." |

---

## Entity Relationships (AI mode only)

| Entity A | Relationship | Entity B |
|----------|-------------|----------|
| Google | owns | YouTube |
| John Smith | CEO of | Acme Corp |
| Acme Corp | headquartered in | New York |

---

## Internal Linking Opportunities

Entities appearing on 3+ pages without cross-links:

| Entity | Pages | Suggested Hub Page |
|--------|-------|--------------------|
| Google Analytics | 8 pages | /tools/google-analytics/ |
| Core Web Vitals | 5 pages | /technical-seo/core-web-vitals/ |

---

## Content Gap: Entities Missing from Your Content

(Requires competitor URL input for comparison)

| Entity | Competitor Mentions | Your Mentions | Gap |
|--------|-------------------|---------------|-----|
| Search Console | 34 | 0 | HIGH |
```

---

## SpaCy Entity Type Mapping

SpaCy uses a different label scheme than casual usage. Here is the mapping:

| SpaCy Label | Meaning | SEO Relevance |
|---|---|---|
| PERSON | Named persons | Author entities, E-E-A-T signals |
| ORG | Companies, agencies | Brand entities, competitor mentions |
| GPE | Countries, cities, states | Local SEO, geo-targeting |
| LOC | Non-GPE locations | Geographic content signals |
| PRODUCT | Objects, software | Product schema, e-commerce |
| EVENT | Named events | Timely content, event schema |
| WORK_OF_ART | Titles of creative works | Content references, citations |
| DATE | Dates and periods | Content freshness signals |
| MONEY | Monetary values | Pricing content, commercial intent |
| NORP | Nationalities, groups | Audience targeting |

---

## Use Cases

### 1. Topical Authority Mapping
Extract entities from your top 50 pages and your top competitor's top 50 pages. Compare entity coverage. Missing entities = missing subtopics.

### 2. Internal Linking Targets
Entities mentioned on 3+ pages are natural internal linking hubs. Create a pillar page for each high-frequency entity and link all mentions to it.

### 3. Content Gap Discovery
Run entity extraction on competitor content that ranks above you. Entities they cover that you do not mention are content gaps to fill.

### 4. E-E-A-T Enhancement
Count PERSON entities on your site. If competitor content mentions more expert names, you may need more expert citations, quotes, and author bios.

### 5. Schema Markup Targets
Every extracted entity is a potential Schema.org markup target: Person, Organization, Place, Product, Event. Entity extraction produces a prioritized list for structured data implementation.

---

## Implementation Notes

This skill does not include a standalone Python script. Instead, it leverages:

- **SpaCy mode:** Run SpaCy directly via Bash tool (`python -c "import spacy; ..."`) or use a temporary inline script generated at runtime. SpaCy NER is fast enough to process in real-time.
- **AI mode:** Send text directly to OpenAI/Anthropic via the API or use the WebFetch tool to call the API endpoint.

The skill orchestration (fetching pages, running NER, aggregating results, generating the report) is handled by Claude Code using the allowed tools.

For large-scale batch processing (100+ URLs), consider:
1. Fetching all pages first and saving text to a temporary directory.
2. Processing all text files through SpaCy in a single Python script invocation.
3. Aggregating results in memory before writing the report.

---

## Cross-References

- **42:content** -- Entity density is a content quality signal; feed entity data into content audits.
- **42:topical-map** -- Entities define topic boundaries; use entity clusters to build topical maps.
- **42:brand-mentions** -- Brand entities overlap with brand mention scanning; cross-reference for authority.
- **42:structured-data** -- Extracted entities map directly to Schema.org types for markup implementation.
- **42:internal-links** -- Cross-page entity frequency identifies internal linking opportunities.
- **42:seo-agi** -- Entity coverage informs content briefs for comprehensive topical authority.
