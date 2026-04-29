---
name: parallel-dispatch
description: Generate copy-paste agent prompts and a coordinator playbook from a pre-built parallel work plan. Use when the user has decomposed a large task into conflict-free parallel tracks and needs formatted prompts for multiple Claude Code sessions. Triggers on "parallel dispatch", "parallel agents", "dispatch tracks", "multi-agent", "generate agent prompts".
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

For each track, produce a fenced code block (```markdown) the user can copy-paste into a new Claude Code session. Use this template:

#### Code track template

```
Read the handover document at `[handover doc path]` and execute all soldiers listed ([soldier IDs]). Read `CLAUDE.md` and `AGENTS.md` first — they contain hard rules you must follow. This is [Track Name] of a parallel workflow. You touch ONLY [CAN touch files]. Do NOT edit [CANNOT touch files]. [Post-completion gates]. Commit and push to main when done. **MANDATORY — do not end the session until you have done BOTH:** (1) Close each of these issues with `gh issue close <N> --comment "summary of what was done"`: [issue numbers]. (2) Verify closures: `for i in [issue numbers]; do gh issue view $i --json state -q .state; done` — all must print CLOSED.
```

#### Analysis track template

```
Read the handover document at `[handover doc path]` and execute all soldiers listed ([soldier IDs]). Read `CLAUDE.md` and `AGENTS.md` first. This is [Track Name] of a parallel workflow. This is READ-ONLY analysis — you do NOT edit any source code. [Describe output artifacts and where to write them]. Commit and push to main. **MANDATORY — do not end the session until you have done BOTH:** (1) Comment on each of these issues with your findings using `gh issue comment <N> --body "..."`: [issue numbers]. (2) Verify comments were posted by checking the issue URL output.
```

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

After the agent prompts, produce a **Coordinator Playbook** section:

```markdown
## Coordinator Playbook

### Launch Order
| Phase | Tracks | Can start |
|-------|--------|-----------|
| 1 | [tracks with no dependencies] | Now |
| 2 | [tracks waiting on phase 1] | After [dependencies] merge |
| ... | ... | ... |

### After Each Track Merges
1. `git pull origin main`
2. Scan for merge conflicts (should be none if file scopes are clean)
3. Verify commit scope matches expected files: `git log -1 --stat` — flag if the commit only touched docs when code changes were expected
4. Verify issue closures: `for i in <expected issue numbers>; do echo -n "#$i: "; gh issue view $i --json state -q .state; done`
5. If any expected issues are still OPEN, close them now with the track's findings
6. [Track-specific verification if any]

### Final Gate (after ALL tracks merge)
```bash
npm run verify                    # Full CI mirror
node scripts/dead-code-check.js   # Dead code scan
# Verify ALL expected issues are closed
gh issue list --label <workflow-label> --state open --limit 50
```

### Issue Closure Checklist
- **[Track Name] closes:** [issue numbers]
- **[Track Name] comments on:** [issue numbers]
- ...

**Coordinator responsibility:** If agents leave issues open (common — see Common Pitfalls), the coordinator closes them during the "After Each Track Merges" step. Do not defer to the Final Gate.
```

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
