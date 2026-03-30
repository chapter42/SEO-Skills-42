---
name: 42-screaming-frog
description: >
  Screaming Frog SEO Spider via CLI: crawls starten met profielen, data exporteren,
  en analyseren (broken links, redirects, canonicals, indexability, orphan pages).
  Integreert met 42: skill suite. Use when user says "screaming frog", "crawl",
  "spider", "broken links", "redirect chains", "orphan pages", "SF crawl",
  "site crawl", "technische crawl".
version: 1.0.0
tags: [seo, crawling, screaming-frog, technical-seo, broken-links, redirects, indexability]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*.seospider"
    - "**/spider.config"
    - "**/screaming*"
  bashPattern:
    - "screamingfrog"
    - "screaming.frog"
    - "seospider"
    - "ScreamingFrog"
---

# Screaming Frog SEO Spider — CLI Integration

## Purpose

Screaming Frog SEO Spider is de industriestandaard voor technische SEO crawls. Deze skill stuurt de CLI-versie aan om crawls te starten, data te exporteren, en resultaten te analyseren — zonder de GUI te hoeven openen. Resultaten integreren met de bestaande 42: skill suite.

**Twee interface-opties:**
1. **CLI direct** — Screaming Frog's eigen command-line interface (altijd beschikbaar)
2. **Python API** — `screaming-frog-api` package voor programmatische analyse (optioneel)
3. **MCP server** — `screaming-frog-mcp` voor tool-based access vanuit Claude (optioneel)

---

## Commands

```
/42:screaming-frog check                          # Installatie + licentie verificatie
/42:screaming-frog crawl <url>                     # Start headless crawl
/42:screaming-frog crawl <url> --profile <name>    # Crawl met specifiek profiel
/42:screaming-frog crawl <url> --sitemap           # Crawl via sitemap
/42:screaming-frog status <url>                    # Crawl voortgang checken
/42:screaming-frog list                            # Alle opgeslagen crawls tonen
/42:screaming-frog export <url> --tab <tab>        # Export specifieke tab als CSV
/42:screaming-frog export <url> --bulk             # Export alle tabs (kitchen sink)
/42:screaming-frog read <file> [--columns a,b,c] [--limit N]  # CSV data lezen
/42:screaming-frog analyze <url|file>              # Volledige analyse met rapporten
/42:screaming-frog compare <crawl1> <crawl2>       # Vergelijk twee crawls (delta)
/42:screaming-frog delete <url>                    # Crawl data verwijderen
/42:screaming-frog storage                         # Disk usage overzicht
```

---

## Part 1: Prerequisites & Installation

### Screaming Frog SEO Spider

- **Versie:** v16+ vereist (getest met v23.x)
- **Licentie:** Free versie beperkt tot 500 URLs. Betaalde licentie nodig voor volledige crawls.
- **Download:** https://www.screamingfrog.co.uk/seo-spider/

### CLI Executable Locaties

| OS | Default pad |
|----|-------------|
| **macOS** | `/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher` |
| **Linux** | `/usr/bin/screamingfrogseospider` |
| **Windows** | `C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe` |

**Override:** Stel `SF_CLI_PATH` environment variable in als de installatie op een custom locatie staat.

```bash
export SF_CLI_PATH="/custom/path/to/ScreamingFrogSEOSpiderLauncher"
```

### Pre-flight Check (`/42:screaming-frog check`)

Voer altijd uit voordat je begint:

```bash
# 1. Check of SF geinstalleerd is
SF_CLI="${SF_CLI_PATH:-/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher}"
if [ ! -f "$SF_CLI" ]; then
    echo "ERROR: Screaming Frog niet gevonden op $SF_CLI"
    echo "Installeer via https://www.screamingfrog.co.uk/seo-spider/"
    echo "Of stel SF_CLI_PATH in: export SF_CLI_PATH=/pad/naar/executable"
    exit 1
fi

# 2. Check versie
"$SF_CLI" --version 2>/dev/null || echo "WARN: Versie check gefaald — mogelijk GUI lock"

# 3. Check of GUI draait (database lock)
if pgrep -f "ScreamingFrogSEOSpider" > /dev/null 2>&1; then
    echo "WARNING: Screaming Frog GUI is actief."
    echo "De GUI moet GESLOTEN zijn voordat CLI commands werken."
    echo "De database is single-process — GUI en CLI kunnen niet tegelijk draaien."
fi
```

### Optionele Python Dependencies

```bash
# Voor programmatische analyse (broken links, redirects, etc.)
pip install screaming-frog-api

# Voor MCP server integratie
pip install screaming-frog-mcp
```

**screaming-frog-api dependencies:**
- `duckdb>=1.5.0` — Analytics engine voor crawl data
- `jaydebeapi>=1.2.3` — Java DB connectivity (Derby databases)
- `JPype1>=1.5.0` — Java/Python bridge
- `sf-config-builder>=0.1.6` — Configuration builder

---

## Part 2: Profile Management

### Wat zijn profielen?

Screaming Frog slaat crawl-configuratie op in `.seospider` bestanden. Een profiel bepaalt:
- Welke URLs worden gecrawld (inclusie/exclusie regels)
- Crawl snelheid en limieten
- Welke data wordt verzameld (custom extractions, JavaScript rendering)
- Export instellingen

### Config Locatie

```bash
# Standaard config
~/.ScreamingFrogSEOSpider/spider.config

# Windows
%APPDATA%/ScreamingFrogSEOSpider/spider.config

# Override
export SCREAMINGFROG_SPIDER_CONFIG=/pad/naar/spider.config
```

### Aanbevolen Profielen

Maak deze profielen aan in Screaming Frog GUI en sla ze op als `.seospider` bestanden:

| Profiel | Doel | Key Settings | Integreert met |
|---------|------|-------------|---------------|
| `technical-audit` | Volledige technische crawl | Alle tabs, max 10.000 URLs, JS rendering aan | 42:technical |
| `content-audit` | Content metrics focus | Word count, readability, heading extraction | 42:content |
| `link-audit` | Link structuur analyse | Inlinks, outlinks, anchor text, orphan detection | 42:internal-links |
| `schema-audit` | Structured data validatie | Custom extraction voor JSON-LD, schema types | 42:structured-data |
| `quick-check` | Snelle health check | Max 100 URLs, basis tabs, geen JS rendering | — |
| `full-export` | Alles exporteren | Kitchen sink: alle tabs, alle filters | 42:audit |

### Profiel Laden

```bash
# Crawl met specifiek profiel
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --config "/pad/naar/technical-audit.seospider" \
    --save-crawl \
    --output-folder "/pad/naar/output"
```

### ConfigPatches (Python API)

Voor programmatisch profiel aanpassen via `screaming-frog-api`:

```python
from screamingfrog.config.patches import ConfigPatches

patches = ConfigPatches()

# Custom extraction toevoegen
patches.add_extraction("Price", xpath="//span[@class='price']")

# Custom search toevoegen
patches.add_search("Missing H1", query="<h1", mode="NOT_CONTAINS", scope="HTML")

# JavaScript snippet
patches.add_javascript("Get Schema", script='document.querySelector("script[type=application/ld+json]")?.textContent', timeout=5000)

# Toepassen op config
patches.write("/pad/naar/profiel.seospider")
```

---

## Part 3: Crawling

### Start een Crawl

```bash
SF_CLI="${SF_CLI_PATH:-/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher}"

# Basis headless crawl
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --save-crawl \
    --output-folder "./sf-output" \
    --timestamped-output

# Met profiel
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --config "/pad/naar/technical-audit.seospider" \
    --save-crawl \
    --output-folder "./sf-output"

# Sitemap-based crawl
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --use-sitemap \
    --save-crawl \
    --output-folder "./sf-output"

# Met URL-limiet
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --max-crawl-depth 5 \
    --save-crawl \
    --output-folder "./sf-output"
```

### Crawl Limieten

| Limiet | Waarde | Reden |
|--------|--------|-------|
| Max concurrent crawls | 2 | SF resource-intensief |
| Max URLs (free) | 500 | Licentiebeperking |
| Max URLs (aanbevolen) | 10.000 | Performance |
| Max URLs (hard limit) | 100.000 | Memory/disk |
| Timeout per crawl | 60 min | Voorkom hangende processen |

### GUI Lock Detectie

Screaming Frog's database is **single-process**. De GUI en CLI kunnen NIET tegelijk de database benaderen.

```bash
# Check voor GUI lock
if pgrep -f "ScreamingFrogSEOSpider" > /dev/null 2>&1; then
    echo "ERROR: Screaming Frog GUI is actief."
    echo "Sluit de GUI volledig af voordat je CLI commands uitvoert."
    echo ""
    echo "macOS: Cmd+Q (niet alleen venster sluiten)"
    echo "Windows: Taakbeheer → Screaming Frog → Taak beëindigen"
    echo "Linux: killall screamingfrogseospider"
    exit 1
fi
```

---

## Part 4: Export & Data Access

### Export via CLI

```bash
# Export specifieke tab
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --export-tabs "Internal:All,Response Codes:All" \
    --output-folder "./sf-output"

# Bulk export (alle tabs)
"$SF_CLI" --headless \
    --crawl "https://example.com" \
    --bulk-export "All" \
    --output-folder "./sf-output"
```

### Belangrijkste Export Tabs

| Tab | Filter | Wat het bevat | Gebruik voor |
|-----|--------|-------------|-------------|
| **Internal:All** | Alle interne URLs | URL, status, title, description, H1, word count | Basis overzicht |
| **Internal:HTML** | Alleen HTML pagina's | Idem maar gefilterd op content type | Content analyse |
| **Internal:Non-Indexable** | Niet-indexeerbare pagina's | URLs met noindex, canonical issues, etc. | Indexability audit |
| **Response Codes:All** | Alle status codes | URL, status code, redirect URL | Error detectie |
| **Response Codes:Client Error (4xx)** | 404 etc. | Kapotte pagina's | Broken links |
| **Response Codes:Server Error (5xx)** | 500 etc. | Server problemen | Uptime issues |
| **Response Codes:Redirection (3xx)** | Redirects | Redirect chains | Redirect audit |
| **Page Titles:All** | Alle titels | URL, title, length, pixel width | On-page SEO |
| **Page Titles:Missing** | Ontbrekende titels | URLs zonder title tag | Quick fixes |
| **Page Titles:Duplicate** | Dubbele titels | URLs met dezelfde title | Deduplicatie |
| **Meta Description:All** | Alle descriptions | URL, description, length | On-page SEO |
| **Meta Description:Missing** | Ontbrekend | URLs zonder meta description | Quick fixes |
| **H1:All** | Alle H1 tags | URL, H1 text, count | Heading audit |
| **H1:Missing** | Ontbrekende H1 | URLs zonder H1 | Quick fixes |
| **Images:All** | Alle afbeeldingen | URL, alt text, size, dimensions | Image audit |
| **Images:Missing Alt Text** | Geen alt text | Images zonder alt attribut | Accessibility |
| **Images:Over 100KB** | Grote afbeeldingen | Images die geoptimaliseerd moeten | Performance |
| **Canonicals:All** | Alle canonicals | URL, canonical URL, status | Canonical audit |
| **Canonicals:Non-Indexable** | Problemen | Canonical conflicts | Indexability |
| **Hreflang:All** | Alle hreflang | URL, hreflang tags, validation | i18n audit |
| **Structured Data:All** | Alle schema | URL, schema types, validation | Schema audit |
| **Inlinks:All** | Interne links naar | Source, target, anchor text, type | Link audit |
| **Outlinks:All** | Externe links | Source, target, status, anchor | External links |
| **Sitemaps:All** | Sitemap URLs | URL, in sitemap, indexable | Sitemap audit |

Zie `references/export-tabs.md` voor de volledige lijst met alle 600+ tabs en filters.

### Data Lezen en Filteren

```bash
# Lees CSV export met specifieke kolommen
head -1 sf-output/internal_all.csv  # Bekijk beschikbare kolommen

# Filter op specifieke kolommen
cut -d',' -f1,3,5 sf-output/internal_all.csv | head -20

# Filter op status code
awk -F',' '$3 == "404"' sf-output/response_codes_all.csv

# Tel pagina's per status code
awk -F',' 'NR>1 {count[$3]++} END {for (c in count) print c, count[c]}' sf-output/response_codes_all.csv | sort -k2 -rn
```

**Via Python API (als geïnstalleerd):**

```python
from screamingfrog import Crawl

# Laad crawl data
crawl = Crawl.load("./sf-output")

# Bekijk pagina's
for page in crawl.pages():
    print(page.url, page.status_code, page.title)

# Filter op specifieke tab
for row in crawl.tab("Page Titles:Missing"):
    print(row)

# Custom SQL query
results = crawl.sql("SELECT url, status_code FROM internal WHERE status_code >= 400")
```

---

## Part 5: Analyse

### Ingebouwde Analyse Rapporten (via screaming-frog-api)

Wanneer `screaming-frog-api` is geïnstalleerd, zijn deze analyse-functies beschikbaar:

```python
from screamingfrog import Crawl

crawl = Crawl.load("./sf-output")
```

#### Broken Links Report

```python
report = crawl.broken_links_report()
# Returns: URLs met 4xx/5xx status, inclusief inlink samples
# (welke pagina's linken naar de kapotte URL)
```

**Output:** Lijst van kapotte URLs met:
- Doel-URL en status code
- Bron-pagina's die ernaar linken (inlink samples)
- Anchor text van de kapotte link
- Aanbeveling: redirect, verwijderen, of fixen

#### Indexability Audit

```python
report = crawl.indexability_audit()
# Returns: niet-indexeerbare pagina's met reden
```

**Output:** Pagina's die niet geïndexeerd worden, gegroepeerd op reden:
- `noindex` meta tag
- Canonical wijst naar andere URL
- Robots.txt blocked
- 4xx/5xx status
- Redirect (niet de eindbestemming)

#### Orphan Pages Report

```python
report = crawl.orphan_pages_report()
# Returns: pagina's zonder interne links die ernaar wijzen
```

**Output:** URLs die door geen enkele andere pagina intern gelinkt worden. Dit zijn "onvindbare" pagina's die zelden gecrawld en nooit geciteerd worden.

#### Redirect Chains

```python
report = crawl.redirect_chains(max_hops=3)
# Returns: redirect/canonical chains met hop count
```

**Output:** Chains van A→B→C (of langer), met:
- Volledige chain (alle hops)
- Hop count
- Type per hop (301, 302, canonical, meta refresh)
- Aanbeveling: directe redirect van A→C

#### Security Report

```python
report = crawl.security_report()
# Returns: beveiligingsproblemen
```

**Output:** Mixed content, HTTP pagina's, ontbrekende security headers, onveilige formulieren.

#### Canonical Report

```python
report = crawl.canonical_report()
# Returns: canonical tag problemen
```

**Output:** Self-referencing issues, canonical chains, conflicting canonicals, canonicals naar 4xx pagina's.

#### Hreflang Report

```python
report = crawl.hreflang_report()
# Returns: hreflang fouten
```

**Output:** Ontbrekende return tags, ongeldige language codes, x-default problemen, inconsistenties.

#### Crawl Vergelijking (Delta)

```python
crawl_old = Crawl.load("./sf-output-january")
crawl_new = Crawl.load("./sf-output-february")

diff = crawl_new.compare(crawl_old)
# Returns: CrawlDiff met alle wijzigingen
```

**Output:** `CrawlDiff` object met:
- Nieuwe URLs (toegevoegd sinds vorige crawl)
- Verwijderde URLs
- Status code wijzigingen
- Title/description wijzigingen
- Redirect wijzigingen
- Custom field wijzigingen

---

## Part 6: Workflow — Volledige Analyse

Wanneer de gebruiker `/42:screaming-frog analyze <url>` uitvoert:

### Stap 1: Pre-flight

```bash
# Check installatie
# Check GUI lock
# Check disk space
```

### Stap 2: Crawl

```bash
# Start headless crawl met technical-audit profiel
"$SF_CLI" --headless \
    --crawl "$URL" \
    --config "technical-audit.seospider" \
    --save-crawl \
    --output-folder "./sf-crawl-$(date +%Y%m%d)" \
    --timestamped-output \
    --export-tabs "Internal:All,Response Codes:All,Page Titles:All,Page Titles:Missing,Page Titles:Duplicate,Meta Description:Missing,H1:Missing,Images:Missing Alt Text,Images:Over 100KB,Canonicals:All,Hreflang:All,Structured Data:All,Inlinks:All,Sitemaps:All"
```

### Stap 3: Analyse (als Python API beschikbaar)

```python
from screamingfrog import Crawl

crawl = Crawl.load("./sf-crawl-*")

reports = {
    "broken_links": crawl.broken_links_report(),
    "indexability": crawl.indexability_audit(),
    "orphan_pages": crawl.orphan_pages_report(),
    "redirect_chains": crawl.redirect_chains(),
    "security": crawl.security_report(),
    "canonicals": crawl.canonical_report(),
    "hreflang": crawl.hreflang_report(),
}
```

### Stap 4: Rapport Genereren

Genereer `SF-CRAWL-REPORT.md`:

```markdown
# Screaming Frog Crawl Report — [Domain]
Date: [Date]
URLs Crawled: [Count]
Profile: [Profile Name]

## Summary

| Metric | Count | Status |
|--------|-------|--------|
| Total URLs | [X] | — |
| HTML Pages | [X] | — |
| 2xx Responses | [X] | [%] |
| 3xx Redirects | [X] | [warn if >10%] |
| 4xx Errors | [X] | [critical if >0] |
| 5xx Errors | [X] | [critical if >0] |
| Non-Indexable | [X] | [warn if >20%] |
| Orphan Pages | [X] | [warn if >0] |
| Missing Titles | [X] | [warn if >0] |
| Missing H1 | [X] | [warn if >0] |
| Missing Meta Desc | [X] | [warn if >0] |
| Missing Alt Text | [X] images | [warn if >10%] |
| Redirect Chains | [X] | [warn if >0] |
| Canonical Issues | [X] | [warn if >0] |

## Broken Links (4xx/5xx)
| Broken URL | Status | Linked From | Anchor Text |
|-----------|--------|-------------|-------------|

## Redirect Chains
| Start URL | Hops | End URL | Type |
|-----------|------|---------|------|

## Orphan Pages
| URL | Title | In Sitemap |
|-----|-------|-----------|

## Non-Indexable Pages
| URL | Reason | Recommendation |
|-----|--------|---------------|

## Canonical Issues
| URL | Canonical | Issue |
|-----|-----------|-------|

## Missing On-Page Elements
### Missing Titles
### Missing H1
### Missing Meta Descriptions
### Duplicate Titles

## Images Without Alt Text
| Image URL | Page | Recommendation |
|-----------|------|---------------|

## Prioritized Actions
### Critical (fix immediately)
### High (fix within 1 week)
### Medium (fix within 1 month)
### Low (backlog)
```

---

## Part 7: Integratie met 42: Suite

Screaming Frog crawl data verrijkt andere 42: skills:

| 42: Skill | SF Data Input | Hoe te gebruiken |
|-----------|--------------|-----------------|
| **42:technical** | Response codes, redirects, canonicals, CWV data | SF vindt issues die curl-based checks missen (JS-rendered content, complexe redirects) |
| **42:content** | Word counts, heading extraction, thin content detectie | SF's word count per pagina als input voor content quality assessment |
| **42:structured-data** | Structured Data tab export | SF valideert schema op schaal — resultaten als input voor schema skill |
| **42:internal-links** | Inlinks/Outlinks export | SF's link data voor volledige link graph analyse |
| **42:hreflang** | Hreflang tab export | SF's hreflang validatie als bron voor de hreflang skill |
| **42:sitemap** | Sitemaps tab | Vergelijk sitemap URLs met gecrawlde URLs (coverage gaps) |
| **42:images** | Images tab (missing alt, oversized) | SF's image data voor optimalisatie-aanbevelingen |
| **42:audit** | Volledige crawl data | SF als data-bron voor de unified audit orchestrator |

### Voorbeeld: SF + 42:technical

```bash
# 1. Crawl met SF
/42:screaming-frog crawl https://example.com --profile technical-audit

# 2. Gebruik SF data als input voor technical audit
/42:technical https://example.com
# → De technical skill leest SF CSV exports als aanvulling op eigen checks
```

---

## Part 8: Error Handling

| Situatie | Detectie | Actie |
|----------|----------|-------|
| SF niet geïnstalleerd | CLI executable niet gevonden | Installatie-instructies tonen |
| GUI lock | `pgrep` detecteert draaiend SF proces | Waarschuwing: "Sluit SF GUI" |
| Licentie verlopen/free | Crawl stopt bij 500 URLs | Waarschuwing + adviseer licentie |
| Crawl timeout | Proces draait >60 min | Kill process, rapporteer partial results |
| Disk space vol | `df` check voor crawl | Waarschuwing + `storage` command suggereren |
| Export tab niet gevonden | CLI error op onbekende tab naam | Toon beschikbare tabs uit referentie |
| Python API niet geïnstalleerd | ImportError op `screamingfrog` | Fallback naar CSV parsing, adviseer pip install |
| Database corrupt | Derby/DuckDB read error | Suggereer recrawl |

---

## Part 9: MCP Server Integratie (Optioneel)

Als `screaming-frog-mcp` is geïnstalleerd, zijn deze MCP tools beschikbaar:

| MCP Tool | Equivalent Command | Beschrijving |
|----------|-------------------|-------------|
| `sf_check` | `check` | Installatie + licentie verificatie |
| `crawl_site` | `crawl <url>` | Start headless crawl |
| `crawl_status` | `status <url>` | Voortgang checken |
| `list_crawls` | `list` | Opgeslagen crawls tonen |
| `export_crawl` | `export <url> --tab` | CSV export genereren |
| `read_crawl_data` | `read <file>` | CSV data lezen met filtering |
| `delete_crawl` | `delete <url>` | Crawl data verwijderen |
| `storage_summary` | `storage` | Disk usage |

**MCP installatie:**

```bash
pip install screaming-frog-mcp

# Claude Code configuratie
claude mcp add screaming-frog -- uvx screaming-frog-mcp
```

Wanneer MCP tools beschikbaar zijn, gebruik ze in plaats van directe CLI calls — ze bieden betere error handling en output parsing.

---

## Cross-References

- Voor **volledige technische audit** → `/42:technical` (gebruikt SF data als input)
- Voor **content quality analyse** → `/42:content` (word counts uit SF)
- Voor **schema validatie** → `/42:structured-data` (structured data tab uit SF)
- Voor **link structuur analyse** → `/42:internal-links` (inlinks/outlinks uit SF)
- Voor **international SEO** → `/42:hreflang` (hreflang tab uit SF)
- Voor **image optimalisatie** → `/42:images` (images tab uit SF)
- Voor **sitemap analyse** → `/42:sitemap` (sitemaps tab uit SF)
- Voor **unified audit** → `/42:audit` (SF als data-bron)
