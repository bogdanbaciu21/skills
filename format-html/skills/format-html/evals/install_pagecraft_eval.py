#!/usr/bin/env python3
"""Install Format HTML/Pagecraft assets into a temp repo and verify the manifest."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
INSTALLER = SKILL_DIR / "install-pagecraft.sh"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "target"
        target.mkdir()
        result = subprocess.run(["sh", str(INSTALLER), str(target)], capture_output=True, text=True)
        if result.returncode:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode

        manifest_path = target / "tests" / "pagecraft" / "pagecraft-install.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        missing = [asset for asset in manifest["installed_assets"] if not (target / asset).exists()]
        if missing:
            print("missing installed assets: " + ", ".join(missing), file=sys.stderr)
            return 1
        if not manifest["pagecraft_version"]:
            print("manifest pagecraft_version is empty", file=sys.stderr)
            return 1

    print("pagecraft installer eval passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
