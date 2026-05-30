#!/bin/sh
# sync-skills.sh — propagate canonical skills from THIS marketplace repo to the
# machine-level skill dirs that already carry them, ending copy-drift.
#
# Canonical source = this repo (the dir holding this script). Targets = every
# ~/.<tool>/skills that already contains the 'handoff' skill, so we only refresh
# real installs and never inject skills into unrelated (e.g. firecrawl-only) dirs.
#
# Two kinds of source skill are recognized:
#   1. A top-level dir with its own SKILL.md (e.g. handoff/).
#   2. A skill nested inside a multi-skill plugin bundle — a top-level dir that
#      has a skills/ subdir (e.g. pagecraft/skills/verify-text-wrap/).
# Nested skills are FLATTENED on export: each installs as a top-level loose skill
# (~/.tool/skills/<name>/) so tools that don't recurse into a plugin's skills/
# dir still find them by their bare name. Inside the repo they stay bundled.
#
# Usage:
#   sh sync-skills.sh <skill> [<skill> ...]   # sync the named skill(s)
#   sh sync-skills.sh --all                   # sync every skill in this repo
#   sh sync-skills.sh --all --dry-run         # preview only, change nothing
set -u
REPO=$(cd "$(dirname "$0")" && pwd)

# Enumerate every syncable skill as "name<TAB>srcdir", flattening bundles.
enumerate() {
  for d in "$REPO"/*/; do
    name=$(basename "$d")
    [ "$name" = ".git" ] && continue
    if [ -f "$d/SKILL.md" ]; then
      printf '%s\t%s\n' "$name" "${d%/}"
    elif [ -d "${d}skills" ]; then
      for s in "${d}skills"/*/; do
        [ -f "${s}SKILL.md" ] || continue
        printf '%s\t%s\n' "$(basename "$s")" "${s%/}"
      done
    fi
  done
}

ALL_PAIRS=$(enumerate)

DRY=""; ALL=""; NAMED=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY="-n" ;;
    --all)     ALL=1 ;;
    --*)       echo "unknown flag: $a" >&2; exit 2 ;;
    *)         NAMED="$NAMED $a" ;;
  esac
done

if [ -n "$ALL" ]; then
  PAIRS="$ALL_PAIRS"
elif [ -n "$NAMED" ]; then
  PAIRS=""
  for n in $NAMED; do
    match=$(printf '%s\n' "$ALL_PAIRS" | awk -F'\t' -v n="$n" '$1==n')
    if [ -z "$match" ]; then echo "  ! '$n' not found in repo — skip" >&2; continue; fi
    PAIRS="${PAIRS}${match}
"
  done
else
  echo "usage: sh sync-skills.sh <skill>... | --all [--dry-run]" >&2; exit 2
fi

# Only dirs that already carry your skills (detected via the 'handoff' skill).
TARGETS=""
for d in "$HOME"/.*/skills; do
  [ -d "$d/handoff" ] && TARGETS="$TARGETS $d"
done
if [ -z "$TARGETS" ]; then echo "no target skill dirs (none contain 'handoff')" >&2; exit 1; fi

echo "canonical : $REPO"
echo "targets   :$TARGETS"
echo "skills    :$(printf '%s\n' "$PAIRS" | awk -F'\t' 'NF{print $1}' | tr '\n' ' ')"
[ -n "$DRY" ] && echo "(dry-run — no changes written)"
echo

rc=0
for t in $TARGETS; do
  printf '%s\n' "$PAIRS" | while IFS="$(printf '\t')" read -r name src; do
    [ -n "$name" ] || continue
    printf "==> %s\n" "$t/$name"
    rsync -a $DRY --delete \
      --exclude '.git' --exclude '.DS_Store' --exclude '__pycache__' --exclude '*.pyc' \
      "$src/" "$t/$name/" || echo "  ! rsync failed for $t/$name"
  done
done
echo
echo "${DRY:+[dry-run] }sync complete"
