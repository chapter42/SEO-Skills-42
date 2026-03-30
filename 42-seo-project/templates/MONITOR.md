# Monitoring — {{DOMAIN}}

**Monitoring since:** {{DATE}}
**Check interval:** 30 days
**Next check due:** {{NEXT_DATE}}

---

## Score History

| Date | SEO Score | GEO Score | SEO Delta | GEO Delta | Notes |
|------|-----------|-----------|-----------|-----------|-------|
| {{DATE}} | {{SCORE}} | {{SCORE}} | baseline | baseline | Initial discovery |
| {{DATE}} | {{SCORE}} | {{SCORE}} | {{DELTA}} | {{DELTA}} | Post-implementation |

---

## Trend

```
SEO: {{SCORE}} → {{SCORE}} → {{SCORE}}  ({{OVERALL_TREND}})
GEO: {{SCORE}} → {{SCORE}} → {{SCORE}}  ({{OVERALL_TREND}})
```

---

## Recent Check: {{DATE}}

### Changes Since Last Check
- {{CHANGE}}

### New Issues Detected
- {{ISSUE or "None"}}

### Content Decay Signals
- {{SIGNAL or "None detected"}}

### New Opportunities
- {{OPPORTUNITY or "None identified"}}

---

## Action Items from Monitoring

| # | Action | Priority | Status | Added |
|---|--------|----------|--------|-------|
| M-01 | {{ACTION}} | {{PRIORITY}} | pending | {{DATE}} |

---

## Audit Snapshots

Full audit snapshots are stored in `history/`:
- `history/audit-{{DATE}}.md` — {{DESCRIPTION}}
