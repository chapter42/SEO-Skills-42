---
name: 42-product-titles
description: >
  Product title optimization via competitor gap analysis (MPN-matched),
  SERP-driven title patterns, and AI title standardization. Finds missing
  keywords in your product titles vs competitors, analyzes winning SERP
  title patterns by word position, and generates standardized title
  templates per category. Use when user says "product titles", "title gap",
  "competitor titles", "title optimization", "product title vergelijking",
  "titel optimalisatie", "MPN matching", "SERP title pattern", "title
  template", "titel standaardisatie", "product naam analyse".
version: 1.0.0
tags: [seo, ecommerce, product-titles, competitor-analysis, serp-patterns, title-optimization]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*product*"
    - "**/*title*"
    - "**/*competitor*"
    - "**/*serp*"
    - "**/PRODUCT-TITLES.md"
  bashPattern:
    - "product.title"
    - "title.gap"
    - "title.pattern"
---

# Product Title Optimization — Gap Analysis, SERP Patterns & Standardization

## Purpose

Optimize product titles through three complementary approaches:

1. **Competitor Title Gap:** Match products by MPN/SKU/GTIN, find words competitors use that you don't
2. **SERP Title Patterns:** Analyze position-based word frequency in ranking titles to discover winning patterns
3. **AI Standardization:** Generate consistent title templates per category and rewrite all titles to match

---

## Commands

```
/42:product-titles gap <your-products.csv> <competitor-products.csv>
/42:product-titles serp-pattern <serp-titles.csv>
/42:product-titles standardize <products.csv> [--template "{brand} {product} {color} {size}"]
```

---

## Mode 1 — Competitor Title Gap

### Input

Two CSV files with product data. Must contain:
- **title**: product title / product name
- **mpn** or **sku** or **gtin/ean**: identifier for matching
- Optional: **category**, **brand**

### Workflow

1. **Match products** across catalogs by MPN/SKU/GTIN:
   - Exact match first (normalized: stripped, lowered, no leading zeros)
   - Fuzzy fallback with RapidFuzz (threshold: 90) for minor format differences
2. **For each matched pair:**
   - Tokenize both titles
   - Extract words present in competitor title but absent in yours
   - Record the "missing words" per product
3. **Aggregate missing words** by frequency across all products:
   - Most commonly missing words = highest priority enrichment
   - Group by category if available
4. **Rank by search potential** (if volume data attached to CSV)

### Example Output

```
TOP MISSING WORDS (across 234 matched products):

Word          | Missing From | Competitor Uses | Example
"waterproof"  | 47 titles    | 47/47           | "Sony WF-1000XM5 Waterproof..."
"bluetooth"   | 31 titles    | 31/31           | "JBL Flip 6 Bluetooth Speaker..."
"2024"        | 28 titles    | 28/28           | "Samsung Galaxy S24 2024..."
```

---

## Mode 2 — SERP Title Patterns

### Input

CSV with SERP title data (from Screaming Frog SERP export or DataForSEO):
- **title**: SERP result title
- **position/rank**: ranking position
- **keyword/query**: search query (optional, for grouping)
- **category**: product category (optional)

### Workflow

1. **Parse SERP titles** from ranking pages
2. **Analyze word frequency by position** in the title:
   - Position 1 (first word), position 2, position 3, etc.
   - What words appear most at each position?
3. **Identify patterns** per category/query group:
   - "Brand always comes first" (brand at position 1 in 87% of top-3 results)
   - "Color appears in positions 4-6" (color word at position 4-6 in 62%)
   - "Size/spec at end" (measurement unit at position 7+ in 71%)
4. **Generate data-driven title templates** based on patterns

### Example Output

```
SERP TITLE PATTERNS — Category: "Headphones"

Position | Most Common Words (top 3 results)
1        | Brand name (89%): Sony, Bose, JBL...
2        | Model identifier (76%): WH-1000XM5, QC45...
3        | Product type (68%): Headphones, Earbuds...
4-5      | Feature (54%): Wireless, Noise Cancelling...
6-7      | Modifier (41%): Over-Ear, In-Ear...
8+       | Color/variant (29%): Black, White...

Suggested template: "{Brand} {Model} {Type} {Feature} {Modifier} {Color}"
```

---

## Mode 3 — AI Standardization

### Input

Product CSV with titles and categories. Optional: `--template` flag with desired format.

### Workflow

1. **Analyze existing titles** per category:
   - Extract common components (brand, product type, color, size, features)
   - Detect current inconsistencies
2. **Generate standardized template** per category:
   - Default: `{Brand} {Product Type} {Key Feature} {Size/Spec} - {Differentiator}`
   - Or use user-provided template
3. **Claude rewrites all titles** to consistent format:
   - Preserves all factual information
   - Standardizes order and formatting
   - Adds missing searchable attributes from product data

### Example Output

```
BEFORE → AFTER:

"Sony headphones noise cancel WH1000XM5 black"
→ "Sony WH-1000XM5 Wireless Noise Cancelling Over-Ear Headphones - Black"

"Apple 15 inch laptop MacBook Air M3"
→ "Apple MacBook Air 15 inch M3 Laptop - 2024"
```

---

## Running the Script

```bash
# Competitor Title Gap
python3 scripts/product_title_gap.py gap your-products.csv competitor-products.csv

# SERP Title Patterns
python3 scripts/product_title_gap.py serp-pattern serp-titles.csv

# Standardize (template generation only — Claude does the rewriting)
python3 scripts/product_title_gap.py standardize products.csv --template "{brand} {product} {color} {size}"
```

### Dependencies

```bash
pip install rapidfuzz
```

The script outputs JSON to stdout. Claude reads the JSON and generates the final PRODUCT-TITLES.md report. For Mode 3 (standardize), Claude uses the pattern analysis from the script and applies AI rewriting.

---

## Output Format — PRODUCT-TITLES.md

```markdown
# Product Title Optimization Report

## Executive Summary
- X products matched across catalogs
- Y unique missing words identified
- Z title pattern templates generated

## Competitor Title Gap Analysis

### Most Commonly Missing Words
| Word | Missing From | Priority | Category |
|------|-------------|----------|----------|
| waterproof | 47 titles | HIGH | Audio |

### Per-Product Gap Details
| Your Title | Competitor Title | Missing Words | MPN |
|-----------|-----------------|--------------|-----|
| Sony WH... | Sony WH-1000XM5 Waterproof... | waterproof | WH1000XM5 |

## SERP Title Patterns
### [Category]
| Position | Pattern | Frequency |
|----------|---------|-----------|
| 1 | Brand | 89% |

## Standardized Titles
| Original | Rewritten | Changes Made |
|----------|-----------|-------------|
| ... | ... | Added brand prefix, standardized format |

## Recommendations
1. Add top 10 missing words to affected product titles
2. Adopt SERP-winning title patterns per category
3. Implement standardized templates in PIM system
```

---

## Cross-references

- **42:meta-optimizer** — Optimize meta descriptions after title optimization
- **42:striking-distance** — Find which optimized titles push pages to page 1
- **42:ecom-taxonomy** — Align product titles with category taxonomy
