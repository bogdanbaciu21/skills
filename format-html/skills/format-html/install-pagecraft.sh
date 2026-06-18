#!/bin/sh
# Install the Pagecraft bundle (the real, proven tools) into a repo.
#
# Usage:
#   sh install-pagecraft.sh /path/to/repo [static-root]
#
# static-root is optional and defaults to the repo root. Copies the bundled CSS,
# the wrap-safe probe, and the verifiers. It does not edit app templates — add
# assets/css/pagecraft.css to the app's CSS entrypoint yourself.

set -eu

# This script lives in the pagecraft overview skill. The probe + verifiers are
# self-contained in the sibling verify-text-wrap skill in both plugin and flat
# installs.
skill_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -d "$skill_dir/../verify-text-wrap" ]; then
  vtw_dir=$(CDPATH= cd -- "$skill_dir/../verify-text-wrap" && pwd)
elif [ -d "$skill_dir/verify-text-wrap" ]; then
  vtw_dir=$(CDPATH= cd -- "$skill_dir/verify-text-wrap" && pwd)
else
  echo "ERR_PAGECRAFT_INSTALL missing verify-text-wrap sibling for $skill_dir" >&2
  exit 2
fi
target=${1:-$(pwd)}
static_root=${2:-"$target"}
pagecraft_version=$(git -C "$skill_dir" rev-parse --short HEAD 2>/dev/null || printf '%s' "0.1.0")

mkdir -p "$target/scripts" "$target/tests/pagecraft" "$target/assets/css"

# CSS — the comprehensive Pagecraft stylesheet (keystone + .bbt + number formats)
# plus the minimal wrap-safe reset for repos that want only the reset.
cp "$skill_dir/assets/css/pagecraft.css" "$target/assets/css/pagecraft.css"
cp "$vtw_dir/wrap-safe.css"              "$target/assets/css/wrap-safe.css"

# Probe + verifiers — the real implementations from the verify-text-wrap skill.
# runner.py defaults to a wrapcheck.js sibling, so install one next to it in
# scripts/; also drop a copy in assets/ for sites that <script src> the probe.
cp "$vtw_dir/wrapcheck.js"       "$target/assets/wrapcheck.js"
cp "$vtw_dir/wrapcheck.js"       "$target/scripts/wrapcheck.js"
cp "$vtw_dir/check-keystone.py"  "$target/scripts/check-keystone.py"
cp "$vtw_dir/runner.py"          "$target/scripts/runner.py"
cp "$vtw_dir/browserbase.py"     "$target/scripts/browserbase.py"
chmod +x "$target/scripts/check-keystone.py" "$target/scripts/runner.py"

# Synthetic good/bad fixtures for testing the checker without keeping broken pages.
if [ -d "$skill_dir/assets/wrap-lab" ]; then
  rm -rf "$target/tests/pagecraft/wrap-lab"
  mkdir -p "$target/tests/pagecraft/wrap-lab"
  cp "$skill_dir/assets/wrap-lab/"*.html "$target/tests/pagecraft/wrap-lab/" 2>/dev/null || true
fi

if [ ! -f "$target/tests/pagecraft/wrap-known-issues.json" ]; then
  printf '%s\n' '{"known":[]}' > "$target/tests/pagecraft/wrap-known-issues.json"
fi

cat > "$target/tests/pagecraft/pagecraft-install.json" <<JSON
{
  "pagecraft_version": "$pagecraft_version",
  "version_source": "git-commit-or-local-fallback",
  "installed_assets": [
    "assets/css/pagecraft.css",
    "assets/css/wrap-safe.css",
    "assets/wrapcheck.js",
    "scripts/wrapcheck.js",
    "scripts/check-keystone.py",
    "scripts/runner.py",
    "scripts/browserbase.py"
  ],
  "self_test": "python3 scripts/check-keystone.py --css assets/css/pagecraft.css --quiet"
}
JSON

echo "Running Pagecraft install self-test..."
if command -v python3 >/dev/null 2>&1; then
  (cd "$target" && python3 scripts/check-keystone.py --css assets/css/pagecraft.css --quiet)
else
  echo "  ! python3 not found; skipping check-keystone self-test" >&2
fi

cat <<MSG
Pagecraft bundle installed into: $target

  Manifest       tests/pagecraft/pagecraft-install.json
  CSS            assets/css/pagecraft.css   — add to the app's HTML/CSS entrypoint
  Keystone guard python3 scripts/check-keystone.py --portal "$static_root"
                 (deterministic, no browser — wire into pre-commit + CI)
  Browser probe  python3 scripts/runner.py --local --portal "$static_root" \\
                   --known-issues tests/pagecraft/wrap-known-issues.json
                 (8-viewport wrap + right-edge check — run post-edit / post-deploy)

For migrating a messy table estate to one canonical component, use the
table-system-migration skill alongside this bundle.
MSG
