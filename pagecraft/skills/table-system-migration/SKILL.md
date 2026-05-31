---
name: table-system-migration
description: Audit, migrate, and regression-test table systems across content-heavy websites, blogs, documentation sites, and admin surfaces. Use when Codex needs to normalize many ad hoc HTML table styles into a canonical table component, preserve legacy/admin table behavior, build a no-new-violations ratchet, add real-browser CSS regression coverage for table layout, or prepare a public-safe writeup/skill from a private table cleanup.
---

# Table System Migration

## Overview

Use this skill to turn a messy estate of one-off HTML tables into a durable table system: a canonical component, compatibility rules for legacy/admin surfaces, a ratcheting linter, and real-browser layout regression tests.

## Confidentiality Gate

Before writing or publishing any reusable output, scrub it as if the target repository is public.

- Do not include local absolute paths, private repo names, production domains, customer names, emails, usernames, hostnames, tokens, passwords, keys, analytics IDs, database credentials, or commit hashes.
- Do not paste private source files, proprietary copy, unreleased content, exact defect counts, or internal incident details into the skill or writeup.
- Generalize examples. Prefer "content site", "admin grid", "canonical table class", and "legacy table class" over project-specific names.
- If the user explicitly wants project-specific wording, keep it in the private repo or ask before staging it in a public skills repo.
- Run a secret/string scan on the final diff before staging. Treat suspicious matches as blockers until explained or removed.

## Workflow

### 1. Map The Table Estate

Inspect the repository before editing.

- Identify content directories, templates/components, CSS entry points, generated assets, test commands, and CI gates.
- Inventory table markup patterns: canonical classes, legacy classes, wrapper classes, naked `<table>` elements, per-page `<style>` blocks, captions, footnotes, scroll wrappers, numeric cells, total rows, and admin/data-grid tables.
- Separate user-facing content tables from operational/admin grids. They may share CSS selectors but often need different layout behavior.
- Note existing failures or intentional baseline debt. Do not promise a full cleanup if the requested task is only a ratchet or migration of priority surfaces.

### 2. Define The Canonical System

Specify the smallest table API that covers the real use cases.

- Choose one canonical table class and one canonical wrapper class.
- Define header, body, numeric, label, total-row, caption, source, footnote, methodology/detail, grouped-header, and horizontal-scroll behavior only when each is actually needed.
- Preserve a compatibility layer for legacy/admin table classes if removing them would widen the blast radius.
- Avoid one-off per-post or per-page table classes unless they encode a genuinely distinct component.

### 3. Migrate In Risk Order

Make narrow, reviewable passes.

- Start with the reported broken table or highest-traffic content.
- Convert repeated old patterns to the canonical wrapper/table pair.
- Keep content semantics intact: headings remain headings, captions remain captions, source notes remain source notes, and data values do not change unless the user asked for content edits.
- Preserve intentional wide-table behavior with a wrapper-level scroll container instead of forcing every cell to wrap.
- For a long supporting table that sits below a summary or callout, collapse it by default inside a native disclosure element and surface a row-count or scope hint in the toggle, so the summary carries the answer and the full table stays available as on-demand detail.
- Avoid unrelated copy edits while touching content files.

### 4. Add A Ratchet

Add a deterministic check that blocks new table debt without requiring a full historical cleanup.

- Start from the bundled `table-ratchet.py` script and
  `references/table-ratchet-checklist.md` when the target repo does not already
  have a table-debt gate. The checklist lives under `references/` because it is
  implementation guidance; the executable script stays at the skill root so it
  can be copied or invoked directly.
- Configure the canonical table class, canonical wrapper class, generated-folder excludes, and any narrow legacy/admin table allowlists before creating the baseline.
- Scan content/templates for new unsanctioned table classes, new per-page table CSS, and new unwrapped tables.
- Store a baseline when legacy debt already exists.
- Refresh the baseline only after reviewing current debt and confirming the
  new counts are intentional:

```bash
python3 table-ratchet.py --root <repo> \
  --canonical-table-class <class> \
  --canonical-wrapper-class <wrapper> \
  --write-baseline
```

- Fail only when a file exceeds the baseline or a new file introduces debt.
- Print actionable remediation text: which file regressed, what count increased, and which canonical classes to use.

### 5. Add Real-Browser Regression Tests

Use browser-backed tests for layout behavior that DOM-only environments cannot see.

- Mount minimal fixtures for each shared surface: content table, admin grid, wide table, caption/source block, total row, grouped header, and any special numeric alignment convention.
- Assert computed style and actual box geometry where layout matters: widths, min-width behavior, wrapping, sticky columns, overflow, hover backgrounds, and padding after prose resets.
- Build/import the real compiled CSS bundle rather than duplicating CSS in the test.
- Include at least one test that protects admin/data-grid tables from changes made for prose/content tables.

### 6. Validate Before Calling Done

Run the smallest complete gate set for the touched stack.

- Run the table ratchet.
- If using the bundled artifact, run `python3 table-ratchet.py --root <repo> ...` with the same class and allowlist flags used to write the baseline.
- Rebuild CSS/assets if tests import generated bundles.
- Run browser/CSS regression tests.
- Run compile/type/lint checks that CI uses for touched code.
- Check `git diff --check` and confirm the working tree contains only intended files.
- If full tests are known to have unrelated failures, report the exact focused gates that passed and the known reason full tests were not used.

## Output Contract

When reporting status, distinguish these clearly:

- **Landed changes:** canonical CSS/classes, migrated files, tests, linter, docs.
- **Verification:** exact commands run and pass/fail results, including the table-ratchet command and baseline path if one was added.
- **Remaining debt:** legacy classes/unwrapped tables that are intentionally baselined.
- **Review notes:** files staged, files not staged, and any suspicious scrub findings that were removed or intentionally kept.

## Example Prompts

- "Use `$table-system-migration` to migrate this blog's tables to one canonical component and add a no-new-violations check."
- "Use `$table-system-migration` after this table CSS change; I want proof that admin grids did not collapse."
- "Use `$table-system-migration` to turn this private table cleanup into a public-safe skill without leaking project details."

## Skill Maintenance

When editing the ratchet script, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_table_ratchet.py
```
