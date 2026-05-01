---
name: blog-image-gen
description: Generate hero images for blog posts using OpenAI gpt-image-2 (Images 2.0 with high thinking). Use when the user asks to create, generate, regenerate, or batch produce hero/header images for blog posts in priv/content/posts. Also use to ingest manually-downloaded images from the art/ folder into the served location and wire them to the blog.
---

# Blog Image Generation

Generate editorial hero images for posts on bogdanbaciu.com via OpenAI's
`gpt-image-2` (released April 21, 2026). Images land at
`priv/static/images/posts/<slug>/hero.png` and are auto-rendered on the post
page by `Bogdan.Content.Post.detect_hero/1` (no frontmatter changes needed).

## When to use

- "Generate the image for `<slug>`."
- "Generate images for every post that's missing one."
- "I dumped some PNGs into `art/` — wire them up."
- "Show me what's done and what's still pending."

## Required setup (verify once per session)

1. `OPENAI_API_KEY` is set in the shell that will run the script.
2. `pip show openai` returns a version (install with `pip install --upgrade openai` if not).
3. The user understands cost: ChatGPT Plus does NOT include API access —
   `gpt-image-2` bills separately, ~$0.17–$0.40 per image at `quality="high"`,
   `size="1536x1024"`. 70 images ≈ $12–28. Confirm before any `--all` run.

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

### Step 6 — Commit

```bash
git add priv/static/images/posts/
git commit -m "blog: add hero images for <N> posts"
```

The PNGs are committed to the repo (Fly.io builds the release from this tree;
`priv/static/` ships in the artifact).

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

| Constant | Default | Notes |
|---|---|---|
| `MODEL` | `gpt-image-2` | The April 2026 model |
| `SIZE` | `"1536x1024"` | Edges must be multiples of 16, max 3840, ratio ≤ 3:1, total pixels 655,360–8,294,400 |
| `QUALITY` | `"high"` | `low` / `medium` / `high` / `auto` |
| `OUTPUT_FORMAT` | `"png"` | `png` / `jpeg` / `webp` (jpeg is faster) |
| `MODERATION` | `"auto"` | `auto` / `low` |
| `SLEEP_BETWEEN_CALLS_SEC` | `3` | Polite throttle for batch runs |

## On "thinking" / reasoning mode

The script uses the Responses API thinking path by default
(`client.responses.create` with `reasoning={"effort": "high"}` and
the `image_generation` tool). A planner (`gpt-5`) reasons about the
prompt before invoking `gpt-image-2` as a tool. This is mandated by
project `CLAUDE.md` — every blog-draft hero gets the thinking path.

```python
client.responses.create(
    model="gpt-5",
    input=prompt,
    tools=[{"type": "image_generation", "model": "gpt-image-2",
            "size": "1536x1024", "quality": "high",
            "output_format": "webp", "moderation": "auto"}],
    reasoning={"effort": "high"},
)
```

Image bytes come back as a base64 string on the
`image_generation_call` output item (`response.output[i].result`).
Do not downgrade to plain `client.images.generate` — that path is
intentionally not used.

## What this skill does NOT do

- Does not edit blog post frontmatter — hero detection is automatic via filename.
- Does not push images to a CDN — they ship in the Phoenix release artifact.
- Does not retry failed API calls inline — re-run the command to retry skipped slugs.
- Does not write prompts for you when a pre-written one is desired; draft those in `blog-image-prompts.md` first.
