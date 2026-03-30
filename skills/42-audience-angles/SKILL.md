---
name: 42-audience-angles
description: >
  Audience-first content discovery via 10 psychologische dimensies.
  Genereert 50 content angles (5 per dimensie) vanuit het doelgroep-
  perspectief. Drie modes: angles (puur), keywords (+ zoektermen),
  validate (+ DataForSEO zoekvolume). Input: URL, file, of tekst.
  Use when user says "audience angles", "content angles", "doelgroep
  analyse", "buyer intent", "content discovery", "audience research",
  "pijnpunten", "pain points", "content ideeën", "klantinzichten",
  "doelgroep inzichten", "audience mapping", "content inspiratie",
  "wat wil mijn doelgroep", "customer insights", "angle brainstorm".
user-invokable: true
argument-hint: "angles|keywords|validate <url|file|tekst>"
version: 1.0.0
tags: [seo, audience, content-discovery, intent, strategy, angles]
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - WebFetch
  - AskUserQuestion
metadata:
  filePattern:
    - "**/AUDIENCE-ANGLES*.md"
    - "**/audience-angles*.md"
    - "**/content-angles*.md"
  bashPattern:
    - "audience.angle"
    - "content.angle"
    - "doelgroep.analyse"
---

# Audience Angles — Content Discovery via 10 Psychologische Dimensies

## Purpose

Genereer content angles vanuit het perspectief van de doelgroep, niet vanuit
keyword tools. In plaats van "wat zoeken mensen?" beantwoordt deze skill de
vraag "**waarom** zoeken mensen, wat drijft hen, en welke content sluit
daarop aan?"

10 dimensies dekken het volledige spectrum van menselijke motivatie:
vragen, problemen, alternatieven, frustraties, angsten, zorgen, doelen,
mythes, interesses en misverstanden. Per dimensie worden 5 specifieke
content angles gegenereerd — concreet genoeg om er direct een brief van
te maken.

---

## Commands

```
/42:audience-angles angles <url|file|tekst>       # 50 content angles, platte lijst
/42:audience-angles keywords <url|file|tekst>     # Angles + zoektermen + intentie
/42:audience-angles validate <url|file|tekst>     # Angles + keywords + DataForSEO volume
```

---

## Subcommand: `angles`

Genereert 50 content angles (5 per dimensie) zonder keyword-data. Puur
audience-gedreven. Geen API keys nodig.

## Subcommand: `keywords`

Alles van `angles` plus:
- Per angle 2-3 zoektermen (AI-gegenereerd, geen API)
- Zoekintentie-classificatie per angle (informational / commercial / navigational / transactional)

Geen API keys nodig.

## Subcommand: `validate`

Alles van `keywords` plus:
- Maandelijks zoekvolume per zoekterm (DataForSEO)
- Keyword Difficulty score
- Huidige SERP features (featured snippet, PAA, video, etc.)

**Vereist**: `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD` environment variables.

```bash
# DataForSEO configureren (eenmalig)
export DATAFORSEO_LOGIN="your_email"
export DATAFORSEO_PASSWORD="your_api_token"
```

---

## Process

### Step 0: Parse Input

Detect input type:
- **URL** (begint met `http://` of `https://`) — fetch met WebFetch. Extraheer:
  titel, H1, meta description, body content (eerste 2000 woorden), heading
  structuur, product/dienst-indicatoren.
- **File path** (bestand bestaat lokaal) — lees met Read tool. Extraheer dezelfde
  elementen.
- **Plain text** — verwerk direct uit het prompt. Verwacht een beschrijving van
  de niche, het product/de dienst, en de doelgroep.

Auto-detect taal (NL/EN) op basis van de input content.

### Step 1: Niche & Doelgroep Profiel

Destilleer uit de input:

```markdown
**Niche profiel**
- Product/dienst: [wat wordt aangeboden]
- Branche: [sector]
- B2B / B2C: [type]
- Primaire doelgroep: [wie koopt/gebruikt dit]
- Pijnpunt-context: [welk overkoepelend probleem lost dit op]
```

Toon dit profiel aan de gebruiker met de vraag: **"Klopt dit profiel? Wil je
iets aanpassen?"**

Pas aan op basis van feedback voordat je doorgaat.

### Step 2: Genereer 10 Dimensies x 5 Angles

Genereer per dimensie 5 content angles. Elk angle bevat:

| Veld | Beschrijving |
|------|-------------|
| **Angle titel** | Korte beschrijving, max 80 chars |
| **Hook** | 1 zin die de lezer direct aanspreekt |
| **Content format** | Blogpost / FAQ / Vergelijking / Video / How-to / Opinie / Infographic / Case study / Checklist / Interview |

#### De 10 Dimensies

**Q — Vragen**
Algemene vragen die de doelgroep heeft over het product, de dienst, materialen,
werking, onderhoud, of keuzeproces. Dit zijn de "hoe werkt...", "wat is...",
"welke soorten..." vragen.

Richtlijnen:
- Vraag moet vanuit een niet-expert komen
- Antwoord moet substantieel zijn (niet 1 zin)
- Varieer: 1x definitie, 1x werking, 1x keuze, 1x onderhoud, 1x proces

**P — Problemen**
Concrete, specifieke problemen die de doelgroep ervaart en waarvoor ze een
oplossing zoeken. Niet "ik wil iets kopen" maar "ik heb een probleem en
zoek een oplossing."

Richtlijnen:
- Probleem moet herkenbaar en urgent zijn
- Moet oplosbaar zijn (met of zonder het product)
- Varieer: technisch probleem, gebruiksprobleem, keuzeprobleem, tijdsprobleem, budgetprobleem

**A — Alternatieven**
Vergelijkingen en keuzes waar de doelgroep voor staat. X vs Y, merk A vs merk B,
methode 1 vs methode 2.

Richtlijnen:
- Vergelijking moet eerlijk en informatief zijn
- Beide opties moeten realistisch zijn (geen stroman)
- Varieer: product vs product, methode vs methode, DIY vs professional, goedkoop vs duur, oud vs nieuw

**F — Frustraties**
Irritaties en onopgeloste issues die de doelgroep dagelijks ervaart. De "waarom
werkt dit niet?!" en "dit zou toch beter moeten kunnen" momenten.

Richtlijnen:
- Frustratie moet echt en herkenbaar zijn
- Content moet erkenning + oplossing bieden
- Varieer: productfrustratie, procesfrustratie, informatiefrustratie, servicefrustratie, prijsfrustratie

**F — Angsten**
Onderliggende zorgen en angsten die mensen tegenhouden bij een aankoop of
beslissing. De "wat als..." scenario's.

Richtlijnen:
- Angst moet psychologisch reëel zijn (niet overdreven)
- Content moet geruststellen met feiten, niet met beloftes
- Varieer: financieel risico, sociaal risico, veiligheidsrisico, kwaliteitsrisico, tijdsrisico

**C — Zorgen**
Urgente zorgen met significante levensimpact. Zwaarder dan frustraties, concreter
dan angsten. De dingen waar mensen wakker van liggen.

Richtlijnen:
- Zorg moet serieus zijn (niet triviaal)
- Content moet empathisch en behulpzaam zijn
- Varieer: gezondheid, financiën, relaties, carrière, veiligheid (afhankelijk van niche)

**G — Doelen**
Aspiraties, mijlpalen en resultaten die de doelgroep wil bereiken. De "ik wil..."
en "hoe kan ik..." gedachten.

Richtlijnen:
- Doel moet haalbaar en meetbaar zijn
- Content moet een pad naar het doel schetsen
- Varieer: korte-termijn doel, lange-termijn doel, vaardigheidsdoel, resultaatdoel, lifestyle-doel

**M — Mythes**
Wijdverbreide misvattingen en onjuiste aannames in de branche die weerlegging
nodig hebben. De "iedereen denkt dat... maar eigenlijk..." momenten.

Richtlijnen:
- Mythe moet daadwerkelijk wijdverbreid zijn
- Weerlegging moet met bewijs komen, niet met mening
- Varieer: productmythe, procesmythe, prijsmythe, gezondheidsmythe, technische mythe

**I — Interesses**
Bredere interesses, trends, nieuws en ontwikkelingen waar de doelgroep om geeft
maar die niet direct over het product gaan. Het "rondom" de aankoop.

Richtlijnen:
- Interest moet relevant zijn voor de doelgroep (niet random)
- Content moet informatief of inspirerend zijn
- Varieer: trend, innovatie, community, lifestyle, achtergrondverhaal

**M — Misverstanden**
Subtiele individuele aannames die niet zozeer "mythes" zijn maar eerder
persoonlijke misinterpretaties of incomplete kennis. De "ja maar ik dacht
dat..." momenten.

Richtlijnen:
- Verschil met Mythes: misverstanden zijn subtieler en persoonlijker
- Content moet educatief zijn zonder neerbuigend te worden
- Varieer: terminologieverwarring, procesaanname, kostenaanname, kwaliteitsaanname, verwachtingsaanname

### Step 3: Output Genereren

Presenteer per dimensie een tabel:

```markdown
## Q — Vragen

| # | Angle | Hook | Format |
|---|-------|------|--------|
| Q1 | [titel] | [hook zin] | Blogpost |
| Q2 | [titel] | [hook zin] | FAQ |
| Q3 | [titel] | [hook zin] | How-to |
| Q4 | [titel] | [hook zin] | Video |
| Q5 | [titel] | [hook zin] | Vergelijking |
```

Na alle 10 dimensies, toon een samenvattingsblok:

```markdown
## Samenvatting

| Dimensie | Angles | Formats |
|----------|--------|---------|
| Q — Vragen | 5 | 2x Blogpost, 1x FAQ, 1x How-to, 1x Video |
| P — Problemen | 5 | ... |
| A — Alternatieven | 5 | ... |
| F — Frustraties | 5 | ... |
| F — Angsten | 5 | ... |
| C — Zorgen | 5 | ... |
| G — Doelen | 5 | ... |
| M — Mythes | 5 | ... |
| I — Interesses | 5 | ... |
| M — Misverstanden | 5 | ... |
| **Totaal** | **50** | |
```

### Step 4: Keywords toevoegen (alleen `keywords` en `validate`)

Voor elke angle, genereer 2-3 zoektermen die iemand met dit angle in Google
zou typen. Classificeer de zoekintentie:

| Intentie | Kenmerk | Voorbeeld |
|----------|---------|-----------|
| Informational | Wil iets weten | "hoe werkt...", "wat is..." |
| Commercial | Vergelijkt opties | "beste...", "X vs Y", "review..." |
| Transactional | Wil iets kopen/doen | "kopen", "bestellen", "aanvragen" |
| Navigational | Zoekt specifieke plek | "merknaam", "product + winkel" |

Extra kolommen in de tabel:

```markdown
| # | Angle | Hook | Format | Zoektermen | Intentie |
|---|-------|------|--------|------------|----------|
| Q1 | [titel] | [hook] | Blogpost | "zoekterm 1", "zoekterm 2" | Informational |
```

### Step 5: DataForSEO validatie (alleen `validate`)

Gebruik het DataForSEO Keywords Data API endpoint om per zoekterm op te halen:
- Maandelijks zoekvolume (gemiddeld 12 maanden)
- Keyword Difficulty (0-100)
- SERP features aanwezig

**API endpoint**: `https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live`

**Request format**:
```json
[{
  "keywords": ["zoekterm 1", "zoekterm 2"],
  "language_code": "nl",
  "location_code": 2528
}]
```

Location codes: Nederland = 2528, België = 2056, VS = 2840, UK = 2826.
Detect locatie op basis van taal en context. Default NL voor Nederlandse content.

Extra kolommen in de tabel:

```markdown
| # | Angle | Hook | Format | Zoektermen | Vol | KD | SERP Features | Intentie |
|---|-------|------|--------|------------|-----|----|--------------|---------|
| Q1 | [titel] | [hook] | Blogpost | "zoekterm 1" | 1.2K | 34 | PAA, Snippet | Informational |
```

Bij ontbrekende API credentials, toon een duidelijke melding:

```
DataForSEO credentials niet gevonden. Stel in:
  export DATAFORSEO_LOGIN="your_email"
  export DATAFORSEO_PASSWORD="your_api_token"

Teruggevallen op 'keywords' mode (zonder volumes).
```

### Step 6: Opslaan

Sla de volledige output op als markdown:

```
output/AUDIENCE-ANGLES-{slug}.md
```

Waarbij `{slug}` wordt afgeleid van:
- URL → domeinnaam + pad fragment (bijv. `example-nl-elektrische-fietsen`)
- Tekst → eerste 3-4 woorden (bijv. `duurzame-mode-vrouwen-25-45`)

---

## Rules

1. **Content-anchored** — Bij URL-input moeten alle angles relevant zijn voor de
   daadwerkelijke content, niche en doelgroep. Geen generieke angles die overal
   op zouden passen.

2. **Geen generieke lijsten** — Elk angle moet specifiek genoeg zijn om er direct
   een contentbrief van te schrijven. "Tips voor betere X" is te generiek.
   "Waarom je wasmachine stinkt na 3 jaar en hoe je het in 20 minuten oplost"
   is specifiek genoeg.

3. **Taal-matching** — Nederlandse input = Nederlandse output. Engelse input =
   Engelse output. Auto-detect op basis van content. Meng geen talen.

4. **Geen overlap** — Alle 50 angles moeten uniek zijn. Geen herhalingen tussen
   dimensies. Als een angle onder zowel Problemen als Frustraties zou passen,
   kies de best passende dimensie en maak het andere angle over iets anders.

5. **Format-variatie** — Verdeel de 50 angles over minstens 6 verschillende
   content formats. Niet alles is een blogpost. Denk aan: FAQ, vergelijking,
   how-to guide, video script, opinie, infographic, case study, checklist,
   interview, tool/calculator.

6. **Specifiek voor de niche** — Gebruik terminologie, merknamen, productnamen
   en scenario's die specifiek zijn voor de niche. Een angle voor een
   loodgieter moet anders klinken dan een angle voor een SaaS-bedrijf.

7. **Hooks zijn geen clickbait** — Elke hook moet een belofte doen die de content
   kan waarmaken. "Je gelooft nooit wat er dan gebeurt" is verboden.
   "Waarom 73% van de installateurs deze fout maakt" is acceptabel (mits het
   getal klopt of duidelijk illustratief is).

---

## Cross-References

- **42:topical-map** — Gebruik angles als input voor topic cluster hiërarchie
- **42:seo-plan** — Angles voeden de content strategie planning
- **42:content** — Beoordeel bestaande content op dekking van de angles
- **42:genai-optimizer** — Herschrijf bestaande content vanuit een specifiek angle
- **42:paa-scraper** — Verdiep de Q-dimensie met PAA-data uit Google
- **42:blog-strategy** — Vertaal angles naar een editorial calendar
- **42:title-optimizer** — Optimaliseer titels voor de gegenereerde content angles
- **42:striking-distance** — Combineer met GSC data: welke angles heb je al (bijna) rankings voor?
