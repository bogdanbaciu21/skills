# Table Ratchet Checklist

Use this checklist when adding a no-new-debt guard to a site that already has
legacy table markup. The goal is not to clean every table immediately. The goal
is to stop the estate from getting worse while priority tables migrate to the
canonical system.

## 1. Configure The Contract

- Pick one canonical prose/content table class.
- Pick one canonical wrapper class for wide or scrollable tables.
- Identify legacy/admin table classes that are intentionally exempt.
- Decide which generated folders should be excluded from source scanning.

Example:

```sh
python3 pagecraft/skills/table-system-migration/table-ratchet.py \
  --root . \
  --canonical-table-class content-table \
  --canonical-wrapper-class table-scroll \
  --allow-table-class admin-grid \
  --allow-unwrapped-table-class admin-grid \
  --write-baseline
```

## 2. Review The Baseline

- Open `.table-ratchet-baseline.json`.
- Confirm the debt counts match known legacy files.
- If a count is surprising, inspect that file before committing the baseline.
- Keep the baseline generic and public-safe: no private domains, customer names,
  internal incident details, or local absolute paths.

## 3. Wire The Ratchet

Add the check to the smallest reliable gate: package script, pre-commit hook, or
CI job.

```sh
python3 pagecraft/skills/table-system-migration/table-ratchet.py \
  --root . \
  --canonical-table-class content-table \
  --canonical-wrapper-class table-scroll \
  --allow-table-class admin-grid \
  --allow-unwrapped-table-class admin-grid
```

The check should fail only when a file exceeds its baseline count or a new file
introduces table debt.

## 4. Acceptance Checks

- New prose/content tables use the canonical table class.
- Wide tables sit inside the canonical wrapper.
- Table-specific inline CSS moves into the shared table stylesheet.
- Intentional admin/data-grid behavior is allowlisted by class, not by broad
  directory exemption.
- The failure message names the file, violation type, old count, new count, and
  sample line numbers.
- The full validation report distinguishes landed changes, verification, and
  remaining baselined debt.

## 5. Refresh Discipline

- Refresh the baseline only after reviewing the current diff.
- Do not refresh the baseline to hide new debt.
- When legacy debt is removed, regenerate the baseline so future regressions are
  blocked at the lower count.
- Run `git diff --check` and a secret/string scan before publishing reusable
  ratchet artifacts.
