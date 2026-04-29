# Skills Collection

Production-focused skills for agent workflows. Each skill lives in its own folder and is defined by `SKILL.md` with frontmatter metadata and deterministic operating instructions.

## Quick Start

1. Pick a skill from the catalog below.
2. Open `<skill>/README.md` for intent + trigger examples.
3. Open `<skill>/SKILL.md` for the full executable behavior contract.
4. Install/publish through your preferred skills registry workflow.

> This repository is intentionally registry-agnostic. If you publish on skills.sh, use the install command generated on each skill page after publishing.

## Skill Catalog

| Skill | Maturity | Purpose |
|---|---|---|
| `handoff` | Stable | Creates a structured, copy-paste handoff block for continuing in a fresh chat. |
| `grill-me` | Stable | Runs one-question-at-a-time decision interrogation before implementation. |
| `parallel-dispatch` | Stable | Produces multi-agent prompts and coordinator playbook from a parallel plan. |
| `excel-wow` | Draft | Placeholder; not ready for production invocation. |

## Repository Structure

```text
skills/
├─ README.md
├─ LICENSE
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
├─ SECURITY.md
├─ .github/workflows/skill-quality.yml
├─ scripts/validate-skills.sh
└─ <skill>/
   ├─ README.md
   └─ SKILL.md
```

## Quality Gates

A change is merge-ready only when:

- Frontmatter has `name` and `description`.
- Workflow semantics exist (`## Workflow` or `## When invoked`).
- Output contract exists (`## Output format` or `## Output rules`).
- Local validation passes:

```bash
./scripts/validate-skills.sh
```

CI enforces the same checks on pull requests and branch pushes.

## Release Hygiene

- Follow semantic versioning for releases/tags.
- Record user-visible changes in `CHANGELOG.md`.
- Keep draft skills marked explicitly until complete.

## Governance

- Contribution process: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Community standards: [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- Security reporting: [`SECURITY.md`](./SECURITY.md)
- License: [`LICENSE`](./LICENSE)
