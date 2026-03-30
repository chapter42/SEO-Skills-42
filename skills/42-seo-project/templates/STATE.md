# SEO Project State

```yaml
site: {{URL}}
domain: {{DOMAIN}}
business_type: {{TYPE}}
language: {{LANG}}
created: {{DATE}}
last_updated: {{DATE}}

current_phase: init
phase_status: pending

capabilities:
  screaming_frog: null         # true | false (auto-detected)
  dataforseo: null             # true | false
  gsc: null                    # true | false
  ahrefs: null                 # true | false
  semrush: null                # true | false
  embedding_provider: null     # openai | gemini | anthropic | ollama | null

competitors: []
additional_urls: []

phases:
  init:
    status: pending
    completed_at: null
  crawl:
    status: pending
    completed_at: null
    sf_available: null
    export_path: null
    pages_crawled: null
  discover:
    status: pending
    completed_at: null
    seo_score: null
    geo_score: null
    seo_categories:
      technical: null
      content: null
      on_page: null
      schema: null
      performance: null
      ai_readiness: null
      images: null
    geo_categories:
      citability: null
      brand_mentions: null
      eeat: null
      technical: null
      schema: null
      platform: null
  diagnose:
    status: pending
    completed_at: null
    issues:
      critical: 0
      high: 0
      medium: 0
      low: 0
    skills_run: []
  strategize:
    status: pending
    completed_at: null
    decisions_locked: 0
  implement:
    status: pending
    current_wave: 0
    total_waves: 4
    tasks_completed: 0
    tasks_total: 0
    waves:
      1: { status: pending, tasks: 0, completed: 0 }
      2: { status: pending, tasks: 0, completed: 0 }
      3: { status: pending, tasks: 0, completed: 0 }
      4: { status: pending, tasks: 0, completed: 0 }
  verify:
    status: pending
    completed_at: null
    seo_score_after: null
    geo_score_after: null
    seo_delta: null
    geo_delta: null
  monitor:
    status: pending
    next_check: null
    checks_completed: 0
    score_history: []

blockers: []
notes: []
```
