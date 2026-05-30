#!/bin/sh
# sync-skills.sh — propagate canonical skills from THIS marketplace repo to the
# machine-level skill dirs that already carry them, ending copy-drift.
#
# Canonical source = this repo (the dir holding this script). Targets = every
# ~/.<tool>/skills that already contains the 'handoff' skill, so we only refresh
# real installs and never inject skills into unrelated (e.g. firecrawl-only) dirs.
#
# Usage:
#   sh sync-skills.sh <skill> [<skill> ...]   # sync the named skill(s)
#   sh sync-skills.sh --all                   # sync every skill in this repo
#   sh sync-skills.sh --all --dry-run         # preview only, change nothing
set -u
REPO=$(cd "$(dirname "$0")" && pwd)

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
  SKILLS=$(find "$REPO" -maxdepth 2 -name SKILL.md -exec dirname {} \; | sed "s#^$REPO/##" | sort -u)
elif [ -n "$NAMED" ]; then
  SKILLS="$NAMED"
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
echo "skills    :$SKILLS"
[ -n "$DRY" ] && echo "(dry-run — no changes written)"
echo

rc=0
for t in $TARGETS; do
  for s in $SKILLS; do
    if [ ! -d "$REPO/$s" ]; then echo "  ! '$s' not in repo — skip"; rc=1; continue; fi
    printf "==> %s\n" "$t/$s"
    rsync -a $DRY --delete \
      --exclude '.git' --exclude '.DS_Store' --exclude '__pycache__' --exclude '*.pyc' \
      "$REPO/$s/" "$t/$s/" || { echo "  ! rsync failed for $t/$s"; rc=1; }
  done
done
echo
echo "${DRY:+[dry-run] }sync complete (rc=$rc)"
exit "$rc"
