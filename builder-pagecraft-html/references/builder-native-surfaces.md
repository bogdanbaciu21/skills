# Builder Native Surfaces

Use this reference when the task touches Builder rules, skills, subagents,
starter templates, Netlify integration, Builder Desktop, or CLI code generation.
The repo-local policy stays authoritative; Builder docs explain mechanisms.

## Instruction Layer

Builder reads several instruction surfaces. Use them for different jobs:

| Surface | Purpose | Dan-specific use |
|---|---|---|
| `AGENTS.md` | Repo-wide agent contract shared across tools | Canonical non-Claude rules; never fork this just for Builder |
| `.builderrules` | Compact root Builder rules | Short compatibility layer pointing Builder to AGENTS, UX OS, Pagecraft, and draft PRs |
| `.builder/rules/*.mdc` | Scoped Builder rules with frontmatter | Focused rules for UX OS, workspace routing, Pagecraft QA, and HTML replacement |
| `.builder/skills/*/SKILL.md` | Builder-discovered repeatable workflow | Builder-native mirror of this skill |
| `.builder/agents/*.md` | Focused delegated reviewers | Pagecraft QA, UX OS design review, and design-system indexing review |

Keep rules actionable, focused, precise, and scoped. Prefer examples and real
local file paths. Avoid vague taste guidance, conflicting rules, and copied
blocks from other instruction files.

## Skills

Builder discovers skills from `.builder/skills/` first and `.claude/skills/`
second. Only `SKILL.md` is auto-loaded, so the Builder-native copy should be
self-contained enough to route work even when helper references are ignored.

For this repo:

- Primary Builder path: `.builder/skills/builder-pagecraft-html/SKILL.md`
- Codex path: `.agents/skills/builder-pagecraft-html/SKILL.md`
- Claude path: `.claude/skills/builder-pagecraft-html/SKILL.md`

When editing the skill, keep all three copies aligned unless the target surface
requires a small compatibility note.

## Subagents

Builder subagents live in `.builder/agents/` and use YAML frontmatter with
`name`, `description`, `tools`, and `model`. Descriptions should contain clear
automatic triggers such as `Use immediately after...` or `Use proactively...`.

Use focused subagents, not one broad reviewer:

- `pagecraft-qa-reviewer`: run after Builder changes HTML/CSS/visual components.
- `uxos-design-reviewer`: run before a Builder PR is opened for visual work.
- `builder-dsi-index-reviewer`: run when Builder indexing, DSI, or design-system
  context changes.

Grant only the needed tools. These reviewers should inspect, run local checks,
and recommend source edits; they should not weaken gates.

## CLI Code Generation

Builder's CLI code generation can work interactively or non-interactively, but
Dan's repo policy keeps it behind stronger guardrails:

- Commit or use a clean worktree before generation so Builder changes are
  isolated.
- Run Builder commands from the specific project root, not a monorepo or broad
  parent directory.
- Use small, specific prompts. Break large UI changes into reviewable steps.
- Use `.builderignore`, `.builderrules`, and `.builder/rules/*.mdc` to protect
  critical files and keep generated code focused.
- `npx builder.io@latest code` is blocked in this repo without current-turn
  approval and a draft-PR path.

Approved local proof commands are in `builder.config.json` and
`config/builder_html_process.json`.

## Builder Desktop

Use Builder Desktop local execution when the target repo needs local tools,
services, environment variables, or private context. Prefer local-machine or
local-container execution for Dan's private repos; cloud containers are useful
only when the required context is safe and fully configured there.

Default local launch:

**LOCAL Mac -- zsh**

```bash
cd /Users/danb/src/dans-brain
python3 bin/builder_html_workflow.py --profile launch --execute
```

For app repos that need a dev server, pass the port and command through the
workflow wrapper or Builder launch with `--privacyMode --no-open`.

## Starter Templates

Starter templates are setup assets for repeatable Builder projects. They are
useful when Builder should consistently start from Dan UX OS, Pagecraft, and a
known repo structure.

Capture starter-template choices in docs/config:

- template name and owning Builder project
- connected repositories and whether the design system is in the same repo
- framework preset, setup script, server port, and environment assumptions
- instructions supplied to Builder about Dan UX OS, Pagecraft, and brand routing

Do not treat a starter template as proof that generated output is acceptable.
Every generated branch still needs Pagecraft, UX OS, brand, and git review.

## Netlify

Builder's Netlify integration is a deployment integration, not an HTML quality
gate. Use it only when the task explicitly involves deployment or preview
hosting, and keep Netlify side effects behind the repo's normal deploy policy.

For Dan-owned or dormant Netlify projects, verify the target repo/project first.
Do not connect or deploy from Builder merely because an artifact is HTML.

## Proof

Run these when Builder process files change:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/builder_docs_audit.py --json
python3 bin/builder_html_doctor.py --json
python3 -m unittest tests/test_builder_html_doctor.py
```
