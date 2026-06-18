# Builder Workflow Reference

Use Builder as the visual/code front door while keeping repo governance local.
Do not let Builder turn context folders into write targets or replace Pagecraft
proof.

## Source Files To Read

Resolve paths with `references/contract-locations.md` when the current repo is
not `dans-brain`.

- `builder.config.json` (`dans-brain`)
- `config/builder_html_process.json` (`dans-brain`)
- `docs/builder-html-process.md` (`dans-brain`)
- `docs/builder-best-practices.md` (`dans-brain`)
- `.builderrules` (repo-local; canonical in `dans-brain`)
- `.builder/rules/*.mdc` (repo-local; canonical in `dans-brain`)
- `.builder/agents/*.md` (`dans-brain`, or linked from repo-local rules)
- `references/design-production-routing.md` for repo-specific playbooks.

## Builder Availability Decision

Use Builder directly only when the current machine has Builder auth and the
action is within the approved side-effect boundary.

- Auth/status, dry-run connect, dry-run push/pull, launch, and index probes are
  allowed by the local Builder policy.
- Builder Agents Run API, non-dry-run `push`, non-dry-run `pull`, and recurring
  Builder jobs require current-turn approval.
- Builder code generation should stay on a branch or draft PR.
- If Builder auth is missing on the VPS, prepare the Builder prompt and run
  repo-side checks only. Do not imply Builder generated the artifact.

## Commands

Builder-authenticated machine check:

**LOCAL Mac -- zsh**

```bash
cd /Users/danb/src/dans-brain
npx builder.io@latest auth status
```

Repo-side readiness check:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/builder_html_doctor.py --json
```

Prepare the Builder workflow on the Builder-authenticated machine:

**LOCAL Mac -- zsh**

```bash
cd /Users/danb/src/dans-brain
python3 bin/builder_html_workflow.py --profile prepare --execute --allow-prompts --write-proof
```

Launch Builder without opening a browser window:

**LOCAL Mac -- zsh**

```bash
cd /Users/danb/src/dans-brain
python3 bin/builder_html_workflow.py --profile launch --execute
```

Review a Builder branch or local visual diff:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/builder_output_review.py --base origin/main --head HEAD --write
```

## Workspace Routing

Builder should treat these as context unless the user explicitly asks to edit
the system itself:

- `brain/_repos/Bogdan-Baciu-Design-System`
- `.agents/skills/pagecraft`
- `.agents/skills/bogdan-baciu-design`
- `.agents/skills/builder-pagecraft-html`
- `config/uxos`
- `.builder/rules`
- `.builder/agents`
- `PRODUCT.md` and `design.md` in `bogdanbaciu-dot-com`
- `.agents/skills/ljbcpa-design` in LJB

Normal write targets are the requested artifact/page/component and its narrowly
needed local CSS or tests. Do not edit runtime folders (`state/`, `logs/`,
`inbox/`) or secrets.

## Upstream Design Packs

The upstream `nextlevelbuilder/ui-ux-pro-max-skill` can be used as reference for
task routing and asset-type checklists, but Builder briefs must still name the
local brand route, source files, privacy boundary, and proof commands. Do not
paste a generic upstream prompt into Builder without repo-specific constraints.
Load `references/upstream-design-adapter.md` before using upstream design-pack
language in a Builder prompt.

## Builder Prompt Checklist

Every Builder generation brief should include:

- artifact type and target path
- reader, decision, and privacy boundary
- brand route and files Builder should read
- data/source paths and claims that must remain factual
- expected sections, table shapes, and UI states
- explicit anti-patterns from Dan UX OS and Pagecraft
- proof commands that must pass before PR readiness
