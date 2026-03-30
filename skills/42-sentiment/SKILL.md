---
name: 42-sentiment
description: >
  Ad-hoc sentiment analysis van online bronnen. Crawlt Reddit, nieuwssites, forums,
  review sites en social media (via workaround) met Firecrawl. Geeft sentiment scores,
  topics, emoties en concrete citaten met bronlinks.
  Gebruik: /sentiment <query> [--period 1y] [--sources reddit,news] [--depth normaal] [--lang nl]
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Sentiment42

Analyseer online sentiment over elk onderwerp door meerdere bronnen te crawlen met Firecrawl CLI.

## 1. Argument Parsing

Parse the user's input from `$ARGUMENTS`:

1. **Extract the search query:** Everything before the first `--` flag is the search query. Trim whitespace.

2. **Extract flags with defaults:**

   | Flag | Values | Default | Description |
   |------|--------|---------|-------------|
   | `--period` | `5y`, `3y`, `1y`, `3m`, `1m` | `1y` | Tijdsframe voor resultaten |
   | `--sources` | Comma-separated: `reddit`, `news`, `forums`, `reviews`, `social` | all | Welke bronnen crawlen |
   | `--depth` | `snel`, `normaal`, `diep` | `normaal` | Crawl diepte |
   | `--lang` | `nl`, `en` | `nl` | Taal van output |
   | `--compare` | Any value | _(none)_ | Vergelijkingsmodus (Phase 4) |
   | `--help` | _(none)_ | _(none)_ | Toon hulptekst en stop |

3. **Handle `--help`:** If present, print the following and stop:

   ```
   Sentiment42 — Online sentiment analyse via Firecrawl

   Gebruik:
     /sentiment <zoekopdracht> [opties]

   Opties:
     --period <periode>    Tijdsframe voor resultaten
                           5y | 3y | 1y (standaard) | 3m | 1m

     --sources <bronnen>   Welke bronnen crawlen (kommagescheiden)
                           reddit | news | forums | reviews | social
                           Standaard: alles

     --depth <diepte>      Crawl diepte (meer = meer credits)
                           snel (~25 credits) | normaal (~50, standaard) | diep (~80)

     --lang <taal>         Taal van de output
                           nl (standaard) | en

     --compare <query>     Vergelijkingsmodus (nog niet beschikbaar)

     --help                Toon deze hulptekst

   Voorbeelden:
     /sentiment Tesla --period 3m --depth snel
     /sentiment "iPhone 16" --sources reddit,news --lang en
     /sentiment bol.com --period 1y --sources reddit,reviews
     /sentiment Coolblue vs bol.com --depth diep

   Output:
     • Chat samenvatting met sentiment scores, emoties en topics
     • HTML rapport (geopend in browser) met interactieve charts
     • Markdown rapport voor archivering
     Bestanden in: ~/sentiment-reports/
   ```

4. **Handle `--compare`:** If present, print the following and stop:
   - NL: "Vergelijkingsmodus is nog niet beschikbaar. Dit wordt toegevoegd in een toekomstige update."
   - EN: "Comparison mode is not yet available. This will be added in a future update."

4. **Map depth to result limits:**
   - `snel` -> primary=10, secondary=10
   - `normaal` -> primary=30, secondary=10
   - `diep` -> primary=50, secondary=10

5. **Generate query slug:** Lowercase the query, replace spaces with hyphens, remove special characters, truncate to 30 characters. Example: "Tesla Model Y reviews" -> `tesla-model-y-reviews`

6. **Map period to `--tbs` flag:**
   - `1m` -> `--tbs qdr:m`
   - `3m` -> `--tbs qdr:m3`
   - `1y` -> `--tbs qdr:y`
   - `3y` or `5y` -> no `--tbs` flag (filter in post-processing)

7. **Validate:** If the query is empty, show usage example and stop:
   ```
   Gebruik: /sentiment <zoekopdracht> [opties]

   Voorbeeld:
     /sentiment Tesla Model Y --period 3m --sources reddit,news
     /sentiment "iPhone 16 review" --depth diep --lang en

   Opties:
     --period   Tijdsframe: 5y, 3y, 1y (standaard), 3m, 1m
     --sources  Bronnen: reddit, news, forums, reviews, social (standaard: alles)
     --depth    Diepte: snel, normaal (standaard), diep
     --lang     Taal: nl (standaard), en
     --compare  Vergelijking (nog niet beschikbaar)
   ```

## 2. Prerequisites Check

Before starting the crawl:

1. **Check Firecrawl CLI:** Run `firecrawl --status` via Bash.
   - If the command succeeds: continue.
   - If "command not found": Run `npm install -g firecrawl-cli`, then `firecrawl login --browser` and ask the user to authenticate in the browser. After authentication, run `firecrawl --status` again to confirm.
   - If authentication error: Run `firecrawl login --browser` and ask the user to authenticate.
   - **PATH note:** If installed via npm global, firecrawl may be at `~/.npm-global/bin/firecrawl`. Ensure this is on PATH or use the full path.

2. **Create output directory:**
   ```bash
   mkdir -p .firecrawl/sentiment/{slug}
   ```

3. **Print start message:**
   - NL: `Sentiment analyse gestart voor: "{query}"`
   - EN: `Sentiment analysis started for: "{query}"`
   - Print settings: `Periode: {period} | Diepte: {depth} | Bronnen: {sources}`

## 3. Crawl Orchestration

Load the source strategies reference for detailed per-source commands:

```
Read ~/.claude/skills/sentiment42/references/source-strategies.md
```

### Determine Sources to Crawl

Based on the `--sources` flag, determine which sources to include:

| `--sources` value | Sources included |
|-------------------|-----------------|
| `all` (default) | Reddit, News, HN, Quora, niche forums, review sites, X/Twitter, LinkedIn |
| `reddit` | Reddit only |
| `news` | News only |
| `forums` | HN, Quora, niche forums |
| `reviews` | Review sites (Trustpilot + topic-relevant) |
| `social` | X/Twitter, LinkedIn |

Multiple values can be combined: `--sources reddit,news,forums`

### Select Topic-Specific Sources

Before crawling, determine topic-relevant sources:

- **Niche forums:** Based on the query topic, identify 0-2 relevant specialized forums. Consult the forum examples in source-strategies.md. Only add forums that are genuinely relevant to the topic. If unsure, skip niche forums.

- **Review sites:** Always include Trustpilot. Add 1-2 more review sites relevant to the topic type (consumer products -> Amazon; SaaS -> G2, Capterra; restaurants -> Yelp; etc.). Consult the review site mapping in source-strategies.md.

### Execute Crawls in Priority Groups

Execute sources in three priority groups, reporting status between each group. Use the exact command templates from source-strategies.md, substituting the query, depth, slug, and tbs flag.

**IMPORTANT CONSTRAINTS:**
- ALWAYS use unique output filenames per source (prevent file collisions in parallel execution)
- ALWAYS include the `--tbs` flag when period is 1y or less
- NEVER hardcode forum or review site lists -- determine relevant ones per topic
- ALWAYS report source failures gracefully -- never crash on a single source failure

#### Group 1: Reddit + News (high priority)

Run Reddit and News crawl commands in parallel using `&` and `wait`.

After both complete, for each source:
- Check if output file exists (Firecrawl does NOT create the file when 0 results are found)
- Count results using the correct JSON path per source type:
  - Reddit: `jq '.data.web | length' {output_file} 2>/dev/null || echo 0`
  - News: `jq '.data.news | length' {output_file} 2>/dev/null || echo 0` (News uses `data.news[]` not `data.web[]`)
- Print status line:
  - NL: `Crawling Reddit...        ✓ {N} resultaten` or `✗ Mislukt`
  - EN: `Crawling Reddit...        ✓ {N} results` or `✗ Failed`

#### Group 2: Forums (HN, Quora, niche forums)

Run all forum crawl commands in parallel.

After all complete, print status per forum source.

#### Group 3: Review Sites + Social (X/Twitter, LinkedIn)

Run all review site and social crawl commands in parallel.

After all complete, print status per source. For X/Twitter and LinkedIn, always note the workaround limitation:
- NL: `⚠ {N} resultaten (beperkt -- via zoekmachine workaround)`
- EN: `⚠ {N} results (limited -- via search engine workaround)`

### Track Results

After all groups complete, build a results tracker:
```
source_results = {
  "reddit": { "success": true/false, "count": N, "file": "path" },
  "news": { ... },
  "hn": { ... },
  ...
}
```

Count total sources attempted, succeeded, and failed.

## 4. Result Processing

Load the data model reference:

```
Read ~/.claude/skills/sentiment42/references/data-model.md
```

### Normalize Results

For each successful source:
1. Read the output JSON file (if the file does not exist, the source returned 0 results -- skip it)
2. Extract items from the correct array based on source type:
   - **News** (when using `--sources news`): items are in `data.news[]` with fields: `title`, `url`, `snippet`, `date`, `imageUrl`, `position`
   - **All other sources**: items are in `data.web[]` with fields: `title`, `url`, `description`, `markdown` (if `--scrape` was used)
3. Map each item to a CrawledItem (following the normalization rules in data-model.md):
   - Set `source` and `source_label` based on which crawl produced this result
   - Map `url`, `title`
   - Map `content` from: `markdown` (if available and non-empty) > `snippet` (news) > `description` (web)
   - Extract `date`: News items have a `date` field directly (e.g., "4 weeks ago", "Jul 23, 2025"). For other sources, follow the date extraction priority in data-model.md.
   - Set `relevance` based on query match quality
   - Set source-specific `metadata` fields
4. Truncate `content` to ~1000 words per item (especially important for HN scraped results which can be 100K+ chars)

### Deduplicate

Apply deduplication following the strategy in data-model.md:
1. **URL-based:** Normalize URLs (strip tracking params, trailing slashes, www prefix), keep first occurrence from higher-priority source
2. **Title similarity:** For items with different URLs but >80% word overlap in titles, keep the one with more content

### Filter by Time Period

If `--period` is 3y or 5y (where `--tbs` was not used):
- Filter out items with `date` outside the requested period
- Keep items with `date_confidence: "unknown"` (benefit of the doubt)

### Assess Relevance

For each normalized item, assign relevance:
- **high**: Title or content directly addresses the query. Contains substantive discussion or opinion.
- **medium**: Related but tangential. Mentions the topic alongside other subjects.
- **low**: Only peripherally related. Query terms appear but content is about something else.

## 5. Graceful Degradation (CRAWL-06)

After processing, check source coverage:

1. **Count successful sources:** How many distinct sources returned at least 1 result?

2. **Minimum source check:** If fewer than 3 sources succeeded:
   - NL: "Te weinig bronnen beschikbaar voor een betrouwbare analyse. Slechts {N}/7 bronnen gaven resultaten. Probeer een breder onderwerp of andere zoektermen."
   - EN: "Too few sources available for a reliable analysis. Only {N}/7 sources returned results. Try a broader topic or different search terms."
   - **Stop execution.** Do not proceed to analysis.

3. **Limited source marking:** If a source returned fewer than 5 results, mark it as "beperkt" (limited) with ⚠ in the coverage summary.

4. **Always show coverage summary** using the format from data-model.md:

   NL example:
   ```
   Bronnen Overzicht:
     Reddit:        ✓ 23 resultaten
     Nieuws:        ✓ 30 resultaten
     Hacker News:   ✓ 8 resultaten
     Quora:         ✗ Geen resultaten gevonden
     Trustpilot:    ✓ 12 resultaten
     X/Twitter:     ⚠ 3 resultaten (beperkt -- via zoekmachine workaround)
     LinkedIn:      ✗ Geblokkeerd

     Totaal: 76 resultaten uit 4/7 bronnen
     Na deduplicatie: 68 unieke resultaten
   ```

## 5.5 Sentiment Analysis

After result processing (step 4) produces the normalized CrawledItem array, perform the sentiment analysis.

### 1. Load Analysis Schema

```
Read ~/.claude/skills/sentiment42/references/analysis-schema.md
```

Use the AnalysisResult schema to structure all analysis output.

### 2. Content Budget Check

Count total words across all normalized CrawledItems:

- If total > 80,000 words: drop items with `relevance: "low"` first
- If still > 80,000 words: drop items with `relevance: "medium"` (keep `"high"` only)
- Log how many items were dropped:
  - NL: `Context budget: {N} items verwijderd ({reason}) om binnen de analyselimiet te blijven.`
  - EN: `Context budget: {N} items removed ({reason}) to stay within analysis limit.`

### 3. Perform Analysis

Analyze all remaining CrawledItems following the AnalysisResult schema:

**a. Score sentiment per source**
- Group items by `source`
- For each source group, assess overall positive/negative/neutral percentages
- Assign per-source confidence based on item count and content quality (see analysis-schema.md)

**b. Calculate overall sentiment**
- Use weighted aggregation: equal base weight per source, confidence multiplier (high=1.0, medium=0.7, low=0.4)
- Round to whole percentages; adjust largest category if sum is not exactly 100%

**c. Extract topics and group into themes**
- Extract 8-15 specific, concrete topics from the source content
  - GOOD: "Batterijdegradatie na 2 jaar", "Autopilot false braking incidents"
  - BAD: "Productkwaliteit", "Klantenservice" (too generic)
- Topics must reference specific aspects actually discussed in the sources
- Group topics into 3-5 broader themes
- Rank topics by prevalence within each theme

**d. For each topic, produce:**
- **Sentiment percentages** (positive/negative/neutral, must sum to 100%)
- **Explanation** (analytical, neutral tone, research-report style):
  - Major topics: 4-6 sentences
  - Minor topics: 2-3 sentences
- **Dominant emotions** (top 1-2 emotions detected for this topic)
- **Per-source sentiment lean** (only sources with data on this topic): "positive", "negative", "neutral", or "mixed"
- **Quotes** (2-3 representative quotes):
  - Verbatim from CrawledItem `content` -- do NOT paraphrase
  - 1-2 sentences each, short and punchy
  - Include `source_label` and `url` directly from the CrawledItem
- **Sarcasm note** (string or null): only when sarcasm is prevalent in this topic's discussion, especially in Reddit/forum content. Example: "Reddit-discussies gebruiken vaak sarcasme bij dit onderwerp, wat het werkelijke sentiment positiever maakt dan de letterlijke tekst suggereert."

**e. Account for sarcasm in scoring**
- Internally detect sarcasm when scoring sentiment (especially Reddit and forum content)
- Adjust sentiment scores to reflect the intended meaning, not the literal text
- Add `sarcasm_note` to a topic ONLY when sarcasm is prevalent in that topic's discussion

**f. Build overall emotion profile**
- 5 core emotions (always present): trust, frustration, excitement, disappointment, concern
- 2-3 dynamic context-specific emotions (e.g., humor, outrage, hope, nostalgia)
- All percentages (core + dynamic) MUST sum to exactly 100%
- Use localized labels (see analysis-schema.md Language Rules)

**g. Assess confidence levels**
- Per source: based on item count and content quality
- Overall: based on total sources, total items, and source agreement (see analysis-schema.md)

**h. Write executive summary**
- 3-5 sentences, narrative style with key numbers embedded
- Written in `{lang}`
- Include: overall sentiment direction and percentage, top topics with their sentiment, source count

### Critical Instructions

- All text output (executive summary, topic explanations, emotion labels, theme names, topic names) MUST be in `{lang}`. Quotes stay in their **original language**.
- All percentage splits MUST sum to exactly 100%. Round to whole percentages and adjust the largest category if needed.
- Quotes must be **verbatim** from CrawledItem content -- do not paraphrase. Include the exact `url` and `source_label` from the CrawledItem.
- Topics must be **specific and concrete**, not generic categories. They should reference specific aspects mentioned in the source content.

### 4. Verify Consistency

Before proceeding, self-check the AnalysisResult:

| Check | Rule |
|-------|------|
| Overall sentiment | positive + negative + neutral = 100% |
| Per-source sentiment | Each source: positive + negative + neutral = 100% |
| Per-topic sentiment | Each topic: positive + negative + neutral = 100% |
| Emotion profile | All core + dynamic percentages = 100% |
| Topic count | 8-15 total across all themes |
| Theme count | 3-5 themes |
| Topics per theme | 2-5 per theme |
| Quote URLs | Every quote has a valid URL from a CrawledItem |
| Executive summary | 3-5 sentences |
| Dynamic emotions | 2-3 context-specific emotions |

If any check fails: fix it before proceeding.

### 5. Hold AnalysisResult in Memory

Keep the complete AnalysisResult in working memory for report generation (Phase 3). Do NOT write it to a file -- analysis and report generation happen in the same skill invocation.

## 6. Output

After analysis, print the following to chat:

### 1. Executive Summary

Print the `executive_summary` from the AnalysisResult.

### 2. Source Coverage Summary

Print the source coverage summary (already produced in Section 5).

### 3. Per-Source Sentiment Overview

For each source in `per_source_sentiment`, print a one-line summary:

```
  Reddit:        62% positief / 25% negatief / 13% neutraal (23 items)
  Nieuws:        48% positief / 32% negatief / 20% neutraal (30 items)
  Hacker News:   35% positief / 45% negatief / 20% neutraal (8 items)
```

English variant:
```
  Reddit:        62% positive / 25% negative / 13% neutral (23 items)
  News:          48% positive / 32% negative / 20% neutral (30 items)
  Hacker News:   35% positive / 45% negative / 20% neutral (8 items)
```

### 4. Emotion Profile Highlights

Print the top 3 emotions with percentages:

- NL: `Dominante emoties: Vertrouwen (28%), Enthousiasme (22%), Frustratie (18%)`
- EN: `Dominant emotions: Trust (28%), Excitement (22%), Frustration (18%)`

### 5. Topics and Themes Summary

Print the number of themes and topics found:

- NL: `{N} thema's met {M} topics geidentificeerd.`
- EN: `{N} themes with {M} topics identified.`

### 6. Generate Reports

After printing the chat summary, generate the full reports:

**a. Write AnalysisResult to temporary JSON file:**

Write the complete AnalysisResult (the structured data from Section 5.5, NOT the chat summary text) as JSON to a temporary file:
```
/tmp/sentiment42-{slug}-analysis.json
```
Ensure all fields from analysis-schema.md are included. Use the same slug used for crawl directories.

**b. Run the report generation script:**

```bash
python3 ~/.claude/skills/sentiment42/references/report-template.py \
  --brand-dir "$(pwd)/brand-assets" \
  --output-dir ~/sentiment-reports \
  < /tmp/sentiment42-{slug}-analysis.json
```

Note: The `--brand-dir` path must point to the sentiment42 project directory's `brand-assets/` folder. Use the working directory if available, otherwise use the absolute path where `brand-assets/` is located.

**c. Capture output file paths** from stdout (one path per line).

**d. Delete the temporary JSON file:**

```bash
rm /tmp/sentiment42-{slug}-analysis.json
```

**e. Open the HTML report in the browser:**

```bash
open ~/sentiment-reports/{slug}-{datum}.html
```

**f. Report to the user:**

- NL: "Rapporten gegenereerd:\n  Markdown: ~/sentiment-reports/{slug}-{datum}.md\n  HTML: ~/sentiment-reports/{slug}-{datum}.html (geopend in browser)"
- EN: "Reports generated:\n  Markdown: ~/sentiment-reports/{slug}-{datum}.md\n  HTML: ~/sentiment-reports/{slug}-{datum}.html (opened in browser)"

**Error handling:** If the Python script fails (non-zero exit code), print the stderr output and fall back to:
- NL: "Rapportgeneratie mislukt. Analyse is wel voltooid -- zie samenvatting hierboven."
- EN: "Report generation failed. Analysis is complete -- see summary above."

## 7. Cleanup

The `.firecrawl/sentiment/{slug}/` directory contains temporary crawl output files. These can be cleaned up after analysis is complete. Do NOT auto-delete -- the user or future analysis phases may need the raw data.

Mention to the user:
- NL: "Ruwe crawl data opgeslagen in `.firecrawl/sentiment/{slug}/`. Kan verwijderd worden na analyse."
- EN: "Raw crawl data saved in `.firecrawl/sentiment/{slug}/`. Can be removed after analysis."
