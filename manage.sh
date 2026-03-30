#!/usr/bin/env bash
set -euo pipefail

# ─── Config ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
SKILLS_TARGET="$HOME/.claude/skills"
MANIFEST="$SCRIPT_DIR/.installed"

# ─── Helpers ──────────────────────────────────────────────────────────
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
dim()    { printf '\033[2m%s\033[0m\n' "$*"; }

die() { red "Error: $*" >&2; exit 1; }

# Find all skill dirs (contain SKILL.md) inside skills/
find_skills() {
  find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" -exec dirname {} \; | sort
}

# ─── Install ──────────────────────────────────────────────────────────
cmd_install() {
  local dry_run=false
  [[ "${1:-}" == "--dry-run" ]] && dry_run=true

  mkdir -p "$SKILLS_TARGET"

  local count=0
  local skipped=0
  local ref_count=0

  : > "$MANIFEST.tmp"

  while IFS= read -r skill_dir; do
    local name
    name=$(basename "$skill_dir")

    local target="$SKILLS_TARGET/$name"

    # Skip if real directory (not symlink) already exists
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      yellow "  SKIP $name (real directory exists, not overwriting)"
      skipped=$((skipped + 1))
      continue
    fi

    if $dry_run; then
      dim "  WOULD link $name → $skill_dir"
    else
      ln -sfn "$skill_dir" "$target"
      echo "$name" >> "$MANIFEST.tmp"
      count=$((count + 1))
    fi

    # Fix shared references: if skill references references/ but has none
    if grep -q 'references/' "$skill_dir/SKILL.md" 2>/dev/null; then
      if [ ! -e "$skill_dir/references" ]; then
        if $dry_run; then
          dim "  WOULD add shared references → $name/references"
        else
          ln -sfn "$SCRIPT_DIR/references" "$skill_dir/references"
          ref_count=$((ref_count + 1))
        fi
      fi
    fi

  done < <(find_skills)

  if $dry_run; then
    echo
    dim "Dry run — no changes made."
  else
    mv "$MANIFEST.tmp" "$MANIFEST"
    echo
    green "✓ Installed $count skills into $SKILLS_TARGET"
    [ "$ref_count" -gt 0 ] && dim "  + $ref_count shared reference links added"
    [ "$skipped" -gt 0 ] && yellow "  $skipped skipped (real directories)"
  fi
}

# ─── Uninstall ────────────────────────────────────────────────────────
cmd_uninstall() {
  if [ ! -f "$MANIFEST" ]; then
    # Fallback: remove any symlink in skills/ pointing into our dir
    yellow "No manifest found, scanning for links pointing here..."
    local count=0
    for link in "$SKILLS_TARGET"/*/; do
      link="${link%/}"
      if [ -L "$link" ]; then
        local target
        target=$(readlink "$link" 2>/dev/null || true)
        if [[ "$target" == "$SCRIPT_DIR"* ]]; then
          rm "$link"
          count=$((count + 1))
        fi
      fi
    done
    green "✓ Removed $count symlinks"
  else
    local count=0
    while IFS= read -r name; do
      local target="$SKILLS_TARGET/$name"
      if [ -L "$target" ]; then
        rm "$target"
        count=$((count + 1))
      fi
    done < "$MANIFEST"
    rm "$MANIFEST"
    green "✓ Removed $count symlinks"
  fi

  # Clean up shared reference symlinks inside skill dirs
  local ref_count=0
  while IFS= read -r skill_dir; do
    if [ -L "$skill_dir/references" ]; then
      rm "$skill_dir/references"
      ref_count=$((ref_count + 1))
    fi
  done < <(find_skills)
  [ "$ref_count" -gt 0 ] && dim "  + $ref_count shared reference links removed"
}

# ─── Check Python deps ────────────────────────────────────────────────
cmd_check() {
  local fix=false
  [[ "${1:-}" == "--fix" ]] && fix=true

  # Find python3
  local python
  python=$(command -v python3 2>/dev/null || true)
  if [ -z "$python" ]; then
    red "✗ python3 not found"
    return 1
  fi
  green "✓ python3 → $python ($($python --version 2>&1))"

  # Find pip
  local pip
  pip=$(command -v pip3 2>/dev/null || command -v pip 2>/dev/null || true)
  if [ -z "$pip" ]; then
    red "✗ pip not found"
    return 1
  fi

  # Parse requirements.txt: core (uncommented) and optional (commented)
  local req_file="$SCRIPT_DIR/requirements.txt"
  if [ ! -f "$req_file" ]; then
    red "✗ requirements.txt not found"
    return 1
  fi

  echo
  echo "Core dependencies:"
  local core_missing=()
  local core_ok=0
  while IFS= read -r line; do
    # Skip empty lines and pure comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Extract package name (before >= or any version spec)
    local pkg
    pkg=$(echo "$line" | sed 's/[><=!].*//' | xargs)
    [ -z "$pkg" ] && continue

    if $python -c "import importlib; importlib.import_module('${pkg//-/_}')" 2>/dev/null; then
      local ver
      ver=$($python -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>/dev/null || echo "?")
      green "  ✓ $pkg ($ver)"
      core_ok=$((core_ok + 1))
    else
      red "  ✗ $pkg"
      core_missing+=("$line")
    fi
  done < "$req_file"

  echo
  echo "Optional dependencies:"
  local opt_missing=()
  local opt_ok=0
  while IFS= read -r line; do
    # Only process commented-out packages (lines starting with #)
    [[ "$line" =~ ^[[:space:]]*#[[:space:]]*([a-zA-Z][a-zA-Z0-9_-]*) ]] || continue
    local pkg="${BASH_REMATCH[1]}"
    # Skip lines that are just comments (no package-like pattern)
    [[ "$pkg" == "Also" || "$pkg" == "pip" ]] && continue

    local import_name="${pkg//-/_}"
    if $python -c "import importlib; importlib.import_module('$import_name')" 2>/dev/null; then
      local ver
      ver=$($python -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>/dev/null || echo "?")
      green "  ✓ $pkg ($ver)"
      opt_ok=$((opt_ok + 1))
    else
      dim "  ○ $pkg (not installed)"
      # Extract the commented requirement line
      local req
      req=$(echo "$line" | sed 's/^[[:space:]]*#[[:space:]]*//' | sed 's/[[:space:]]*#.*//')
      opt_missing+=("$req")
    fi
  done < "$req_file"

  # Playwright special check
  if $python -c "import playwright" 2>/dev/null; then
    if command -v npx >/dev/null 2>&1 && npx playwright install --dry-run >/dev/null 2>&1; then
      green "  ✓ playwright browsers"
    else
      yellow "  ⚠ playwright installed but browsers may need: playwright install"
    fi
  fi

  # spaCy model check
  if $python -c "import spacy" 2>/dev/null; then
    if $python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
      green "  ✓ spacy en_core_web_sm model"
    else
      yellow "  ⚠ spacy installed but model missing: python -m spacy download en_core_web_sm"
    fi
  fi

  # Summary
  echo
  if [ ${#core_missing[@]} -eq 0 ]; then
    green "✓ All core dependencies installed"
  else
    red "✗ ${#core_missing[@]} core dependencies missing"
    if $fix; then
      echo
      yellow "Installing core dependencies..."
      $pip install -r "$req_file"
    else
      echo
      echo "Run to fix:"
      echo "  pip install -r $req_file"
      echo
      echo "Or: $(basename "$0") check --fix"
    fi
  fi

  if [ ${#opt_missing[@]} -gt 0 ]; then
    dim "${#opt_missing[@]} optional packages not installed (install as needed)"
  fi
}

# ─── Status ───────────────────────────────────────────────────────────
cmd_status() {
  local installed=0
  local missing=0
  local total=0

  echo "Skills in $(dim "$SCRIPT_DIR"):"
  echo

  while IFS= read -r skill_dir; do
    local name
    name=$(basename "$skill_dir")
    total=$((total + 1))

    local target="$SKILLS_TARGET/$name"
    if [ -L "$target" ]; then
      green "  ● $name"
      installed=$((installed + 1))
    else
      dim "  ○ $name"
      missing=$((missing + 1))
    fi
  done < <(find_skills)

  echo
  echo "$installed/$total installed"
}

# ─── Main ─────────────────────────────────────────────────────────────
case "${1:-help}" in
  install)    cmd_install "${2:-}" ;;
  uninstall)  cmd_uninstall ;;
  check)      cmd_check "${2:-}" ;;
  status)     cmd_status ;;
  help|--help|-h)
    echo "Usage: $(basename "$0") <command>"
    echo
    echo "Commands:"
    echo "  install [--dry-run]  Create symlinks in ~/.claude/skills/"
    echo "  uninstall            Remove symlinks"
    echo "  check [--fix]        Check Python dependencies"
    echo "  status               Show which skills are active"
    echo
    ;;
  *)
    die "Unknown command: $1 (try: install, uninstall, check, status)"
    ;;
esac
