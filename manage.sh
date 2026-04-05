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

  local req_file="$SCRIPT_DIR/requirements.txt"
  if [ ! -f "$req_file" ]; then
    red "✗ requirements.txt not found"
    return 1
  fi

  # Single Python call checks all packages at once
  local result
  result=$($python -c "
import importlib.metadata, re, sys

# Read requirements.txt
core, optional = [], []
with open('$req_file') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            # Extract commented package name
            m = re.match(r'#\s*([a-zA-Z][a-zA-Z0-9_-]+)', line)
            if m and m.group(1) not in ('Also', 'pip', 'Tip'):
                optional.append(m.group(1))
        elif not line.startswith('#'):
            pkg = re.split(r'[><=!]', line)[0].strip()
            if pkg:
                core.append(pkg)

installed = {d.metadata['Name'].lower(): d.version for d in importlib.metadata.distributions()}

core_missing = 0
print('SECTION:core')
for pkg in core:
    ver = installed.get(pkg.lower())
    if ver:
        print(f'OK:{pkg}:{ver}')
    else:
        print(f'MISS:{pkg}')
        core_missing += 1

opt_missing = 0
print('SECTION:optional')
for pkg in optional:
    ver = installed.get(pkg.lower())
    if ver:
        print(f'OK:{pkg}:{ver}')
    else:
        print(f'MISS:{pkg}')
        opt_missing += 1

print(f'STATS:{core_missing}:{opt_missing}')
" 2>/dev/null)

  local core_missing_count=0
  local opt_missing_count=0
  local section=""

  while IFS= read -r line; do
    case "$line" in
      SECTION:core)
        echo
        echo "Core dependencies:"
        section="core"
        ;;
      SECTION:optional)
        echo
        echo "Optional dependencies:"
        section="optional"
        ;;
      OK:*)
        local pkg ver
        pkg=$(echo "$line" | cut -d: -f2)
        ver=$(echo "$line" | cut -d: -f3)
        green "  ✓ $pkg ($ver)"
        ;;
      MISS:*)
        local pkg
        pkg=$(echo "$line" | cut -d: -f2)
        if [ "$section" = "core" ]; then
          red "  ✗ $pkg"
          core_missing_count=$((core_missing_count + 1))
        else
          dim "  ○ $pkg (not installed)"
          opt_missing_count=$((opt_missing_count + 1))
        fi
        ;;
      STATS:*)
        core_missing_count=$(echo "$line" | cut -d: -f2)
        opt_missing_count=$(echo "$line" | cut -d: -f3)
        ;;
    esac
  done <<< "$result"

  # Summary
  echo
  if [ "$core_missing_count" -eq 0 ]; then
    green "✓ All core dependencies installed"
  else
    red "✗ $core_missing_count core dependencies missing"
    if $fix; then
      echo
      yellow "Installing core dependencies..."
      $python -m pip install -r "$req_file"
    else
      echo
      echo "Run to fix:"
      echo "  pip install -r $req_file"
      echo
      echo "Or: $(basename "$0") check --fix"
    fi
  fi

  if [ "$opt_missing_count" -gt 0 ]; then
    dim "$opt_missing_count optional packages not installed (install as needed)"
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
