---
name: 42-genai-optimizer
description: "Rewrite existing text for maximum AI extractability and citability. Accepts URL, file path, or plain text. Never fabricates information. Marks uncertainties as footnotes. Preserves original language and tone of voice. Scores before and after on the 5 Lenses of LLM Utility. Supports Dutch and English. Use when user says genai optimizer, geo herschrijf, geo rewrite, herschrijf voor AI, rewrite for AI, maak citeerbaar, make citable, optimize for LLM, optimaliseer voor AI, 42-genai, genai optimize."
user-invokable: true
argument-hint: "url, file of tekst [--mode full|compare]"
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebFetch
  - AskUserQuestion
---

# 42 GenAI Optimizer

Rewrite existing text for maximum AI extractability and citability. This skill does not write new content. It restructures existing text so AI systems can extract, understand, and cite individual passages without surrounding context.

Two absolute rules:

1. **Never fabricate.** Do not add new facts, figures, or claims. Anything not in the source text becomes a footnote.
2. **Preserve the author.** Maintain the original language, tone of voice, and writing style.

---

## Process

### Step 1: Parse Input and Gather Context

Detect input type:
- **URL** — fetch with WebFetch
- **File path** — read with Read tool
- **Plain text** — process directly from prompt

Extract from the input: full text and word count, heading structure (H1-H6), individual passages per section, tables, lists, claims with numbers, language (NL/EN auto-detect), tone of voice (formal/informal, u/je/jij, contractions).

**Before starting, collect three inputs from the user:**

1. **Target keyword** — Detect a suggestion from the H1/title. Ask for confirmation.
2. **Visitor intent** — What does the visitor want to achieve on this page? (e.g., "compare and purchase", "gather information", "solve a problem")
3. **Mode** — FULL or COMPARE (see Step 2).

The visitor intent drives the entire rewrite: section ordering, which information gets front-loaded, and the CTA at the end.

### Step 2: Select Mode

Present the choice:

1. **FULL** — Every passage rewritten for maximum AI extractability. Content gaps marked as footnotes.
2. **COMPARE** — Original vs. rewritten shown per passage. User selects which versions to adopt. Content gaps as footnotes.

Default to FULL when the user does not choose or says "just do it."

### Step 3: Score BEFORE

Score the original text on the 5 Lenses of LLM Utility (see Scoring section). This becomes the "before" column in the scorecard.

### Step 4: Rewrite

Apply three layers per passage, in order:

#### Layer 1: Structured Language (per sentence)

Every sentence must contain four elements:

| Element | Requirement | Example |
|---------|------------|---------|
| **Entity** | Explicitly name who/what | No "it", "this", "they" — name the subject |
| **Relationship** | Clear verb | "costs", "supports", "differs from" |
| **Condition** | When does this apply? | "for teams over 50 people", "since 2025" |
| **Specifics** | Verifiable details | No "many" or "significant" — state the number or add a footnote |

**Semantic triples** (subject, predicate, object) are the smallest unit of machine-readable meaning. The four elements above enforce triples automatically.

#### Layer 2: Passage Architecture (per section)

| Principle | Rule |
|-----------|------|
| AI Inverted Pyramid | First 40-60 words = direct claim or answer |
| Grounding budget | Passages of 120-180 words, self-contained |
| Isolation test | Every passage must work without surrounding context |
| No broken references | No "above", "as mentioned earlier", "this gives" |

#### Layer 3: Page Structure (whole document)

| Element | Rule |
|---------|------|
| Headings | Question-based H2s where appropriate. Triple-headings where the original heading is vague |
| Tables | Comparison tables where 3+ items are compared (no bullet lists) |
| Citation capsules | 40-60 word definitive statements per section |
| Front-loading | Strongest content in the first 3 sections |
| Keyword integration | Target keyword in H1 and at least 2 H2s. Use natural synonyms and semantic variants elsewhere. No keyword stuffing — if it sounds forced, use a variant |
| Keyword in opening | Target keyword or recognizable synonym within first 100 words |
| Internal links | Place `[LINK: anchor text, target page suggestion]` markers where a reference logically helps the reader. Maximum 1-2 per passage. Not every passage needs a link — only where it is a logical next-step or deepening for the visitor |

**Triple-headings** — When an original heading is vague or generic, rewrite as a semantic triple matching an AI query. Only apply when the original heading is vague. Leave specific headings unchanged.

#### Scope Rules

| Change type | Action |
|-------------|--------|
| Structure and phrasing (vague reference, broken sentence, bad ordering) | Rewrite directly |
| Content gap (missing data, vague claim, missing table) | Footnote with QUESTION FOR AUTHOR |
| Unverifiable claim carried over from original | Footnote with VERIFY |
| New fact or figure needed | Never fill in — always footnote |

### Step 5: Score AFTER

Score the rewritten text on the same 5 lenses.

### Step 6: Generate Output

Write the MD file to the same directory as the source file, or to `~/Documents/GenAI-Optimizer/` when input is a URL or plain text.

Filename: `{original-name}-geo-optimized.md` or `{slug-from-title}-geo-optimized.md`.

For research data (grounding budget, passage benchmarks, AI system preferences, stress tests), load `references/geo-research.md`.

---

## Forbidden Patterns (always rewrite)

| Pattern | Example | Problem | Fix |
|---------|---------|---------|-----|
| Unresolved pronoun | "It features a 120Hz display" | Which device? | Name the subject explicitly |
| Vague demonstrative | "This gives it an advantage" | What gives what an advantage? | Name both entities |
| Context-dependent | "The above specs outperform the competition" | Which specs? Which competition? | Repeat the specifics |
| Stripped conditions | "The price has dropped significantly" | From what? To what? When? | Add conditions or footnote |
| Assumed knowledge | "The popular supplement helps with recovery" | Which supplement? Recovery from what? | Name explicitly or footnote |
| Relative claim | "Our best-selling product" | How fast? Compared to what? | Quantify or footnote |
| Marketing fluff | "Revolutionary solution that makes everything easier" | Nothing extractable | Rewrite with specifics or remove |

## Desired Patterns (apply where possible)

| Pattern | Example | Why it works |
|---------|---------|-------------|
| Definition opening | "Content delivery networks are distributed server systems that..." | Directly matchable with "What is X?" queries |
| Quantified answer | "The average cost is EUR 4,500 per month" | Extractable as fact |
| Comparative answer | "X differs from Y in three ways: [list]" | Matchable with comparison queries |
| Conditional answer | "For teams over 50 people, Plan X costs EUR 24.99 per user" | Self-contained citable with context |

---

## Anti-Slop Rules (Lens 5: NL Quality)

The rewrite itself must not read as AI-generated content.

**Never use:**
- Filler openers ("In today's digital world...", "It won't surprise you that...")
- Adverbs as crutch ("significantly", "incredibly", "undeniably")
- Binary contrasts ("It's not about X, it's about Y")
- Dramatic fragmentation ("And then? Silence.")
- Em dashes
- Pull-quote-like sentences (if it sounds like a poster, rewrite it)
- Passive constructions where an actor exists
- Generic intros ("In today's fast-paced world", "Whether you're a ... or a ...")

**Always do:**
- Preserve the tone of voice from the original
- Vary sentence length (two items better than three)
- Active voice, concrete subject
- Specifics over adjectives
- Trust the reader — no hand-holding

**Dutch-specific:** No anglicisms where a Dutch word exists (unless the original uses them). Preserve "u" vs "je" from original.

**English-specific:** No British/American switching — follow the original. Preserve contractions from original.

**Core rule:** The rewritten text must read as if the same author wrote it, but with sharper structure.

---

## Scoring: 5 Lenses of LLM Utility

Score text before and after rewriting. Per lens 0-10, total (raw/50) x 100 = 0-100.

| Lens | What it measures | 9-10 | 3-4 |
|------|-----------------|------|-----|
| **Structural Fitness** | Hierarchy and relationships | Correct H1 hierarchy, triple-headings, comparison tables, citation capsules | Minimal structure, wall-of-text, no tables |
| **Selection Criteria** | Information density | Every section opens with 40-60 word direct answer, no fluff | Answers buried, lots of vague language |
| **Extractability** | Self-contained passages | 90%+ passages self-contained, no vague pronouns | 30-49% self-contained, lots of context dependency |
| **Entity Completeness** | Explicit triples | Every claim has subject + predicate + object | Many implicit subjects, unclear relationships |
| **NL Quality** | Natural language | Tone of voice preserved, no AI patterns, varied sentence length | Clearly mechanical, repetitive structure |

**Thresholds:** 80-100 Excellent | 60-79 Good | 40-59 Moderate | 0-39 Weak

---

## Output Format

### FULL mode

```markdown
---
title: "42-GenAI Optimizer Output"
source: "[original title, URL, or 'plain text']"
date: YYYY-MM-DD
lang: nl | en
mode: full-rewrite
target_keyword: "[primary keyword]"
visitor_intent: "[what the visitor wants to achieve]"
geo_score_before: XX/100
geo_score_after: XX/100
---

## SEO Meta

**Suggested meta description** (max 155 characters):
> [Motivating description addressing visitor intent, containing target keyword
> or natural synonym, giving the reader a reason to click.
> No generic summary — write from what the visitor wants to know.]

---

# [Title — preserved or improved]

[Full rewritten text with consecutively numbered footnotes.
Internal link markers where appropriate: [LINK: anchor text, target page suggestion]]

---

## CTA and Next Steps

[Call-to-action matching visitor intent and tone of voice of the original.
No generic "contact us" — specific and action-oriented.]

**Logical next steps for the visitor:**
- [Next-step 1 with link suggestion to related article/page]
- [Next-step 2 if applicable]

---

## GEO Scorecard (5 Lenses of LLM Utility)

| Lens | Before | After | Notes |
|------|--------|-------|-------|
| Structural Fitness | X/10 | X/10 | [what changed] |
| Selection Criteria | X/10 | X/10 | [what changed] |
| Extractability | X/10 | X/10 | [what changed] |
| Entity Completeness | X/10 | X/10 | [what changed] |
| NL Quality | X/10 | X/10 | [what changed] |
| **Total** | **XX/100** | **XX/100** | |

## Changelog

| # | Passage/Heading | Change | Reason |
|---|----------------|--------|--------|
| 1 | [location] | [what] | [why — reference layer/lens] |

## Verify Before Publication

[^1]: **VERIFY** — [claim from original that cannot be verified, with suggestion where to check]
[^2]: **QUESTION FOR AUTHOR** — [content gap: missing data, vague point, missing context. Ask a concrete question.]
```

### COMPARE mode

Same structure (including SEO Meta, CTA and Next Steps), but the rewritten text section is replaced by per-passage comparisons:

```markdown
## Passage 1: [Heading]

**Original:**
> [original text]

**Rewritten:**
> [new text with footnotes]

**Changes:** [short summary of what changed and why]
```

Scorecard, changelog, and footnotes remain identical to FULL mode.
