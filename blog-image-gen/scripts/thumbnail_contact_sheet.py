#!/usr/bin/env python3
"""Build an HTML contact sheet for generated blog hero thumbnails."""

import argparse
import html
from pathlib import Path


def discover_heroes(root):
    image_root = root / "priv" / "static" / "images" / "posts"
    if not image_root.exists():
        return []
    return sorted(image_root.glob("*/hero.*"))


def render_sheet(root, images):
    cards = []
    for image in images:
        rel = image.relative_to(root).as_posix()
        slug = image.parent.name
        cards.append(
            f'<figure><img src="{html.escape(rel)}" alt="{html.escape(slug)} hero">'
            f"<figcaption>{html.escape(slug)}</figcaption></figure>"
        )
    body = "\n".join(cards) or "<p>No hero images found.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Blog Hero Contact Sheet</title>
  <style>
    body {{ margin: 32px; font-family: system-ui, sans-serif; color: #1f2933; background: #faf7f0; }}
    h1 {{ margin: 0 0 20px; font-size: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; }}
    figure {{ margin: 0; border: 1px solid #d8d1c4; background: #fffdf8; }}
    img {{ display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; }}
    figcaption {{ padding: 10px 12px; font-size: 13px; font-variant-numeric: tabular-nums; }}
  </style>
</head>
<body>
  <h1>Blog Hero Contact Sheet</h1>
  <main class="grid">
{body}
  </main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Create a local HTML contact sheet for blog hero images.")
    parser.add_argument("--repo", default=".", help="Blog repo root. Default: current directory.")
    parser.add_argument("--out", default="priv/static/images/posts/contact-sheet.html", help="Output HTML path relative to repo.")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    images = discover_heroes(root)
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_sheet(root, images), encoding="utf-8")
    print(f"wrote {out} ({len(images)} images)")


if __name__ == "__main__":
    main()
