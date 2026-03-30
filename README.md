# 42 SEO Skills

54 AI-agent skills voor SEO, GEO en content-analyse. Gebouwd als [Claude Code](https://claude.ai/code) skills, maar de methodologie en Python scripts zijn framework-onafhankelijk.

Alle skills oproepbaar met `42:` prefix. Dual-perspective: traditionele SEO (Google rankings) en GEO (AI-zoekmachine citaties).

## Snelstart

```bash
# 1. Clone
git clone https://github.com/your-org/42-seo-skills.git
cd 42-seo-skills

# 2. Installeer skills in Claude Code
./manage.sh install          # symlinks naar ~/.claude/skills/
./manage.sh check --fix      # installeer Python dependencies

# 3. API keys configureren
cp .env.example .env
# Vul GOOGLE_API_KEY en DATAFORSEO_LOGIN/PASSWORD in

# 4. Gebruik als Claude Code skills
/42-audit https://example.com              # Volledige SEO + GEO audit
/42-audit https://example.com --seo        # Alleen SEO
/42-audit https://example.com --geo        # Alleen GEO (AI-zoekmachines)
/42-technical https://example.com           # Technische audit
/42-content https://example.com             # Content quality + E-E-A-T
/42-striking-distance gsc-export.csv        # Quick wins op positie 4-20
/42-page-health sf-internal.csv             # Per-URL gezondheidscore
```

### Beheer

```bash
./manage.sh install [--dry-run]  # Symlink skills naar ~/.claude/skills/
./manage.sh uninstall            # Verwijder alle symlinks
./manage.sh check [--fix]        # Check/installeer Python dependencies
./manage.sh status               # Toon welke skills actief zijn
```

## Wat zit erin

### Orchestrators

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:seo-project](42-seo-project/) | `/42:seo-project start <url>` | Project lifecycle orchestrator: 7 fasen (Crawl→Discover→Diagnose→Strategize→Implement→Verify→Monitor). State tracking over sessies, multi-site, decision locking. Coördineert alle andere skills. |
| [42:audit](42-audit/) | `/42:audit <url>` | Unified SEO + GEO audit. Business type detectie, parallel subagent delegatie, dual scoring (SEO Health Score + GEO Score). |

### Geconsolideerde Skills

Skills die meerdere bronnen combineren met `--seo` / `--geo` mode flags.

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:technical](42-technical/) | `/42:technical <url>` | 10-categorie technische audit: crawlability, indexability, security, URL structure, mobile, CWV, SSR, page speed, structured data, IndexNow. |
| [42:content](42-content/) | `/42:content <url>` | E-E-A-T scoring + keyword optimalisatie (SEO) + passage architectuur en citability (GEO) + topical authority. |
| [42:structured-data](42-structured-data/) | `/42:structured-data <url>` | Schema.org detectie, validatie, scoring (0-100), JSON-LD generatie. `--blog` mode voor kant-en-klare @graph. |
| [42:geo-report](skills/42-geo-report/) | `/42:geo-report <url>` | Client-ready GEO rapport in markdown. |

### SEO Specialists

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:seo-agi](42-seo-agi/) | `/42:seo-agi <keyword>` | Elite SEO agent: live SERP data (DataForSEO), content gap analyse, verticale instructies. |
| [42:ai-visibility](42-ai-visibility/) | `/42:ai-visibility <domain>` | AI visibility tracking via 6 databronnen (GSC, forums, PAA, AI-citaties). |
| [42:competitor-pages](42-competitor-pages/) | `/42:competitor-pages <url>` | "X vs Y" vergelijkingspagina's genereren met feature matrices en schema. |
| [42:seo-geo](42-seo-geo/) | `/42:seo-geo <url>` | AI Overviews optimalisatie: citability, structural readiness, authority signals. |
| [42:hreflang](42-hreflang/) | `/42:hreflang <url>` | International SEO: hreflang validatie, return tags, x-default, language codes. |
| [42:images](42-images/) | `/42:images <url>` | Afbeelding-optimalisatie: alt text, WebP/AVIF, responsive, lazy loading, CLS. |
| [42:page-analysis](42-page-analysis/) | `/42:page-analysis <url>` | Deep single-page analyse: on-page, content, meta, schema, images, performance. |
| [42:seo-plan](42-seo-plan/) | `/42:seo-plan <type>` | Strategische planning met 6 industry templates (SaaS, local, ecom, publisher, agency). |
| [42:programmatic-seo](42-programmatic-seo/) | `/42:programmatic-seo` | Pagina's op schaal: templates, URL patterns, thin content safeguards. |
| [42:qrg](42-qrg/) | `/42:qrg <url>` | Google Quality Rater Guidelines assessment: YMYL, MC quality, E-E-A-T, Needs Met. |
| [42:sitemap](42-sitemap/) | `/42:sitemap <url>` | XML sitemap audit of generatie met quality gates. |

### GEO Specialists

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:citability](42-citability/) | `/42:citability <url>` | Passage-level AI citability scoring (0-100) met 5-dimensie rubric. |
| [42:crawlers](42-crawlers/) | `/42:crawlers <url>` | AI crawler access audit: 14+ crawlers in 3 tiers, robots.txt analyse. |
| [42:llmstxt](42-llmstxt/) | `/42:llmstxt <url>` | llms.txt analyse en generatie. |
| [42:brand-mentions](42-brand-mentions/) | `/42:brand-mentions <url>` | Brand authority scanning: YouTube, Reddit, Wikipedia, LinkedIn, Crunchbase. |
| [42:platform-optimizer](42-platform-optimizer/) | `/42:platform-optimizer <url>` | Per-platform optimalisatie: Google AIO, ChatGPT, Perplexity, Gemini, Bing Copilot. |
| [42:geo-compare](42-geo-compare/) | `/42:geo-compare <domain>` | Maandelijkse delta-tracking met 6-maanden trajectory. |
| [42:geo-proposal](42-geo-proposal/) | `/42:geo-proposal <domain>` | Client proposal met 3 service tiers en ROI projectie. |
| [42:geo-prospect](42-geo-prospect/) | `/42:geo-prospect <cmd>` | CRM-lite pipeline: prospects, audits, proposals, status tracking. |

### Analytics & Optimization

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:striking-distance](42-striking-distance/) | `/42:striking-distance <gsc.csv>` | Quick wins: positie 4-20, keyword ontbreekt in title/H1. Opportunity scoring. |
| [42:content-decay](42-content-decay/) | `/42:content-decay <gsc.csv>` | Traffic decline vs piek. Anomalie-detectie, algorithm update correlatie. |
| [42:page-health](42-page-health/) | `/42:page-health <sf.csv>` | Per-URL gezondheidscore (0-100): 7 risicosignalen, pagina-type thresholds. |
| [42:serp-cluster](42-serp-cluster/) | `/42:serp-cluster <serp.csv>` | Keyword clustering op gedeelde SERP URLs. 3 algoritmes. |
| [42:share-of-voice](42-share-of-voice/) | `/42:share-of-voice <rankings.csv>` | Competitieve SOV met 4 CTR-modellen. |
| [42:meta-optimizer](42-meta-optimizer/) | `/42:meta-optimizer <url>` | AI meta descriptions: scoren (0-40), herschrijven, snippet generatie. |
| [42:title-optimizer](42-title-optimizer/) | `/42:title-optimizer <url>` | Iteratieve title tag optimizer: 3 rondes, 7-dimensie scoring. |
| [42:migration](42-migration/) | `/42:migration validate <spec.csv> <crawl.csv>` | Redirect validatie, content change detectie, Wayback Machine analyse. |

### Content Intelligence

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:keyword-discovery](42-keyword-discovery/) | `/42:keyword-discovery <seed>` | Seed keyword → complete lijst: DataForSEO suggestions + related, intent classificatie, opportunity scoring. Mock modus zonder API. |
| [42:passage-analyzer](42-passage-analyzer/) | `/42:passage-analyzer <url>` | Passage-level scoring: 6-dimensie heuristic + Gemini embedding retrieval. |
| [42:keyword-mapper](42-keyword-mapper/) | `/42:keyword-mapper <sf.csv> <gsc.csv>` | Keyword→pagina mapping via embeddings. Content gaps, cannibalisatie, quick wins. |
| [42:near-duplicates](42-near-duplicates/) | `/42:near-duplicates <sf-dir>` | 4-laags duplicate detectie: MD5, MinHash, semantic, component-analyse. |
| [42:audience-angles](42-audience-angles/) | `/42:audience-angles <url>` | Audience-first content discovery: 10 dimensies, 50 angles. |
| [42:paa-scraper](42-paa-scraper/) | `/42:paa-scraper <keyword>` | Recursief PAA tot 5 niveaus diep via DataForSEO. |
| [42:entity-extractor](42-entity-extractor/) | `/42:entity-extractor <url>` | Named Entity Recognition + relatie mapping. |
| [42:topical-map](42-topical-map/) | `/42:topical-map <keywords.csv>` | AI topic hiërarchie (2-5 niveaus): pillars, clusters, subtopics. |
| [42:content-repurposer](42-content-repurposer/) | `/42:content-repurposer <url>` | 1 content → 10 platform formaten (Twitter, LinkedIn, YouTube, etc.). |
| [42:readability](42-readability/) | `/42:readability <sf-text-dir>` | Bulk readability: Flesch, Gunning Fog, SMOG, grade level. |

### Blog Utilities

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:blog-geo](42-blog-geo/) | `/42:blog-geo <url>` | Blog AI citability audit met citation capsules. |
| [42:blog-seo-check](42-blog-seo-check/) | `/42:blog-seo-check <url>` | Post-writing SEO validatie: pass/fail checklist. |
| [42:blog-schema](42-blog-schema/) | `/42:blog-schema <file>` | Blog JSON-LD @graph generator (6 schema types). |
| [42:cannibalization](42-cannibalization/) | `/42:cannibalization` | Keyword cannibalisatie detectie met severity scoring. |

### Crawling & Data

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:screaming-frog](42-screaming-frog/) | `/42:screaming-frog <cmd>` | SF CLI integratie: crawls, exports (600+ tabs), analyse, profielen. |
| [42:genai-optimizer](42-genai-optimizer/) | `/42:genai-optimizer <text>` | Tekst herschrijven voor maximale AI extractability. |
| [42:internal-links](42-internal-links/) | `/42:internal-links <url>` | Competitive e-commerce internal link analyse (27 link blocks). |
| [42:sentiment](42-sentiment/) | `/42:sentiment <query>` | Sentiment analyse: Reddit, news, forums, reviews, social. |

### eCommerce

| Skill | Command | Wat het doet |
|-------|---------|-------------|
| [42:ecom-taxonomy](42-ecom-taxonomy/) | `/42:ecom-taxonomy discover <products.csv>` | Categorie-ontdekking + breadcrumb relevantie check. |
| [42:product-titles](42-product-titles/) | `/42:product-titles gap <csv> <competitor.csv>` | Product title gap analyse (MPN-matched) + SERP patronen. |
| [42:link-graph](42-link-graph/) | `/42:link-graph visualize <sf-inlinks.csv>` | NetworkX link graph: PageRank, centrality, orphans, revenue-vs-links. |

---

## Requirements

### Python 3.10+

```bash
pip install -r requirements.txt
```

Kern-dependencies:

| Package | Versie | Waarvoor |
|---------|--------|----------|
| `google-generativeai` | >=0.8.0 | Gemini embeddings (keyword-mapper, passage-analyzer) |
| `beautifulsoup4` | >=4.12.0 | HTML parsing (audit, technical) |
| `requests` | >=2.32.4 | HTTP client |
| `lxml` | >=6.0.2 | XML/HTML parsing (sitemap, schema) |
| `numpy` | >=2.0.0 | Embedding vectors, matrix operaties |
| `scipy` | >=1.14.0 | Cosine similarity op schaal |

Optioneel:

| Package | Waarvoor |
|---------|----------|
| `playwright` | Browser automation (internal-links, seo-agi) |
| `textstat` | Readability scoring (readability) |
| `networkx` | Link graph analyse (link-graph) |
| `rapidfuzz` | Fuzzy matching (product-titles, ecom-taxonomy) |
| `spacy` | NER entity extractie (entity-extractor) |
| `nltk` | N-gram extractie (ecom-taxonomy) |
| `google-auth` + `google-api-python-client` | GSC integratie (seo-agi) |

### API Keys

**Optie 1: `.env` bestand** (aanbevolen)

```bash
cp .env.example .env
# Vul je keys in
```

**Optie 2: Shell environment** (handig voor CI of als je keys al elders beheert)

```bash
# Voeg toe aan ~/.zshrc of ~/.bashrc:
export GOOGLE_API_KEY="je-google-api-key"
export DATAFORSEO_LOGIN="je-login"
export DATAFORSEO_PASSWORD="je-password"
export GOOGLE_SERVICE_ACCOUNT_JSON="/pad/naar/service-account.json"
```

Shell-variabelen hebben voorrang boven `.env`. Alle Python scripts laden keys automatisch via `references/load_env.py`.

| Key | Provider | Waarvoor | Kosten |
|-----|----------|----------|--------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | Gemini embeddings + AI skills | Gratis tier, daarna ~$0.075/1M tokens |
| `DATAFORSEO_LOGIN` | [DataForSEO](https://dataforseo.com) | SERP data, keywords, backlinks | ~$0.01-0.05 per call |
| `DATAFORSEO_PASSWORD` | DataForSEO | Idem | Idem |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | [Google Cloud Console](https://console.cloud.google.com/) | GSC data pull | Gratis |

### Screaming Frog

Meerdere skills gebruiken Screaming Frog SEO Spider als databron:

- **Versie:** v22+ (voor embeddings), v16+ (voor basis exports)
- **Licentie:** Betaald (free versie beperkt tot 500 URLs)
- **Embedding provider:** Configureer Gemini in `Config > API Access > AI`
- **Download:** [screamingfrog.co.uk](https://www.screamingfrog.co.uk/seo-spider/)

---

## Architectuur

### Embedding Stack

Eén model overal: **Gemini `text-embedding-004`**.

```
Screaming Frog (pagina embeddings)
        ↓ CSV export
keyword_embedder.py (keyword embeddings)  ←  GSC export / keyword CSV
        ↓
similarity.py (cosine similarity matrix)
        ↓
42:keyword-mapper / 42:near-duplicates / 42:passage-analyzer
```

Alle embeddings moeten van hetzelfde model komen — anders zijn de vectoren incompatibel.

### Skill Types

```
Meta-orchestrator (1)   42:seo-project (lifecycle over meerdere sessies)
    ↓ delegeert naar
Orchestrator (1)        42:audit (single-session audit)
    ↓ delegeert naar
Geconsolideerd (4)      42:technical, 42:content, 42:structured-data, 42:geo-report
    ↓ en naar
Specialisten (48)       42:citability, 42:crawlers, 42:striking-distance, ...
```

**Geconsolideerde skills** combineren SEO + GEO perspectief met mode flags:
- `--seo` → Google ranking signals
- `--geo` → AI citability, SSR critical, sameAs
- *(geen flag)* → beide scores

### Gedeelde Modules

| Module | Locatie | Gebruikt door |
|--------|---------|--------------|
| `load_env.py` | `references/` | Alle Python scripts (auto-load .env) |
| `sf_parser.py` | `references/similarity/` | keyword-mapper, near-duplicates |
| `keyword_embedder.py` | `references/similarity/` | keyword-mapper, passage-analyzer |
| `similarity.py` | `references/similarity/` | keyword-mapper, near-duplicates |
| `eeat-scoring-rubric.md` | `references/` | content, audit |

---

## Data Flow

```
                    ┌──────────────┐
                    │ Screaming    │
                    │ Frog Crawl   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌──────▼─────┐  ┌──▼──────────┐
    │ Internal   │  │ Embeddings │  │ Near Dupes   │
    │ HTML CSV   │  │ CSV        │  │ + Semantic   │
    └─────┬──────┘  └──────┬─────┘  └──┬───────────┘
          │                │           │
    ┌─────▼──────┐  ┌──────▼─────┐  ┌──▼───────────┐
    │ page-health│  │ keyword-   │  │ near-         │
    │ striking-  │  │ mapper     │  │ duplicates    │
    │ distance   │  │ passage-   │  │               │
    └────────────┘  │ analyzer   │  └───────────────┘
                    └──────┬─────┘
                           │
                    ┌──────▼─────┐
                    │ GSC Export  │
                    │ (queries,  │
                    │  clicks)   │
                    └────────────┘
```

---

## Changelog

### v1.1.0 (2026-03-30)

**Package management & repo reorganisatie**

- Alle 54 skill directories verplaatst naar `skills/` subfolder
- `manage.sh` — install/uninstall/status/check script voor skill lifecycle
  - `install` symlinkt alle skills naar `~/.claude/skills/` met manifest tracking
  - `uninstall` verwijdert clean via manifest (of fallback scan)
  - `check` toont core + optional Python dependency status
  - `check --fix` installeert ontbrekende core dependencies
  - `install --dry-run` voor preview zonder wijzigingen
- Automatische shared references: skills zonder eigen `references/` krijgen symlink naar root `references/`
- `CLAUDE.md` met architectuurbeslissingen en conventies
- `.installed` manifest in `.gitignore`
- PDF report generatie verwijderd (42-geo-report) — alles is nu markdown-only
  - `generate_pdf_report.py` verwijderd
  - `reportlab` uit optional dependencies
  - `--pdf` flag en bijbehorende documentatie verwijderd

### v1.0.0 (2026-03-30)

**Initial release — 54 skills**

Consolidation:
- Merged 38 source skills into unified `42:` namespace
- 5 merged skills: audit, technical, content, structured-data, geo-report
- 25 skills renamed with `42:` prefix
- Shared E-E-A-T scoring rubric (`references/eeat-scoring-rubric.md`)

New skills built from scratch:
- `42:screaming-frog` — SF CLI integration (crawls, 600+ export tabs, Python API)
- `42:keyword-mapper` — Embedding-based keyword→page mapping with GSC integration
- `42:near-duplicates` — 4-layer duplicate detection (MD5, MinHash, semantic, component)
- `42:passage-analyzer` — Passage-level scoring (heuristic + Gemini embeddings)
- `42:page-health` — Per-URL health score (0-100) with 7 risk signals
- `42:striking-distance` — Quick wins on position 4-20
- `42:content-decay` — Traffic decline detection with algorithm update correlation
- `42:serp-cluster` — SERP URL overlap clustering (3 algorithms)
- `42:share-of-voice` — CTR-adjusted competitive visibility (4 models)
- `42:meta-optimizer` — AI meta description grading + rewriting
- `42:title-optimizer` — Iterative title tag optimization (3 rounds, 7 dimensions)
- `42:migration` — Redirect validation, content change detection, Wayback Machine
- `42:paa-scraper` — Recursive PAA tree (5 levels) via DataForSEO
- `42:entity-extractor` — NER entity extraction (SpaCy/AI)
- `42:topical-map` — AI-generated topic hierarchies (2-5 levels)
- `42:content-repurposer` — 1 content → 10 platform formats
- `42:readability` — Bulk readability scoring (5 metrics)
- `42:audience-angles` — Audience-first content discovery (10 dimensions)
- `42:ecom-taxonomy` — eCommerce category discovery from product inventory
- `42:product-titles` — Product title gap analysis (MPN-matched)
- `42:link-graph` — NetworkX internal link graph with PageRank
- `42:seo-project` — Project lifecycle orchestrator (7 phases, state tracking, multi-site)
- `42:keyword-discovery` — Seed keyword expansion via DataForSEO (suggestions + related, intent, opportunity)

Infrastructure:
- Unified `.env` configuration with auto-loading (`references/load_env.py`)
- Gemini `text-embedding-004` as single embedding provider everywhere
- Shared similarity engine (`references/similarity/`)
- URL slug boost + reverse mapping in keyword-mapper

---

## Project Structure

```
42-seo-skills/
├── manage.sh                          # Install/uninstall/check script
├── CLAUDE.md                          # Architectuur & conventies
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template
├── .gitignore                         # Ignores .env, TODO/, NOSHARE/, __pycache__/
│
├── references/                        # Shared modules
│   ├── load_env.py                    # Auto-load .env into os.environ
│   ├── eeat-scoring-rubric.md         # E-E-A-T scoring (4×25pts)
│   └── similarity/                    # Embedding & similarity engine
│       ├── sf_parser.py               # Parse SF exports (embeddings, internal, GSC)
│       ├── keyword_embedder.py        # Embed keywords via Gemini
│       ├── similarity.py              # Cosine similarity, clustering, URL boost
│       └── requirements.txt           # numpy, scipy, google-generativeai
│
└── skills/                            # All 54 skill directories
    ├── 42-audit/                      # Orchestrator
    │   ├── SKILL.md
    │   ├── requirements.txt
    │   ├── scripts/                   # fetch_page.py, parse_html.py, etc.
    │   ├── references/                # CWV thresholds, E-E-A-T, quality gates
    │   └── schema/                    # JSON-LD templates
    │
    ├── 42-seo-agi/                    # Elite SERP agent
    │   ├── SKILL.md, SPEC.md, CLAUDE.md
    │   ├── scripts/                   # research.py, gsc_pull.py, lib/
    │   ├── tests/                     # test_dataforseo.py, test_env.py
    │   └── references/                # Templates, checklists
    │
    └── 42-[skill-name]/              # 52 more skill directories
        ├── SKILL.md                   # Skill definition (always present)
        └── scripts/                   # Python scripts (where applicable)
```

---

## License

MIT

---

## Contributing

Skills zijn Markdown bestanden met YAML frontmatter. Nieuwe skills toevoegen:

1. Maak een directory `42-[naam]/`
2. Schrijf `SKILL.md` met frontmatter: `name`, `description`, `version`, `tags`, `allowed-tools`, `metadata`
3. Voeg Python scripts toe in `scripts/` als nodig
4. Update deze README
5. Test: `python3 -c "import ast; ast.parse(open('42-[naam]/scripts/[script].py').read())"`
