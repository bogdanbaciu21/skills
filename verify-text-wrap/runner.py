#!/usr/bin/env python3
"""verify-text-wrap runner — local + deployed mode.

See ../SKILL.md for the protocol this implements.

Usage:
    python3 runner.py --local --portal portal/ --gate-key KEY [--known-issues PATH]
    python3 runner.py --deployed URL [--gate-key KEY --gate-password PASSWORD] [--known-issues PATH]

Exit codes:
    0 — all pages pass (or only known-issue matches)
    1 — at least one NEW finding (wrap, typography, overflow, right-edge spread)
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

# Default location of the wrap-safe probe. Prefer the local file bundled in this
# skill so edits take effect immediately against deployed pages. Fall back to the
# public CDN when the runner is copied somewhere without wrapcheck.js next to it.
DEFAULT_WRAPCHECK_URL = "https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/verify-text-wrap/wrapcheck.js"
DEFAULT_WRAPCHECK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "wrapcheck.js"))
DEFAULT_VIEWPORTS = [
    {"name": "wide", "width": 1440, "height": 900},
    {"name": "desktop", "width": 1280, "height": 900},
    {"name": "laptop", "width": 1024, "height": 900},
    {"name": "tablet-wide", "width": 820, "height": 900},
    {"name": "tablet", "width": 768, "height": 900},
    {"name": "phone-wide", "width": 430, "height": 844},
    {"name": "mobile", "width": 390, "height": 844},
    {"name": "phone-narrow", "width": 360, "height": 780},
]

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
    // Walk up to the main page/prose ancestor, checking for any grid/flex
    // parent with > 1 visible column.
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 8) {
      if (node.matches('.article, .doc, .prose, main, [class$="-page"], body, html')) break;
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

  function isInFramedComponent(el) {
    // Right-edge alignment is a main-reading-flow check. Text inside cards,
    // notes, panels, hero bands, footers, and other framed components has its
    // own padding box by design and should not be compared to the page edge.
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 8) {
      if (node.matches('.article, .doc, .prose, [class$="-page"], main, body, html')) break;
      const cls = typeof node.className === 'string' ? node.className : '';
      if (/(^|[-_\\s])(card|tile|panel|note|not|callout|hero|foot|footer|nav|stage|stop|chip|badge|kpi|metric|banner|alert|summary|meta|head|body|link|quote)([-_\\s]|$)/i.test(cls)) {
        return true;
      }
      const cs = getComputedStyle(node);
      const bg = cs.backgroundColor;
      const hasPaintedBox = (
        cs.borderTopStyle !== 'none' ||
        cs.borderRightStyle !== 'none' ||
        cs.borderBottomStyle !== 'none' ||
        cs.borderLeftStyle !== 'none' ||
        parseFloat(cs.borderTopWidth) > 0 ||
        cs.boxShadow !== 'none' ||
        parseFloat(cs.borderTopLeftRadius) > 0 ||
        (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent')
      );
      if (hasPaintedBox) return true;
      node = node.parentElement;
      depth++;
    }
    return false;
  }

  const SEL = 'main h1, main h2, main h3, main h4, main h5, main h6, ' +
              'main p, main li, main blockquote, main dd, main dt, main figcaption, ' +
              '[class$="-page"] h1, [class$="-page"] h2, [class$="-page"] h3, ' +
              '[class$="-page"] h4, [class$="-page"] h5, [class$="-page"] h6, ' +
              '[class$="-page"] p, [class$="-page"] li, [class$="-page"] blockquote, ' +
              '.doc h1, .doc h2, .doc h3, .doc h4, .doc h5, .doc h6, ' +
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
    if (isInFramedComponent(el)) { skipped++; continue; }
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

def check_page(page, page_url, known_issues, screenshot_dir, wrapcheck_source, viewport, settle_ms, font_timeout_ms):
    """Run probe + right-edge check on the given (already-navigated) page."""
    _wait_for_fonts(page, font_timeout_ms)

    if settle_ms > 0:
        page.wait_for_timeout(settle_ms)  # let charts / embeds settle

    # Load wrap-safe probe if not already on the page.
    if not page.evaluate("typeof window.__wrapcheck === 'function'"):
        _add_wrapcheck_script(page, wrapcheck_source)
        try:
            page.wait_for_function("typeof window.__wrapcheck === 'function'", timeout=5000)
        except Exception:
            return {"page": page_url, "viewport": viewport, "error": f"could not load wrapcheck.js from {wrapcheck_source}"}

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
        slug = f"{slug}__{viewport['name']}_{viewport['width']}x{viewport['height']}"
        sp = os.path.join(screenshot_dir, slug + ".png")
        try:
            page.screenshot(path=sp, full_page=True)
        except Exception:
            sp = None
    else:
        sp = None

    return {
        "page": page_url,
        "viewport": viewport,
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
    viewports = _parse_viewports(args.viewports)
    wrapcheck_source = _default_wrapcheck_source(args.wrapcheck_url)
    print(f"\n[verify-text-wrap] local mode · portal={portal} · pages={len(pages)} · viewports={_viewport_summary(viewports)}", flush=True)
    print(f"[verify-text-wrap] wrapcheck={wrapcheck_source}", flush=True)

    with local_server(portal) as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch()
        reports = []
        for viewport in viewports:
            ctx = browser.new_context(viewport={"width": viewport["width"], "height": viewport["height"]})
            _install_gate_bypass(ctx, args.gate_key)
            page = ctx.new_page()
            for pname in pages:
                url = f"{base_url}/{pname}"
                try:
                    page.goto(url, wait_until=args.wait_until, timeout=args.nav_timeout_ms)
                except Exception as e:
                    reports.append({"page": pname, "viewport": viewport, "error": str(e)})
                    continue
                reports.append(check_page(page, pname, known, args.screenshot_dir, wrapcheck_source, viewport, args.settle_ms, args.font_timeout_ms))
            ctx.close()
        browser.close()

    return _emit(reports, args)


def run_deployed(args):
    known = _load_known_issues(args.known_issues)
    base_url = args.deployed.rstrip("/")
    pages = args.pages or ["/"]
    viewports = _parse_viewports(args.viewports)
    wrapcheck_source = _default_wrapcheck_source(args.wrapcheck_url)
    print(f"\n[verify-text-wrap] deployed mode · base={base_url} · pages={len(pages)} · viewports={_viewport_summary(viewports)}", flush=True)
    print(f"[verify-text-wrap] wrapcheck={wrapcheck_source}", flush=True)

    # If Browserbase is wired up, prefer it; otherwise fall back to local Playwright.
    bb_ctx = use_browserbase_if_available()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        reports = []
        for viewport in viewports:
            ctx = browser.new_context(viewport={"width": viewport["width"], "height": viewport["height"]})
            _install_gate_bypass(ctx, args.gate_key)
            page = ctx.new_page()
            for pname in pages:
                url = base_url if pname == "/" else f"{base_url}/{pname.lstrip('/')}"
                try:
                    resp = page.goto(url, wait_until=args.wait_until, timeout=args.nav_timeout_ms)
                except Exception as e:
                    reports.append({"page": pname, "viewport": viewport, "error": str(e)})
                    continue
                # Sanity guard: real HTTP 200 + real content.
                if resp and resp.status >= 400:
                    reports.append({"page": pname, "viewport": viewport, "error": f"HTTP {resp.status} (URL probably wrong)"})
                    continue
                body_len = page.evaluate("document.body.textContent.trim().length")
                if body_len < 200:
                    reports.append({"page": pname, "viewport": viewport, "error": f"body length {body_len} chars — wrong URL or hard error"})
                    continue
                # If gate is still showing, try password.
                if args.gate_password and page.evaluate("!!document.querySelector('input[type=password]')") and page.evaluate("document.querySelector('input[type=password]').offsetParent !== null"):
                    try:
                        page.fill("input[type=password]", args.gate_password)
                        page.press("input[type=password]", "Enter")
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass  # fall through; check_page may still find content
                reports.append(check_page(page, url, known, args.screenshot_dir, wrapcheck_source, viewport, args.settle_ms, args.font_timeout_ms))
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


def _default_wrapcheck_source(cli_value):
    if cli_value:
        return cli_value
    if os.path.exists(DEFAULT_WRAPCHECK_PATH):
        return DEFAULT_WRAPCHECK_PATH
    return DEFAULT_WRAPCHECK_URL


def _add_wrapcheck_script(page, source):
    if source.startswith(("http://", "https://")):
        page.add_script_tag(url=source)
    else:
        page.add_script_tag(path=os.path.abspath(source))


def _install_gate_bypass(ctx, gate_key):
    if not gate_key:
        return
    script = (
        "try { "
        f"sessionStorage.setItem({json.dumps(gate_key)}, '1'); "
        f"localStorage.setItem({json.dumps(gate_key)}, '1'); "
        "} catch (e) {}"
    )
    ctx.add_init_script(script)


def _wait_for_fonts(page, timeout_ms):
    if timeout_ms <= 0:
        return
    try:
        page.wait_for_function(
            "() => !document.fonts || document.fonts.status === 'loaded'",
            timeout=timeout_ms,
        )
    except Exception:
        # Keep the guard useful even on pages with a slow/missing font file.
        # The screenshot and report still show what rendered.
        pass


def _parse_viewports(raw):
    if not raw:
        return DEFAULT_VIEWPORTS
    presets = {v["name"]: v for v in DEFAULT_VIEWPORTS}
    out = []
    items = []
    for part in raw:
        items.extend([x for x in part.split(",") if x])
    for item in items:
        item = item.strip()
        if not item:
            continue
        if item in presets:
            out.append(dict(presets[item]))
            continue
        if "x" not in item:
            raise SystemExit(f"unknown viewport '{item}' (use one of {', '.join(presets)} or WIDTHxHEIGHT)")
        width, height = item.lower().split("x", 1)
        try:
            width_i = int(width)
            height_i = int(height)
        except ValueError:
            raise SystemExit(f"bad viewport '{item}' (expected WIDTHxHEIGHT)")
        out.append({"name": item, "width": width_i, "height": height_i})
    return out or DEFAULT_VIEWPORTS


def _viewport_summary(viewports):
    return ", ".join(f"{v['name']}:{v['width']}x{v['height']}" for v in viewports)


def _emit(reports, args):
    """Print human-readable report and return exit code."""
    if getattr(args, "json_report", None):
        _write_json_report(args.json_report, reports)

    any_failure = False
    for r in reports:
        viewport = r.get("viewport") or {}
        vp_label = f"{viewport.get('name', '?')} {viewport.get('width', '?')}x{viewport.get('height', '?')}"
        if "error" in r:
            print(f"\n  ✗ {r['page']} [{vp_label}]: {r['error']}")
            any_failure = True
            continue
        new = r["findings_new"]
        edge = r["edge_failure"]
        print(f"\n  {r['page']} [{vp_label}]")
        if new:
            any_failure = True
            print(f"    ✗ wrap-safe probe: {len(new)} NEW finding(s)")
            for f in new[:6]:
                kind = f.get("kind", "?")
                if kind in ("short-text-many-lines", "heading-many-lines", "caterpillar-element"):
                    print(f"        {kind}: <{f.get('tag')}.{f.get('cls','')}> w={f.get('cellWidth')}px lines={f.get('textLines')} \"{f.get('textPreview','')}\"")
                elif kind == "typography-anti-pattern":
                    rules = ", ".join(f.get("rules", []))
                    print(f"        {kind}: <{f.get('selector', f.get('tag'))}> w={f.get('cellWidth')}px rules={rules} \"{f.get('textPreview','')}\"")
                elif kind == "dense-prose-in-narrow-column":
                    print(f"        {kind}: <{f.get('selector', f.get('tag'))}> w={f.get('cellWidth')}px lines={f.get('textLines')} \"{f.get('textPreview','')}\"")
                elif kind in ("display-text-orphan-line", "display-text-short-final-line"):
                    label = f.get("orphanText") or f.get("finalLineText") or ""
                    lines = " / ".join(f.get("lineTexts", [])[-3:])
                    print(f"        {kind}: <{f.get('selector', f.get('tag'))}> w={f.get('cellWidth')}px final=\"{label}\" lines=\"{lines}\"")
                elif kind == "clipped-text":
                    print(f"        {kind}: <{f.get('selector', f.get('tag'))}> hiddenX={f.get('hiddenX')}px hiddenY={f.get('hiddenY')}px \"{f.get('textPreview','')}\"")
                elif kind in ("body-horizontal-overflow", "element-horizontal-overflow"):
                    print(f"        {kind}: <{f.get('selector', f.get('tag', 'body'))}> overflow={f.get('overflowPx')}px \"{f.get('textPreview','')}\"")
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


def _write_json_report(path, reports):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "checks": len(reports),
            "failures": sum(1 for r in reports if r.get("error") or r.get("findings_new") or r.get("edge_failure")),
        },
        "reports": reports,
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


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
    p.add_argument("--viewports", nargs="*", default=None,
                   help="Viewport presets/numbers to test. Default: wide laptop tablet mobile. Accepts comma-separated values and WIDTHxHEIGHT.")
    p.add_argument("--wait-until", default="domcontentloaded",
                   choices=["commit", "domcontentloaded", "load", "networkidle"],
                   help="Playwright navigation readiness. Default domcontentloaded keeps portal-wide static sweeps fast; the probe still waits briefly before measuring.")
    p.add_argument("--nav-timeout-ms", type=int, default=8000,
                   help="Per-page navigation timeout in milliseconds. Default 8000.")
    p.add_argument("--settle-ms", type=int, default=750,
                   help="Delay after navigation before measuring. Default 750; use 0-250 for fast full-estate static sweeps, higher for animated/chart-heavy pages.")
    p.add_argument("--font-timeout-ms", type=int, default=5000,
                   help="Wait up to this many ms for document.fonts to load before measuring. Default 5000; use 0 to disable.")
    p.add_argument("--json-report", default=None,
                   help="Optional path to write the structured report JSON.")
    p.add_argument("--wrapcheck-url", default=None,
                   help=f"URL or local path of wrap-safe's wrapcheck.js (default: sibling {DEFAULT_WRAPCHECK_PATH}, fallback {DEFAULT_WRAPCHECK_URL})")
    args = p.parse_args()

    if args.local:
        return run_local(args)
    return run_deployed(args)


if __name__ == "__main__":
    sys.exit(main())
