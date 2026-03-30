---
name: 42-content-repurposer
description: >
  Take one piece of content and AI-generate 10 platform-specific formats.
  Maximize ROI from a single content asset. Supports Twitter/X threads,
  LinkedIn posts, Instagram captions, Reddit posts, Quora answers, email
  newsletters, YouTube scripts, podcast talking points, SMS/WhatsApp, and
  blog summaries. Use when user says "repurpose content", "content repurposing",
  "social media formats", "turn blog into tweets", "linkedin post from article",
  "repurpose for social", "content distribution", "cross-platform content",
  "42-content-repurposer", "repurpose", "multi-platform content".
version: 1.0.0
tags: [seo, content, repurposing, social-media, distribution, twitter, linkedin, instagram, youtube, email]
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - WebFetch
metadata:
  filePattern:
    - "**/blog/**"
    - "**/content/**"
    - "**/posts/**"
    - "**/articles/**"
    - "**/*.mdx"
    - "**/*.md"
  bashPattern:
    - "repurpose"
    - "content.repurpose"
    - "social.media"
---

# Content Repurposer — 10 Platform Formats from One Asset

## Purpose

Transform a single piece of content into 10 platform-optimized formats. Every platform has different audience expectations, character limits, tone requirements, and metadata needs. This skill extracts the core value from source content and reshapes it for maximum impact on each platform.

---

## Commands

```
/42:content-repurposer <url-or-file> [--platforms all] [--tone professional]
/42:content-repurposer <url-or-file> --platforms twitter,linkedin,email
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--platforms` | `all` | Comma-separated list of platforms to generate. Options: `twitter`, `linkedin`, `instagram`, `reddit`, `quora`, `email`, `youtube`, `podcast`, `sms`, `blog-summary`, `all` |
| `--tone` | `professional` | Voice for all outputs: `professional`, `casual`, `authoritative` |
| `--cta` | none | Custom call-to-action to include across all formats |
| `--brand` | none | Brand name to include for consistent attribution |

---

## Input

The skill accepts three input types:

| Input | How It Works |
|-------|-------------|
| **URL** | Fetched via WebFetch. Full page content extracted, metadata parsed. |
| **File path** | Read via Read tool. Supports .md, .mdx, .html, .txt files. |
| **Pasted text** | Processed directly from the user's message. |

---

## Workflow

### Step 1: Extract Source Content

Fetch or read the source content. Extract:

- **Title and H1**
- **Full body text** (stripped of navigation, footers, sidebars)
- **Key statistics and data points** (numbers, percentages, dates)
- **Direct quotes** (attributed statements)
- **Core argument or thesis** (the single main point)
- **Supporting points** (3-7 secondary arguments)
- **Target audience** (inferred from content style and topic)
- **Word count** of original

### Step 2: Identify Key Messages

Distill the source into reusable building blocks:

| Block | Description |
|-------|-------------|
| **Hook** | The single most attention-grabbing insight or statistic |
| **Thesis** | One-sentence summary of the core argument |
| **Data points** | 3-5 specific numbers, stats, or facts worth citing |
| **Quotes** | 1-3 quotable passages (original phrasing or paraphrased) |
| **Takeaways** | 3-5 actionable lessons or conclusions |
| **CTA** | What should the reader do next? |

### Step 3: Generate Platform-Specific Formats

For each selected platform, generate a format-specific version using the building blocks from Step 2. Apply platform rules (see Platform Specifications below).

### Step 4: Add Platform Metadata

For each output, include platform-specific metadata:

- Character/word counts with limit compliance
- Hashtags (where applicable)
- Tags or categories
- Suggested posting time (general best practice)
- Media suggestions (image descriptions, video hooks)

---

## Platform Specifications

### 1. Twitter/X Thread

| Attribute | Specification |
|-----------|--------------|
| Format | 5-10 tweets in a thread |
| Character limit | 280 chars per tweet |
| Structure | Hook tweet (strongest stat/claim) -> supporting tweets -> CTA tweet |
| Hashtags | 2-3 relevant hashtags on first and last tweet only |
| Style | Short sentences. Line breaks for readability. Use numbers and stats. |
| Media | Suggest image or chart for first tweet |

```
Tweet 1 (Hook):
[Most surprising stat or claim from the article]

Thread below...

Tweet 2-8 (Supporting):
[One key point per tweet. Numbered if listing.]

Tweet 9-10 (CTA):
[Summary + link + hashtags]
```

### 2. LinkedIn Post

| Attribute | Specification |
|-----------|--------------|
| Format | 3-5 paragraphs, professional tone |
| Character limit | 1,300 characters (visible before "see more") |
| Structure | Hook line (pattern interrupt) -> story/insight -> data -> takeaway -> question |
| Hashtags | 3-5 hashtags at the end |
| Style | First-person perspective. "I" statements. Professional but human. |
| Line breaks | Single-sentence paragraphs for mobile readability |

### 3. Instagram Caption

| Attribute | Specification |
|-----------|--------------|
| Format | Casual, visually descriptive, emoji-rich |
| Character limit | 2,200 chars (150 visible before "more") |
| Structure | Hook (first 150 chars critical) -> value -> story -> CTA |
| Hashtags | 25-30 relevant hashtags (in first comment or end of caption) |
| Style | Conversational, emoji line breaks, relatable language |
| Media | Describe ideal carousel or single image concept |

### 4. Reddit Post

| Attribute | Specification |
|-----------|--------------|
| Format | Value-first, educational, no self-promotion |
| Structure | TL;DR at top -> detailed breakdown -> personal experience angle -> discussion question |
| Style | Community-native tone. "I found..." not "Our company..." Never link in body (link in comments if relevant). |
| Suggested subreddits | 2-3 relevant subreddits based on topic |
| Flair | Suggested post flair |

### 5. Quora Answer

| Attribute | Specification |
|-----------|--------------|
| Format | Authoritative, experience-based |
| Word count | 300-500 words |
| Structure | Direct answer (first sentence) -> credentials/context -> detailed explanation -> examples -> summary |
| Style | Third-person authority. Cite sources. Use "In my experience..." framing. |
| Suggested questions | 3-5 Quora questions this answer would fit |

### 6. Email Newsletter

| Attribute | Specification |
|-----------|--------------|
| Subject line | 40-60 chars, curiosity-driven or benefit-focused |
| Preview text | 80-100 chars, complements subject line |
| Body structure | Personal opener -> key insight -> 3 bullet points -> CTA button text |
| CTA | Single clear action (read full article, download, reply) |
| Word count | 150-300 words |
| Style | Matches `--tone` flag. Conversational for casual, polished for professional. |

### 7. YouTube Script

| Attribute | Specification |
|-----------|--------------|
| Format | Full script with timing markers |
| Structure | Hook (0-15s) -> Intro + subscribe CTA (15-30s) -> Content sections (30s-8min) -> Summary + CTA (final 30s) |
| Hook | Pattern interrupt or surprising stat from the article |
| Sections | 3-5 clearly labeled sections with transition phrases |
| Description | 200-word description with timestamps, links, and keywords |
| Tags | 10-15 relevant YouTube tags |
| Thumbnail text | 3-5 word overlay suggestion |

### 8. Podcast Talking Points

| Attribute | Specification |
|-----------|--------------|
| Format | Segment outline, not word-for-word script |
| Structure | Cold open hook -> Topic intro -> 3-4 discussion segments -> Key takeaways -> Listener CTA |
| Segments | Each with: main point, supporting evidence, personal angle, transition |
| Questions | 5-7 discussion questions (for interview or solo reflection) |
| Key takeaways | 3 bullet points for show notes |
| Duration estimate | Based on segment count |

### 9. SMS / WhatsApp

| Attribute | Specification |
|-----------|--------------|
| Character limit | 160 characters (1 SMS segment) |
| Format | Ultra-concise: hook + link + CTA |
| Style | Direct, urgent, personal |
| Variations | Generate 3 versions (curiosity, benefit, urgency) |

```
Version 1 (Curiosity): [Surprising fact] — full breakdown: [link]
Version 2 (Benefit): [What they'll learn] — read here: [link]
Version 3 (Urgency): [Time-sensitive angle] — check it out: [link]
```

### 10. Blog Summary

| Attribute | Specification |
|-----------|--------------|
| Word count | 200 words |
| Format | Recap for syndication or content aggregators |
| Structure | What the article covers -> key findings -> why it matters -> link to full piece |
| Style | Neutral, informative, third-person |
| Use case | Medium cross-post intro, newsletter roundup, content syndication |

---

## Tone Configuration

| Tone | Characteristics | Best For |
|------|----------------|----------|
| `professional` | Polished, data-driven, no slang, formal structure | LinkedIn, email, Quora, blog summary |
| `casual` | Conversational, contractions, humor allowed, relatable | Twitter, Instagram, Reddit, SMS |
| `authoritative` | Expert positioning, citations, definitive statements | YouTube, podcast, Quora, LinkedIn |

When `--tone` is set, all platforms adapt within their format constraints. Instagram stays emoji-friendly even in `professional` tone; Reddit stays community-native even in `authoritative` tone.

---

## Output Format

Output file: `REPURPOSED-CONTENT.md` in the working directory.

```markdown
# Repurposed Content — [Source Title]

**Source:** [URL or file path]
**Generated:** [date]
**Tone:** [professional/casual/authoritative]
**Platforms:** [list of generated platforms]

---

## Source Summary

- **Title:** [title]
- **Word count:** [count]
- **Key message:** [one-sentence thesis]
- **Data points:** [3-5 stats extracted]

---

## 1. Twitter/X Thread

**Character count per tweet:** [listed]
**Suggested posting time:** Tuesday-Thursday, 9-11 AM

[Full thread content]

---

## 2. LinkedIn Post

**Character count:** [count] / 1,300
**Hashtags:** [list]

[Full post content]

---

[... remaining platforms ...]

---

## Platform Checklist

| Platform | Status | Char/Word Count | Within Limits |
|----------|--------|----------------|---------------|
| Twitter/X | Done | 5 tweets, avg 240 chars | Yes |
| LinkedIn | Done | 1,180 / 1,300 chars | Yes |
| Instagram | Done | 1,950 / 2,200 chars | Yes |
| Reddit | Done | 420 words | Yes |
| Quora | Done | 380 / 300-500 words | Yes |
| Email | Done | 220 / 150-300 words | Yes |
| YouTube | Done | 6:30 estimated runtime | Yes |
| Podcast | Done | 4 segments | Yes |
| SMS | Done | 3 versions, all < 160 | Yes |
| Blog Summary | Done | 195 / 200 words | Yes |
```

---

## AI Configuration

- **Model:** OpenAI (gpt-4o or gpt-4o-mini) or Anthropic Claude — configurable per project
- **Temperature:** 0.7 (balanced creativity for marketing copy)
- **Prompt strategy:** Generate all 10 formats in a single pass when using capable models. For smaller models, batch into 3-4 platform groups.
- **Quality check:** Verify character/word counts after generation. Regenerate any platform output that exceeds limits.

---

## Cross-References

- **42:content** — Assess source content quality before repurposing
- **42:genai-optimizer** — Optimize source content for AI citability before repurposing
- **42:blog-geo** — Audit blog posts for AI citation readiness, then repurpose top performers
