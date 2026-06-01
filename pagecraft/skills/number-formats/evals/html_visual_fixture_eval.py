#!/usr/bin/env python3
"""Optional screenshot smoke test for the HTML number-format parity fixture."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "html-table-parity.html"
CONTRACT = ROOT / "fixtures" / "html-parity-screenshot-contract.json"


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("number-formats HTML visual eval skipped: Playwright is not installed")
        return 0

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    viewport = contract["viewport"]
    screenshot = Path(contract["screenshot"])
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport=viewport)
        page.goto(FIXTURE.resolve().as_uri())
        for item in contract["selectors"]:
            if page.locator(item["selector"]).count() == 0:
                print(f"missing visual selector: {item['selector']}", file=sys.stderr)
                browser.close()
                return 1
        page.screenshot(path=str(screenshot), full_page=True)
        browser.close()
    print(f"number-formats HTML visual eval passed: {screenshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
