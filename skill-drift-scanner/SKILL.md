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
- Claude user skills at `~/.claude/skills`
- state and reports under a local state directory

It checks:

1. Missing installed skills
2. Content drift between source and installed copies
3. Unmanaged custom skills in either install root
4. Scheduler health for sync/report timers
5. Whether the last sync changed skill content, which implies Codex may need restart while Claude may only need reload or a fresh skill scan

## Workflow

### Step 1 — Run the status command

Use the environment's installed scanner command. On this machine:

```bash
/root/.local/bin/codex-skill-sync status
```

This should print the current report without mutating anything.

### Step 2 — If the user wants reconciliation, run sync

On this machine:

```bash
/root/.local/bin/codex-skill-sync sync
```

Use this when the user wants the machine brought back to source of truth, not just inspected.

### Step 3 — Interpret results by tool

- **Missing Installed Skills** means the source repo has a skill that an install root does not.
- **Content Drift** means the skill exists in both places but file content differs.
- **Unmanaged Custom Skills** means there are extra custom skills under an install root that the autosync subsystem does not own.
- **Codex restart recommended after last change: yes** means a background sync changed installed content and open Codex sessions may still have stale skill state.
- Claude can hot-reload in some setups, but do not claim reload success unless verified on the installed Claude version.

## Output contract

Return:

1. The top-line status in one sentence
2. The highest-signal per-tool sections from the report
3. The exact reconcile command if drift exists

If the user asks for the full report, point them to the local report path the scanner prints or to the state/report directory for that environment.

## What this skill does NOT do

- It does not push changes to GitHub.
- It does not assume every tool hot-reloads skills the same way.
- It does not delete unmanaged custom skills unless the user explicitly asks.
