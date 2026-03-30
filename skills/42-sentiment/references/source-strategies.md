# Source Crawl Strategies

Per-source Firecrawl CLI commands and strategies for the Sentiment42 skill.
Loaded by SKILL.md during crawl orchestration.

**Validated:** 2026-03-05 with Firecrawl CLI v1.9.4, tested against "Tesla" query.

## Variables

All commands below use these template variables:
- `{query}` -- the user's search query (freeform text)
- `{slug}` -- URL-safe query slug (lowercase, hyphens, max 30 chars)
- `{depth}` -- result limit mapped from `--depth` flag:
  - `snel` = 10 (primary sources), 10 (secondary)
  - `normaal` = 30 (primary sources), 10 (secondary)
  - `diep` = 50 (primary sources), 10 (secondary)
- Primary sources: Reddit, News
- Secondary sources: all others (Forums, Reviews, Social)

## Credit Cost Estimate

Tested with "Tesla" query (2026-03-05):
- 9 search commands consumed 29 credits total
- Basic search (no --scrape): ~2 credits per command
- Search with --scrape: ~5-7 credits per command (depends on content size)
- Estimated cost for `--depth snel` (all sources): ~25-35 credits
- Estimated cost for `--depth normaal`: ~40-60 credits
- Estimated cost for `--depth diep`: ~60-90 credits

## Time Period Mapping

Map the `--period` flag to Firecrawl `--tbs` parameter:

| Period | `--tbs` value | Notes |
|--------|---------------|-------|
| 1m | `qdr:m` | Past month |
| 3m | `qdr:m3` | Past 3 months |
| 1y | `qdr:y` | Past year |
| 3y | _(omit --tbs)_ | Filter by date in post-processing |
| 5y | _(omit --tbs)_ | Filter by date in post-processing |

For periods 3y and 5y, omit the `--tbs` flag entirely and filter results by date during normalization.

When `--tbs` is applicable, append it to every `firecrawl search` command.

## Source 1: Reddit (CRAWL-01) -- Primary

**Strategy:** Search WITHOUT scraping. Reddit blocks Firecrawl's scrape step -- `--scrape` returns empty markdown while still costing extra credits.

**Validated behavior (2026-03-05):**
- `--scrape --scrape-formats markdown`: Returns 10 results but markdown field is always empty (0 chars). Reddit's anti-scraping blocks content extraction. Wastes credits.
- Without `--scrape`: Returns 10 results with useful description snippets (~140 chars each). Same URLs and titles. More credit-efficient.

**Command:**
```bash
firecrawl search "{query} site:reddit.com" --limit {depth} --json -o .firecrawl/sentiment/{slug}/reddit.json
```

Add `{tbs_flag}` if period is 1y or less.

Do NOT use `--scrape` -- it wastes credits and returns empty markdown due to Reddit's anti-scraping measures.

**Fallback (two-phase for --depth diep):** If deeper content is needed for specific high-value threads:
```bash
# Phase 2: Scrape top 3-5 individual post URLs for full content
firecrawl scrape "{post_url}" -o .firecrawl/sentiment/{slug}/reddit-post-{n}.md
```
Only use this fallback when `--depth diep` is selected and for the most relevant threads. Each individual scrape costs additional credits.

**Depth mapping:** Uses primary depth (snel=10, normaal=30, diep=50).

**Expected output:** JSON with `data.web[]` array containing:
- `url` -- Reddit post URL (includes subreddit URLs and post URLs)
- `title` -- Post title
- `description` -- Snippet (~140 chars, useful for sentiment)

**Note:** Results may include subreddit landing pages (e.g., `reddit.com/r/teslamotors/`) alongside actual posts. Filter for URLs containing `/comments/` to get actual discussion threads.

**Extracting results:**
```bash
# Count results
jq '.data.web | length' .firecrawl/sentiment/{slug}/reddit.json

# Extract URLs and titles
jq -r '.data.web[] | "\(.title): \(.url)"' .firecrawl/sentiment/{slug}/reddit.json
```

**Known limitations:**
- Reddit anti-scraping blocks the `--scrape` step entirely (empty markdown)
- Description snippets are short (~140 chars) but contain useful sentiment signals
- Results include subreddit pages alongside actual posts -- filter by URL pattern
- Older Reddit threads may not be well-indexed

**Retry:** 1x retry on failure, then skip. Report as failed source.

---

## Source 2: News (CRAWL-02) -- Primary

**Strategy:** Use `--sources news` flag to get actual news articles. Broad web search returns generic pages (company websites, Wikipedia) that are not useful for sentiment analysis.

**Validated behavior (2026-03-05):**
- Broad search (no --sources flag): Returns generic web results -- Tesla.com, Wikipedia, X.com profile. NOT useful for sentiment.
- `--sources news`: Returns actual news articles from outlets like The Atlantic, Barron's, CNBC with headlines and article snippets. MUCH better for sentiment analysis.
- Results go into `data.news[]` array (not `data.web[]`) when using `--sources news`.

**Command:**
```bash
firecrawl search "{query}" --sources news --limit {depth} --json -o .firecrawl/sentiment/{slug}/news.json
```

Add `{tbs_flag}` if period is 1y or less.

Do NOT use `--scrape` for news (search snippets are usually sufficient for sentiment analysis, saves credits).

ALWAYS use `--sources news` -- broad web search returns generic pages that are not useful for sentiment.

**Depth mapping:** Uses primary depth (snel=10, normaal=30, diep=50).

**Expected output:** JSON with `data.news[]` array containing:
- `url` -- Article URL
- `title` -- Article headline
- `description` -- Article snippet/summary (~100-160 chars)

**IMPORTANT:** When using `--sources news`, results are in `data.news[]` NOT `data.web[]`. The result counting command must be adjusted:
```bash
# Count results
jq '.data.news | length' .firecrawl/sentiment/{slug}/news.json

# Extract URLs and titles
jq -r '.data.news[] | "\(.title): \(.url)"' .firecrawl/sentiment/{slug}/news.json
```

**Known limitations:**
- Paywalled articles show truncated content
- Date accuracy varies by source
- News results are already curated -- no need for Claude to filter out non-news items

**Retry:** 1x retry on failure, then skip.

---

## Source 3: Forums (CRAWL-03) -- Secondary

Three sub-sources, each run as a separate command:

### 3a: Hacker News

**Validated behavior (2026-03-05):**
- `--scrape` works excellently on HN -- returns full discussion threads with all comments
- Content sizes are large (90K-346K chars per result) -- content truncation is essential
- HN is the highest-value forum source for sentiment -- rich discussion threads with genuine opinions

```bash
firecrawl search "{query} site:news.ycombinator.com" --scrape --scrape-formats markdown --limit 10 --json -o .firecrawl/sentiment/{slug}/hn.json
```

Add `{tbs_flag}` if period is 1y or less.

Use `--scrape` for HN -- it works and provides full discussion threads (comments are valuable for sentiment). Note: scraping HN uses more credits (~5-7 per search) but the content quality justifies it.

**WARNING:** HN scraped content is very large (up to 346K chars per result). ALWAYS truncate to ~1000 words during normalization.

### 3b: Quora

**Validated behavior (2026-03-05):**
- Returns 10 results with description snippets (~150 chars)
- No markdown (scrape not used) -- descriptions contain question and partial answer text
- Results come from topic-specific Quora spaces (e.g., teslafollowers.quora.com)
- Usable for sentiment but lower quality than Reddit/HN

```bash
firecrawl search "{query} site:quora.com" --limit 10 --json -o .firecrawl/sentiment/{slug}/quora.json
```

Add `{tbs_flag}` if period is 1y or less.

No `--scrape` for Quora (search snippets usually contain the answer; saves credits).

### 3c: Niche Forums

Claude determines 1-2 relevant niche forums based on the query topic. Examples:

| Topic domain | Relevant forums |
|-------------|-----------------|
| Automotive / Tesla | `site:teslamotorsclub.com`, `site:bimmerpost.com` |
| Gaming | `site:resetera.com`, `site:neogaf.com` |
| Tech / software | `site:lobste.rs`, `site:slashdot.org` |
| Finance | `site:bogleheads.org`, `site:wallstreetbets.com` |
| Health / fitness | `site:myfitnesspal.com`, `site:patient.info` |
| Photography | `site:dpreview.com`, `site:fredmiranda.com` |
| Home / DIY | `site:diychatroom.com`, `site:gardenersworld.com` |

**Guidance for Claude:** Think about what specialized communities discuss this topic. If no obvious niche forum exists, skip this sub-source. Do NOT force a niche forum -- only add one if it is genuinely relevant.

```bash
firecrawl search "{query} site:{niche-forum}" --limit 10 --json -o .firecrawl/sentiment/{slug}/forum-{name}.json
```

**Depth mapping:** Always 10 results (secondary source).

**Known limitations:**
- HN discussions can be very technical; sentiment may skew negative
- Quora quality varies; some answers are SEO spam
- Niche forums may not be well-indexed for all topics

**Retry:** 1x retry per sub-source on failure, then skip that sub-source.

---

## Source 4: Review Sites (CRAWL-04) -- Secondary

**Validated behavior (2026-03-05, Trustpilot):**
- Returns 10 results with description snippets containing review counts and rating mentions
- Results are mostly aggregate review pages (e.g., "Tesla Reviews | Read Customer Service Reviews of...")
- Individual reviews are not returned -- aggregate pages are the norm
- No markdown needed -- descriptions contain useful summary sentiment

Claude selects relevant review sites based on the query topic:

| Topic type | Review sites |
|-----------|-------------|
| Consumer products | `site:trustpilot.com`, `site:amazon.com` (reviews) |
| SaaS / tech products | `site:g2.com`, `site:capterra.com` |
| Restaurants / local | `site:yelp.com` |
| Travel / hospitality | `site:tripadvisor.com` |
| General (always include) | `site:trustpilot.com` |

**Command pattern:**
```bash
firecrawl search "{query} site:{review-site}" --limit 10 --json -o .firecrawl/sentiment/{slug}/{site-name}.json
```

Add `{tbs_flag}` if period is 1y or less.

No `--scrape` for review sites (search snippets include ratings and review text).

**Guidance for Claude:** Always include Trustpilot. Add 1-2 more review sites relevant to the topic. Do NOT include all review sites for every query.

**Depth mapping:** Always 10 results (secondary source).

**Expected output:** JSON with `data.web[]` array. Look for:
- Rating numbers in title or description (e.g., "4.2/5", "3 stars")
- Review text snippets
- Review count indicators

**Known limitations:**
- Review site search results return aggregate pages, not individual reviews
- Amazon review scraping is limited; aggregate ratings are more reliable
- Some review sites block or limit indexed content
- Multiple regional Trustpilot domains may appear (e.g., ca.trustpilot.com, www.trustpilot.com)

**Retry:** 1x retry per review site on failure, then skip that site.

---

## Source 5: X/Twitter (CRAWL-05) -- Secondary

**Strategy:** Search engine index workaround. Direct x.com scraping is blocked by Firecrawl.

**Validated behavior (2026-03-05):**
- The site:x.com workaround works -- returned 10 results for "Tesla"
- Results include official accounts (@Tesla), individual tweet URLs, and profile pages
- Description snippets (~150 chars) contain tweet text
- No markdown content (not using --scrape)
- Better results than expected -- the workaround is viable for sentiment analysis

**Command:**
```bash
firecrawl search "{query} site:x.com" --limit 10 --json -o .firecrawl/sentiment/{slug}/twitter.json
```

Add `{tbs_flag}` if period is 1y or less.

Do NOT use `--scrape` (saves credits; x.com direct scraping is blocked anyway).

**Depth mapping:** Always 10 results (secondary source).

**Known limitations:**
- Results come from Google's index of x.com, NOT from Twitter's API
- Coverage is shallow -- many tweets are not indexed
- Results mix official accounts with individual tweets -- filter for `/status/` URLs to get actual tweets
- Recent tweets (past few hours/days) are unlikely to appear
- Content is limited to what search engines have cached (~150 char descriptions)
- Report this limitation clearly in the source coverage summary

**Retry:** 1x retry on failure, then skip. Acceptable to have 0 results.

---

## Source 6: LinkedIn -- Secondary

**Strategy:** Same search engine index workaround as X/Twitter.

**Validated behavior (2026-03-05):**
- The site:linkedin.com workaround works -- returned 10 results for "Tesla"
- Results include: company pages, LinkedIn Pulse articles, and individual posts
- Description snippets (~100-150 chars) contain post/article previews
- Better than expected -- LinkedIn articles (Pulse) and posts are indexed
- Company pages are noise -- filter for `/pulse/` and `/posts/` URLs for actual content

**Command:**
```bash
firecrawl search "{query} site:linkedin.com" --limit 10 --json -o .firecrawl/sentiment/{slug}/linkedin.json
```

Add `{tbs_flag}` if period is 1y or less.

Do NOT use `--scrape` (LinkedIn blocks direct scraping).

**Depth mapping:** Always 10 results (secondary source).

**Known limitations:**
- Mix of company pages, job postings, articles, and posts -- filter for content URLs
- Most LinkedIn content requires authentication to view full text
- Description snippets are short but usable for basic sentiment
- LinkedIn Pulse articles are the highest-value results from this source
- Low priority source -- acceptable to have 0 results

**Retry:** 1x retry on failure, then skip. Acceptable to have 0 results.

---

## Parallel Execution Pattern

Execute sources in priority groups with status updates between groups:

```bash
mkdir -p .firecrawl/sentiment/{slug}

# === Priority Group 1: Reddit + News (high priority, run first) ===
firecrawl search "{query} site:reddit.com" --limit {depth} {tbs_flag} --json -o .firecrawl/sentiment/{slug}/reddit.json &
PID_REDDIT=$!
firecrawl search "{query}" --sources news --limit {depth} {tbs_flag} --json -o .firecrawl/sentiment/{slug}/news.json &
PID_NEWS=$!
wait $PID_REDDIT $PID_NEWS
# >> Report status for Reddit and News

# === Priority Group 2: Forums (HN, Quora, niche) ===
firecrawl search "{query} site:news.ycombinator.com" --scrape --scrape-formats markdown --limit 10 {tbs_flag} --json -o .firecrawl/sentiment/{slug}/hn.json &
PID_HN=$!
firecrawl search "{query} site:quora.com" --limit 10 {tbs_flag} --json -o .firecrawl/sentiment/{slug}/quora.json &
PID_QUORA=$!
# (niche forum commands added here if applicable)
wait $PID_HN $PID_QUORA
# >> Report status for Forums

# === Priority Group 3: Review sites + Social (low priority) ===
firecrawl search "{query} site:trustpilot.com" --limit 10 {tbs_flag} --json -o .firecrawl/sentiment/{slug}/trustpilot.json &
PID_TP=$!
# (additional review site commands)
firecrawl search "{query} site:x.com" --limit 10 {tbs_flag} --json -o .firecrawl/sentiment/{slug}/twitter.json &
PID_TW=$!
firecrawl search "{query} site:linkedin.com" --limit 10 {tbs_flag} --json -o .firecrawl/sentiment/{slug}/linkedin.json &
PID_LI=$!
wait $PID_TP $PID_TW $PID_LI
# >> Report status for Reviews + Social
```

**Between each group:** Read output files, count results per source, print status line.

**Result counting:** Note that News results are in `data.news[]` (when using `--sources news`) while all other sources use `data.web[]`:
```bash
# For news:
jq '.data.news | length' .firecrawl/sentiment/{slug}/news.json 2>/dev/null || echo 0

# For all other sources:
jq '.data.web | length' .firecrawl/sentiment/{slug}/{source}.json 2>/dev/null || echo 0
```

**Status line format:**
```
Crawling Reddit...        ✓ 23 resultaten
Crawling Nieuws...        ✓ 30 resultaten
Crawling Hacker News...   ✓ 8 resultaten
Crawling Quora...         ✗ Geen resultaten
Crawling Trustpilot...    ✓ 12 resultaten
Crawling X/Twitter...     ⚠ 3 resultaten (beperkt)
Crawling LinkedIn...      ✗ Geblokkeerd
```

Use Dutch labels by default (unless `--lang en`).
