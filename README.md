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

**Boundary:** this repository is the shared/global skill source. It must contain
portable skills that are safe to propagate into multiple machines and client
repos. Brain-owned orchestration skills, repo-specific Builder workflows,
`.builder/` routing, and client-specific bindings stay in their owning repo and
fan out directly from that repo only after explicit approval. In particular,
`builder-pagecraft-html` is a `dans-brain` project skill, not a global skills
repo skill.

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
├─ sync-skills.sh    (propagate canonical skills → machine skill dirs)
├─ scripts/skillopt_pilot.py
│                   (no-mutate skill benchmark/proposal harness)
├─ tests/           (repo-level harness tests)
├─ agent-coordination/
│  └─ SKILL.md
├─ handoff/
│  └─ SKILL.md
├─ grill-me/
│  └─ SKILL.md
├─ parallel-dispatch/
│  └─ SKILL.md
├─ insight-lock/
│  └─ SKILL.md
├─ skill-drift-scanner/
├─ bogdan-baciu-design/
│  ├─ SKILL.md
│  ├─ references/brand-system.md
│  └─ assets/design-system/      (tokens, fonts, images, previews, UI kit)
├─ format-html/                  (multi-skill plugin bundle)
│  ├─ .claude-plugin/plugin.json
│  └─ skills/
│     ├─ format-html/            (overview + installer + shared design assets)
│     │  ├─ SKILL.md
│     │  ├─ install-pagecraft.sh
│     │  ├─ assets/css/pagecraft.css
│     │  ├─ assets/wrap-lab/     (good/bad wrap fixtures)
│     │  └─ references/          (tables, headers, text-wrap, number-formats, …)
│     ├─ verify-text-wrap/       (canonical home of the wrap probe + verifiers)
│     │  ├─ SKILL.md
│     │  ├─ runner.py · check-keystone.py · browserbase.py
│     │  └─ wrap-safe.css · wrapcheck.js   (wrap-safe runtime library)
│     ├─ table-system-migration/
│     │  ├─ SKILL.md
│     │  ├─ table-ratchet.py       (baseline ratchet for no-new table debt)
│     │  └─ table-ratchet-checklist.md
│     ├─ number-formats/
│     │  ├─ SKILL.md
│     │  ├─ formats.json         (byte-exact Excel format codes)
│     │  └─ apply-number-formats.py
│     └─ reskin/
│        ├─ SKILL.md
│        ├─ reskin.py            (detect → sync → reframe; hybrid bespoke/generic)
│        └─ reskin.example.json
├─ excel-wow/
│  └─ SKILL.md
└─ blog-image-gen/
   └─ SKILL.md
```

> **Bundles vs. loose skills.** Most folders are single skills (one `SKILL.md`).
> `format-html` is a multi-skill **plugin bundle**: its members live under
> `format-html/skills/` and stay self-contained (each owns its own tools, nothing
> vendored or duplicated). `sync-skills.sh` *flattens* bundle members on export,
> so each still installs as a top-level loose skill (`~/.tool/skills/<name>/`)
> invokable by its bare name.

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

## SkillOpt pilot

This repo includes a conservative SkillOpt-style pilot at
`scripts/skillopt_pilot.py`. It does not call an LLM and does not mutate
`SKILL.md`. It scores a skill document against deterministic benchmark rows,
applies curated section patches to a copy of the body, and writes
`proposed.md` plus `receipt.json` for human review.

The first concrete benchmark lives at `excel-wow/evals/skillopt_pilot.jsonl`.
It is intentionally aimed at the draft `excel-wow` skill so the pilot has real
headroom to measure.

**LOCAL Mac - zsh**

```bash
cd /Users/danb/src/skills
PYTHONDONTWRITEBYTECODE=1 python3 scripts/skillopt_pilot.py \
  --skill excel-wow/SKILL.md \
  --benchmark excel-wow/evals/skillopt_pilot.jsonl \
  --out-dir /tmp/excel-wow-skillopt-pilot
```

Review `/tmp/excel-wow-skillopt-pilot/proposed.md` and
`/tmp/excel-wow-skillopt-pilot/receipt.json`; copy changes manually only after
review. Generated in-repo `skillopt-pilot/` folders are ignored by git.

Run the pilot tests with:

**LOCAL Mac - zsh**

```bash
cd /Users/danb/src/skills
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_skillopt_pilot.py
```

---

## Current skills

| Skill | Status | Purpose |
|---|---|---|
| `agent-coordination` | Ready | Coordinates multi-vendor AI deliberation through a shared markdown log — preface format, phase model, convergence ledger, approval gate, clean handoff. |
| `handoff` | Ready | Creates a structured session handoff for continuation in a new chat. |
| `grill-me` | Ready | Runs a one-question-at-a-time pressure-test interview for plans/decisions. |
| `parallel-dispatch` | Ready | Generates multi-agent prompts and coordinator playbook from a parallel work plan. |
| `quiz-me` | Ready | Active-recall quiz on a topic, doc, codebase area, or interview prep — one question at a time, adaptive difficulty. |
| `insight-lock` | Ready | Preserves and distills a high-value conversation into durable downstream context — raw capture, distilled insight memo, retrieval hooks, and a light future-use note. The capture skill `parallel-dispatch` runners use per track. |
| `chat-analysis` | Ready | Analyzes Codex or Claude Code session transcripts for friction patterns, redacts sensitive text, and proposes reviewed agent-instruction improvements. |
| `weekly-update` | Ready | Drafts evidence-driven stakeholder updates from git plus issue-tracker data, with GitHub, Linear, and Jira data contracts. |
| `format-html` | Ready | Multi-skill **plugin bundle** for HTML formatting + visual safety. Contains the mechanics skills below; `format-html/skills/format-html` is the overview + installer. |
| `format-html » verify-text-wrap` | Ready | Verifies static HTML portals for caterpillar text, narrow containers, and right-edge layout drift. Canonical home of the `wrap-safe` runtime library (`wrap-safe.css` reset + `wrapcheck.js` probe) it drives. |
| `format-html » table-system-migration` | Ready | Audits, migrates, and regression-tests messy HTML table systems with a public-safe scrub gate. |
| `format-html » number-formats` | Ready | Applies the Macabacus financial number-format standard (en-dash zeros, aligned parenthesized negatives, blue inputs, green links, grey-italic margins, bold totals) to Excel models and HTML tables. Byte-exact codes + openpyxl applicator. |
| `format-html » reskin` | Ready | Detects a repo's design system (a `*-design`/`*-brand` skill, tokens stylesheet, or `reskin.json`) and applies its brand frame (nav/hero/footer + tokens + assets) across the site. Hybrid: runs the repo's bespoke applier if it has one, else a built-in frame injector. Idempotent + dry-run-able. |
| `skill-drift-scanner` | Ready | Audits Codex and Claude skill deployment drift, autosync health, scheduler status, and reload requirements across machine-level skill installs. |
| `excel-wow` | Draft | Placeholder for a future Excel/financial-modeling workflow skill. |
| `blog-image-gen` | Ready | Generates editorial hero images for blog posts through the blog repo's OpenAI image scripts, with current-doc verification, batch/ingest workflows, and thumbnail review. |
| `bogdan-baciu-design` | Ready | Applies Bogdan Baciu's personal editorial design system to sites, prototypes, documents, slide decks, and scoped financial artifacts, bundling tokens, fonts, imagery, previews, and the brand reference. |
| `deep-research-agents` | Ready | Treats Claude Managed Agent, Gemini Deep Research, and Parallel.ai as one deep-research capability with repo-specific harness guidance. |

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
