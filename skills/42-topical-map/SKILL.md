---
name: 42-topical-map
description: >
  AI-generated hierarchical topic maps (2-5 levels deep) from keyword lists.
  Organizes keywords into pillar pages, topic clusters, and subtopics for
  content architecture. Classifies existing content into topic hierarchies.
  Identifies content gaps and orphaned pages. Use when user says "topical map",
  "topic cluster", "content architecture", "pillar pages", "topic hierarchy",
  "content structure", "keyword grouping", "hub and spoke", "topic tree",
  "classify content", "content mapping", "topic taxonomy".
version: 1.0.0
tags: [seo, geo, topical-map, topic-clusters, pillar-pages, content-architecture, keyword-grouping, taxonomy]
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - WebFetch
metadata:
  filePattern:
    - "**/*keyword*"
    - "**/*topic*"
    - "**/*cluster*"
    - "**/*pillar*"
    - "**/*.csv"
  bashPattern:
    - "topical.map"
    - "topic.cluster"
    - "content.architecture"
---

# Topical Map Generator — AI-Powered Content Architecture

## Purpose

Build hierarchical topic maps from keyword lists or classify existing content into a structured taxonomy. Topic maps are the foundation of content strategy — they define which pillar pages anchor the site, which cluster pages support them, and where content gaps exist.

Two modes:

1. **Generate Map** — Transform a keyword list into a 2-5 level topic hierarchy
2. **Classify Content** — Map existing pages into topic clusters and find orphaned content

---

## Commands

```
/42:topical-map <keywords.csv> [--levels 3] [--format tree|table|json]
/42:topical-map classify <content.csv>
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--levels` | `3` | Depth of hierarchy (2-5). Level 1 = pillars, 2 = clusters, 3-5 = subtopics |
| `--format` | `tree` | Output format: `tree` (indented), `table` (markdown table), `json` (structured) |

---

## Input Formats

### Mode 1: Keyword CSV (Generate Map)

Required column: `keyword`. Optional columns: `volume`, `intent`.

```csv
keyword,volume,intent
project management software,12000,commercial
agile project management,8100,informational
kanban board tools,3600,commercial
scrum vs kanban,2400,informational
how to run a sprint retrospective,1900,informational
```

If `volume` and `intent` columns are missing, the AI infers intent from keyword phrasing and assigns relative priority.

### Mode 2: Content CSV (Classify Content)

Required columns: `url`, `title`. Optional column: `h1`.

```csv
url,title,h1
https://example.com/project-management,Project Management Guide,The Complete Guide to Project Management
https://example.com/agile,Agile Methodology,What Is Agile?
https://example.com/kanban-tools,Best Kanban Tools 2025,10 Best Kanban Tools Compared
```

---

## Workflow — Mode 1: Generate Map

### Step 1: Parse and Batch Keywords

Read the keyword CSV. If the list exceeds 200 keywords, batch into groups of 200 for processing. Deduplicate exact matches. Normalize casing. Count total unique keywords.

### Step 2: Identify Pillar Topics (Level 1)

Analyze the full keyword set to identify **5-15 pillar topics** — the broadest thematic categories. Pillars are:

- High-volume head terms or broad concepts
- Distinct enough to avoid overlap (< 20% keyword sharing between pillars)
- Comprehensive enough to anchor 5+ cluster topics each

For each pillar, assign:
- **Pillar name** — Short, descriptive label (2-4 words)
- **Pillar keyword** — The single best target keyword for this pillar page
- **Content type** — Always "pillar"
- **Estimated total volume** — Sum of all keywords under this pillar

### Step 3: Group Into Topic Clusters (Level 2)

For each pillar, group related keywords into **topic clusters**. Each cluster:

- Shares semantic similarity (related entities, modifiers, or intent)
- Contains 3-20 keywords
- Has a clear "cluster keyword" (highest volume or most representative)
- Maps to a single page or content piece

Assign each cluster:
- **Cluster name** — Descriptive label
- **Parent pillar** — Which pillar this belongs to
- **Content type** — "cluster"
- **Primary keyword** — Best target keyword for this cluster page
- **Search intent** — Informational / commercial / transactional / navigational

### Step 4: Subdivide Into Subtopics (Levels 3-5)

Based on `--levels` flag, further subdivide clusters into subtopics. Each subtopic:

- Answers a specific question or addresses a narrow angle
- Contains 1-5 keywords
- Has a clear parent cluster
- Maps to supporting content (blog post, FAQ, comparison page)

Assign each subtopic:
- **Subtopic name**
- **Parent cluster**
- **Content type** — "supporting"
- **Primary keyword**
- **Suggested content format** — How-to guide, listicle, comparison, FAQ, case study, definition

### Step 5: Map Hub-and-Spoke Relationships

For each pillar, define the internal linking architecture:

- **Hub page** — The pillar page (spoke center)
- **Spoke pages** — Cluster pages that link to/from the hub
- **Leaf pages** — Subtopic pages that link to their parent cluster

Identify cross-cluster links where topics in different clusters share keywords or entities.

### Step 6: Identify Content Gaps

Scan the completed map for:

- **Thin clusters** — Clusters with fewer than 3 keywords (may need more research)
- **Missing intents** — Pillars without commercial or informational coverage
- **Orphan keywords** — Keywords that do not fit any cluster (flag for review)
- **Suggested additions** — Topics implied by the taxonomy but missing from the keyword list

---

## Workflow — Mode 2: Classify Content

### Step 1: Read Content Inventory

Parse the content CSV. Extract URL, title, and H1 for each page. If H1 is missing, use title as proxy.

### Step 2: Derive Topic Taxonomy

Analyze all titles and H1s to inductively build a topic taxonomy:

- Identify recurring themes and entities across titles
- Group pages by semantic similarity
- Build a 2-3 level hierarchy from the content itself

### Step 3: Classify Each Page

For each piece of content, assign:

| Field | Description |
|-------|-------------|
| **Primary topic** | The single best-fit topic cluster |
| **Hub category** | The pillar-level category |
| **Subtopics** | Array of 0-3 related subtopics this page also covers |
| **Content type** | Pillar / cluster / supporting |
| **Confidence** | High / medium / low — how well the page fits its assigned cluster |

### Step 4: Identify Orphaned Content

Flag pages that:

- Do not fit any identified cluster (confidence = low)
- Cover topics no other page addresses (isolated)
- Have titles unrelated to the site's core themes

### Step 5: Identify Missing Content

Compare the derived taxonomy against the content inventory:

- **Empty clusters** — Topic clusters with zero pages
- **Thin clusters** — Clusters with only 1 page (need supporting content)
- **Missing content types** — Clusters without a pillar page, or pillars without supporting content
- **Suggested pages** — Specific content pieces to fill each gap, with suggested titles

---

## Output Format

Output file: `TOPICAL-MAP.md` in the working directory.

### Tree Format (default)

```
# Topical Map — [Domain/Topic]

## Summary
- Total keywords: 247
- Pillars: 8
- Clusters: 34
- Subtopics: 89
- Orphan keywords: 12

## Topic Tree

### 1. Project Management (pillar) — "project management software" [12,000 vol]
  ├── 1.1 Agile Methodology (cluster) — "agile project management" [8,100 vol]
  │   ├── 1.1.1 Scrum Framework (supporting) — "scrum methodology" [2,900 vol]
  │   ├── 1.1.2 Kanban Method (supporting) — "kanban vs scrum" [2,400 vol]
  │   └── 1.1.3 Sprint Planning (supporting) — "how to plan a sprint" [1,200 vol]
  ├── 1.2 Project Management Tools (cluster) — "best PM tools" [6,600 vol]
  │   ├── 1.2.1 Tool Comparisons (supporting) — "asana vs monday" [3,100 vol]
  │   └── 1.2.2 Free PM Tools (supporting) — "free project management software" [2,200 vol]
  └── 1.3 Team Collaboration (cluster) — "team collaboration tools" [4,400 vol]

## Content Gaps
- [List of missing topics and suggested content]

## Hub-and-Spoke Map
- [Internal linking recommendations per pillar]
```

### Table Format

| # | Level | Topic | Parent | Content Type | Primary Keyword | Volume | Intent | Suggested Format |
|---|-------|-------|--------|-------------|----------------|--------|--------|-----------------|
| 1 | 1 | Project Management | — | Pillar | project management software | 12,000 | Commercial | Ultimate guide |
| 1.1 | 2 | Agile Methodology | Project Management | Cluster | agile project management | 8,100 | Informational | Hub page |
| 1.1.1 | 3 | Scrum Framework | Agile Methodology | Supporting | scrum methodology | 2,900 | Informational | How-to guide |

### JSON Format

```json
{
  "domain": "example.com",
  "generated": "2025-01-15",
  "summary": { "total_keywords": 247, "pillars": 8, "clusters": 34, "subtopics": 89 },
  "topics": [
    {
      "id": "1",
      "name": "Project Management",
      "level": 1,
      "content_type": "pillar",
      "primary_keyword": "project management software",
      "volume": 12000,
      "children": [
        {
          "id": "1.1",
          "name": "Agile Methodology",
          "level": 2,
          "content_type": "cluster",
          "parent": "1",
          "primary_keyword": "agile project management",
          "volume": 8100,
          "children": []
        }
      ]
    }
  ],
  "content_gaps": [],
  "orphan_keywords": []
}
```

---

## AI Configuration

- **Model:** OpenAI `gpt-4o-mini` (cost-efficient for large keyword sets) or Anthropic Claude
- **Prompt engineering:** Request structured JSON output from the model. Enforce consistent taxonomy labels across batches. Use few-shot examples for intent classification.
- **Batching:** Process in groups of 200 keywords. After each batch, merge results into the running taxonomy to maintain consistency.
- **Temperature:** 0.3 (low creativity, high consistency for classification tasks)

---

## Prompt Template (Internal)

For pillar identification:

```
Analyze these keywords and identify 5-15 pillar topics (broadest thematic categories).
Each pillar must be distinct (< 20% keyword overlap with other pillars).
Return as JSON: [{"name": "...", "keyword": "...", "rationale": "..."}]

Keywords:
{keyword_list}
```

For cluster grouping:

```
Given pillar topic "{pillar_name}", group these keywords into topic clusters.
Each cluster: 3-20 keywords, clear primary keyword, single search intent.
Return as JSON: [{"name": "...", "primary_keyword": "...", "intent": "...", "keywords": [...]}]

Keywords under this pillar:
{filtered_keywords}
```

---

## Cross-References

- **42:seo-plan** — Use topical map output as input for content strategy planning
- **42:keyword-mapper** — Map keywords to existing pages after building the topic hierarchy
- **42:content** — Assess content quality for pages within each cluster
- **42:serp-cluster** — Validate clusters against actual SERP overlap
