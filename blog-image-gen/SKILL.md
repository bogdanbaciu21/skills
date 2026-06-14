---
name: blog-image-gen
description: Generate hero images for blog posts using the blog repo's OpenAI image-generation scripts after verifying current official API docs for model names, tool syntax, size/quality options, and pricing. Use when the user asks to create, generate, regenerate, or batch produce hero/header images for blog posts in priv/content/posts. Also use to ingest manually-downloaded images from the art/ folder into the served location and wire them to the blog.
---

# Blog Image Generation

Generate editorial hero images for posts on bogdanbaciu.com via the blog repo's
image-generation scripts. Images land at
`priv/static/images/posts/<slug>/hero.png` and are auto-rendered on the post
page by `Bogdan.Content.Post.detect_hero/1` (no frontmatter changes needed).

## When to use

- "Generate the image for `<slug>`."
- "Generate images for every post that's missing one."
- "I dumped some PNGs into `art/` — wire them up."
- "Show me what's done and what's still pending."

## Required setup (verify once per session)

1. Work from the blog repo root. On this machine the expected repo is:
   `/Users/danb/Desktop/bogdanbaciu-dot-com`.
2. Confirm the project scripts exist before invoking anything:

```bash
test -f scripts/gen_blog_image.py && test -f scripts/ingest_art.py
```

If either script is missing, stop and locate it with:

```bash
rg --files /Users/danb/Desktop | rg '(^|/)gen_blog_image\.py$|(^|/)ingest_art\.py$'
```

3. `OPENAI_API_KEY` is set in the shell that will run the script.
4. `pip show openai` returns a version (install with `pip install --upgrade openai` if not).
5. Verify current OpenAI image-generation model names, tool syntax, pricing,
   size limits, and quality options from official OpenAI docs before quoting or
   relying on them. Do not treat model names or per-image costs in this skill as
   evergreen.
6. Confirm estimated batch cost with the user before any `--all` run. ChatGPT
   subscriptions do not imply API credits.

## Workflow

### Step 1 — Check what's pending

```bash
python3 scripts/gen_blog_image.py --list
```

This prints one line per post showing whether it's already done (and where) or
PENDING. Posts are considered done if EITHER of these exists:

- `priv/static/images/posts/<slug>/hero.png` (script output, served)
- `art/<slug-no-hyphens>.png` (manual download — needs ingest)

### Step 2 — If the user has manual downloads in `art/`, ingest first

```bash
python3 scripts/ingest_art.py --dry-run    # preview
python3 scripts/ingest_art.py              # do it
```

This copies `art/<compact>.png` → `priv/static/images/posts/<slug>/hero.png`
by matching the compact (no-hyphen) filename to a real post slug. Orphans
(filenames that don't map to a slug) are reported but left alone.

### Step 3 — Smoke-test on one post (dry run, then real)

```bash
python3 scripts/gen_blog_image.py <slug> --dry-run    # prints final prompt
python3 scripts/gen_blog_image.py <slug>              # one real call (~$0.30)
```

Open the generated `priv/static/images/posts/<slug>/hero.png` and confirm
quality before any batch run.

### Step 4 — Batch the rest

```bash
python3 scripts/gen_blog_image.py --all
```

Sequential, with `SLEEP_BETWEEN_CALLS_SEC = 3` between calls. Already-done
slugs are skipped automatically. Failures are logged but don't halt the loop —
re-run to retry.

### Step 5 — Verify rendering

Boot the server (`mix phx.server`) and visit `/thoughts/<slug>`. The hero
should appear between the title and the lede. If it doesn't:

- Check `Bogdan.Content.Post.detect_hero/1` — it reads via
  `:code.priv_dir(:bogdan)`, which requires a recompile after adding files
  (touch `lib/bogdan/content.ex` or restart the server).
- Confirm the file is at the exact path `priv/static/images/posts/<slug>/hero.png`.

### Step 6 — Prompt-quality and thumbnail review

Before accepting a generated image:

- The image matches the post's concrete subject, not just its mood.
- It is editorial and specific, not generic stock imagery.
- It has no fake screenshots, fake UI, fake charts, unreadable text, distorted
  hands/faces, or accidental brand/logo claims.
- It works as a crop at article-card size and as a full hero.
- It is visually distinct from nearby posts in the image inventory.
- The prompt mentions the one or two actual concepts the article is about and
  avoids stuffing in every paragraph of the post.

Output a compact review table:

| Slug | Thumbnail path | Pass/Revise | Reason | Follow-up |
|---|---|---|---|---|
| `<slug>` | `priv/static/images/posts/<slug>/hero.png` | Pass | Specific to the article; clean crop | None |

If a thumbnail needs revision, keep the prior image until the replacement is
generated and reviewed.

For batch review, build a local contact sheet from the blog repo root:

```bash
python3 /Users/danb/src/skills/blog-image-gen/scripts/thumbnail_contact_sheet.py --repo .
```

Open `priv/static/images/posts/contact-sheet.html` and scan for duplicate visual
ideas, awkward crops, distorted text, and subject drift before accepting a batch.

### Step 7 — Commit

```bash
git add priv/static/images/posts/
git commit -m "blog: add hero images for <N> posts"
```

The PNGs are committed to the repo (Fly.io builds the release from this tree;
`priv/static/` ships in the artifact).

## Skill maintenance evals

When editing prompt parsing or review workflow text in this skill, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /Users/danb/src/skills/blog-image-gen/evals/prompt_fixture_eval.py
```

The fixture locks the contract that `--dry-run` output must expose the final
prompt as a fenced `FINAL PROMPT` block before any real API call is made.

## Prompt sourcing

`scripts/gen_blog_image.py` resolves the prompt for each slug in this order:

1. **Pre-written:** if `blog-image-prompts.md` has a section
   `## N. <slug> — ...` with a fenced code block, that exact prompt is used.
2. **Auto-generated:** otherwise the script prepends the house-style preamble
   to a one-liner derived from the post title + description (or first ~300
   words of body if no description). The auto path is fine for batch but
   pre-written prompts produce noticeably better results — encourage the user
   to draft one in `blog-image-prompts.md` for any post they care strongly
   about before running.

## Tunable knobs (top of `scripts/gen_blog_image.py`)

Verify current allowed values in official OpenAI docs before changing these.

| Constant | Default | Notes |
|---|---|---|
| `MODEL` | script-defined | Verify current image-generation model name |
| `SIZE` | script-defined | Verify current allowed sizes and aspect limits |
| `QUALITY` | script-defined | Verify current quality options |
| `OUTPUT_FORMAT` | `"png"` | `png` / `jpeg` / `webp` (jpeg is faster) |
| `MODERATION` | `"auto"` | `auto` / `low` |
| `SLEEP_BETWEEN_CALLS_SEC` | `3` | Polite throttle for batch runs |

## On "thinking" / reasoning mode

The script may use the Responses API with an image-generation tool and a
separate planning model. Verify the current OpenAI API surface before editing
this path; model names, tool payloads, and reasoning options are time-sensitive.

```python
client.responses.create(
    model="<current-planning-model>",
    input=prompt,
    tools=[{"type": "image_generation", "model": "<current-image-model>",
            "size": "<verified-size>", "quality": "<verified-quality>",
            "output_format": "webp", "moderation": "auto"}],
    reasoning={"effort": "<verified-effort>"},
)
```

Image bytes come back as a base64 string on the
image-generation output item. Do not downgrade to another API path without
checking the project script and the current official docs.

## What this skill does NOT do

- Does not edit blog post frontmatter — hero detection is automatic via filename.
- Does not push images to a CDN — they ship in the Phoenix release artifact.
- Does not retry failed API calls inline — re-run the command to retry skipped slugs.
- Does not write prompts for you when a pre-written one is desired; draft those in `blog-image-prompts.md` first.
