# Screaming Frog Export Tabs Reference

> Volledige referentie van beschikbare export tabs in Screaming Frog SEO Spider.
> 601 van 628 tabs zijn volledig gemapped. Gebruik met `/42:screaming-frog export <url> --tab "<tab:filter>"`.

---

## Tab Syntax

```
--export-tabs "TabName:Filter"
--export-tabs "Tab1:Filter1,Tab2:Filter2"   # meerdere tabs
--bulk-export "All"                          # alle tabs tegelijk
```

---

## Interne Pagina's

| Tab | Filter | Beschrijving | Typisch gebruik |
|-----|--------|-------------|----------------|
| Internal | All | Alle interne URLs met metadata | Basis crawl overzicht |
| Internal | HTML | Alleen HTML pagina's | Content analyse |
| Internal | JavaScript | JS bestanden | Performance audit |
| Internal | CSS | Stylesheets | Performance audit |
| Internal | Images | Interne afbeeldingen | Image audit |
| Internal | PDF | PDF documenten | Content inventaris |
| Internal | Flash | Flash content | Legacy detectie |
| Internal | Other | Overige resource types | Inventaris |
| Internal | Non-Indexable | Pagina's die niet geïndexeerd worden | Indexability audit |
| Internal | Indexable | Pagina's die wel geïndexeerd worden | Content scope |

## Response Codes

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Response Codes | All | Alle URLs met status codes |
| Response Codes | Success (2xx) | Succesvolle responses |
| Response Codes | Redirection (3xx) | Alle redirects |
| Response Codes | Redirection (301) | Permanente redirects |
| Response Codes | Redirection (302) | Tijdelijke redirects |
| Response Codes | Client Error (4xx) | Client errors (404 etc.) |
| Response Codes | Server Error (5xx) | Server errors |
| Response Codes | No Response | Timeout / geen response |
| Response Codes | Blocked by Robots.txt | Geblokkeerd door robots.txt |
| Response Codes | Blocked Resource | Andere blokkering |

## Page Titles

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Page Titles | All | Alle titels met lengte |
| Page Titles | Missing | Pagina's zonder title tag |
| Page Titles | Duplicate | Identieke titels op meerdere pagina's |
| Page Titles | Over 60 Characters | Te lange titels (afgekapt in SERP) |
| Page Titles | Below 30 Characters | Te korte titels |
| Page Titles | Over 568 Pixels | Te breed in SERP (pixel-based) |
| Page Titles | Same as H1 | Title identiek aan H1 |
| Page Titles | Multiple | Meerdere title tags op één pagina |

## Meta Description

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Meta Description | All | Alle meta descriptions |
| Meta Description | Missing | Pagina's zonder meta description |
| Meta Description | Duplicate | Identieke descriptions |
| Meta Description | Over 155 Characters | Te lang |
| Meta Description | Below 70 Characters | Te kort |
| Meta Description | Over 990 Pixels | Te breed (pixel-based) |
| Meta Description | Multiple | Meerdere meta descriptions |

## Meta Keywords

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Meta Keywords | All | Alle meta keywords (grotendeels nutteloos voor SEO) |
| Meta Keywords | Missing | Geen meta keywords |

## Headings (H1, H2)

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| H1 | All | Alle H1 tags |
| H1 | Missing | Pagina's zonder H1 |
| H1 | Duplicate | Identieke H1 tags |
| H1 | Over 70 Characters | Te lange H1 |
| H1 | Multiple | Meerdere H1 tags op één pagina |
| H2 | All | Alle H2 tags |
| H2 | Missing | Pagina's zonder H2 |
| H2 | Duplicate | Identieke H2 tags |
| H2 | Multiple | Meerdere identieke H2 tags |

## Images

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Images | All | Alle afbeeldingen |
| Images | Missing Alt Text | Zonder alt attribut |
| Images | Missing Alt Attribute | Alt attribut helemaal afwezig |
| Images | Alt Text Over 100 Characters | Te lange alt text |
| Images | Over 100KB | Grote afbeeldingen (performance) |
| Images | Over 200KB | Zeer grote afbeeldingen |

## Canonicals

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Canonicals | All | Alle canonical tags |
| Canonicals | Self Referencing | Canonical wijst naar zichzelf (correct) |
| Canonicals | Canonicalised | Canonical wijst naar andere URL |
| Canonicals | Missing | Geen canonical tag |
| Canonicals | Non-Indexable Canonical | Canonical wijst naar niet-indexeerbare URL |

## Directives

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Directives | All | Alle robots directives |
| Directives | Index | Pagina's met index directive |
| Directives | Noindex | Pagina's met noindex |
| Directives | Follow | Pagina's met follow |
| Directives | Nofollow | Pagina's met nofollow |
| Directives | None | Geen directive |
| Directives | NoArchive | noarchive directive |
| Directives | NoSnippet | nosnippet directive |

## Hreflang

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Hreflang | All | Alle hreflang annotations |
| Hreflang | Contains Hreflang | Pagina's met hreflang |
| Hreflang | Non-200 Hreflang URLs | Hreflang naar niet-2xx pagina's |
| Hreflang | Unlinked Hreflang URLs | Geen return tag gevonden |
| Hreflang | Missing Self Reference | Geen self-referencing hreflang |
| Hreflang | Not Using Canonical | Hreflang conflict met canonical |
| Hreflang | Missing X-Default | Geen x-default tag |
| Hreflang | Inconsistent Language | Taalcode mismatch |

## Structured Data

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Structured Data | All | Alle structured data |
| Structured Data | Contains Structured Data | Pagina's met schema |
| Structured Data | Missing Structured Data | Pagina's zonder schema |
| Structured Data | Validation Errors | Schema met validatie-fouten |
| Structured Data | Validation Warnings | Schema met waarschuwingen |
| Structured Data | JSON-LD | Alleen JSON-LD |
| Structured Data | Microdata | Alleen Microdata |
| Structured Data | RDFa | Alleen RDFa |

## Sitemaps

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Sitemaps | All | Alle sitemap-gerelateerde data |
| Sitemaps | URLs in Sitemap | Pagina's die in sitemap staan |
| Sitemaps | URLs Not in Sitemap | Pagina's die NIET in sitemap staan |
| Sitemaps | Orphan URLs | In sitemap maar niet gecrawld |
| Sitemaps | Non-Indexable URLs in Sitemap | Niet-indexeerbaar maar wel in sitemap |

## Links

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Inlinks | All | Alle interne links (naar pagina X) |
| Outlinks | All | Alle uitgaande links (van pagina X) |
| External | All | Alle externe links |
| External | Broken (4xx) | Kapotte externe links |
| External | Server Error (5xx) | Externe server errors |

## Content

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Content | All | Content metrics per pagina |
| Content | Near Duplicates | Bijna-identieke pagina's |
| Content | Exact Duplicates | Volledig identieke pagina's |
| Content | Low Content Pages | Pagina's met weinig content |
| Content | Readability | Readability scores |

## Page Speed

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Page Speed | All | Speed metrics per pagina |
| Page Speed | Slow (Over 1s) | Langzame pagina's |
| Page Speed | Contains Render Blocking | Render-blocking resources |

## Security

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Security | All | Alle security checks |
| Security | HTTP URLs | Onveilige HTTP pagina's |
| Security | Mixed Content | HTTPS pagina met HTTP resources |
| Security | Missing HSTS | Ontbrekende HSTS header |
| Security | Form Not Secure | Formulieren over HTTP |

## AMP

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| AMP | All | Alle AMP pagina's |
| AMP | Non-200 AMP URLs | AMP errors |
| AMP | Missing Canonical | AMP zonder canonical naar non-AMP |

## Custom (gebruiker-gedefinieerd)

| Tab | Filter | Beschrijving |
|-----|--------|-------------|
| Custom Extraction | All | Custom regex/XPath extracties |
| Custom Search | All | Custom zoekresultaten |
| Custom JavaScript | All | Custom JS extracties |

---

## Bulk Export Profielen

### Kitchen Sink — Alle Tabs

Gebruik `--bulk-export "All"` voor een volledige export van alle bovenstaande tabs.

**Let op:** Dit genereert tientallen CSV-bestanden. Gebruik voor specifieke analyses liever individuele tabs.

### Aanbevolen Export Sets per Use Case

**Quick Health Check:**
```
"Internal:All,Response Codes:Client Error (4xx),Response Codes:Server Error (5xx),Page Titles:Missing,Meta Description:Missing,H1:Missing"
```

**Technical Audit:**
```
"Internal:All,Internal:Non-Indexable,Response Codes:All,Canonicals:All,Directives:All,Sitemaps:All,Security:All,Structured Data:All"
```

**Content Audit:**
```
"Internal:HTML,Page Titles:All,Page Titles:Duplicate,Meta Description:All,H1:All,H2:All,Content:All,Content:Near Duplicates"
```

**Link Audit:**
```
"Inlinks:All,Outlinks:All,External:All,External:Broken (4xx),Response Codes:Redirection (3xx)"
```

**Image Audit:**
```
"Images:All,Images:Missing Alt Text,Images:Over 100KB"
```

**International SEO:**
```
"Hreflang:All,Hreflang:Unlinked Hreflang URLs,Hreflang:Missing X-Default"
```
