# Analysis Schema

Structured output model for sentiment analysis in Sentiment42.
Produced by SKILL.md Section 5.5, consumed by Phase 3 report generation.

## AnalysisResult Schema

```
AnalysisResult:
  query: string                          # Original search query
  period: string                         # Timeframe used: "1m" | "3m" | "1y" | "3y" | "5y"
  lang: "nl" | "en"                      # Output language
  total_sources: number                  # Distinct sources that returned data
  total_items: number                    # Total crawled items analyzed (after dedup + filtering)

  executive_summary: string
    # 3-5 sentences, narrative style with key numbers embedded
    # Written in {lang}
    # Example (NL): "Sentiment rond Tesla is overwegend positief (62%).
    #   De belangrijkste topics zijn batterijkwaliteit (negatief) en Autopilot (positief).
    #   68 bronnen uit 5 platforms."
    # Example (EN): "Sentiment around Tesla is predominantly positive (62%).
    #   Key topics include battery quality (negative) and Autopilot (positive).
    #   68 sources from 5 platforms."

  overall_sentiment:
    positive: number                     # Percentage (0-100)
    negative: number                     # Percentage (0-100)
    neutral: number                      # Percentage (0-100)
    # MUST sum to exactly 100

  per_source_sentiment:                  # Array, one entry per source that returned data
    - source: string                     # e.g., "reddit", "news", "hn"
      source_label: string               # Localized label, e.g., "Reddit", "Nieuws"
      item_count: number                 # Items analyzed from this source
      sentiment:
        positive: number
        negative: number
        neutral: number
        # MUST sum to 100
      confidence: "high" | "medium" | "low"

  emotion_profile:
    core_emotions:                       # Always exactly 5, in this order
      - name: "trust"
        label: string                    # Localized: "Vertrouwen" / "Trust"
        percentage: number
      - name: "frustration"
        label: string                    # "Frustratie" / "Frustration"
        percentage: number
      - name: "excitement"
        label: string                    # "Enthousiasme" / "Excitement"
        percentage: number
      - name: "disappointment"
        label: string                    # "Teleurstelling" / "Disappointment"
        percentage: number
      - name: "concern"
        label: string                    # "Bezorgdheid" / "Concern"
        percentage: number
    dynamic_emotions:                    # 2-3 context-specific emotions
      - name: string                     # e.g., "humor", "outrage", "hope"
        label: string                    # Localized label
        percentage: number
    # All core + dynamic percentages MUST sum to exactly 100

  theme_groups:                          # 3-5 broad themes
    - theme: string                      # Localized theme name, e.g., "Productkwaliteit"
      topics:                            # 2-5 topics per theme, ranked by prevalence
        - name: string                   # Specific and concrete topic name
                                         # GOOD: "Batterijdegradatie na 2 jaar"
                                         # BAD:  "Productkwaliteit" (too generic)
          sentiment:
            positive: number
            negative: number
            neutral: number
            # MUST sum to 100
          explanation: string            # Analytical, neutral tone, research-report style
                                         # 4-6 sentences for major topics
                                         # 2-3 sentences for minor topics
          dominant_emotions:             # Top 1-2 emotions for this topic
            - name: string
              label: string
          per_source:                    # Only sources with data on this topic
            - source_label: string
              sentiment_lean: "positive" | "negative" | "neutral" | "mixed"
          quotes:                        # 2-3 representative quotes
            - text: string               # Verbatim from CrawledItem content
                                         # 1-2 sentences, original language
              source_label: string       # e.g., "Reddit", "Hacker News"
              url: string                # Direct link from CrawledItem.url
          sarcasm_note: string | null    # Only when sarcasm is prevalent in this topic
                                         # e.g., "Reddit-discussies gebruiken vaak sarcasme..."
    # Total topics across all themes: 8-15
    # Total themes: 3-5

  confidence_assessment:
    overall: "high" | "medium" | "low"
    reasoning: string                    # Brief explanation in {lang}
    source_quality_notes: string[]       # Per-source notes if relevant
```

## Source Weighting Strategy

Aggregation from per-source sentiment to overall sentiment:

1. Calculate sentiment per source independently (group CrawledItems by source)
2. Assign equal base weight to each source: `1.0`
3. Apply confidence multiplier based on data quality:

| Confidence | Multiplier | Criteria |
|------------|------------|----------|
| high | 1.0 | 5+ items with substantive content |
| medium | 0.7 | 3-4 items, or mostly short snippets |
| low | 0.4 | 1-2 items |

4. Weighted average across all sources = overall sentiment
5. Round to whole percentages; adjust the largest category if sum is not exactly 100

**Formula:**
```
For each sentiment dimension (positive/negative/neutral):
  overall[dim] = sum(source[dim] * weight[source]) / sum(weight[source])
  where weight[source] = base_weight * confidence_multiplier
```

## Confidence Level Calculation

### Overall Confidence

| Level | Sources | Items | Additional |
|-------|---------|-------|------------|
| HIGH | 5+ sources returned data | 20+ total items | Multiple sources agree on sentiment direction |
| MEDIUM | 3-4 sources returned data | 10-19 total items | OR sources disagree significantly (mixed signals) |
| LOW | <3 sources (passed min-3 gate) | <10 total items | OR most content is short snippets only |

### Per-Source Confidence

| Level | Criteria |
|-------|----------|
| high | 5+ items with substantive content (full text or long descriptions) |
| medium | 3-4 items, or mostly short snippets (~150 chars) |
| low | 1-2 items from this source |

## Validation Rules

Before finalizing the AnalysisResult, verify ALL of the following:

1. **Percentage sums:** Every sentiment split (overall, per-source, per-topic) sums to exactly 100%
2. **Emotion sum:** All core_emotions + dynamic_emotions percentages sum to exactly 100%
3. **Topic count:** Total topics across all theme_groups is between 8 and 15 (inclusive)
4. **Theme count:** Number of theme_groups is between 3 and 5 (inclusive)
5. **Topics per theme:** Each theme has 2-5 topics
6. **Quote validity:** Every quote has a non-empty `text`, `source_label`, and `url` that matches a CrawledItem
7. **Quote verbatim:** Quotes are exact text from CrawledItem content, not paraphrased
8. **Executive summary length:** Between 3 and 5 sentences
9. **Dynamic emotions count:** Between 2 and 3 dynamic emotions
10. **Rounding fix:** If percentages do not sum to 100 after rounding, adjust the largest category

**If validation fails:** Fix the issue before proceeding. Do not output an invalid AnalysisResult.

## Language Rules

- All text output (executive_summary, theme names, topic names, explanations, emotion labels, confidence reasoning) MUST be in `{lang}`
- Quotes (`quotes[].text`) stay in their **original language** -- do not translate
- Localized emotion labels:

| name | NL label | EN label |
|------|----------|----------|
| trust | Vertrouwen | Trust |
| frustration | Frustratie | Frustration |
| excitement | Enthousiasme | Excitement |
| disappointment | Teleurstelling | Disappointment |
| concern | Bezorgdheid | Concern |

Dynamic emotion labels are also localized in `{lang}`.
