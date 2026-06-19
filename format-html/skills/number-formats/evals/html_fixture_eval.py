#!/usr/bin/env python3
"""Static parity checks for the number-formats HTML fixture."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "html-table-parity.html"
SCREENSHOT_CONTRACT = ROOT / "fixtures" / "html-parity-screenshot-contract.json"


def main():
    html = FIXTURE.read_text(encoding="utf-8")
    required = [
        "class=\"num cell-link\"",
        "class=\"num cell-input fill\"",
        "class=\"num cell-error\"",
        "tr class=\"margin\"",
        "tr class=\"tot\"",
        "<span class=\"aff-l\">(</span>",
        "–",
        "(42.0)",
    ]
    missing = [needle for needle in required if needle not in html]
    if missing:
        raise SystemExit("HTML parity fixture missing: " + ", ".join(missing))
    contract = json.loads(SCREENSHOT_CONTRACT.read_text(encoding="utf-8"))
    if not contract.get("selectors") or contract.get("viewport", {}).get("width") < 360:
        raise SystemExit("HTML parity screenshot contract is malformed")
    print("number-formats HTML fixture eval passed")


if __name__ == "__main__":
    main()
