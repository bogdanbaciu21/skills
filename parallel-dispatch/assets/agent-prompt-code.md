Read the repo's agent instructions first (`AGENTS.md`, `CLAUDE.md`, or equivalent if present). This is [Track Name] of a parallel workflow.

Goal / evidence: [self-contained goal, failing tests/errors, expected behavior, and acceptance checks].

Read the handover document at `[handover doc path]` and execute all soldiers listed ([soldier IDs]). Touch ONLY [CAN touch files]. Do NOT edit [CANNOT touch files]. Stay inside this problem domain; if the root cause requires out-of-scope edits, stop and report the scope issue instead of broadening the work.

**Isolation:** Start in an isolated worktree: `git wt [worktree-slug]`. Commit locally in that worktree only. **Do NOT push to `main`.** The coordinator lands tracks serially.

[Post-completion gates]. When done, return a landing packet: summary, worktree path, `git log -1 --stat`, verification output, and issue-close comments drafted (coordinator closes after land unless you are the sole integrator). **MANDATORY before ending:** prepare close comments for issues [issue numbers]; coordinator will run `gh issue close` after your track lands and verify with `gh issue view`.
