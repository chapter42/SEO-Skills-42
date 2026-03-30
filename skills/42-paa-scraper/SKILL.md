---
name: 42-paa-scraper
description: "Recursively scrape People Also Ask questions up to 5 levels deep plus Related Searches tree. Builds a question tree for FAQ content and featured snippet strategy. Use when user says paa scraper, people also ask, paa tree, question research, faq mining, paa extraction, related searches, question tree, paa depth, 42-paa."
user-invokable: true
argument-hint: "<keyword> [--depth 3] [--related] [--provider dataforseo]"
version: "1.0.0"
tags:
  - seo
  - paa
  - serp
  - content-strategy
  - faq
  - featured-snippets
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
metadata:
  filePattern: "**/*paa*,**/*question*,**/*faq*"
  bashPattern: "python*paa*"
---

# 42 PAA Scraper

Recursively scrape People Also Ask (PAA) questions and Related Searches from Google SERPs. Builds a hierarchical question tree that reveals exactly what users are asking about a topic, enabling FAQ content strategy and featured snippet targeting.

---

## Why PAA Matters

People Also Ask boxes appear on approximately 65% of Google SERPs. Each PAA question, when clicked, reveals more questions -- creating an infinite expansion of user intent signals. By recursively following this tree, you build a complete map of every question Google associates with a topic.

This data directly fuels:
- **FAQ sections** that match exact user questions
- **Featured snippet targeting** (PAA answers are pulled from featured snippets)
- **Content gap discovery** (questions your site does not answer)
- **Topical authority planning** (breadth of questions reveals topic scope)
- **AI citation optimization** (question-answer pairs are the format AI models prefer to cite)

---

## Commands

```
/42:paa-scraper <keyword> [--depth 3] [--related] [--depth 3] [--related]
/42:paa-scraper <csv-file> [--depth 3] [--related] [--depth 3] [--related]
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `keyword` or `csv-file` | Yes | -- | Seed keyword string, or path to CSV file with one keyword per line (or column named `keyword`) |
| `--depth` | No | `3` | Maximum recursion depth (1-5). Each level multiplies API calls by ~4x. Depth 3 is a good balance. |
| `--related` | No | `false` | Also build a Related Searches tree alongside the PAA tree |
| `--provider` | No | `dataforseo` | SERP API provider (DataForSEO) |
| `--location` | No | `United States` | Geographic location for SERP results |
| `--language` | No | `en` | Language code for SERP results |
| `--delay` | No | `1.0` | Seconds between API requests (rate limiting) |
| `--output` | No | `PAA-TREE.md` | Output filename |

---

## API Configuration

### DataForSEO (Primary)

Set environment variables:
```bash
export DATAFORSEO_LOGIN="your_login"
export DATAFORSEO_PASSWORD="your_password"
```

API endpoint: `https://api.dataforseo.com/v3/serp/google/organic/live/advanced`

The script extracts PAA from the `people_also_ask` field and Related Searches from the `related_searches` field in the API response.

---

## Workflow

### Step 1: Parse Input

- If input is a keyword string: use it as the single seed keyword.
- If input is a CSV file: read all keywords from the file. Support both single-column CSVs and CSVs with a `keyword` column header.
- Validate that at least one keyword is provided.

### Step 2: Fetch SERP for Seed Keyword

For each seed keyword:
1. Call the SERP API with the keyword, location, and language.
2. Extract the PAA questions from the response (typically 4 questions per SERP).
3. If `--related` is set, also extract Related Searches (typically 8 per SERP).
4. Store each question/search as a node in the tree with metadata: parent keyword, depth level, position.

### Step 3: Recursive PAA Expansion

For each PAA question extracted at depth N (where N < max depth):
1. Wait `--delay` seconds (rate limiting).
2. Fetch the SERP for that exact question.
3. Extract child PAA questions from the response.
4. Check each child against the global deduplication set.
5. If the child is new (not seen before), add it to the tree at depth N+1.
6. If the child is a duplicate, mark it as `[seen]` but do not recurse into it.
7. Continue until max depth is reached or no new questions are found.

### Step 4: Related Searches Tree (Optional)

If `--related` is enabled, build a parallel tree:
1. For each Related Search at depth N (where N < max depth):
   - Fetch its SERP.
   - Extract its Related Searches.
   - Deduplicate and add to tree.
2. Related Searches tree is kept separate from PAA tree in the output.

### Step 5: Deduplication

Maintain a global set of all seen questions (normalized: lowercased, stripped of punctuation). This prevents:
- The same question appearing in multiple branches.
- Infinite loops where PAA questions reference each other.
- Wasted API calls on already-explored questions.

### Step 6: Generate Output

Produce three output formats:
1. **PAA-TREE.md** -- Hierarchical tree with indentation showing parent-child relationships.
2. **Flat list** -- All unique questions as a simple bulleted list (appended to the same file).
3. **CSV export** -- `paa-export.csv` with columns: `question`, `depth`, `parent`, `seed_keyword`.

---

## Output Format: PAA-TREE.md

```markdown
# PAA Tree: [seed keyword]

**Generated:** [date]
**Depth:** [max depth]
**Total unique questions:** [count]
**API calls made:** [count]

---

## Hierarchical Question Tree

- **What is [topic]?**
  - What is [topic] used for?
    - What are the benefits of [topic]?
    - How does [topic] work in practice?
  - What is the difference between [topic] and [alternative]?
    - Which is better, [topic] or [alternative]?
  - What is [topic] in simple terms?
- **How to [topic]?**
  - How to [topic] for beginners?
    - What is the easiest way to [topic]?
  - How to [topic] step by step?
- **Is [topic] worth it?**
  - How much does [topic] cost?
  - What are the disadvantages of [topic]?

## Related Searches Tree (if --related)

- [related search 1]
  - [child related search]
- [related search 2]

---

## Flat Question List (for content planning)

1. What is [topic]?
2. What is [topic] used for?
3. What are the benefits of [topic]?
...

---

## Export

CSV exported to: `paa-export.csv`
```

---

## Rate Limiting and Cost Awareness

| Depth | Approx. API Calls (1 seed) | DataForSEO Cost (~$0.002/call) |
|---|---|---|
| 1 | 1 | $0.002 |
| 2 | ~5 | $0.01 |
| 3 | ~21 | $0.04 |
| 4 | ~85 | $0.17 |
| 5 | ~341 | $0.68 |

For a CSV with 10 keywords at depth 3: ~210 API calls, ~$0.42.

Default delay of 1 second between requests. Increase with `--delay 2` for conservative usage.

---

## Script Location

```
scripts/paa_scraper.py
```

Run directly:
```bash
python scripts/paa_scraper.py "best crm software" --depth 3 --related
python scripts/paa_scraper.py keywords.csv --depth 2
```

---

## Cross-References

- **42:seo-agi** -- Use PAA tree output to inform content brief structure and FAQ sections.
- **42:content** -- PAA questions map directly to H2/H3 headings and FAQ schema.
- **42:blog-geo** -- PAA questions are the exact format AI models cite; use for AI-optimized content.
- **42:topical-map** -- PAA tree reveals topic boundaries and subtopic relationships.
- **42:striking-distance** -- Cross-reference PAA questions with pages already ranking positions 4-20.
