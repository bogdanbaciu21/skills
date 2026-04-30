---
name: quiz-me
description: Run an active-recall quiz on a topic, document, book chapter, codebase area, interview subject, meeting-prep topic, or study material the user wants to learn or retain. Use when the user says "quiz me", "test me on", "drill me on", "flashcard me", "ask me questions about", "help me study", "interview prep on", "I need to retain this", or asks to stress-test their understanding of a body of material. Ask one question at a time and adapt difficulty based on responses. Do NOT use to stress-test a plan or decision before implementation — that's `grill-me`. Do NOT use for trivia games unrelated to learning.
---

# Quiz Me

Run a focused, adaptive quiz that helps the user retain material. Probe understanding, application, and judgment rather than trivia or keyword recall.

## Workflow

### Step 1 — Establish the source of truth

- Use the specific source the user names: a document, file, codebase area, book chapter, notes, pasted text, or topic.
- If the source is a file, document, or codebase area, read it before generating questions. Do not quiz from memory when an available source can be inspected.
- If the source is only a broad topic, ask what depth they want: intro, working knowledge, or expert.
- If the topic depends on current facts, standards, laws, prices, APIs, schedules, or other changing information, verify the current source before quizzing.

### Step 2 — Set the format once

Ask for only the missing preferences, then proceed:

- Question count: default to 5, then offer to continue.
- Style: default to open-ended for retention; allow multiple choice or mixed if the user asks or speed matters.
- Difficulty: default to medium with one stretch question; allow easy, medium, hard, or mixed.

If the user already implies these choices, do not ask. Start the quiz.

### Step 3 — Ask one question at a time

- Ask one question, then wait for the user's answer.
- Never dump all questions upfront.
- Track score, current question number, correct/partial/incorrect count, streaks, and weak concepts internally.
- Accept "I don't know" as an answer, then teach the answer before moving on.

### Step 4 — Design strong questions

Mix question types across the round:

- Definition or distinction.
- Application to a realistic scenario.
- Comparison between two concepts.
- Edge case or failure mode.
- "Why does this work this way?"
- "What would break if this changed?"
- Synthesis across multiple concepts.

For code or technical topics, include at least one "predict the output", "trace the flow", or "spot the bug" question when relevant.

Avoid:

- Yes/no questions.
- Trivia, dates, or names unless they are central to the user's stated goal.
- Questions copied verbatim from the source.
- Questions answerable by matching keywords without understanding.

### Step 5 — Grade before continuing

After each answer:

- Mark it correct, partial, or incorrect.
- For partial or incorrect answers, give the correct answer and one sentence explaining why.
- For correct answers, confirm briefly and add one adjacent piece of useful context that raises the user's understanding.
- Push back on hand-wavy answers by asking for the missing specificity when that would teach more than immediately revealing the answer.
- Do not inflate praise. Be calibrated and useful.

### Step 6 — Adapt difficulty

- Two correct answers in a row: make the next question harder or probe an edge case.
- Two partial or incorrect answers in a row: lower difficulty and revisit the underlying concept before continuing.
- Consistently strong answers: shift toward application, synthesis, and transfer.
- Consistently weak answers: shift toward foundations, definitions, and simple examples.

### Step 7 — End the round

When the round is complete, provide:

- Score: X / N correct, with partials noted separately when useful.
- The 1-2 concepts that need more work.
- A specific study suggestion, such as rereading a named section, retrying a missed problem type, or reviewing a concrete source excerpt.
- Offer three next options: another round, a harder round, or a focus round on the weak concepts.

## Output Format

Question:

```text
Q[n]/[N] - [difficulty]
[question]
```

After the user's answer:

```text
[correct / partial / incorrect]
[One-sentence grading explanation, plus one adjacent piece of useful context.]
```

End-of-round:

```text
Score: X / N
Needs work: [concepts]
Suggested next step: [specific action]

Next: another round, harder round, or focus round?
```

## Tone

Be direct, encouraging, and calibrated. Act like a tough but fair tutor: matter-of-fact when the user is wrong, brief when they are right, and always oriented toward retention.
