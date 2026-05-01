---
name: agent-coordination
description: Coordinate a deliberation across multiple AI agents (Claude, Gemini, Codex, Cursor, Antigravity, etc.) using a shared markdown log. Teaches Claude to read the full log before responding, append entries with the locked preface format, follow the phase model (Research → Converge → Stabilize → Action-List → Approval → Execute → Closeout), enforce the approval gate, and hand off cleanly to the next named agent. Also scaffolds a new coordination session on request. Triggers on "agent coordination", "coordination session", "multi-agent", "round-robin", "files-received", or any mention of `agent-research/agent-coordination.md` or `agent-research/files-received/`. SKIP for generic single-model multi-turn work — this skill is only for sessions where the human is brokering between multiple distinct AI agents through a shared file.
---

# Agent Coordination

A protocol for running a deliberation across multiple AI agents from
different vendors, where the only shared memory is a markdown file in
the user's repo. Claude is one participant. The user is the messenger
between agents — pasting prompts into Gemini, Codex, Cursor,
Antigravity, etc. — but every agent reads and writes to the same file,
so context never gets lost in chat windows.

This skill makes Claude play its part correctly: read the full log
before responding, append in the locked format, respect the current
phase, surface convergence honestly, refuse to execute without
approval, and hand off cleanly when its turn ends.

## When to use

- The user mentions starting a multi-agent / round-robin / coordination session.
- A repo contains `agent-research/agent-coordination.md`.
- The user asks Claude to take its turn / participate / append to the log.
- The user asks Claude to parse files dropped in `agent-research/files-received/`.
- The user says "kickoff a coordination session on X."

## When NOT to use

- Single-model multi-turn work (regular Claude Code session).
- Generic "the agents did X" framing that's not about this protocol.
- A repo without an `agent-research/` folder when the user hasn't asked to start one.

---

## Two modes

### Mode A — Kickoff (user asks to start a session)

Triggers: "start a coordination session on X", "kickoff agent
coordination for Y", `/agent-coordination start ...`.

Steps Claude runs in this order:

1. **Surface the privacy/cost checklist** (verbatim, before scaffolding):
   ```
   Before starting, confirm:
   1. No secrets, credentials, .env, or NDA'd material in the repo — or it's gitignored.
   2. You're OK with the contents being read by every provider you'll prompt
      (Anthropic, Google, OpenAI, Cursor, Google Labs / Antigravity, …).
   3. Per-provider training/retention is set as you want it.
   4. Cost awareness: each agent reads the full log each turn. A 30-turn
      deliberation across 6 agents on a 50K-token log ≈ 9M input tokens.
   ```
   Wait for the user to confirm before continuing.

2. **Scaffold the folder structure:**
   ```
   agent-research/
     agent-coordination.md
     files-received/
     files-received/parsed/
   ```
   Folder names are locked: hyphenated, lowercase. Do not rename.

3. **Initialize `agent-coordination.md`** with the topic the user gave
   you and the protocol header (see "File template" below). Do not
   invent the topic — use the user's words verbatim.

4. **Print a copy-paste kickoff prompt** the user can send to each
   other agent. The prompt must include the protocol rules verbatim
   (preface format, phase model, convergence-ledger requirement,
   sentinel formats) so other agents — who don't have this skill —
   know the conventions.

5. **Commit and push the scaffold to GitHub** so other agents can
   read the file via raw URL.

### Mode B — Participant (Claude is taking a turn)

Triggers: user prompts Claude with anything that implies it's now
Claude's turn — "your turn", "Claude, append your view", "Claude,
execute item #4", or a `HANDOFF → Anthropic / Claude` line in the
most recent log entry.

Always run these steps in order:

1. **Read the entire `agent-coordination.md` file before generating
   any response.** Bottom-up first to find the current phase from
   the most recent entry's heading; then top-down for full context.
2. **If a `Read first:` list applies to you** (because the most
   recent `HANDOFF →` named you), read every file listed before
   generating output.
3. **Determine the current phase** from the most recent entry's
   heading (`Phase: …`). Behave according to that phase's rules
   (see "Phase rules" below).
4. **Compose your entry** following the entry template for the
   current phase.
5. **End your entry** with `HANDOFF → [target]` (with `Reason:` and
   `Read first:` lines) or `HOLD`.
6. **Append, commit, and push** to GitHub in the same turn so other
   agents see your update.

---

## File and folder conventions

Locked defaults. Do not rename or relocate without the user's
explicit instruction.

| Path | Purpose |
|---|---|
| `agent-research/agent-coordination.md` | The shared deliberation log. Append-only by convention. |
| `agent-research/files-received/` | Inbound raw material the user drops here (PDFs, transcripts, CSVs, images). |
| `agent-research/files-received/parsed/` | Machine-readable `.md` versions produced by an agent on request. |

The folder is **committed to the repo by default** so non-Claude
agents reading via GitHub can see it. If the user wants the
deliberation private, ask before committing — but the protocol
assumes shared visibility.

---

## Preface line spec

Every entry begins with an H3 heading in this exact form:

```
### Firm — Agent + variant — YYYY-MM-DD HH:MM TZ — Phase: <Phase>[ — Refs: <citation>]
```

Five fields, separated by ` — ` (em-dash with single spaces on each side):

1. **Firm** — `Anthropic`, `Google`, `OpenAI`, `Cursor`, `Google Labs`, etc.
2. **Agent + variant** — full model name, including reasoning level or
   context-window setting if relevant. Example: `Claude Opus 4.7 1M Extra High`.
3. **Timestamp** — ISO date + 24h or 12h time + timezone abbreviation.
   Use ISO date (`YYYY-MM-DD`), not US `MM-DD-YY`, to avoid
   transatlantic ambiguity.
4. **Phase** — exactly one of: `Research`, `Converge`, `Stabilize`,
   `Action-List`, `Approval`, `Execute`, `Closeout`. Unknown phase
   tokens are flagged on next read.
5. **Refs** *(optional)* — short pointer to entries this one
   responds to. Example: `Refs: Google 2026-05-01 11:42`.

When Claude is the author, the Firm is `Anthropic` and the agent
string is the running model's identifier as known to Claude in this
session.

---

## Log shape

**Pure chronological.** All entries are appended at the bottom in
time order. There is no top-of-file status block, no fixed phase
sections, no per-phase subdocuments. The current phase is whatever
the most recent entry's heading says.

A consequence: a fresh agent reads bottom-up first to find the
current phase, then top-down for the full deliberation.

---

## Phase rules

There are seven phases. An entry's behavior depends on which phase
its heading declares. Claude must not switch phases unilaterally —
phase transitions are authored by the agent ending its turn, and
Stabilize / Approval / Execute transitions are gated by the user.

### Research

First-pass independent analysis. Each agent reads the topic + any
material in `files-received/parsed/` and writes its own view. No
critique of other agents yet. Treat other Research-phase entries as
inputs to consider, not targets to attack.

Entry shape:
- 1–3 paragraphs of analysis
- Bulleted "Key claims" so later phases can cite them by line
- `HANDOFF → [next agent]` per the kickoff order

### Converge

Cross-evaluation across agents. Goal: grow the agreement surface,
shrink the disagreement surface to zero, surface clarifying questions.

Every entry in this phase **must end with three labeled blocks**, in
this order:

```
**Agree**
- Concur with [Firm — Agent — timestamp] on [specific point]. [optional one-line reason]
- ...

**Disagree**
- Re: [Firm — Agent — timestamp]
  > "exact quote of the claim"
  Disagreement: [one sentence — what's wrong].
  Alternative: [one sentence — what to do instead].
  Conviction: Strong disagree | Weak disagree | Friendly amendment
- ...

**Open questions**
- → [target: another agent / User / All] [the question]
- ... (soft cap 3 per entry, hard cap 5)

**Convergence ledger:** N agreements, M disagreements remaining, K open questions.
```

Rules:
- **Quote, don't paraphrase.** Disagreements that paraphrase the
  target are rejected — paraphrasing leads to strawmanning.
- **Empty Agree or Disagree blocks are acceptable.** Vague "I broadly
  agree" is not.
- **Self-revision is allowed but must be flagged.** If you're
  changing your own earlier view, label the block
  `Self-revision of [my earlier timestamp]`.
- **Question routing.** Each open question gets `→ [target]`.
  Questions to `User` should only be raised when no other agent
  can answer them.

**Stop signal:** when your ledger reads `0 disagreements remaining`
and `≤ 1 open question` for **two consecutive rounds** (your current
entry plus the previous one from any agent), end your entry with:

```
Recommend: ready for Stabilize phase. Awaiting user confirmation.
```

Do not auto-advance the phase. The user transitions.

### Stabilize → Action-List

Once the user has signaled "stabilize," the next agent's entry
phase-tags as `Action-List` and contains a draft list of tasks in
this exact shape:

```
## Action List — Draft N — YYYY-MM-DD HH:MM TZ — Author: <Firm / Agent>

1. [Task in one imperative sentence]
   - Owner: User | Anthropic / Claude | OpenAI / Codex | Google / Gemini | …
   - Depends on: #3, #5  (or "none")
   - Acceptance: concrete, testable signal that this is done
   - Status: Proposed
2. ...
```

Mandatory rules:
- **All five fields populated.** No `Owner: TBD`, no
  `Acceptance: see above`. If you can't fill a field, raise it as
  an Open question and don't post a half-list.
- **Owner is exact.** Use `Codex`, not "an agent".
- **Numbering is stable across drafts.** Item #4 in Draft 2 is the
  same intent as item #4 in Draft 1; if scope changes, append a
  new item rather than renumbering.

Subsequent revisions are appended as new entries with phase
`Action-List`, each containing:
- A new `## Action List — Draft N+1` block, AND
- A `### Diff vs. Draft N` block listing additions, removals,
  edits to ownership / acceptance / dependencies.

### Approval

Author: **`User`** only. Skill rejects approval entries authored by
any agent. Three valid sentinel forms:

```
APPROVED: Action List — Draft N.
APPROVED-PARTIAL: Items #1, #2, #3 of Draft N.
REVOKED: Approval of Draft N.
```

Sentinels are uppercase. The Draft number is mandatory. The skill
matches via regex when scanning bottom-up.

What the gate enforces:

1. **No `Phase: Execute` entry exists in the log without a matching
   `APPROVED:` or `APPROVED-PARTIAL:` line above it referencing the
   same Draft.** If Claude is asked to execute, scan bottom-up for
   the most recent approval sentinel; if absent, refuse and tell
   the user.
2. **No agent flips an item's Status to In-progress or Done unless
   that item is Approved.**
3. **Each Draft needs its own approval.** Stale `APPROVED: Draft 3`
   does not carry forward to Draft 4.

### Execute

In-flight work. Each entry corresponds to one or more items moving
forward. The body contains a `Status update:` block (append-only —
do not edit prior Drafts):

```
**Status update**
- Item #4: In-progress (was Approved). Updated by OpenAI / Codex.
- Item #7: Done (was In-progress). Updated by OpenAI / Codex.
  Commit: abc1234. Files: lib/foo.ex, test/foo_test.exs.
  Acceptance check: "tests pass on CI" — green at https://….
- Item #9: Blocked (was In-progress). Reason: upstream API returns 500. → HANDOFF → User.
```

Rules:
- **Append-only.** Original Drafts are immutable; current Status
  is whatever the most recent entry says.
- **Transitions are explicit.** `Done (was In-progress)`, not bare
  `Done`. Forces the writer to acknowledge what they're flipping.
- **Done requires citing Acceptance + concrete artifact** (commit
  SHA, file paths, URL, screenshot path). Bare "completed" is rejected.
- **Blocked is a real state.** `Blocked (was …). Reason: …` followed
  by `HANDOFF → User`. Do not silently sit on a block.

### Closeout

Final entry of the session, authored by the last agent before the
deliberation ends (or by the user). Phase tag `Closeout`. Body
contains a single recap table or list:

```
## Closeout summary — YYYY-MM-DD HH:MM TZ

| # | Task | Final status | Owner | Evidence |
|---|------|--------------|-------|----------|
| 1 | …    | Done         | …     | abc1234  |
| 2 | …    | Done         | …     | …        |
| 3 | …    | Blocked      | …     | …        |
```

After Closeout, the session is considered closed. Reopening means a
new Action-List Draft and a new Approval.

---

## Handoff protocol

Every entry ends with **exactly one** of:

```
HANDOFF → Firm / Agent
Reason: [why this agent is next; reference an Action-List item or open question]
Read first: agent-research/agent-coordination.md (full), [other paths in files-received/parsed/ if relevant]
```

```
HANDOFF → User
Reason: [decision / approval / unblocking needed]
```

```
HOLD
```

Rules:
- **Every entry has a trailing sentinel.** Silent end-of-turn is
  rejected.
- **The agent named in `HANDOFF →` must match the Owner of the next
  active item**, OR be `User` if the gate is approval. If you can't
  identify a single named target, hand off to `User`.
- **`Read first:` is mandatory** on `HANDOFF → another agent`.
  Always lists `agent-coordination.md (full)` first; add specific
  parsed-input files when relevant. This is what stops the
  receiving agent from cold-loading and inventing context.
- **HOLD = same agent will append again next turn.** Use it
  mid-task when execution will continue without changing hands.

When Claude is the receiver (the user has prompted it because a
`HANDOFF → Anthropic / Claude` named it), Claude scans bottom-up for
the most recent such sentinel, reads everything in its `Read first:`
list, and only then begins composing.

---

## Inbound files — `files-received/`

When the user drops a PDF, transcript, CSV, or image into
`agent-research/files-received/`, an agent (often Claude) is asked
to parse it into a machine-readable `.md` file at
`agent-research/files-received/parsed/<source-stem>.md`.

Rules:
- **Preserve facts; do not summarize away detail.** Tables stay as
  markdown tables. Numbered lists stay numbered. Speaker turns in
  transcripts stay attributed.
- **Cite location.** Page numbers, timestamps, or row indices stay
  inline so later phases can reference them.
- **Sensitive-pattern guard.** Before writing the parsed `.md`,
  scan the source for: API key formats (long alphanumeric tokens),
  `BEGIN PRIVATE KEY` / `BEGIN OPENSSH PRIVATE KEY`, `.env`-style
  `KEY=VALUE` lines, AWS access key IDs (`AKIA…`), JWTs (three
  base64 segments separated by dots). On any match, **stop and
  flag to the user** before writing the parsed file. The user
  decides per-file whether the match is a false positive.

After parsing, append a Research-phase entry summarizing what was
parsed and where, so other agents know the file is ready.

---

## File template (kickoff scaffold)

```markdown
# Agent Coordination — <Topic in user's words>

This file is the shared deliberation log for a multi-agent
coordination session. Every participating agent reads the entire
file before responding and appends a new entry at the bottom.

## Protocol summary

- **Preface line:** H3 heading — `Firm — Agent + variant — YYYY-MM-DD HH:MM TZ — Phase: <Phase>[ — Refs: <citation>]`
- **Phases:** Research → Converge → Stabilize → Action-List → Approval → Execute → Closeout
- **Convergence-phase entries** end with Agree / Disagree / Open Questions blocks + a Convergence ledger line
- **Approval gate:** literal `APPROVED: Action List — Draft N.` line authored by `User`
- **Handoff:** every entry ends with `HANDOFF → [target]` (Reason + Read first) or `HOLD`
- **Inbound material** goes in `files-received/`; agents parse it to `files-received/parsed/<stem>.md`

Full protocol: <link to this file in the agent-coordination skill or to a public version>

---

<entries appended below this line>
```

---

## Privacy and cost guardrails

The kickoff checklist (Mode A, Step 1) is the upfront warning.
During Participant mode, the only runtime guard is the
sensitive-pattern scan during inbound parsing (above).

Claude does not enforce policy across other providers. Once the
user pastes log content into Gemini or Codex, that content lives
under those vendors' terms. The protocol is opt-in per session.

---

## Failure modes to watch for

These are the modes that break the protocol when an agent gets
sloppy. If Claude notices another agent doing one of these in the
log, flag it in the next Converge-phase entry as a friendly
amendment.

- **False consensus.** An entry that says "I broadly agree" with no
  citations to specific points. Reject by asking for specifics.
- **Hallucinated reads.** An entry whose claims about prior entries
  don't match what's actually in the log. Cite the mismatch.
- **Phase drift.** An entry tagged `Converge` that's really doing
  Research (no engagement with prior entries) or Execute (acting
  on items that aren't approved yet). Flag and ask for re-tagging.
- **Stale approval.** An Execute entry that cites approval of an
  earlier Draft when the most recent Draft is newer. Refuse to act.
- **Silent handoff.** An entry without a trailing `HANDOFF` or
  `HOLD`. Ask the author to add one.

---

## What this skill does NOT do

- It does not enforce the protocol on other AI providers. Their
  agents follow the rules only because the kickoff prompt names
  the rules.
- It does not auto-advance phases. Stabilize / Approval / Execute
  transitions are user-gated.
- It does not run a server, watch the file for changes, or notify
  the user when an external agent appends. The user is the
  orchestrator; this skill makes Claude's part of the workflow
  consistent and machine-checkable.
