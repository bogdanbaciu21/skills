# Domain Examples

## Code

Subject: "Add role-based access to the admin dashboard."

Good first branch: source of truth for roles.

Recommended first question: "Which system is authoritative for role membership: the app database, the identity provider, or a config file? Recommended answer: identity provider if it already owns login, because duplicating roles in app state creates drift."

## Business

Subject: "Decide whether to launch a paid pilot."

Good first branch: success criteria and downside exposure.

Recommended first question: "What measurable outcome makes the pilot worth extending after 30 days? Recommended answer: one commercial metric and one operational metric, both observable without new instrumentation."

## FP&A

Subject: "Build an AI-assisted monthly close variance package."

Good first branch: source data and sign-off boundary.

Recommended first question: "Which numbers are allowed to be machine-drafted versus human-approved? Recommended answer: let AI draft variance explanations from locked actuals, but keep account mapping, materiality thresholds, and final commentary approval with Finance."
