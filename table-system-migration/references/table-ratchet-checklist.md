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
python3 format-html/skills/table-system-migration/table-ratchet.py \
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
python3 format-html/skills/table-system-migration/table-ratchet.py \
  --root . \
  --canonical-table-class content-table \
  --canonical-wrapper-class table-scroll \
  --allow-table-class admin-grid \
  --allow-unwrapped-table-class admin-grid
```

### npm script

```json
{
  "scripts": {
    "test:tables": "python3 format-html/skills/table-system-migration/table-ratchet.py --root . --canonical-table-class content-table --canonical-wrapper-class table-scroll"
  }
}
```

### pytest wrapper

```python
import subprocess


def test_table_ratchet():
    result = subprocess.run(
        [
            "python3",
            "format-html/skills/table-system-migration/table-ratchet.py",
            "--root",
            ".",
            "--canonical-table-class",
            "content-table",
            "--canonical-wrapper-class",
            "table-scroll",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
```

### GitHub Actions

```yaml
name: table-ratchet
on: [pull_request]
jobs:
  table-ratchet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: python3 format-html/skills/table-system-migration/table-ratchet.py --root . --canonical-table-class content-table --canonical-wrapper-class table-scroll
```

## 4. Acceptance Checks

- New prose/content tables use the canonical table class.
- Wide tables sit inside the canonical wrapper.
- Table-specific inline CSS moves into the shared table stylesheet.
- No `canonical_override`: no page-local rule out-specifies the canonical header
  (e.g. `table.legacy thead th { background }` ties the canonical `table.<c>
  thead th` at 0,1,3 and wins on source order). Adding the class is not enough —
  the canonical styling must actually win. Verify the computed `thead th`
  background after a cache-bypassing reload. Genuine data-viz (heatmaps,
  color-encoded matrices, frozen-corner pivots) are allowlisted, not flattened.
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
