---
name: parallel-dispatch
description: Generate copy-paste agent prompts and a coordinator playbook from a pre-built parallel work plan. Use when the user has decomposed a large task into independent, conflict-free parallel tracks and needs formatted prompts for multiple Claude Code sessions. Triggers on "parallel dispatch", "parallel agents", "dispatch tracks", "multi-agent", "generate agent prompts". Do NOT use to invent a decomposition from scratch, to author handover documents, or to launch/monitor agents. Do NOT use for single-session sub-agent delegation via the Agent tool — this is for spinning up separate Claude Code sessions.
---

# Parallel Dispatch

Generate structured agent prompts and a coordinator playbook from a user-provided parallel work plan. The user has already done the decomposition — this skill validates that the tracks are actually parallel-safe, then formats the output.

## When invoked

### Step 0 — Confirm parallel fit

Before generating prompts, verify that the plan is a good candidate for parallel dispatch:

| Check | Dispatch if true | Do not dispatch if true |
|-------|------------------|-------------------------|
| **Independence** | Each track has a distinct problem domain | A fix in one track is likely to change the diagnosis for another |
| **Context shape** | Each agent can succeed from a narrow, self-contained prompt plus handover doc | Agents need the full system story or the coordinator's private context |
| **Shared state** | Tracks do not edit the same files, mutate the same data, or compete for the same external resource | Tracks touch shared state without an explicit dependency |
| **Payoff** | There are 2+ genuinely independent tracks; 3+ is usually where the benefit is clearest | One focused session would likely finish faster than coordinating agents |

If the tracks are related, have shared state, or are still exploratory, tell the user to run one sequential investigation first. If the decomposition is incomplete, ask for the missing track fields instead of inventing tracks.

### Step 1 — Collect track definitions

Ask the user for track definitions if not already provided. Each track needs these fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Short label (e.g., "Track A — Server Conversion") |
| **Handover doc** | Yes | Path to the handover document for this track |
| **Goal / evidence** | Yes | Self-contained problem statement, expected outcome, and concrete evidence such as failing tests, errors, URLs, or acceptance checks |
| **Soldiers** | Yes | List of sub-task IDs the agent should execute |
| **File scope** | Yes | CAN touch / CANNOT touch — explicit file lists or globs |
| **Issues** | Yes | GitHub issue numbers to close (code tracks) or comment on (analysis tracks) |
| **Dependencies** | No | Which tracks must merge before this one starts (default: none) |
| **Type** | No | `code` (default) or `analysis` |

The user may provide these as a table, a list, or point to a file. Accept any format — extract the required and optional fields.

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
- **Self-contained context:** Prompts must not depend on the coordinator's current chat history. Include the track goal, concrete evidence, and expected output directly in the prompt, even when a handover doc exists.
- **Focused scope:** One agent gets one problem domain. Do not use prompts like "fix all failing tests"; use prompts like "fix these failures in this file/subsystem."
- **Constraints:** Tell the agent not to broaden scope. If the evidence points outside its file scope, it should stop and report the scope issue instead of editing unrelated files.
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

### Context leakage — prompt assumes the agent has your chat history

Agents in separate sessions do not inherit the coordinator's context. If a prompt says "fix the race condition we discussed" without naming the file, failing test, error, expected behavior, constraints, and return format, the agent will burn time rediscovering context or solve the wrong problem. Put the smallest complete context package directly in the prompt.

### False parallelism — independent-looking failures share a root cause

Parallel dispatch is counterproductive when failures are symptoms of one underlying change. If the same module, fixture, migration, environment variable, or external service appears across tracks, either collapse the work into one investigation or add dependencies so agents do not make contradictory fixes.

## What this skill does NOT do

- **Decompose work into tracks** — the user does that upfront
- **Invent parallelism** — this skill validates the user's tracks and flags unsafe plans, but does not manufacture a work split from vague input
- **Create handover documents** — the user writes those
- **Create GitHub issues** — the user has those already
- **Launch agents** — the user copy-pastes prompts into separate Claude Code sessions
- **Monitor agents** — the user coordinates manually
