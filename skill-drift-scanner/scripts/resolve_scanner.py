#!/usr/bin/env python3
"""Resolve the preferred codex-skill-sync command without assuming a platform."""

import os
import shutil
from pathlib import Path


def resolve(environ=os.environ, which=shutil.which, home=None):
    override = environ.get("CODEX_SKILL_SYNC")
    if override:
        return override
    from_path = which("codex-skill-sync")
    if from_path:
        return from_path
    home_path = Path(home or environ.get("HOME", "~")).expanduser() / ".local" / "bin" / "codex-skill-sync"
    return str(home_path)


def main():
    print(resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
