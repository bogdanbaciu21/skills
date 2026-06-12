---
name: insight-lock
description: Preserve and distill long, high-value conversations into durable downstream context. Use when the user says to "capture this", "park this thread", "fossilize this", "save the transcript", "lock this down", "don't lose this", "distill this back-and-forth", "make this available downstream", or when a lengthy strategic exchange contains ephemeral insights, relationship reads, event prep, private disclosures, or future-use context that should not disappear between sessions. Also use when the user wants a light handoff of context without a full task-resumption handoff.
---

# Insight Lock

## Overview

Turn an important conversation into durable context: a raw transcript capture, a distilled insight memo, retrieval hooks, and a light future-use note. This is not the same as a normal `handoff`: preserve the thinking and relationship signal, not just outstanding tasks.

`insight-lock` is the canonical capture skill. If older notes, prompts, or users
mention `capture-context`, treat that as a legacy name for this skill rather than
recreating or invoking a separate duplicate.

## Workflow

### 1. Define The Capture Boundary

Identify exactly what is being preserved:

- Current chat only.
- Current chat plus named local files, emails, meeting notes, screenshots, or repo artifacts.
- A specific event-prep thread, such as a demo, call, negotiation, private session, or board-style meeting.

If the boundary is ambiguous, use the smallest sensible boundary and say what was included and excluded.

### 2. Choose Storage

For `/root/dans-brain`, prefer:

```text
brain/context-captures/YYYY-MM-DD-short-slug.md
brain/context-captures/raw/YYYY-MM-DD-short-slug.private.md
```

Use the raw `.private.md` file only when the user asked to preserve the full transcript or when the exact language is itself valuable. The brain-vault rule allows sensitive non-env material, but never save live credentials, API keys, OAuth tokens, SSH private keys, or social-publishing credentials.

For another repo, use that repo's established private/briefing area if one exists. If no durable location is obvious, use:

```text
.agent-handoffs/context-captures/YYYY-MM-DD-short-slug.md
```

Do not put raw transcripts under `logs/` if the user wants the capture committed; `logs/` is local runtime storage.

### 3. Preserve The Raw Layer

Create a raw capture when requested. Include:

- Timestamp and timezone.
- Scope statement.
- Source limitations, such as "visible chat only" or "local files read: ...".
- Verbatim user/assistant turns when available.
- Pointers to attachments or screenshots instead of duplicating large binary data.

Do not claim full fidelity if the exact original transcript is not accessible. If only a synthesis is possible, say so plainly.

### 4. Distill The Signal

Create a concise durable memo with these sections, omitting empty sections:

```markdown
# [Title]

## Why This Matters
[The practical reason this capture exists.]

## Trigger / Deadline
[Upcoming demo, call, meeting, decision, or risk clock.]

## Core Read
[The strongest synthesis in 3-8 bullets.]

## Fresh Insights
[New or revised insights that were not already obvious.]

## Contradictions To Hold
[Tensions that should not be flattened too early.]

## Evidence And Source Pointers
[Local paths, emails, meeting notes, screenshots, user statements.]

## Open Questions
[Unknowns that materially affect strategy.]

## Downstream Hooks
[Keywords, people, projects, repo paths, and future phrases that should retrieve this.]

## Future-Agent Note
[Light handoff: what a later agent should preserve, avoid, or read first.]

## Privacy Boundary
[What can be reused in artifacts, what is internal-only, and what must not be quoted.]
```

### 5. Separate Fact, Inference, And Strategy

Use clear labels:

- **Observed:** directly from transcript, local file, email, or meeting note.
- **Inferred:** reasoned interpretation from the evidence.
- **Hypothesis:** plausible but unproven.
- **Actionable:** useful next move or artifact.
- **Do not use externally:** private or sensitive material that can guide posture but must not appear in client/stakeholder artifacts.

This distinction matters when private disclosures, relationship reads, or fast-moving business risks are involved.

### 6. Add Event Prep Only When The Thread Needs It

If the user mentions a specific demo, call, meeting, negotiation, deadline, or decision point, add an event-prep block. Do not add this section merely because a capture feels important; use it when there is a real external clock or a concrete near-term moment to prepare for.

```markdown
## Event Prep

### What To Learn
[What the event must clarify.]

### Questions To Ask
[Specific questions, ordered by importance.]

### Watch Signals
[What would increase or reduce concern.]

### Red Flags
[What should trigger follow-up or skepticism.]

### Post-Event Capture
[What to record immediately after the event.]
```

### 7. Update Existing Durable Notes Sparingly

If the capture produces a stable new fact, update the relevant durable page, such as:

- `brain/people/<person>.md`
- `brain/projects/<project>.md`
- `brain/projects/<project>-*.md`
- A repo-local `briefings/` or `deliverables-private/` note

Keep those durable pages short. Put the full transcript and detailed synthesis in the context capture, then link or summarize from the durable page.

Do not let ingest become write-only accumulation. When a capture changes what is
known about a person, project, finance topic, client, or operating procedure:

- update the narrow entity page in the same turn when safe;
- add a source pointer to the capture or raw evidence path;
- label contradictions instead of flattening them away;
- use a memory candidate rather than active memory when the fact is plausible
  but not yet reviewed.

If filing back is unsafe, too broad, or blocked by missing source access, say so
explicitly in the final response as `entity-page update deferred: <reason>`.

### 8. Optional Local Receipt

Never send a network callback, webhook, or remote telemetry event from this skill.

If the local environment explicitly defines `INSIGHT_LOCK_RECEIPT_LOG` or
`DAN_INSIGHT_LOCK_RECEIPT_LOG`, append one JSONL receipt after the capture files
are written. The receipt is metadata only:

```json
{"schema_version":1,"skill":"insight-lock","created_at":"2026-06-03T00:00:00Z","repo":"/path/to/repo","path":"/path/to/capture.md","raw_saved":false,"sha256":"...","privacy":"memo"}
```

Do not include transcript text, private excerpts, credentials, API keys, OAuth
tokens, SSH material, or social-publishing credentials in the receipt. If the
receipt append fails, mention the failure in the final response but do not block
the capture.

### 9. Verify And Commit

Before finalizing:

- Run `git status --short --branch -uall`.
- Check for accidental live credentials or runtime streams.
- Re-read created files.
- Report whether a durable entity/project/finance/procedure page was updated,
  not needed, or deferred with a reason.
- Follow the repo policy for committing and pushing changes unless the user says not to.

Final response should include:

- The skill or capture name.
- Files created or updated.
- Whether the raw transcript was saved.
- What was not captured or remains approximate.
