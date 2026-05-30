#!/bin/sh
# Deterministic Pagecraft policy guard.
#
# Usage:
#   sh scripts/check-pagecraft-policy.sh --full
#   sh scripts/check-pagecraft-policy.sh --staged
#   sh scripts/check-pagecraft-policy.sh path/to/file.html path/to/file.css

set -u

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
MIN_GRID_PX=${PAGECRAFT_MIN_GRID_PX:-220}

mode="${1:-}"
files=""

case "$mode" in
  --staged)
    files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(html|css|scss|tsx|jsx|svelte|vue)$' || true)
    ;;
  --full)
    files=$(find "$root" \
      \( -path '*/.git' -o -path '*/node_modules' -o -path '*/vendor' -o -path '*/dist' -o -path '*/build' \) -prune \
      -o -type f \( -name '*.html' -o -name '*.css' -o -name '*.scss' -o -name '*.tsx' -o -name '*.jsx' -o -name '*.svelte' -o -name '*.vue' \) -print | sort)
    ;;
  "")
    files=$(git diff --name-only --diff-filter=ACM HEAD -- . 2>/dev/null | grep -E '\.(html|css|scss|tsx|jsx|svelte|vue)$' || true)
    ;;
  *)
    files="$@"
    ;;
esac

[ -z "$files" ] && {
  echo "pagecraft-policy: no HTML/CSS-like files"
  exit 0
}

bad=0
for f in $files; do
  case "$f" in
    /*) path="$f" ;;
    *) path="$root/$f" ;;
  esac
  [ -f "$path" ] || continue

  out=$(awk -v MIN="$MIN_GRID_PX" '
    /wrap-exempt:|width-exempt:|pagecraft-exempt:/ { next }

    /grid-template-columns:[^;]*repeat\(auto-(fit|fill),[[:space:]]*minmax\([0-9]+px,[[:space:]]*1fr\)/ {
      line = $0
      sub(/.*minmax\(/, "", line)
      sub(/px.*/, "", line)
      n = line + 0
      if (n < MIN) {
        printf "  %s:%d  auto grid minmax(%dpx, 1fr) is too narrow; use >= %dpx or add /* wrap-exempt: reason */\n", FILENAME, NR, n, MIN
      }
    }

    /grid-template-columns:[^;]*repeat\([3-9][0-9]*,[[:space:]]*minmax\(0,[[:space:]]*1fr\)/ {
      printf "  %s:%d  fixed 3+ column minmax(0, 1fr) grid can squeeze text to zero; use auto-fit minmax(%dpx, 1fr) or add /* wrap-exempt: reason */\n", FILENAME, NR, MIN
    }

    /grid-template-columns:[^;]*repeat\([3-9][0-9]*,[[:space:]]*1fr\)/ {
      printf "  %s:%d  fixed 3+ column 1fr grid can squeeze text; use auto-fit minmax(%dpx, 1fr) or add /* wrap-exempt: reason */\n", FILENAME, NR, MIN
    }

    /max-width:[[:space:]]*[0-9.]+ch/ {
      printf "  %s:%d  max-width in ch units recreates inconsistent right edges; move width to the container or add /* width-exempt: reason */\n", FILENAME, NR
    }

    /word-break:[[:space:]]*break-all/ {
      printf "  %s:%d  word-break: break-all garbles words; fix the container instead or add /* wrap-exempt: reason */\n", FILENAME, NR
    }

    /hyphens:[[:space:]]*auto/ {
      printf "  %s:%d  hyphens:auto is not a generic wrap fix; use only after visual proof or add /* wrap-exempt: reason */\n", FILENAME, NR
    }

    /text-wrap:[[:space:]]*(pretty|balance)/ {
      printf "  %s:%d  text-wrap pretty/balance is display-only, not a prose default; add /* wrap-exempt: reason */ if deliberate\n", FILENAME, NR
    }

    /<table([[:space:]>]|$)/ && $0 !~ /(class=|className=)/ {
      printf "  %s:%d  naked <table>; use pc-table/bbt classes or add a repo-specific table component\n", FILENAME, NR
    }
  ' "$path")

  if [ -n "$out" ]; then
    printf "%s\n" "$out"
    bad=1
  fi
done

if [ "$bad" -ne 0 ]; then
  echo ""
  echo "Pagecraft policy violation(s) above."
  echo "Prefer Pagecraft primitives: .pc-grid, .pc-card-grid, .pc-table-wrap + .pc-table, .pc-section-break."
  echo "Real exceptions require an inline /* wrap-exempt: reason */, /* width-exempt: reason */, or /* pagecraft-exempt: reason */ comment."
  exit 1
fi

echo "pagecraft-policy: OK"
exit 0
