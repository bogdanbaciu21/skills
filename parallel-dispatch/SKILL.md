---
name: parallel-dispatch
description: Generate copy-paste agent prompts and a coordinator playbook from a pre-built parallel work plan. Use when the user has decomposed a large task into conflict-free parallel tracks and needs formatted prompts for multiple Claude Code sessions. Triggers on "parallel dispatch", "parallel agents", "dispatch tracks", "multi-agent", "generate agent prompts". Do NOT use to decompose a task into tracks (the user does that upfront), to author handover documents, or to launch/monitor agents. Do NOT use for single-session sub-agent delegation via the Agent tool — this is for spinning up separate Claude Code sessions.
---

# Parallel Dispatch

Generate structured agent prompts and a coordinator playbook from a user-provided parallel work plan. The user has already done the decomposition — this skill formats the output.

## When invoked

### Step 1 — Collect track definitions

Ask the user for track definitions if not already provided. Each track needs these 5 fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Short label (e.g., "Track A — Server Conversion") |
| **Handover doc** | Yes | Path to the handover document for this track |
| **Soldiers** | Yes | List of sub-task IDs the agent should execute |
| **File scope** | Yes | CAN touch / CANNOT touch — explicit file lists or globs |
| **Issues** | Yes | GitHub issue numbers to close (code tracks) or comment on (analysis tracks) |
| **Dependencies** | No | Which tracks must merge before this one starts (default: none) |
| **Type** | No | `code` (default) or `analysis` |

The user may provide these as a table, a list, or point to a file. Accept any format — extract the 5 fields.

### Step 2 — Validate file scope

Before generating prompts, check for file overlap between tracks:

1. Compare the "CAN touch" file lists across all tracks
2. If two tracks claim the same file (or overlapping globs), **stop and flag it**:
   > "Tracks A and D both claim `netlify/functions/firm-comp.mts`. This will cause merge conflicts. Either split the file scope or add a dependency so they run sequentially."
3. Analysis tracks (read-only) are exempt from overlap checks — they don't edit files

### Step 3 — Generate agent prompts

For each track, produce a fenced code block (```markdown) the user can copy-paste into a new Claude Code session. Use the template that matches the track type:

- Code track: [`assets/agent-prompt-code.md`](assets/agent-prompt-code.md)
- Analysis track: [`assets/agent-prompt-analysis.md`](assets/agent-prompt-analysis.md)

Read the appropriate template, fill in the bracketed placeholders, and emit the result inside a fenced markdown block.

#### Template rules

- **Dependencies:** If a track has dependencies, prepend: `**DO NOT START until [dependency tracks] have merged their work to main.**`
- **Post-completion gates:** For code tracks, include appropriate verification commands based on the file scope:
  - Touched `shared-engine.cjs` or `parser/`? Add: `Run node tests/ AND npm run test:vitest:tracked`
  - Touched JS/JSX files? Add: `Run node scripts/dead-code-check.js`
  - Final or dependent track? Add: `Run npm run verify`
  - Analysis tracks: no gates
- **Issue action:** Code tracks "close" issues. Analysis tracks "comment on" issues.
- **File scope phrasing:** Be explicit. List specific files when possible. Use "and their `lib/` helpers" for function groups. ALWAYS include both CAN and CANNOT lists.

### Step 4 — Generate coordinator playbook

After the agent prompts, produce a **Coordinator Playbook** section by reading [`assets/coordinator-playbook.md`](assets/coordinator-playbook.md) and filling in the track names, issue numbers, and any track-specific verification commands.

### Step 5 — Summary table

End with a summary table so the user can see the full dispatch at a glance:

```markdown
## Dispatch Summary

| Agent | Track | Type | Soldiers | Issues | Dependencies | Can Start |
|-------|-------|------|----------|--------|--------------|-----------|
| 1 | ... | code | ... | ... | None | Now |
| 2 | ... | code | ... | ... | None | Now |
| 3 | ... | analysis | ... | ... | None | Now |
| 4 | ... | code | ... | ... | After 1+2 | After merge |
```

## Output format

- Agent prompts go inside fenced code blocks for easy copy-paste
- Coordinator playbook is regular markdown (not fenced — it's reference, not copy-paste)
- Keep prompts concise — under 200 words each. The handover doc has the details; the prompt just scopes the work.

## Common Pitfalls

### Zombie issues — code merged, issues still open

When dispatching parallel agents, each agent will do the work but often skip issue closure — leaving issues in a zombie-open state where the code is merged but the issue dangles. This happened systematically on the Layer C migration: all 16 issues across Tracks C and D were left open despite code being committed and pushed.

**Root cause:** Issue closure instructions at the end of an agent prompt are treated as low-priority after the primary code/analysis work is complete. Agents prioritize "commit and push" as their exit signal and drop the issue lifecycle step.

**Prevention:** The agent prompt templates below include gated issue closure (bolded, with "do not end the session until..."). The coordinator playbook includes a verification step. Both are needed — agents will still occasionally skip closure, so the coordinator must catch it.

### Track scope drift — commit doesn't match expected file scope

An agent may commit documentation or minor changes under a track's commit message without touching the primary files it was supposed to modify. Always verify the commit's `--stat` output matches the expected file scope before closing issues.

## What this skill does NOT do

- **Decompose work into tracks** — the user does that upfront
- **Create handover documents** — the user writes those
- **Create GitHub issues** — the user has those already
- **Launch agents** — the user copy-pastes prompts into separate Claude Code sessions
- **Monitor agents** — the user coordinates manually
