# Data Model

Normalized data model for crawled items in Sentiment42.
Used by SKILL.md to structure results after crawling.

## CrawledItem Schema

Each crawled result is normalized into this structure:

```
CrawledItem:
  source: "reddit" | "news" | "hn" | "quora" | "forum" | "trustpilot" | "g2" | "capterra" | "yelp" | "twitter" | "linkedin"
  source_label: Human-readable source name
  url: Original source URL
  title: Page/post title
  content: Main text content (truncated to ~1000 words for context efficiency)
  date: Approximate publication date (ISO format YYYY-MM-DD, extracted from metadata or content)
  date_confidence: "exact" | "approximate" | "unknown"
  relevance: "high" | "medium" | "low"
  metadata:
    subreddit: (Reddit only) e.g., "r/teslamotors"
    comment_count: (Reddit, HN) number of comments if available
    score: (Reddit, HN) upvotes/points if available
    author: (when available) post author
    rating: (review sites only) numeric rating e.g., 4.2
    rating_scale: (review sites only) e.g., "5" for x/5 scale
    completeness: "full" | "partial" -- whether full thread/comments were retrieved
```

### Source Labels

| source | source_label (NL) | source_label (EN) |
|--------|-------------------|-------------------|
| reddit | Reddit | Reddit |
| news | Nieuws | News |
| hn | Hacker News | Hacker News |
| quora | Quora | Quora |
| forum | Forum ({name}) | Forum ({name}) |
| trustpilot | Trustpilot | Trustpilot |
| g2 | G2 | G2 |
| capterra | Capterra | Capterra |
| yelp | Yelp | Yelp |
| twitter | X/Twitter | X/Twitter |
| linkedin | LinkedIn | LinkedIn |

### Relevance Scoring

Assign relevance based on how well the result matches the query:

- **high**: Title or content directly addresses the query topic. Contains substantive discussion, review, or opinion.
- **medium**: Related to the query topic but tangential. Mentions the topic alongside other subjects.
- **low**: Only peripherally related. The query terms appear but the content is about something else.

### Content Truncation

Truncate `content` to approximately 1000 words to keep Claude's context window efficient. Prioritize:
1. The opening/summary paragraph
2. Key opinion statements or sentiment-bearing sentences
3. Conclusions or summary points

For Reddit/HN threads with comments: include the original post plus top 3-5 highest-rated comments.

## Normalization Rules

### From Firecrawl JSON Output

**Validated 2026-03-05.** Firecrawl search returns different JSON structures depending on the `--sources` flag:

#### Web results (default, all non-news sources):
```json
{
  "data": {
    "web": [
      {
        "url": "https://...",
        "title": "...",
        "description": "...",
        "markdown": "..." // only if --scrape was used; empty string for Reddit (blocked)
      }
    ]
  }
}
```

#### News results (when using `--sources news`):
```json
{
  "data": {
    "news": [
      {
        "url": "https://...",
        "title": "...",
        "snippet": "...",
        "date": "4 weeks ago",
        "imageUrl": "...",
        "position": 1
      }
    ]
  }
}
```

**IMPORTANT:** News uses `snippet` (not `description`) and `data.news[]` (not `data.web[]`).

#### File existence
When Firecrawl returns 0 results, the output file is NOT created. Always check file existence before reading.

Map to CrawledItem:
- `url` -> `url`
- `title` -> `title`
- Content priority: `markdown` (if non-empty) > `snippet` (news) > `description` (web) -> `content` (truncated)
- Extract `date` (see Date Extraction below)
- Set `source` based on which crawl command produced this result

### Date Extraction

Try to extract publication date in this priority order:
1. **News `date` field** (if source is news): Contains relative dates ("4 weeks ago") or formatted dates ("Jul 23, 2025"). Parse to ISO format.
2. Explicit date in Firecrawl metadata (if present)
3. Date pattern in URL (e.g., `/2025/03/15/`)
4. Date mentioned near the top of the content
5. Date in page title
6. If none found: set `date_confidence: "unknown"` and leave `date` empty

## Deduplication Strategy

Apply deduplication after normalizing all results across all sources.

### Primary: URL-based

Same URL from multiple search queries = keep the first occurrence (from higher-priority source).

```
# Pseudocode
seen_urls = set()
for item in all_crawled_items (sorted by source priority):
    normalized_url = strip_tracking_params(item.url)
    if normalized_url not in seen_urls:
        seen_urls.add(normalized_url)
        keep(item)
    else:
        discard(item)  # duplicate
```

**URL normalization before comparison:**
- Remove tracking parameters (`utm_*`, `ref`, `source`, `fbclid`, etc.)
- Remove trailing slashes
- Normalize `http://` to `https://`
- Remove `www.` prefix

### Secondary: Title Similarity

For items with different URLs but very similar titles (>80% word overlap):
- Likely the same content syndicated across sites
- Keep the item with more content (longer `content` field)
- Mark the discarded item's URL as an alternate source

## Source Coverage Summary Format

After crawling and normalization, output this summary (Dutch default):

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

English version (when `--lang en`):

```
Source Coverage:
  Reddit:        ✓ 23 results
  News:          ✓ 30 results
  Hacker News:   ✓ 8 results
  Quora:         ✗ No results found
  Trustpilot:    ✓ 12 results
  X/Twitter:     ⚠ 3 results (limited -- via search engine workaround)
  LinkedIn:      ✗ Blocked

  Total: 76 results from 4/7 sources
  After deduplication: 68 unique results
```

### Status Icons

| Icon | Meaning | Condition |
|------|---------|-----------|
| ✓ | Success | 5+ results |
| ⚠ | Limited | 1-4 results, or source with known limitations (X/Twitter, LinkedIn) |
| ✗ | Failed/No results | 0 results or crawl error |

### Quality Threshold

- A source with fewer than 5 results is marked as "beperkt" (limited) in the summary
- Sources with 0 results are marked with ✗
- X/Twitter and LinkedIn always get ⚠ even with 5+ results (due to workaround limitations)
