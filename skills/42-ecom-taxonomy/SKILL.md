---
name: 42-ecom-taxonomy
description: >
  eCommerce category taxonomy discovery from product inventory. Analyzes product
  titles to discover missing category pages via n-gram extraction, and checks
  breadcrumb relevancy with fuzzy matching. Use when user says "taxonomy",
  "category discovery", "missing categories", "breadcrumb analysis",
  "breadcrumb relevancy", "product categorization", "categorie ontdekking",
  "taxonomie analyse", "broodkruimel controle", "ontbrekende categorieen",
  "subcategorie suggesties", "product misclassificatie".
version: 1.0.0
tags: [seo, ecommerce, taxonomy, categories, breadcrumbs, n-grams, product-titles]
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
metadata:
  filePattern:
    - "**/*product*"
    - "**/*taxonomy*"
    - "**/*categor*"
    - "**/*breadcrumb*"
    - "**/ECOM-TAXONOMY.md"
  bashPattern:
    - "taxonomy"
    - "breadcrumb"
    - "category.discover"
---

# eCommerce Taxonomy Discovery & Breadcrumb Relevancy

## Purpose

Discover missing category/subcategory pages from product title patterns and audit breadcrumb accuracy. Two complementary modes:

1. **Category Discovery:** Extract repeated n-gram phrases from product titles that suggest missing category pages
2. **Breadcrumb Relevancy:** Detect miscategorized products by comparing product titles against their breadcrumb path

---

## Commands

```
/42:ecom-taxonomy discover <products.csv> [--min-frequency 5] [--ngram-range 2-3]
/42:ecom-taxonomy breadcrumbs <sf-crawl.csv> [--threshold 0.6]
```

---

## Mode 1 — Category Discovery

### Input

CSV with product data. Flexible column names — the script detects:
- **title**: product title / product name / naam / titel
- **category**: category / categorie / department / afdeling
- **url**: url / address / page / link

### Workflow

1. **Parse product CSV** — normalize column names, handle encoding
2. **Extract n-grams** per existing category:
   - Bigrams and trigrams from product titles (configurable via `--ngram-range`)
   - Stopword removal (Dutch + English)
   - Lowercase normalization
3. **Count frequency** of each n-gram within its parent category
4. **Filter by minimum frequency** (default: 5 products sharing the same n-gram)
5. **Cross-reference with existing category pages:**
   - Does a category page already exist for this phrase?
   - If yes: skip. If no: flag as new category opportunity
6. **Rank opportunities** by: `frequency x estimated_search_value`
   - Higher frequency = more products to fill the category
   - Search value estimated from phrase commercial intent signals

### Example Output

```
Category: "Laptops"
  Suggested subcategory: "gaming laptop" (found in 47 product titles)
  Suggested subcategory: "laptop 15 inch" (found in 31 product titles)
  Suggested subcategory: "laptop touchscreen" (found in 18 product titles)

Category: "Telefoons"
  Suggested subcategory: "refurbished iphone" (found in 23 product titles)
  Suggested subcategory: "telefoon hoesje" (found in 15 product titles)
```

---

## Mode 2 — Breadcrumb Relevancy

### Input

Screaming Frog crawl CSV or any CSV containing:
- **url**: page URL
- **h1** or **title**: product title or H1
- **breadcrumb**: breadcrumb path (e.g., "Home > Electronics > Laptops > Gaming")

### Workflow

1. **Parse crawl data** with breadcrumb information
2. **For each product URL:**
   - Extract the deepest breadcrumb level (last segment = assigned category)
   - Compare product title/H1 with breadcrumb category name
   - Calculate fuzzy similarity using RapidFuzz (token_sort_ratio)
3. **Flag mismatches** where similarity < threshold (default: 0.6)
4. **Group flagged products** by current breadcrumb category
5. **Suggest better categories** based on title keywords matching other existing categories

### Example Output

```
MISCATEGORIZED PRODUCTS (similarity < 0.60):

URL: /product/sony-wh1000xm5-headphones
  Title: "Sony WH-1000XM5 Wireless Noise Cancelling Headphones"
  Breadcrumb: Home > Computers > Accessories
  Similarity: 0.22
  Suggested: Home > Audio > Headphones

URL: /product/samsung-galaxy-tab-s9
  Title: "Samsung Galaxy Tab S9 11 inch Tablet 128GB"
  Breadcrumb: Home > Telefoons > Smartphones
  Similarity: 0.31
  Suggested: Home > Tablets
```

---

## Running the Script

```bash
# Category Discovery
python3 scripts/taxonomy_discovery.py discover products.csv --min-frequency 5 --ngram-range 2-3

# Breadcrumb Relevancy
python3 scripts/taxonomy_discovery.py breadcrumbs sf-crawl.csv --threshold 0.6
```

### Dependencies

```bash
pip install nltk rapidfuzz
```

The script outputs JSON to stdout. Claude reads the JSON and generates the final ECOM-TAXONOMY.md report.

---

## Output Format — ECOM-TAXONOMY.md

```markdown
# eCommerce Taxonomy Analysis

## Executive Summary
- X new category opportunities discovered across Y parent categories
- Z miscategorized products detected

## New Category Opportunities

### [Parent Category]
| Suggested Category | Product Count | Example Products | Exists? |
|-------------------|--------------|-----------------|---------|
| gaming laptop     | 47           | Asus ROG, MSI...| No      |

## Miscategorized Products

| URL | Current Category | Suggested Category | Similarity | Title |
|-----|-----------------|-------------------|-----------|-------|
| /product/... | Computers > Accessories | Audio > Headphones | 0.22 | Sony WH... |

## Recommendations
1. Create new category pages for top opportunities
2. Fix breadcrumb paths for miscategorized products
3. Review categories with >10 miscategorized products
```

---

## Cross-references

- **42:internal-links** — After discovering new categories, audit internal links to/from them
- **42:keyword-mapper** — Map search keywords to newly discovered categories
- **42:seo-plan** — Incorporate new category pages into the SEO roadmap
