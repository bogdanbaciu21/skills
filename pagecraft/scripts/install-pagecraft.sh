#!/bin/sh
# Install Pagecraft assets and checks into a repo.
#
# Usage:
#   sh install-pagecraft.sh /path/to/repo [static-root]
#
# static-root is optional and defaults to the repo root. The installer copies
# assets only; it does not edit application templates automatically.

set -eu

skill_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target=${1:-$(pwd)}
static_root=${2:-"$target"}

mkdir -p "$target/scripts" "$target/tests/pagecraft" "$target/assets/css"

cp "$skill_dir/assets/css/pagecraft.css" "$target/assets/css/pagecraft.css"
cp "$skill_dir/assets/wrapcheck-pagecraft.js" "$target/tests/pagecraft/wrapcheck.js"
cp "$skill_dir/scripts/check-pagecraft-policy.sh" "$target/scripts/check-pagecraft-policy.sh"
cp "$skill_dir/scripts/check-text-wrap.py" "$target/scripts/check-text-wrap.py"
chmod +x "$target/scripts/check-pagecraft-policy.sh" "$target/scripts/check-text-wrap.py"

if [ -d "$skill_dir/assets/wrap-lab" ]; then
  rm -rf "$target/tests/pagecraft/wrap-lab"
  mkdir -p "$target/tests/pagecraft/wrap-lab"
  cp "$skill_dir/assets/wrap-lab/"*.html "$target/tests/pagecraft/wrap-lab/" 2>/dev/null || true
fi

if [ ! -f "$target/tests/pagecraft/wrap-known-issues.json" ]; then
  printf '%s\n' '{"known":[]}' > "$target/tests/pagecraft/wrap-known-issues.json"
fi

cat <<MSG
Pagecraft installed.

CSS:          assets/css/pagecraft.css
Policy:       scripts/check-pagecraft-policy.sh --full
Browser wrap: python3 scripts/check-text-wrap.py --root "$static_root" --known-issues tests/pagecraft/wrap-known-issues.json

Add assets/css/pagecraft.css to the app's HTML/CSS entrypoint, then wire the two checks into pre-commit, pre-push, or CI.
MSG
