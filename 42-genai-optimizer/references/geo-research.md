# GEO Research Data

Reference data for scoring and rewriting decisions. Load when performing analysis or generating output.

## Grounding Budget (DEJAN AI research, 7000+ queries)

- Total per query: ~1,900 words, split across multiple sources
- Per individual webpage: ~380 words allocation
- Pages under 5,000 characters: 66% extraction rate
- Pages over 20,000 characters: 12% extraction rate
- More content = lower coverage per word

## Optimal Passage Characteristics

- Optimal length for AI citation: 134-167 words (Bortolato 2025)
- Definition patterns increase citation rate by 2.1x (Georgia Tech 2024)
- Statistics in passages increase citation by 40% (Princeton GEO study 2024)
- Authority citations increase citation by 115% in certain categories (IIT Delhi 2024)
- Content with source attributions cited 20-25% more often by Perplexity and ChatGPT
- Clear headings above a paragraph improve cosine similarity by up to 17.54% (Eikhart 2025)

## AI System Citation Preferences

| AI System | Preference |
|-----------|-----------|
| ChatGPT (Search) | Passages with explicit definitions, named sources, recent dates. Cites 2-4 sources per response. |
| Perplexity | Fact-dense passages with statistics. Cites 4-8 sources per response. Recency heavily weighted. |
| Gemini (AI Overviews) | Concise answer blocks (40-60 words). Prefers content already ranking in top-10 organically. |
| Claude | Well-structured, comprehensive passages. Values nuance and accuracy over brevity. |
| Copilot (Bing) | Similar to Gemini. Prefers high-authority domains with clear factual claims. |

## The 4 Stress Tests

Validation checks to run after rewriting:

1. **Isolation test** — Select a random sentence from the middle. Is it self-contained?
2. **Context test** — Scroll down twice and start reading. Is the topic immediately clear?
3. **Disambiguation test** — Read a mid-page sentence aloud. Could it be about something completely different?
4. **URL accessibility test** — Can an LLM agent see the raw text, or does JS/bot-protection block it?

## Sources

- Jessier, M. (2026). "How to write for AI search: A playbook for machine-readable content." Search Engine Land.
- Eijkemans, R. (2025). "From structured data to structured language." Eikhart.com.
- Eijkemans, R. (2025). "The shared mechanism." Eikhart.com.
- Aggarwal et al. (2024). "GEO: Generative Engine Optimization." Princeton / Georgia Tech / IIT Delhi.
- DEJAN AI (2025). "How big are Google's grounding chunks?" dejan.ai.
- Bortolato (2025). AI Overview passage length analysis.
- Forrester, D. (2025). "The new content failure mode." Substack.
