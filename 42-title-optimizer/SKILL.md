---
name: 42-title-optimizer
description: >
  Iterative title tag and headline optimizer with multi-round refinement.
  Generates 5 variations per round across 3 rounds (diverge, refine, polish)
  with transparent scoring on 7 dimensions. Accepts URL, file path, or
  plain text with content context. Scores are relative quality indicators,
  not CTR predictions. Supports Dutch and English. Use when user says
  "title optimizer", "titel optimalisatie", "headline optimizer", "title
  variations", "titel variaties", "title test", "headline test", "kop
  variaties", "title score", "titel score", "title rewrite", "verbeter
  titel", "optimize title tag", "title tag optimizer", "koppen testen",
  "discover headline", "title iteratie", "headline refinement".
version: 1.0.0
tags: [seo, title-tag, headline, copywriting, optimization, iterative, scoring]
user-invokable: true
argument-hint: "url, file, of tekst [--rounds 1|2|3] [--focus discover|serp|both]"
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
  - AskUserQuestion
metadata:
  filePattern:
    - "**/TITLE-OPTIMIZER*.md"
    - "**/title-variations*.md"
    - "**/headline*.md"
  bashPattern:
    - "title.optim"
    - "headline.optim"
    - "titel.optim"
---

# Title Optimizer — Iterative Headline Refinement with Scoring

## Purpose

Generate and iteratively refine title tags and headlines through 3 rounds of
AI-powered variation and transparent scoring. Each round builds on the best
results of the previous round, producing a ranked shortlist of optimized titles.

This is NOT a CTR predictor. Scores are relative quality indicators across 7
dimensions — they help you compare variations, not predict traffic.

---

## Commands

```
/42:title-optimizer <url>                        # Fetch page, analyze, 3 rounds
/42:title-optimizer <url> --rounds 1             # Quick: 1 round, 5 variations
/42:title-optimizer <url> --focus discover        # Optimize for Google Discover
/42:title-optimizer <url> --focus serp            # Optimize for search title tags
/42:title-optimizer "<title>" --content <file>   # Manual title + content from file
/42:title-optimizer "<title>" --content "<text>" # Manual title + inline content
```

Default: `--rounds 3 --focus both`

---

## Process

### Step 0: Parse Input and Gather Context

Detect input type:
- **URL** — fetch with WebFetch. Extract: current title tag, H1, meta description,
  first 2000 words of body content, heading structure, word count.
- **File path** — read with Read tool. Extract same elements.
- **Plain text** — user provides title + content directly.

**Collect from the user (ask if not provided):**

1. **Target keyword** — Detect from current title/H1. Ask for confirmation.
2. **Content summary** — Auto-generate a 2-sentence summary of what the page delivers.
   Show to user: "Klopt dit? / Is this accurate?" Adjust if needed.
3. **Focus** — SERP (title tags ≤60 chars), Discover (headlines 60-100 chars), or Both.

The content summary is critical: it prevents clickbait by anchoring every variation
to what the page actually delivers.

### Step 1: Score the Current Title (Baseline)

Score the existing title on all 7 dimensions (see Scoring section below).
Present as a scorecard table. This is the baseline to beat.

```markdown
## Huidige titel: "{current title}"

| Dimensie              | Score | Toelichting                    |
|-----------------------|-------|--------------------------------|
| Keyword-dekking       | 7/10  | Primary keyword aanwezig       |
| Content-alignment     | 5/10  | Titel belooft meer dan content |
| Lengte-optimalisatie  | 8/10  | 54 tekens — goed voor SERP     |
| Entiteit-dichtheid    | 4/10  | Geen herkenbare entiteiten     |
| Emotionele trigger    | 3/10  | Neutraal, geen hook            |
| Leesbaarheid          | 7/10  | Duidelijk, geen jargon         |
| Uniciteit             | 5/10  | Generiek patroon               |
| **Totaal**            | **39/70** |                            |
```

### Step 2: Round 1 — Divergeren (5 variaties)

Generate 5 variations using **different strategic angles**. Each variation must
take a distinct approach:

| # | Strategie | Beschrijving |
|---|-----------|-------------|
| V1 | **Keyword-first** | Target keyword vooraan, directe match op zoekintentie |
| V2 | **Benefit-led** | Leidt met het voordeel/resultaat voor de lezer |
| V3 | **Curiosity hook** | Wekt nieuwsgierigheid zonder clickbait (content moet leveren) |
| V4 | **Data-driven** | Bevat een getal, percentage, of specifiek feit uit de content |
| V5 | **Entity-rich** | Maximaal herkenbare entiteiten (merknamen, plaatsen, personen) |

**Rules for all variations:**
- Every claim in the title MUST be supported by the actual content
- Respect length constraints: SERP ≤60 chars, Discover 60-100 chars
- Keep the target keyword or a close semantic variant
- Match the language of the original (NL/EN auto-detect)
- No ALL CAPS words, no excessive punctuation, no emoji

Score all 5 variations on the 7 dimensions. Present as:

```markdown
## Ronde 1 — Divergeren

| # | Variatie | Strategie | Score | vs Baseline |
|---|----------|-----------|-------|-------------|
| V1 | "..." | Keyword-first | 48/70 | +9 |
| V2 | "..." | Benefit-led | 52/70 | +13 |
| V3 | "..." | Curiosity | 45/70 | +6 |
| V4 | "..." | Data-driven | 51/70 | +12 |
| V5 | "..." | Entity-rich | 43/70 | +4 |

### Top-2 voor Ronde 2: V2, V4
Reden: Hoogste scores + verschillende sterke dimensies (V2: emotie, V4: specificiteit)
```

**If `--rounds 1`**: Stop here. Present final ranking and recommendation.

### Step 3: Round 2 — Verfijnen (5 variaties)

Take the top-2 from Round 1. For each, identify the **weakest scoring dimension**.
Generate 5 new variations that:

- Keep the strengths of the top-2
- Specifically target the weak dimensions
- Cross-pollinate: combine strong elements from both parents

Variation assignment:
| # | Basis | Focus |
|---|-------|-------|
| V6 | Top-1 | Fix weakest dimension |
| V7 | Top-1 | Alternative wording, keep strengths |
| V8 | Top-2 | Fix weakest dimension |
| V9 | Top-2 | Alternative wording, keep strengths |
| V10 | Hybrid | Best elements from both parents |

Score all 5. Present same table format with vs Baseline comparison.

**If `--rounds 2`**: Stop here. Present final ranking.

### Step 4: Round 3 — Polijsten (5 variaties)

Take the top-2 from Round 2. Final polish round focuses on micro-optimization:

- **Character-level tuning**: hit exact length targets (not 1 char over)
- **Power word placement**: front-load the strongest word
- **Rhythm and flow**: natural reading cadence, no awkward breaks
- **Pixel width awareness**: SERP truncation happens on pixels, not chars.
  Narrow chars (i, l, t) buy space; wide chars (m, w, W) cost extra.
  Target: ≤580px for title tags (roughly 50-60 chars depending on font)

Generate 5 final variations (V11-V15). Score all.

### Step 5: Final Output

Present the complete tournament bracket:

```markdown
## Resultaat — Title Optimizer

**Origineel**: "{original title}" — 39/70

### Finale Top-3

| Rank | Titel | Score | vs Original | Sterkste dimensie |
|------|-------|-------|-------------|-------------------|
| 1 | "..." | 58/70 | +19 | Content-alignment (10/10) |
| 2 | "..." | 55/70 | +16 | Keyword-dekking (9/10) |
| 3 | "..." | 54/70 | +15 | Emotionele trigger (9/10) |

### Scorekaart #1 (winnaar)

| Dimensie | Original | Winnaar | Delta |
|----------|----------|---------|-------|
| Keyword-dekking | 7 | 9 | +2 |
| Content-alignment | 5 | 10 | +5 |
| ... | ... | ... | ... |

### Alle rondes

Ronde 1: V1 (48) → V2 (**52**) → V3 (45) → V4 (**51**) → V5 (43)
Ronde 2: V6 (54) → V7 (53) → V8 (**56**) → V9 (52) → V10 (**55**)
Ronde 3: V11 (57) → V12 (**58**) → V13 (54) → V14 (**55**) → V15 (53)
```

Save full output to `output/TITLE-OPTIMIZER-{domain-or-slug}.md`.

---

## Scoring System — 7 Dimensions

Each dimension is scored 1-10. Total: /70. Scores are **relative quality
indicators** — useful for comparing variations, not for predicting traffic.

### 1. Keyword-dekking (1-10)

Does the title contain the target keyword or a close semantic variant?

| Score | Criteria |
|-------|----------|
| 9-10 | Exact match keyword, front-loaded (first 3 words) |
| 7-8 | Exact match keyword, present but not front-loaded |
| 5-6 | Close semantic variant or partial match |
| 3-4 | Related term but not the target keyword |
| 1-2 | No keyword relevance |

### 2. Content-alignment (1-10)

Does the title accurately represent what the page delivers? This is the
**anti-clickbait dimension** — scored by comparing the title's promise against
the actual content summary from Step 0.

| Score | Criteria |
|-------|----------|
| 9-10 | Title promise = content delivery, no gap |
| 7-8 | Title is accurate but slightly broader than content |
| 5-6 | Title implies something the content only partially covers |
| 3-4 | Title overpromises or misleads |
| 1-2 | Title has no relation to actual content |

### 3. Lengte-optimalisatie (1-10)

Is the title within the ideal character range for its target format?

| Focus | Ideal | Acceptable | Too short | Too long |
|-------|-------|------------|-----------|----------|
| SERP | 50-60 chars | 40-65 | <40 | >65 (truncated) |
| Discover | 65-90 chars | 55-100 | <55 | >100 |

| Score | Criteria |
|-------|----------|
| 9-10 | Within ideal range |
| 7-8 | Within acceptable range |
| 5-6 | Slightly outside (±5 chars) |
| 3-4 | Significantly outside range |
| 1-2 | Extreme mismatch (e.g., 20 chars or 120+ chars for SERP) |

### 4. Entiteit-dichtheid (1-10)

Does the title contain recognizable named entities (brands, products, people,
places, organizations) that help search engines classify the content?

| Score | Criteria |
|-------|----------|
| 9-10 | 2+ recognizable entities, contextually relevant |
| 7-8 | 1 strong entity with context |
| 5-6 | 1 entity or generic brand reference |
| 3-4 | Implied entities but not named |
| 1-2 | No entities, fully generic |

### 5. Emotionele trigger (1-10)

Does the title create genuine interest without resorting to clickbait?
Legitimate triggers: curiosity, urgency, specificity, contrast, surprise.
Penalized: information withholding, exaggeration, misleading framing.

| Score | Criteria |
|-------|----------|
| 9-10 | Strong legitimate hook, backed by content |
| 7-8 | Moderate hook, creates interest |
| 5-6 | Neutral, factual, no particular draw |
| 3-4 | Attempts engagement but feels forced |
| 1-2 | Clickbait signals OR completely flat |

### 6. Leesbaarheid (1-10)

Is the title easy to read, scan, and understand at a glance?

| Score | Criteria |
|-------|----------|
| 9-10 | Clear, natural language, no jargon, scannable |
| 7-8 | Clear but slightly complex or niche terminology |
| 5-6 | Readable but requires thought |
| 3-4 | Awkward phrasing or unnecessary complexity |
| 1-2 | Confusing, grammatically broken, keyword-stuffed |

### 7. Uniciteit (1-10)

Does the title stand out from the typical patterns in the SERP/Discover feed?
Generic patterns ("X tips voor Y", "Alles over Z", "De beste X") score low.

| Score | Criteria |
|-------|----------|
| 9-10 | Fresh angle, would stand out in a feed of 10 results |
| 7-8 | Somewhat distinctive, has a unique element |
| 5-6 | Follows common patterns but competently |
| 3-4 | Very generic, interchangeable with competitors |
| 1-2 | Template-like, zero differentiation |

---

## Focus Mode Adjustments

### `--focus serp` (Title Tags)
- Max 60 characters hard limit (pixel-width aware)
- Front-load target keyword
- Weight keyword-dekking higher (1.5x in comparison)
- Include brand suffix consideration (e.g., " | Brand")

### `--focus discover` (Google Discover Headlines)
- Target 65-90 characters
- Weight emotionele trigger and uniciteit higher (1.5x)
- Optimize for feed scanning (mobile-first)
- Visual promise: does the title pair well with an image?

### `--focus both` (Default)
- Generate SERP version AND Discover version for the winner
- Present both in final output:
  ```
  SERP:     "Keyword First: Concise Benefit Statement" (58 chars)
  Discover: "Keyword First: Longer Headline with Curiosity and Detail" (78 chars)
  ```

---

## Rules

1. **Content anchored** — Never write a title that promises something the content
   doesn't deliver. The content summary from Step 0 is the source of truth.
2. **No pseudo-precision** — Scores are 1-10 quality indicators, not statistics.
   Never say "this title will get X% CTR."
3. **Show your work** — For each variation, write a 1-line rationale explaining
   the strategic choice. E.g., "Front-loads keyword + adds year for freshness."
4. **Language matching** — Auto-detect input language. Generate in the same language.
   Dutch input = Dutch variations. English input = English variations.
5. **Build on previous rounds** — Round 2 must reference Round 1 scores. Round 3
   must reference Round 2. Each round must improve on identified weaknesses.
6. **Respect user overrides** — If the user says "shorter" or "more direct" or
   "include brand name", incorporate that as a constraint in the next round.

---

## Example Session

```
User: /42:title-optimizer https://example.com/elektrische-fietsen-kopen

Claude: Target keyword gedetecteerd: "elektrische fietsen kopen" — klopt dit?
User: Ja

Claude: Content samenvatting: "Koopgids voor elektrische fietsen met vergelijking
van 12 modellen op prijs, actieradius en gewicht. Inclusief stappenplan en FAQ."
Klopt dit?
User: Ja, focus op SERP

Claude:
## Huidige titel: "Elektrische Fiets Kopen - Tips & Advies"
| Dimensie | Score |
|----------|-------|
| Keyword-dekking | 8/10 |
| Content-alignment | 4/10 — titel zegt "tips", content is een vergelijking |
| Lengte | 9/10 — 39 chars |
| Entiteiten | 2/10 — geen merken/modellen |
| Emotie | 3/10 — generiek |
| Leesbaarheid | 8/10 |
| Uniciteit | 2/10 — elk resultaat zegt dit |
| **Totaal** | **36/70** |

## Ronde 1 — Divergeren
...
```
