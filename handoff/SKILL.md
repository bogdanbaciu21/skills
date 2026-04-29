---
name: handoff
description: Summarize the current session's work into a structured handoff block that a fresh Claude Code chat can execute on. Use whenever the user says "handoff", "hand off", "pass to next session", "wrap up for handoff", "session summary for next chat", "continue in new chat", or anything about transferring context to a new conversation. Also use when the user is about to end a session with unfinished work. Includes the GitHub issue reference if one exists.
---

# Session Handoff

Produce a structured, copy-pasteable handoff block that gives a fresh Claude Code session everything it needs to pick up where this one left off. The goal is zero context loss between sessions — the next chat should be able to read the handoff and immediately start working without re-exploring the codebase or asking clarifying questions.

## Why this matters

Claude Code sessions are stateless — each new chat starts fresh. CLAUDE.md and memory provide project-level context, but session-specific state (what you just tried, what failed, what decisions were made, what's half-done) is lost. A good handoff captures exactly that session-specific context.

## Workflow

### Step 1 — Gather session context

Collect these automatically (don't ask the user for them):

1. **GitHub issue**: Read `/tmp/.claude-session-issue-number`. If it exists, fetch the issue title and URL via `gh issue view <number> --json title,url`.
2. **Git diff since session start**: Read `/tmp/.claude-session-start-commit`. If it exists, run `git log --oneline <start-commit>..HEAD` and `git diff --stat <start-commit>..HEAD` to see what changed.
3. **Working tree state**: Run `git status --short` to catch uncommitted work.
4. **Conversation review**: Review the full conversation history to extract:
   - The original task/request
   - What was accomplished
   - What was attempted but didn't work (and why)
   - Key decisions or findings
   - What remains to be done

### Step 2 — Ask targeted questions

After gathering automatic context, ask the user only what you can't infer:

- "Is there anything I missed or got wrong in this summary?"
- "Any specific instructions for the next session beyond what's here?"

Keep it to 1–2 questions max. Don't over-interview.

### Step 3 — Generate the handoff block

Output the handoff inside a fenced code block (```markdown) so the user can copy it in one click. Use this structure:

```
## Session Handoff — [brief title]

### GitHub Issue
#[number] — [title]
[URL]

### Original Task
[What the user asked for, in their words or close to it]

### What Was Done
- [Completed item 1]
- [Completed item 2]
- ...

### What's Left
- [ ] [Remaining item 1]
- [ ] [Remaining item 2]
- ...

### Key Decisions & Findings
- [Decision or finding that the next session needs to know]
- [Why something was done a certain way]
- [What was tried and rejected, and why]

### Files Changed
[git diff --stat output or curated list]

### Uncommitted Work
[git status output, or "None — all committed and pushed"]

### Gotchas & Context
- [Anything non-obvious the next session should watch out for]
- [Test failures to be aware of]
- [Blocked dependencies]
```

### Output rules

- **Be specific, not vague.** "Fixed `calcOrigination()` to normalize Infinity in tier bounds" is useful. "Fixed a calculation bug" is not.
- **Include file paths and line numbers** where relevant so the next session can jump straight to the code.
- **Include the exact error messages** if the session ended with a failing test or unresolved bug.
- **Don't pad.** If a section is empty (e.g., no gotchas), omit it entirely rather than writing "None."
- **The "What's Left" section is the most important part.** The next session's first action will be to read this list and start executing. Make it actionable — each item should be something Claude can do without further clarification.
- **Include the GitHub issue** so the next session can pick it up rather than creating a duplicate tracking issue.

### Step 4 — Remind the user

After outputting the handoff block, remind:

> Paste this as your first message in the new chat. The next session will skip creating a new tracking issue and pick up #[number] instead.
