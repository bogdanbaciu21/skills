# Contract Locations

Dan UX OS and Builder rules are authored in `dans-brain`. Other repos carry
local pointers so Builder Fusion and repo-local agents resolve the same
contract without guessing.

## Authority

| File | Canonical home |
|---|---|
| `DESIGN.md` | `dans-brain/DESIGN.md` |
| `docs/uxos.md` | `dans-brain/docs/uxos.md` |
| `config/uxos/*.json` | `dans-brain/config/uxos/` |
| `.builderrules` | repo-local; `dans-brain` is canonical, other repos use pointers |
| `.builder/rules/*.mdc` | repo-local; `dans-brain` is canonical, other repos use pointers |

## Resolve From The Current Repo

Use the first path that exists on disk. Do not invent a missing contract.

### `dans-brain`

Read repo-local files at the repo root:

- `DESIGN.md`
- `docs/uxos.md`
- `config/uxos/tokens.json`
- `config/uxos/components.json`
- `config/uxos/rules.json`
- `.builderrules`
- `.builder/rules/*.mdc`

### `bogdanbaciu-dot-com`

Read local product and design files first, then follow links to `dans-brain`
only when a Dan UX OS rule is needed:

- `AGENTS.md`
- `CLAUDE.md`
- `PRODUCT.md`
- `design.md` - site tokens, components, type, and visual rules
- `.builderrules`
- `.builder/rules/*.mdc`
- `.builder/skills/pagecraft/SKILL.md`

If a linked `dans-brain` file is needed, resolve in this order:

1. `../../` when checked out inside `dans-brain/brain/_repos/bogdanbaciu-dot-com`
2. `../dans-brain/` when `bogdanbaciu-dot-com` and `dans-brain` are sibling dirs
   under `~/src/`
3. `/Users/danb/src/dans-brain` on Dan's Mac
4. `/root/dans-brain` on the VPS

### `Acme`

Read local client instructions and brand sources first:

- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/acme-design/SKILL.md`
- `.agents/skills/pagecraft/SKILL.md`
- `.agents/skills/format-html/SKILL.md`
- `.builderrules`
- `.builder/rules/*.mdc`
- `.builder/skills/pagecraft/SKILL.md`

If a Dan UX OS rule is needed for Builder/Pagecraft mechanics, resolve to
`dans-brain` using sibling `../dans-brain/`, `/Users/danb/src/dans-brain`, or
`/root/dans-brain`. Use `.agents/skills/format-html/SKILL.md` for mechanics-only
work. Do not use Dan/Bogdan brand for Acme client-facing artifacts.

### Global skills install (`~/src/skills`, `.claude/skills`, `.agents/skills`)

The skill package does not own the UX OS contract. Resolve to `dans-brain` using
the Mac or VPS canonical path above before visual decisions.

## Builder Workspace

When Builder Fusion is connected to `dans-brain`, `builder.config.json` already
indexes the contract folders. When Builder is connected to `bogdanbaciu-dot-com`,
read that repo's `.builderrules` and `.builder/rules/` first, then load the
linked `dans-brain` authority files above.

## Proof Commands Stay Repo-Local

- HTML QA for brain artifacts:
  `python3 bin/pagecraft_qa.py --html path/to/file.html` from `dans-brain`
- Acme portal shell checks:
  `bash client-portal/scripts/check-pagecraft.sh` from `Acme`
- Acme dashboard shell checks:
  `python3 dashboard-poc/scripts/wrap_brand_in_portal.py --verify` from `Acme`
- Site CSS regressions for `bogdanbaciu-dot-com`:
  `mix compile --warnings-as-errors` and
  `node scripts/check_tables.mjs --verbose` from that repo

Name whichever proof surface matches the artifact you changed.
