**Capture before exit (insight-lock add-on).** Beyond your file scope, create exactly ONE file at `[capture path]` and include it in your commit. It is unique to your track, so it cannot conflict with another track. If the `insight-lock` skill is available in your session, run it scoped to THIS session only and write to that exact path; otherwise write a ≤250-word memo with these sections (skip any that are empty):

- **Core Read** — what you concluded or built (3-6 bullets).
- **Fresh Insights** — non-obvious things a reviewer would not get from the diff alone.
- **Decisions & Gotchas** — choices you made and traps the next person must know.
- **Contradictions / Integration Risks** — anything that may conflict with another track's assumptions, the shared design, or how the pieces combine when merged. Be specific: this is the section the coordinator condenses across tracks.
- **Pointers** — files, issues, evidence, commands to re-run.

Label each bullet `Observed` / `Inferred` / `Hypothesis`. Keep it tight. Never write credentials, API keys, tokens, or other secrets into the capture.
