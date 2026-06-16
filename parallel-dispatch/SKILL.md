---
name: parallel-dispatch
description: Generate copy-paste agent prompts and a coordinator playbook from a pre-built parallel work plan, or turn a cheap design dispute into competing "code wins" implementation variants. Use when the user has decomposed a large task into independent, conflict-free parallel tracks and needs formatted prompts for multiple coding-agent sessions; or when the user says "parallel dispatch", "parallel agents", "dispatch tracks", "multi-agent", "generate agent prompts", "code wins", "build competing implementations", or "settle this by building variants". Optionally layers in per-runner insight-lock capture (condensed into one cross-track insight memo at the end) and end-of-run pagecraft polish for HTML deliverables. Do NOT use to invent a decomposition from scratch, to author handover documents, or to launch/monitor agents. Do NOT use for single-session sub-agent delegation via the Agent tool — this is for spinning up separate coding-agent sessions.
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

### Step 0.5 — Use code-wins for cheap design disputes

<!-- # patch: claude-sonnet-4-6, 2026-06-12, code-wins keeps parallel-dispatch from over-debating cheap implementation choices. -->
When the unresolved question is a design or implementation preference and
building variants is cheap, dispatch the work as competing artifacts instead of
arguing in prose:

1. Define the shared acceptance criteria and non-negotiable constraints.
2. Assign 2-3 agents to produce divergent implementations in isolated worktrees
   or artifact folders.
3. Require each runner to include a short tradeoff note and proof commands.
4. Compare the artifacts directly, choose one, and either delete the throwaway
   variants or preserve the winning pattern in a follow-up task.

Do not use code-wins when the variants would mutate the same database, send
messages, deploy to production, or change irreversible external state.

### Step 0.7 - Default to serial landing (not parallel push)

<!-- # patch: 2026-06-16, concept-loop P2 multi-agent overlap / landing friction -->
Parallel **investigation** can run concurrently; parallel **landing on `main`**
cannot unless every track has a separate clone/worktree, zero file overlap, and
Dan explicitly accepts push races. Default every code dispatch to a **serial
landing queue**:

| Role | Does | Does NOT |
|------|------|----------|
| **Runner** | Work in `git wt <track-slug>`, commit locally, run track gates, return summary + `git log -1 --stat` + verification + branch/worktree path | Push to `main`, edit outside CAN touch, land from the canonical dirty checkout |
| **Coordinator** | Pull fresh `main`, land one track at a time via `git land` (or repo-specific land path), re-run gates after each land, stop on conflict or scope drift | Let every runner push concurrently, use piped push commands that mask exit codes, or land while another track is still writing |

**When to keep serial (default):** 2+ code tracks, shared repo, any overlap risk,
dans-brain canonical checkout (permanently dirty), Acme/shared-tree history, or
when the concept-loop flagged multi-agent overlap / landing friction.

**When parallel push is allowed:** Dan explicitly opts in **and** the validator
reports zero overlapping `can_touch` scopes **and** each runner uses its own
worktree/clone. Even then, prefer serial unless the tracks are truly trivial.

Read [`assets/serial-landing-queue.md`](assets/serial-landing-queue.md) when
filling the coordinator playbook and code-track prompts.

### Step 0.6 — Babysit open PRs with a bounded `/loop`

Use this recipe when Dan asks to babysit PRs, keep agent branches moving, or run
a standing `/loop` over `dans-brain`, `brain/_repos/*`, and Acme-adjacent repos.
The point is to turn scattered branch/CI state into a small action queue, not to
merge risky work by momentum.

1. Inventory the repos and open PRs: root repo first, then active submodules
   under `brain/_repos/`, then explicitly named repos such as Acme.
2. For each PR, record branch, author/agent, files touched, check status, merge
   conflict status, and whether the PR is mechanical or needs judgment.
3. Apply the CI/CD tier gate: mechanical `auto` failures can be fixed, verified,
   committed, and pushed; `propose` failures get a diagnosis or draft fix only.
4. Land or rebase one clean PR at a time. Use the repo's sanctioned land path
   (`git land`, merge button, or repo-specific instructions), then re-check the
   next PR against fresh `main`.
5. Stop on any conflict, red check that changes behavior, missing secret, or
   unclear ownership. Surface a short queue with owner, blocker, and next action.

The loop is deliberately bounded: run one pass, produce the queue, act only on
safe mechanical items, and end with exact proof links or commands. Do not keep
polling indefinitely, bypass branch protection, rewrite another agent's branch,
or edit workflow/secrets/branch-protection files to make checks green.

### Step 1 — Collect track definitions

Ask the user for track definitions if not already provided. Each track needs these fields:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Short label (e.g., "Track A — Server Conversion") |
| **Handover doc** | Yes | Path to the handover document for this track |
| **Goal / evidence** | Yes | Self-contained problem statement, expected outcome, and concrete evidence such as failing tests, errors, URLs, or acceptance checks |
| **Soldiers** | Yes | List of sub-task IDs the agent should execute |
| **File scope** | Yes | CAN touch / CANNOT touch: explicit file lists or globs (no repo-wide `**` unless the track truly owns everything) |
| **Worktree slug** | Yes (code) | Short slug for `git wt <slug>`: one isolated worktree per code track |
| **Issues** | Yes | GitHub issue numbers to close (code tracks) or comment on (analysis tracks) |
| **Dependencies** | No | Which tracks must **land** before this one starts (default: none) |
| **Landing order** | No | Integer rank for the serial queue when dependencies are insufficient (lower lands first) |
| **Type** | No | `code` (default) or `analysis` |

The user may provide these as a table, a list, or point to a file. Accept any format — extract the required and optional fields.

### Step 2 - Validate file scope and ownership matrix

Before generating prompts, check for file overlap between tracks and emit an
explicit **File Ownership Matrix** (file/area to owning track). Shared infra
must have a single owner or sit in CANNOT touch for every other track:

- `.github/workflows/**`, lockfiles, root build/config (`package.json`,
  `pyproject.toml`, `netlify.toml`, `staticwebapp.config.json`, ...)
- Shared engines (`shared-engine.cjs`, `parser/`, `gate.js`, design tokens)
- Capture dirs, handoff dirs, and coordinator-only landing paths

Validation steps:

1. Compare the "CAN touch" file lists across all tracks.
2. Reject repo-wide or directory-wide globs (`**`, `src/**`, `app/**`) unless
   exactly one code track claims them and others list that tree under CANNOT touch.
3. If two tracks claim the same file (or overlapping globs), **stop and flag it**:
   > "Tracks A and D both claim `netlify/functions/firm-comp.mts`. Split the scope, add a dependency + serial landing order, or collapse into one track."
4. Analysis tracks (read-only) are exempt from overlap checks; they do not edit files.
5. Append the matrix to the dispatch output and coordinator playbook so runners
   see neighbor ownership without reading each other's prompts.

If the plan is available as JSON or YAML, run the bundled validator first:

```bash
python3 scripts/validate_tracks.py path/to/parallel-plan.json
python3 scripts/validate_tracks.py path/to/parallel-plan.yaml
```

It rejects missing goal/evidence, code tracks with no `can_touch` scope,
overlapping edit scopes without dependencies, and explicitly shared state
without dependencies. YAML support uses PyYAML when available and a narrow
track-plan parser when it is not, so simple `tracks:` files remain portable.

### Step 3 — Generate agent prompts

For each track, produce a fenced code block (```markdown) the user can copy-paste into a new coding-agent session. Use the template that matches the track type:

- Code track: [`assets/agent-prompt-code.md`](assets/agent-prompt-code.md)
- Analysis track: [`assets/agent-prompt-analysis.md`](assets/agent-prompt-analysis.md)

Read the appropriate template, fill in the bracketed placeholders, and emit the result inside a fenced markdown block.

#### Template rules

- **Worktree + landing:** Every code prompt must name `git wt <worktree-slug>` and forbid pushing to `main`. Runners return proof; the coordinator lands serially.
- **Dependencies:** If a track has dependencies, prepend: `**DO NOT START until [dependency tracks] have landed on main (coordinator confirmed).**`
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
- **Capture add-on (optional):** If the per-runner capture add-on is enabled (see [Optional add-ons](#optional-add-ons)), append [`assets/runner-capture-addendum.md`](assets/runner-capture-addendum.md) to each prompt and fill its `[capture path]` with `<capture-dir>/<run-slug>/<track-slug>.md`. Pick `<run-slug>` and each `<track-slug>` once, up front, and bake the literal path into each prompt — the separate sessions then need no coordination.

### Step 4 — Generate coordinator playbook

After the agent prompts, produce a **Coordinator Playbook** section by reading [`assets/coordinator-playbook.md`](assets/coordinator-playbook.md) and filling in the track names, issue numbers, and any track-specific verification commands. The playbook carries two optional end-of-run passes (pagecraft HTML polish, combined-insight digest); keep or drop them to match the [Optional add-ons](#optional-add-ons) you enabled.

### Step 5 — Summary table

End with a summary table so the user can see the full dispatch at a glance:

```markdown
## Dispatch Summary

| Agent | Track | Type | Worktree | Soldiers | Issues | Land order | Can Start |
|-------|-------|------|----------|----------|--------|------------|-----------|
| 1 | ... | code | `git wt a` | ... | ... | 1 | Now (work only) |
| 2 | ... | code | `git wt b` | ... | ... | 2 | Now (work only) |
| 3 | ... | analysis | - | ... | ... | - | Now |
| 4 | ... | code | `git wt d` | ... | ... | 3 | After 1+2 land |
```

## Optional add-ons

Two opt-in add-ons. Both default **off** so the base flow is unchanged. Turn them
on when the user asks ("with capture", "insight-lock per runner", "polish the HTML
at the end"), or proactively offer when the conditions below hold. State which
add-ons are on at the top of your output.

### A. Per-runner capture → combined insight (insight-lock)

Each runner writes a short `insight-lock` capture as it finishes; the coordinator
condenses all of them into one cross-track memo at the end and surfaces the
headline. Offer this for research-heavy or multi-track runs where the *learning*
matters as much as the diff.

**How the captures get back with no extra plumbing:** under serial landing, runners
commit captures in their worktrees; the coordinator lands each track (capture
included) and pulls after each land. So:

1. Pick one `<run-slug>` (date + short label, e.g. `2026-06-03-layer-c`) and one
   `<track-slug>` per track, up front.
2. Choose `<capture-dir>` by repo, following `insight-lock`'s storage rule:
   - `/root/dans-brain` (or the Mac mirror): `brain/context-captures/parallel-dispatch/`
   - any other repo: `.agent-handoffs/context-captures/parallel-dispatch/`
3. In Step 3, append [`assets/runner-capture-addendum.md`](assets/runner-capture-addendum.md)
   to each prompt with `[capture path]` = `<capture-dir>/<run-slug>/<track-slug>.md`.
   Because every track's path is a distinct literal string baked into its own
   prompt, the separate sessions never coordinate and never collide.
4. After all tracks merge and you have pulled their captures, read every
   `<capture-dir>/<run-slug>/*.md` and write a condensed
   `<capture-dir>/<run-slug>/_combined.md` from
   [`assets/combined-insight.md`](assets/combined-insight.md). The cross-track value
   is in the disagreements — lift each runner's *Contradictions / Integration Risks*
   into the combined memo. A risk only one track saw is what the others were blind to.
5. **Surface it:** end your final report with the combined memo's **Headline**
   inline, a link to `_combined.md`, and anything in Contradictions / Integration
   Risks that should change the next decision.

The capture file is an allowed addition beyond a track's file scope (it is new,
uniquely named, and conflict-free); tell the coordinator not to flag it as scope
drift.

### B. End-of-run HTML polish (pagecraft)

If any merged track produced or changed **static HTML deliverables**, finish them
with `pagecraft` before declaring done — never ship hand-checked HTML. Auto-offer
whenever a track's file scope includes `.html`/HTML output roots; skip entirely
otherwise. The operational commands live in the coordinator playbook's
"HTML polish with pagecraft" pass: install (or reuse) pagecraft, run the
deterministic `check-keystone.py` guard, then the real-browser `runner.py` probe,
fix keystone/wrap failures, and allowlist only confirmed non-defects.

## Output format

- Agent prompts go inside fenced code blocks for easy copy-paste
- Coordinator playbook is regular markdown (not fenced — it's reference, not copy-paste)
- Keep the work scope of each prompt concise — under ~200 words. The handover doc has the details; the prompt just scopes the work. When the capture add-on is on, the fixed capture block is appended on top of that budget.

## Common Pitfalls

### Cheap building beats long argument

If the team is stuck on "which UI/layout/approach is better" and each option can
be built in under an hour, create variant tracks. The output should be artifacts
plus proof, not essays. Preserve only the winner unless the alternatives teach a
durable lesson worth capturing.

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

### Multi-agent overlap / landing friction - everyone pushed to `main`

The highest-cost failure mode: multiple runners commit/push concurrently in one
repo (especially a shared or dirty canonical checkout). Symptoms: resurrected
files, stale `origin/main` vs worktree truth, push races, hidden scope drift,
and hours lost to sync deadlocks.

**Root cause:** Prompts that say "commit and push to main when done" treat
runners as integrators. In parallel dispatch, runners implement; the coordinator
integrates.

**Prevention (default):**
1. Serial landing queue (Step 0.7): runners stay in `git wt`, coordinator lands
   one track at a time with `git land`.
2. File ownership matrix (Step 2): explicit CAN/CANNOT, no overlapping globs.
3. Verify landings with `git log -1 --stat` + track gates after each land, not
   only at the end.
4. Never pipe push output in a way that masks exit codes; capture `rc=$?` from the bare push.
5. Ground-truth check for "is file on main?" = fresh detached worktree checkout,
   not `git ls-tree origin/main` alone on a shared `.git`.

If a runner already pushed: stop parallel lands, inventory diverged files, land
remaining tracks from isolated worktrees, and rewrite future dispatches to serial
mode.

## What this skill does NOT do

- **Decompose work into tracks** — the user does that upfront
- **Invent parallelism** — this skill validates the user's tracks and flags unsafe plans, but does not manufacture a work split from vague input
- **Create handover documents** — the user writes those
- **Create GitHub issues** — the user has those already
- **Launch agents** — the user copy-pastes prompts into separate coding-agent sessions
- **Monitor agents** — the user coordinates manually

## Skill Maintenance

When editing the validator or dispatch rules, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 evals/run_evals.py
```

## Worked examples

### Example 1: Five-track implementation rollout

User: "I have tracks A-E and want copy-paste prompts."

Do:
- Validate that no two code tracks own the same files.
- Validate file ownership matrix; assign each code track a `git wt` slug.
- Put each track's goal, CAN/CANNOT touch list, gates, worktree rules, and return
  packet requirement directly in the prompt.
- Produce a coordinator playbook with serial landing order and scope check after each land.

### Example 2: Variant design decision

User: "We keep arguing about the dashboard layout."

Use code-wins if each variant can be built safely in its own folder. Create
parallel prompts for 2-3 directions, require screenshots or static checks, then
make the coordinator choose from artifacts.

### Example 3: False parallelism

User: "Split these three failing tests across agents."

If all failures touch the same parser, migration, external service, or fixture,
do not dispatch. Ask for one sequential root-cause investigation first.
