Read `CLAUDE.md` and `AGENTS.md` first — they contain hard rules you must follow. This is [Track Name] of a parallel workflow.

Goal / evidence: [self-contained goal, failing tests/errors, expected behavior, and acceptance checks].

Read the handover document at `[handover doc path]` and execute all soldiers listed ([soldier IDs]). Touch ONLY [CAN touch files]. Do NOT edit [CANNOT touch files]. Stay inside this problem domain; if the root cause requires out-of-scope edits, stop and report the scope issue instead of broadening the work. [Post-completion gates]. Commit and push to main when done. Return a short summary of root cause, files changed, verification, and issue actions. **MANDATORY — do not end the session until you have done BOTH:** (1) Close each of these issues with `gh issue close <N> --comment "summary of what was done"`: [issue numbers]. (2) Verify closures: `for i in [issue numbers]; do gh issue view $i --json state -q .state; done` — all must print CLOSED.
