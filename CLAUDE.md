# CLAUDE.md — 42 SEO Skills

## Wat is dit

54 Claude Code skills voor SEO, GEO en content-analyse in `skills/` subfolder. Elke skill is een directory met een `SKILL.md` en optioneel Python scripts in `scripts/` en referentiedata in `references/`.

## Installatie

```bash
./manage.sh install     # symlinks alle skills naar ~/.claude/skills/
./manage.sh check       # toont ontbrekende Python dependencies
./manage.sh check --fix # installeert ontbrekende core deps
./manage.sh status      # welke skills zijn actief
./manage.sh uninstall   # verwijdert alle symlinks
```

## Architectuurbeslissingen

### Symlinks ipv kopiëren
Skills worden als symlinks in `~/.claude/skills/` geplaatst, niet gekopieerd. Wijzigingen in de repo zijn direct actief. Het `manage.sh` script houdt een `.installed` manifest bij voor clean uninstall.

### Skills in subfolder
Alle 54 skill directories zitten in `skills/`. Root bevat alleen `manage.sh`, `CLAUDE.md`, `README.md`, `requirements.txt`, `.env.example`, en `references/`.

### Shared references via symlinks
Drie skills (`42-content`, `42-keyword-mapper`, `42-near-duplicates`) refereren naar `references/` maar hebben geen eigen references dir. Het install-script maakt automatisch symlinks aan: `skills/42-content/references → ../../references/`. Skills met eigen references (42-audit, 42-genai-optimizer, 42-screaming-frog, 42-sentiment, 42-seo-agi) worden niet aangepast.

### Eén embedding model
Alle embeddings gebruiken Gemini `text-embedding-004`. Screaming Frog, keyword_embedder.py, en similarity.py moeten hetzelfde model gebruiken — anders zijn vectoren incompatibel.

### Core vs optional dependencies
`requirements.txt` scheidt core (altijd nodig) van optional (per skill). `manage.sh check` toont beide met installatiestatus. Core: google-generativeai, beautifulsoup4, requests, lxml, numpy, scipy, urllib3, validators, Pillow. Optional: playwright, reportlab, textstat, networkx, rapidfuzz, spacy, nltk, plotly, google-auth.

### Orchestrator hiërarchie
```
42:seo-project  → lifecycle orchestrator (7 fasen, state over sessies)
  ↓
42:audit        → single-session audit orchestrator
  ↓
42:technical, 42:content, 42:structured-data, 42:geo-report  → geconsolideerd
  ↓
48 specialist skills
```

### Skill naming
Alle skills hebben `42-` prefix. Commands gebruiken `42:` (met dubbele punt). Dit voorkomt conflicten met andere skill packages.

## API Keys

Via `.env` (kopieer `.env.example`). Automatisch geladen door `references/load_env.py`.

| Key | Waarvoor |
|-----|----------|
| `GOOGLE_API_KEY` | Gemini embeddings + AI |
| `DATAFORSEO_LOGIN` / `PASSWORD` | SERP data, keywords |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | GSC data pull |

## Conventies

- Alle Python scripts in `scripts/` subdirectory
- Referentiedata in `references/` (per skill of shared)
- SKILL.md bevat altijd YAML frontmatter met: name, description, version, tags, allowed-tools
- Geconsolideerde skills ondersteunen `--seo` / `--geo` mode flags
- Output gaat naar stdout, nooit naar bestanden tenzij expliciet gevraagd (--output)
