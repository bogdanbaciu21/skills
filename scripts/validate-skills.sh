#!/usr/bin/env bash
set -euo pipefail

errors=0

has_any_heading() {
  local file="$1"
  shift
  local pattern
  for pattern in "$@"; do
    if rg -q "$pattern" "$file"; then
      return 0
    fi
  done
  return 1
}

for skill_file in */SKILL.md; do
  [ -f "$skill_file" ] || continue

  rg -q '^name:\s*' "$skill_file" || { echo "ERROR: Missing frontmatter name in $skill_file"; errors=1; }
  rg -q '^description:\s*' "$skill_file" || { echo "ERROR: Missing frontmatter description in $skill_file"; errors=1; }

  if ! has_any_heading "$skill_file" '^## Workflow' '^## When invoked'; then
    echo "ERROR: Missing required workflow-style section in $skill_file"
    errors=1
  fi

  if ! has_any_heading "$skill_file" '^## Output format' '^## Output rules' '^### Output rules'; then
    echo "ERROR: Missing required output-style section in $skill_file"
    errors=1
  fi
done

if [ "$errors" -ne 0 ]; then exit 1; fi

echo "All skills passed validation."
