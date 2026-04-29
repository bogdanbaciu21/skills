# Skills Collection

A curated, production-ready collection of Codex/Claude-style skills, packaged for easy hosting and reuse.

Each skill lives in its own folder and is defined by a `SKILL.md` file with frontmatter metadata (`name`, `description`) and operational guidance.

## Quick Install Matrix

Use these copy-paste commands with the Codex skills installer:

| Skill | Purpose | Install command |
|---|---|---|
| `handoff` | Session handoff summary for a new chat. | `npx -y @smithery/cli@latest skills add codex --repo bogdanbaciu/skills --skill handoff` |
| `grill-me` | One-question-at-a-time decision stress test. | `npx -y @smithery/cli@latest skills add codex --repo bogdanbaciu/skills --skill grill-me` |
| `parallel-dispatch` | Parallel agent prompt and coordinator playbook generation. | `npx -y @smithery/cli@latest skills add codex --repo bogdanbaciu/skills --skill parallel-dispatch` |
| `excel-wow` | Draft Excel/financial-modeling skill (not production-ready). | `npx -y @smithery/cli@latest skills add codex --repo bogdanbaciu/skills --skill excel-wow` |

> Replace `bogdanbaciu/skills` with your final public GitHub `owner/repo` if different.

---

## Repository structure

```text
skills/
├─ README.md
├─ LICENSE
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
├─ SECURITY.md
├─ CHANGELOG.md
├─ .github/workflows/skill-quality.yml
├─ scripts/validate-skills.sh
├─ handoff/
│  ├─ README.md
│  └─ SKILL.md
├─ grill-me/
│  ├─ README.md
│  └─ SKILL.md
├─ parallel-dispatch/
│  ├─ README.md
│  └─ SKILL.md
└─ excel-wow/
   ├─ README.md
   └─ SKILL.md
```

---

## Skill quality standard

Before publishing a skill, verify:

- [ ] `name` and `description` exist in frontmatter.
- [ ] Trigger phrases are concrete.
- [ ] Workflow is stepwise and deterministic.
- [ ] Output format is explicitly defined.
- [ ] Non-goals are explicitly defined.
- [ ] At least one realistic example exists.

Automated checks run in CI using `scripts/validate-skills.sh`.

---

## Current skills

| Skill | Status | Purpose |
|---|---|---|
| `handoff` | Ready | Creates a structured session handoff for continuation in a new chat. |
| `grill-me` | Ready | Runs a one-question-at-a-time pressure-test interview for plans/decisions. |
| `parallel-dispatch` | Ready | Generates multi-agent prompts and coordinator playbook from a parallel work plan. |
| `excel-wow` | Draft | Placeholder for a future Excel/financial-modeling workflow skill. |

---

## Using these skills

1. Install from the matrix above.
2. Open each skill folder `README.md` for quick usage guidance.
3. Trigger by naming the skill or matching its trigger phrase.
4. Follow output and workflow rules in `SKILL.md`.

---

## Authoring and publishing

1. Create a kebab-case folder (for example, `incident-triage`).
2. Add `SKILL.md` with required frontmatter and sections.
3. Add a folder `README.md` with install + quickstart example.
4. Run `./scripts/validate-skills.sh`.
5. Open PR with rationale and trigger phrases.

---

## Versioning

Use semantic tags:

- **MAJOR**: breaking behavior or output changes.
- **MINOR**: new skill additions or backward-compatible expansions.
- **PATCH**: typo fixes and clarifications.

Track notable changes in [`CHANGELOG.md`](./CHANGELOG.md).

---

## Governance

- Contributing guide: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Code of Conduct: [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- Security policy: [`SECURITY.md`](./SECURITY.md)
- License: [`LICENSE`](./LICENSE)
