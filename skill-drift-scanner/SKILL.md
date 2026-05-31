---
name: skill-drift-scanner
description: Audit Codex and Claude skill installation drift, autosync health, scheduler status, and reload requirements. Use when the user asks whether skills are installed, synced, stale, missing, or drifting from a source skills repo, or when they ask for a skill health report.
---

# Skill Drift Scanner

Inspect whether the machine's active Codex and Claude skills match the intended source-of-truth set, whether the autosync timers are healthy, and whether either tool needs a reload or restart to pick up changes.

## When to use

- "Are my skills installed?"
- "Are all skills synced?"
- "Did autosync run?"
- "What changed in my skills?"
- "Do I have skill drift?"
- "Give me a skills health report"

## Scope

This skill audits a machine-level skill deployment, not a single application repo.

Typical install layout:

- source skills repo clone or mirror
- optional local overlay skills
- Codex user skills at `~/.codex/skills`
- agent-compatible user skills at `~/.agents/skills`
- Claude user skills at `~/.claude/skills`
- repo-local project skill pairs at `.claude/skills` and `.agents/skills`
- state and reports under a local state directory

It checks:

1. Missing installed skills
2. Content drift between source and installed copies
3. Unmanaged custom skills in either install root
4. Repo-local project skills that exist for Claude but not Codex-compatible agents, or the reverse
5. Scheduler health for sync/report timers
6. Whether the last sync changed skill content, which implies Codex may need restart while Claude may only need reload or a fresh skill scan

## Workflow

### Step 1 — Locate the scanner

Use the environment's installed scanner command; do not assume a Linux/root home
path. Prefer an explicit override, then `PATH`, then the user's local bin:

```bash
scanner="${CODEX_SKILL_SYNC:-$(command -v codex-skill-sync || true)}"
[ -n "$scanner" ] || scanner="$HOME/.local/bin/codex-skill-sync"
[ -x "$scanner" ] || { echo "codex-skill-sync not found"; exit 127; }
```

### Step 2 — Run the status command

```bash
"$scanner" status
```

This should print the current report without mutating anything.

### Step 3 — If the user wants reconciliation, run sync

Use the same resolved scanner path:

```bash
"$scanner" sync
```

Use this when the user wants the machine brought back to source of truth, not just inspected.

### Step 4 — Interpret results by tool

- **Missing Installed Skills** means the source repo has a skill that an install root does not.
- **Content Drift** means the skill exists in both places but file content differs.
- **Unmanaged Custom Skills** means there are extra custom skills under an install root that the autosync subsystem does not own.
- **Project Skill Parity** means each real repo's `.claude/skills/<name>` and `.agents/skills/<name>` copies are paired. Missing one side can be reconciled automatically; same-name content conflicts are reported for manual review.
- **Codex restart recommended after last change: yes** means a background sync changed installed content and open Codex sessions may still have stale skill state.
- Claude can hot-reload in some setups, but do not claim reload success unless verified on the installed Claude version.

## Output contract

Return:

1. The top-line status in one sentence
2. The highest-signal per-tool sections from the report
3. The Project Skill Parity section if it reports any missing or drifted repo-local skills
4. The exact reconcile command if drift exists, using the resolved scanner path from Step 1

If the user asks for the full report, point them to the local report path the scanner prints or to the state/report directory for that environment.

## What this skill does NOT do

- It does not push changes to GitHub.
- It does not assume every tool hot-reloads skills the same way.
- It does not delete unmanaged custom skills unless the user explicitly asks.
