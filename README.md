# Skills Collection

![A bundle of skills](assets/a-bundle-of-skills.png)

A curated, production-ready collection of Codex/Claude-style skills, packaged for easy hosting and reuse.

This repository is structured to be readable by both humans and agents: each skill lives in its own folder and is defined by a `SKILL.md` file with frontmatter metadata (`name`, `description`) and operational guidance.

---

## Table of Contents

- [What this repository contains](#what-this-repository-contains)
- [Repository structure](#repository-structure)
- [Skill quality standard](#skill-quality-standard)
- [Current skills](#current-skills)
- [Using these skills](#using-these-skills)
- [Authoring and publishing new skills](#authoring-and-publishing-new-skills)
- [Versioning and releases](#versioning-and-releases)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## What this repository contains

This repo provides:

- **Reusable skill definitions** for common agent workflows.
- **Consistent documentation style** so users can discover and trust each skill.
- **Governance docs** expected in professional open-source repositories (`LICENSE`, contribution guide, code of conduct, security policy).

If your goal is to host skills that feel polished like those on curated skill hubs, this structure gives you a strong baseline.

---

## Repository structure

```text
skills/
├─ README.md
├─ LICENSE
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
├─ SECURITY.md
├─ .gitignore
├─ handoff/
│  └─ SKILL.md
├─ grill-me/
│  └─ SKILL.md
├─ parallel-dispatch/
│  └─ SKILL.md
└─ excel-wow/
   └─ SKILL.md
```

**Conventions**

- One skill per folder.
- Required file in each folder: `SKILL.md`.
- `SKILL.md` starts with YAML frontmatter:
  - `name`: stable slug.
  - `description`: explicit trigger/use-case text.
- Keep skill instructions concrete, testable, and scoped.

---

## Skill quality standard

Use this checklist before publishing a skill:

- [ ] **Trigger clarity:** descriptions include concrete phrases users may type.
- [ ] **Scope boundaries:** explicit non-goals (“what this skill does NOT do”).
- [ ] **Execution workflow:** numbered steps with order dependencies.
- [ ] **Output contract:** exact format expected from the agent.
- [ ] **Failure behavior:** what to do when files, tools, or assumptions are missing.
- [ ] **Safety constraints:** guardrails around destructive or high-risk actions.
- [ ] **Examples:** at least one realistic input → output example.
- [ ] **Source attribution:** include upstream references when adapted.

---

## Current skills

| Skill | Status | Purpose |
|---|---|---|
| `handoff` | Ready | Creates a structured session handoff for continuation in a new chat. |
| `grill-me` | Ready | Runs a one-question-at-a-time pressure-test interview for plans/decisions. |
| `parallel-dispatch` | Ready | Generates multi-agent prompts and coordinator playbook from a parallel work plan. |
| `quiz-me` | Ready | Active-recall quiz on a topic, doc, codebase area, or interview prep — one question at a time, adaptive difficulty. |
| `excel-wow` | Draft | Placeholder for a future Excel/financial-modeling workflow skill. |

---

## Using these skills

1. Browse the skill folder.
2. Open `SKILL.md` and read the trigger description.
3. Invoke by naming the skill or matching its trigger phrase in your prompt.
4. Follow any workflow/output rules exactly.

Tip: keep skills narrowly focused; combine multiple skills only when responsibilities do not overlap.

---

## Authoring and publishing new skills

### 1) Create a folder

Use a short kebab-case folder name (for example, `incident-triage`).

### 2) Add `SKILL.md`

Start from this minimal skeleton:

```md
---
name: incident-triage
description: Triage production incidents with severity classification and immediate stabilization steps.
---

# Incident Triage

## Purpose
...

## When to use
...

## Workflow
### Step 1 — ...
### Step 2 — ...

## Output format
...

## What this skill does NOT do
...
```

### 3) Validate quality

Run through the [Skill quality standard](#skill-quality-standard).

### 4) Open a PR

Include:

- Why the skill is needed.
- Which user prompts should trigger it.
- One example session snippet.

---

## Versioning and releases

This repository can be versioned with semantic tags:

- **MAJOR**: breaking behavior or format changes to existing skills.
- **MINOR**: new skills or backward-compatible expansions.
- **PATCH**: typo fixes, clarifications, metadata cleanups.

For production hosting, publish changelog notes so downstream users can pin versions safely.

---

## Contributing

Please read [`CONTRIBUTING.md`](./CONTRIBUTING.md) for workflow, review expectations, and quality gates.

---

## Security

Please disclose vulnerabilities per [`SECURITY.md`](./SECURITY.md).

---

## License

Distributed under the MIT License. See [`LICENSE`](./LICENSE).
