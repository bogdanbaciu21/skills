#!/usr/bin/env python3
"""verify-text-wrap runner — local + deployed mode.

See ../SKILL.md for the protocol this implements.

Usage:
    python3 runner.py --local --portal portal/ --gate-key KEY [--known-issues PATH]
    python3 runner.py --deployed URL [--gate-key KEY --gate-password PASSWORD] [--known-issues PATH]

Exit codes:
    0 — all pages pass (or only known-issue matches)
    1 — at least one NEW finding (caterpillar / narrow / right-edge spread)
    2 — operational failure (URL unreachable, Playwright not installed, etc.)
"""
import argparse
import contextlib
import functools
import glob
import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[verify-text-wrap] playwright not installed. Run: pip install pytest-playwright && python3 -m playwright install chromium", file=sys.stderr)
    sys.exit(2)

# Optional Browserbase preference for --deployed mode
try:
    from browserbase import use_browserbase_if_available
except ImportError:
    use_browserbase_if_available = lambda *a, **kw: None

# Default location of the wrap-safe wrapcheck.js. After wrap-safe migrates into
# the skills repo at skills/wrap-safe/, this URL is the source of truth. Override
# via --wrapcheck-url during transition periods or for alternate hosting.
DEFAULT_WRAPCHECK_URL = "https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/wrap-safe/wrapcheck.js"
VIEWPORT = {"width": 1440, "height": 900}

# Right-edge spread that's just inline-box variance vs. a real cap mismatch.
RIGHT_EDGE_TOLERANCE_PX = 24


# --------------------------------------------------------------- right-edge probe

RIGHT_EDGE_JS = r"""() => {
  // Measure the right-X coordinate of every MAIN-FLOW prose element.
  // Multi-column layouts (scenario cards, KPI grids, sibling columns) are
  // skipped — elements in those have different right edges by design.
  // We're catching the "phantom vertical line" bug, which is about the main
  // reading column. Cards/grids are intentional design, not bugs.

  function isInMultiColumnLayout(el) {
    // Walk up to .article/.doc/.prose ancestor, checking for any grid/flex
    // parent with > 1 visible column.
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 8) {
      if (node.matches('.article, .doc, .prose, body, html')) break;
      const cs = getComputedStyle(node);
      if (cs.display === 'grid') {
        const cols = cs.gridTemplateColumns;
        // 'none' or a single column = single-column grid (= main flow)
        if (cols && cols !== 'none') {
          const colCount = cols.split(/\s+/).filter(c => c && c !== '0px').length;
          if (colCount > 1) return true;
        }
      } else if (cs.display === 'flex') {
        // Multi-child flex = potential column layout
        if (cs.flexDirection !== 'column' && node.children.length > 1) {
          // Check if children are arranged horizontally (i.e., row direction)
          const firstChild = node.children[0];
          const lastChild = node.children[node.children.length - 1];
          if (firstChild && lastChild) {
            const fr = firstChild.getBoundingClientRect();
            const lr = lastChild.getBoundingClientRect();
            // If first and last children have different x positions, they're side-by-side
            if (Math.abs(fr.left - lr.left) > 50) return true;
          }
        }
      }
      node = node.parentElement;
      depth++;
    }
    return false;
  }

  const SEL = '.doc h1, .doc h2, .doc h3, .doc h4, .doc h5, .doc h6, ' +
              '.doc p, .doc li, .doc blockquote, ' +
              '.article h1, .article h2, .article h3, .article h4, .article h5, .article h6, ' +
              '.article p, .article li, .article blockquote, ' +
              '.prose h1, .prose h2, .prose h3, .prose p, .prose li';
  const rights = {};
  const samplesByEdge = {};
  let skipped = 0;
  for (const el of document.querySelectorAll(SEL)) {
    const r = el.getBoundingClientRect();
    if (r.width < 50) continue;
    if (el.closest('table, .table-scroll, .workbook-wrap, pre, code, ' +
                   '.scenario-pair, .scenario-card, .per-patient, .callout, .openq, ' +
                   '.section-summary, .day-summary, .kpis, .kpi, .lab-card, ' +
                   '.inverse, .compare')) continue;
    if (el.classList.contains('lede') || el.classList.contains('sub-lede')) continue;
    if (isInMultiColumnLayout(el)) { skipped++; continue; }
    // Skip horizontally-centered elements (margin: auto) — those are deliberately
    // positioned off the main left edge (e.g., math formulas, centered callouts).
    {
      const cs = getComputedStyle(el);
      if (cs.marginLeft === 'auto' && cs.marginRight === 'auto') { skipped++; continue; }
      // Skip elements with explicit text-align: center
      if (cs.textAlign === 'center') { skipped++; continue; }
    }
    const right = Math.round(r.right);
    rights[right] = (rights[right] || 0) + 1;
    if (!samplesByEdge[right]) samplesByEdge[right] = [];
    if (samplesByEdge[right].length < 3) {
      const cs = getComputedStyle(el);
      samplesByEdge[right].push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0,3).join('.') : '',
        right, width: Math.round(r.width),
        maxWidth: cs.maxWidth,
        text: el.textContent.trim().slice(0, 50),
      });
    }
  }
  const edges = Object.keys(rights).map(Number).sort((a, b) => a - b);
  return {
    rightEdges: edges,
    spread: edges.length > 1 ? edges[edges.length - 1] - edges[0] : 0,
    counts: rights,
    samplesByEdge,
    skippedMultiColumn: skipped,
  };
}"""


# --------------------------------------------------------------- local http server

def _pick_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextlib.contextmanager
def local_server(directory):
    port = _pick_free_port()
    handler = functools.partial(_QuietHandler, directory=directory)
    srv = socketserver.TCPServer(("127.0.0.1", port), handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    # Wait briefly for the server to accept connections.
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


# --------------------------------------------------------------- check core

def check_page(page, page_url, known_issues, screenshot_dir, wrapcheck_url):
    """Run probe + right-edge check on the given (already-navigated) page."""
    page.wait_for_timeout(1500)  # let charts / embeds settle

    # Load wrap-safe probe if not already on the page.
    if not page.evaluate("typeof window.__wrapcheck === 'function'"):
        page.add_script_tag(url=wrapcheck_url)
        try:
            page.wait_for_function("typeof window.__wrapcheck === 'function'", timeout=5000)
        except Exception:
            return {"page": page_url, "error": f"could not load wrapcheck.js from {wrapcheck_url}"}

    wrap_report = page.evaluate("window.__wrapcheck({silent: true})")
    edge_report = page.evaluate(RIGHT_EDGE_JS)

    # Filter known-issue matches.
    findings = wrap_report.get("findings", [])
    new_findings = []
    for f in findings:
        if not _matches_known(f, page_url, known_issues):
            new_findings.append(f)

    # Magician's-divider check.
    edge_failure = None
    if edge_report["spread"] > RIGHT_EDGE_TOLERANCE_PX:
        edge_failure = edge_report

    # Screenshot for the record.
    if screenshot_dir:
        os.makedirs(screenshot_dir, exist_ok=True)
        slug = page_url.replace("://", "_").replace("/", "_").replace("?", "_").replace("=", "_").replace(":", "_")
        sp = os.path.join(screenshot_dir, slug + ".png")
        try:
            page.screenshot(path=sp, full_page=True)
        except Exception:
            sp = None
    else:
        sp = None

    return {
        "page": page_url,
        "findings_total": len(findings),
        "findings_new": new_findings,
        "findings_known": len(findings) - len(new_findings),
        "right_edge": edge_report,
        "edge_failure": edge_failure,
        "body_scroll_height": wrap_report.get("bodyScrollHeight"),
        "screenshot": sp,
    }


def _matches_known(finding, page_url, known_issues):
    """Match against the repo's known-issues.json entries.

    Normalizes URLs so '/', '', and 'index.html' all match each other (deployed
    Netlify URLs use '/'; known-issues entries are written as 'index.html')."""
    # Build a set of URL aliases that should all match the same known-issue page key.
    aliases = {page_url}
    if page_url.endswith("/"):
        aliases.add(page_url + "index.html")
        aliases.add(page_url.rstrip("/"))
    # If URL has no trailing path, also try with /index.html appended
    if not page_url.endswith(".html") and "?" not in page_url:
        aliases.add(page_url.rstrip("/") + "/index.html")

    for entry in known_issues:
        page_key = entry.get("page", "")
        if not any(alias.endswith(page_key) for alias in aliases):
            continue
        if "textPreview" in entry:
            if finding.get("textPreview") == entry["textPreview"]:
                return True
        elif "match" in entry:
            m = entry["match"]
            if m.startswith("tag:") and m[4:] in str(finding.get("tag", "")):
                return True
    return False


# --------------------------------------------------------------- modes

def run_local(args):
    portal = os.path.abspath(args.portal)
    known = _load_known_issues(args.known_issues)
    pages = _enumerate_pages(portal, args.pages)
    print(f"\n[verify-text-wrap] local mode · portal={portal} · pages={len(pages)}", flush=True)

    with local_server(portal) as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT)
        if args.gate_key:
            ctx.add_init_script(f"try {{ sessionStorage.setItem('{args.gate_key}', '1'); }} catch (e) {{}}")
        page = ctx.new_page()
        reports = []
        for pname in pages:
            url = f"{base_url}/{pname}"
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                reports.append({"page": pname, "error": str(e)})
                continue
            reports.append(check_page(page, pname, known, args.screenshot_dir, args.wrapcheck_url))
        ctx.close()
        browser.close()

    return _emit(reports, args)


def run_deployed(args):
    known = _load_known_issues(args.known_issues)
    base_url = args.deployed.rstrip("/")
    pages = args.pages or ["/"]
    print(f"\n[verify-text-wrap] deployed mode · base={base_url} · pages={len(pages)}", flush=True)

    # If Browserbase is wired up, prefer it; otherwise fall back to local Playwright.
    bb_ctx = use_browserbase_if_available()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT)
        if args.gate_key:
            ctx.add_init_script(f"try {{ sessionStorage.setItem('{args.gate_key}', '1'); }} catch (e) {{}}")
        page = ctx.new_page()
        reports = []
        for pname in pages:
            url = base_url if pname == "/" else f"{base_url}/{pname.lstrip('/')}"
            try:
                resp = page.goto(url, wait_until="networkidle", timeout=20000)
            except Exception as e:
                reports.append({"page": pname, "error": str(e)})
                continue
            # Sanity guard: real HTTP 200 + real content.
            if resp and resp.status >= 400:
                reports.append({"page": pname, "error": f"HTTP {resp.status} (URL probably wrong)"})
                continue
            body_len = page.evaluate("document.body.textContent.trim().length")
            if body_len < 200:
                reports.append({"page": pname, "error": f"body length {body_len} chars — wrong URL or hard error"})
                continue
            # If gate is still showing (sessionStorage didn't unlock), try password.
            if args.gate_password and page.evaluate("!!document.querySelector('input[type=password]')") and page.evaluate("document.querySelector('input[type=password]').offsetParent !== null"):
                try:
                    page.fill("input[type=password]", args.gate_password)
                    page.press("input[type=password]", "Enter")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass  # fall through; check_page may still find content
            reports.append(check_page(page, url, known, args.screenshot_dir, args.wrapcheck_url))
        ctx.close()
        browser.close()

    if bb_ctx:
        bb_ctx.end()
    return _emit(reports, args)


# --------------------------------------------------------------- helpers

def _enumerate_pages(portal, override):
    if override:
        return override
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(portal, "*.html"))
                   if os.path.basename(p) != "404.html")
    return pages


def _load_known_issues(path):
    if not path or not os.path.exists(path):
        return []
    with open(path) as fh:
        data = json.load(fh)
    return data.get("known", [])


def _emit(reports, args):
    """Print human-readable report and return exit code."""
    any_failure = False
    for r in reports:
        if "error" in r:
            print(f"\n  ✗ {r['page']}: {r['error']}")
            any_failure = True
            continue
        new = r["findings_new"]
        edge = r["edge_failure"]
        print(f"\n  {r['page']}")
        if new:
            any_failure = True
            print(f"    ✗ wrap-safe probe: {len(new)} NEW finding(s)")
            for f in new[:6]:
                kind = f.get("kind", "?")
                if kind in ("short-text-many-lines", "heading-many-lines", "caterpillar-element"):
                    print(f"        {kind}: <{f.get('tag')}.{f.get('cls','')}> w={f.get('cellWidth')}px lines={f.get('textLines')} \"{f.get('textPreview','')}\"")
                else:
                    print(f"        {kind}: {f.get('tag')} w={f.get('width', f.get('cellWidth'))}")
        else:
            print(f"    ✓ wrap-safe probe: 0 NEW findings ({r['findings_known']} known-issue match{'es' if r['findings_known'] != 1 else ''})")
        if edge:
            any_failure = True
            counts = edge["counts"]
            samples_by_edge = edge.get("samplesByEdge", {})
            print(f"    ✗ right-edge spread: {edge['spread']}px across {len(edge['rightEdges'])} distinct edges")
            for x in sorted(counts.items(), key=lambda kv: -kv[1])[:5]:
                edge_px = x[0]
                count = x[1]
                print(f"        right={edge_px}px (×{count})")
                # Show one sample per edge so user knows what's at each X
                samples = samples_by_edge.get(str(edge_px)) or samples_by_edge.get(edge_px) or []
                for s in samples[:2]:
                    print(f"          <{s['tag']}.{s['cls']}> w={s['width']} max-width:{s['maxWidth']} \"{s['text']}\"")
        else:
            print(f"    ✓ right-edge alignment: all prose within {RIGHT_EDGE_TOLERANCE_PX}px")
        if r.get("screenshot"):
            print(f"    📸 {r['screenshot']}")

    print(f"\n[verify-text-wrap] {'FAIL' if any_failure else 'PASS'}")
    return 1 if any_failure else 0


# --------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--local", action="store_true", help="Run against local portal directory via http server")
    g.add_argument("--deployed", metavar="URL", help="Run against deployed URL")
    p.add_argument("--portal", default="portal", help="Portal directory for --local mode")
    p.add_argument("--gate-key", default=None, help="sessionStorage key to set for gate bypass")
    p.add_argument("--gate-password", default=None, help="Password to type if sessionStorage bypass fails (deployed mode)")
    p.add_argument("--known-issues", default=None, help="Path to tests/wrap-known-issues.json")
    p.add_argument("--pages", nargs="+", help="Specific pages to test (default: all *.html in portal)")
    p.add_argument("--screenshot-dir", default="/tmp/verify-text-wrap", help="Where to drop screenshots")
    p.add_argument("--wrapcheck-url", default=DEFAULT_WRAPCHECK_URL,
                   help=f"URL of wrap-safe's wrapcheck.js (default: {DEFAULT_WRAPCHECK_URL})")
    args = p.parse_args()

    if args.local:
        return run_local(args)
    return run_deployed(args)


if __name__ == "__main__":
    sys.exit(main())
