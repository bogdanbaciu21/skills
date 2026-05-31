#!/usr/bin/env python3
"""Check that the packaged Bogdan design tokens still include core contracts."""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOKENS = [
    "--sky-600",
    "--sky-700",
    "--paper",
    "--ink",
    "--rule",
    "--font-display",
    "--font-body",
    "--font-mono",
    "--radius-sharp",
    "--type-name-size",
    "--type-body-size",
]
REQUIRED_SCOPES = [":root", ".db-scope"]
REQUIRED_FONTS = [
    "geist-latin.woff2",
    "instrument-serif-regular-latin.woff2",
    "jetbrains-mono-latin.woff2",
]


def check(root):
    css_path = root / "assets" / "design-system" / "colors_and_type.css"
    if not css_path.is_file():
        return [f"missing token stylesheet: {css_path}"]
    css = css_path.read_text(encoding="utf-8")
    errors = []
    for token in REQUIRED_TOKENS:
        if not re.search(rf"{re.escape(token)}\s*:", css):
            errors.append(f"missing token {token}")
    for scope in REQUIRED_SCOPES:
        if scope not in css:
            errors.append(f"missing scope {scope}")
    font_dir = root / "assets" / "design-system" / "fonts"
    for font in REQUIRED_FONTS:
        if not (font_dir / font).is_file():
            errors.append(f"missing font {font}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate packaged Bogdan design tokens.")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    errors = check(args.root.resolve())
    if errors:
        print("token integrity failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("token integrity ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
