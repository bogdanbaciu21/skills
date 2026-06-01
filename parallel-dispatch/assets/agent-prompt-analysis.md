Read the repo's agent instructions first (`AGENTS.md`, `CLAUDE.md`, or equivalent if present). This is [Track Name] of a parallel workflow.

Goal / evidence: [self-contained question, concrete files/data/errors to inspect, expected output, and acceptance checks].

Read the handover document at `[handover doc path]` and execute all soldiers listed ([soldier IDs]). This is READ-ONLY analysis — you do NOT edit source code. Stay inside this problem domain; if the answer depends on another track, call that dependency out clearly instead of expanding scope. [Describe output artifacts and where to write them]. Commit and push to main. Return a short summary of findings, evidence, confidence, risks, and recommended next actions. **MANDATORY — do not end the session until you have done BOTH:** (1) Comment on each of these issues with your findings using `gh issue comment <N> --body "..."`: [issue numbers]. (2) Verify comments were posted by checking the issue URL output.
