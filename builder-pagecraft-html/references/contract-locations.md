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

Read local bridge files first, then follow their links to `dans-brain`:

- `DESIGN.md` - bridge doc; site tokens live in `design.md`
- `docs/uxos.md` - pointer to Dan UX OS runbook
- `.builderrules`
- `.builder/rules/*.mdc`

If a linked `dans-brain` file is needed, resolve in this order:

1. `../../` when checked out inside `dans-brain/brain/_repos/bogdanbaciu-dot-com`
2. `../dans-brain/` when `bogdanbaciu-dot-com` and `dans-brain` are sibling dirs
   under `~/src/`
3. `/Users/danb/src/dans-brain` on Dan's Mac
4. `/root/dans-brain` on the VPS

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
- Site CSS regressions for `bogdanbaciu-dot-com`:
  `mix assets.build && npm run test:css` from that repo's `assets/` directory

Name whichever proof surface matches the artifact you changed.
