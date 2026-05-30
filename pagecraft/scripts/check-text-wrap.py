#!/usr/bin/env python3
"""Run the Pagecraft wrap probe against local static HTML."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import os
from pathlib import Path
import socket
import socketserver
import sys
import threading
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pagecraft-wrap: Playwright missing. Install with: pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
    sys.exit(2)


VIEWPORT = {"width": 1440, "height": 900}
RIGHT_EDGE_TOLERANCE_PX = 24

RIGHT_EDGE_JS = r"""() => {
  function isInMultiColumnLayout(el) {
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 8) {
      const cs = getComputedStyle(node);
      if (cs.display === 'grid') {
        const cols = cs.gridTemplateColumns;
        if (cols && cols !== 'none') {
          const colCount = cols.split(/\s+/).filter(c => c && c !== '0px').length;
          if (colCount > 1) return true;
        }
      } else if (cs.display === 'flex' && cs.flexDirection !== 'column' && node.children.length > 1) {
        const first = node.children[0].getBoundingClientRect();
        const last = node.children[node.children.length - 1].getBoundingClientRect();
        if (Math.abs(first.left - last.left) > 50) return true;
      }
      if (node.matches('article, main, .pc-prose, .prose, body, html')) break;
      node = node.parentElement;
      depth++;
    }
    return false;
  }

  const sel = 'h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,dd,dt';
  const rights = {};
  const samplesByEdge = {};
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    if (r.width < 50) continue;
    if (el.closest('table,.pc-table-wrap,.bbt-wrap,.bb-table-wrap,pre,code,.pc-card-grid,.pc-grid,.pc-kpi-grid,.pc-section-break,.pc-table-cap,.pc-table-source,.pc-callout,.pc-stat')) continue;
    if (isInMultiColumnLayout(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.textAlign === 'center' || (cs.marginLeft === 'auto' && cs.marginRight === 'auto')) continue;
    const right = Math.round(r.right);
    rights[right] = (rights[right] || 0) + 1;
    if (!samplesByEdge[right]) samplesByEdge[right] = [];
    if (samplesByEdge[right].length < 2) {
      samplesByEdge[right].push({
        tag: el.tagName.toLowerCase(),
        cls: typeof el.className === 'string' ? el.className.split(/\s+/).slice(0, 3).join('.') : '',
        right,
        width: Math.round(r.width),
        maxWidth: cs.maxWidth,
        text: el.textContent.trim().slice(0, 60)
      });
    }
  }
  const edges = Object.keys(rights).map(Number).sort((a, b) => a - b);
  return {rightEdges: edges, spread: edges.length > 1 ? edges[edges.length - 1] - edges[0] : 0, counts: rights, samplesByEdge};
}"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        pass


def pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def local_server(directory: Path):
    port = pick_port()
    handler = functools.partial(QuietHandler, directory=str(directory))
    srv = socketserver.TCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.shutdown()
        srv.server_close()


def load_known(path: str | None) -> list[dict]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("known", [])


def is_known(finding: dict, page_name: str, known: list[dict]) -> bool:
    for entry in known:
        if entry.get("page") and not page_name.endswith(entry["page"]):
            continue
        match = entry.get("match", "")
        if match.startswith("tag:") and match[4:] in str(finding.get("tag", "")):
            return True
        if entry.get("textPreview") == finding.get("textPreview"):
            return True
    return False


def enumerate_pages(root: Path, explicit: list[str] | None, include_lab: bool) -> list[str]:
    if explicit:
        return explicit
    pages = []
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root).as_posix()
        if path.name == "404.html":
            continue
        if not include_lab and "/wrap-lab/bad-" in f"/{rel}":
            continue
        pages.append(rel)
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Static HTML root")
    parser.add_argument("--pages", nargs="+", help="Relative HTML pages to check")
    parser.add_argument("--known-issues", default=None)
    parser.add_argument("--wrapcheck", default=None, help="Path to wrapcheck JS")
    parser.add_argument("--gate-key", default=None, help="Storage key to set before navigation")
    parser.add_argument("--include-lab", action="store_true", help="Include bad wrap-lab fixtures")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_dir = Path(__file__).resolve().parents[1]
    wrapcheck = Path(args.wrapcheck).resolve() if args.wrapcheck else skill_dir / "assets" / "wrapcheck-pagecraft.js"
    if not wrapcheck.exists():
        fallback = root / "tests" / "pagecraft" / "wrapcheck.js"
        wrapcheck = fallback if fallback.exists() else wrapcheck
    if not wrapcheck.exists():
        print(f"pagecraft-wrap: wrapcheck not found: {wrapcheck}", file=sys.stderr)
        return 2

    pages = enumerate_pages(root, args.pages, args.include_lab)
    known = load_known(args.known_issues)
    any_failure = False
    print(f"\n[pagecraft-wrap] root={root} pages={len(pages)}")

    with local_server(root) as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT)
        if args.gate_key:
            ctx.add_init_script(
                f"try {{ sessionStorage.setItem('{args.gate_key}', '1'); }} catch (e) {{}}\n"
                f"try {{ localStorage.setItem('{args.gate_key}', '1'); }} catch (e) {{}}"
            )
        page = ctx.new_page()
        for rel in pages:
            try:
                page.goto(f"{base_url}/{rel}", wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(500)
                page.add_script_tag(path=str(wrapcheck))
                report = page.evaluate("window.__wrapcheck({silent:true})")
                edge = page.evaluate(RIGHT_EDGE_JS)
            except Exception as exc:  # noqa: BLE001
                print(f"\n  x {rel}: {exc}")
                any_failure = True
                continue

            findings = [f for f in report.get("findings", []) if not is_known(f, rel, known)]
            print(f"\n  {rel}")
            if findings:
                any_failure = True
                print(f"    x wrap probe: {len(findings)} new finding(s)")
                for f in findings[:6]:
                    print(f"      {f.get('kind')}: {f.get('tag')} w={f.get('width', f.get('cellWidth'))} {f.get('textPreview', '')[:70]}")
            else:
                known_count = len(report.get("findings", []))
                print(f"    ok wrap probe: 0 new findings ({known_count} known/non-new)")

            if edge["spread"] > RIGHT_EDGE_TOLERANCE_PX:
                any_failure = True
                print(f"    x right-edge spread: {edge['spread']}px")
                for right, count in sorted(edge["counts"].items(), key=lambda item: -item[1])[:4]:
                    print(f"      right={right}px x{count}")
            else:
                print(f"    ok right-edge alignment within {RIGHT_EDGE_TOLERANCE_PX}px")

        ctx.close()
        browser.close()

    print(f"\n[pagecraft-wrap] {'FAIL' if any_failure else 'PASS'}")
    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
