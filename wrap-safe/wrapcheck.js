/* ============================================================================
 * wrapcheck.js — v0.1.2
 *
 * Runtime probe for caterpillar-text and container-collapse bugs.
 * Exposes window.__wrapcheck() for manual use; auto-runs on ?wrapcheck=1.
 *
 * Source: https://github.com/bogdanbaciu21/wrap-safe
 * License: MIT
 *
 * v0.1.2 — MAJOR PRECISION UPGRADE.
 *   - Counts visual lines via Range.getClientRects() instead of
 *     height / lineHeight. The old heuristic produced false positives in
 *     table cells (whose height inherits from the tallest cell in the row)
 *     and flex-centered containers (whose height is the container, not
 *     the text). The Range approach reports one rect per visual line by
 *     unique y-coordinate — the truth.
 *   - Expanded the suspect set to <td>, <th>, <h1..h6>, <p>, <li>, <a>,
 *     <span>, <div>, <label>, <summary>, <dt>, <dd>, <caption>. The old
 *     probe only checked p/li/blockquote and missed every table-cell and
 *     KPI-grid case.
 *   - Added "short-text-many-lines" check: any leaf with ≤ 40 chars of text
 *     wrapping to ≥ 3 lines. This is the WEIGHTED-AVG / LIFESPAN class.
 *   - Added "heading-many-lines" check: any h1..h6 wrapping to > 3 lines.
 *
 * v0.1.1 was: raise nuclear-scroll multiplier 10→30 + add opts.nuclearMultiplier.
 * v0.1.0 was: initial release with overly-narrow probe.
 *
 * Usage:
 *   <script src="https://cdn.jsdelivr.net/gh/bogdanbaciu21/wrap-safe@v0.1.2/wrapcheck.js" defer></script>
 *
 * Then in the browser console:
 *   __wrapcheck()              // returns the report and prints to console
 *   __wrapcheck({silent: true}) // returns the report, no console output
 *
 * Or append `?wrapcheck=1` to the URL to auto-run on load.
 *
 * It does NOT modify the DOM. Pure observation.
 * ============================================================================ */

(function () {
  'use strict';

  // bodyScrollHeight > N × viewport — the canonical caterpillar incident was
  // ~56×, normal long-content pages cluster at 10–20×, so 30 is the natural
  // breakpoint. Override via __wrapcheck({nuclearMultiplier: N}).
  var NUCLEAR_SCROLL_MULTIPLIER = 30;
  var NARROW_CONTAINER_SELECTOR = 'article, main, section, .doc, .article, .prose, .news-item, .ma-section, .pa-section, .ts-section';
  var NARROW_CONTAINER_THRESHOLD = 200; // px
  var SHORT_TEXT_MAX_CHARS = 40;        // chars considered "short"
  var SHORT_TEXT_MAX_LINES = 2;         // ≥ 3 lines for short text triggers
  var HEADING_MAX_LINES = 3;            // > 3 lines for any heading triggers
  var CATERPILLAR_LINES = 12;           // > 12 lines triggers regardless of length

  // Suspect element selector for line-count checks. Broad on purpose — the
  // v0.1.0 probe missed table cells, KPI labels, and tile headings because
  // it only looked at p/li/blockquote.
  var TEXT_LEAF_SELECTOR = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'li', 'td', 'th', 'caption',
    'label', 'a', 'span', 'div',
    'summary', 'dt', 'dd',
    'blockquote', 'figcaption'
  ].join(', ');

  // ------------------------------------------------------------------- helpers

  function ancestorChain(el, max) {
    var chain = [];
    var node = el;
    var depth = 0;
    while (node && node !== document.documentElement && depth < (max || 6)) {
      var cs = getComputedStyle(node);
      chain.push({
        tag: node.tagName.toLowerCase() +
             (node.id ? '#' + node.id : '') +
             (node.className && typeof node.className === 'string'
               ? '.' + node.className.split(/\s+/).filter(Boolean).slice(0, 3).join('.')
               : ''),
        width: cs.width,
        maxWidth: cs.maxWidth,
        display: cs.display,
        minWidth: cs.minWidth
      });
      node = node.parentElement;
      depth++;
    }
    return chain;
  }

  /**
   * Count visual lines of TEXT inside `el` using Range.getClientRects().
   * Returns null if `el` doesn't have a text leaf to measure (it has element
   * children or is empty). Returns the number of unique y-coordinates among
   * the text rects — each visual line is one y band.
   */
  function textLineCount(el) {
    if (el.children.length > 0) return null;
    var tn = el.firstChild;
    if (!tn || tn.nodeType !== 3) return null;
    var range = document.createRange();
    range.selectNodeContents(tn);
    var rects = range.getClientRects();
    if (!rects.length) return null;
    var ys = Object.create(null);
    var n = 0;
    for (var i = 0; i < rects.length; i++) {
      var r = rects[i];
      if (r.width < 1 || r.height < 1) continue;
      var y = Math.round(r.top);
      if (!ys[y]) { ys[y] = 1; n++; }
    }
    return n || rects.length;
  }

  function describe(el, lines) {
    var cs = getComputedStyle(el);
    var r = el.getBoundingClientRect();
    return {
      tag: el.tagName.toLowerCase(),
      cls: (el.className && typeof el.className === 'string')
        ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.')
        : '',
      id: el.id || '',
      cellWidth: Math.round(r.width),
      cellHeight: Math.round(r.height),
      textLines: lines,
      textPreview: (el.textContent || '').trim().slice(0, 80),
      textLen: (el.textContent || '').trim().length,
      ancestors: ancestorChain(el)
    };
  }

  // -------------------------------------------------------------------- checks

  function checkBodyScroll(multiplier) {
    var viewport = window.innerHeight || document.documentElement.clientHeight;
    var scrollH = document.body.scrollHeight;
    if (scrollH > viewport * multiplier) {
      return {
        kind: 'nuclear-scroll-height',
        scrollHeight: scrollH,
        viewport: viewport,
        ratio: Math.round(scrollH / viewport)
      };
    }
    return null;
  }

  function checkNarrowContainers() {
    var findings = [];
    var nodes = document.querySelectorAll(NARROW_CONTAINER_SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var cs = getComputedStyle(el);
      var width = parseFloat(cs.width);
      if (!isFinite(width)) continue;
      if (el.childElementCount < 1 && el.textContent.trim().length < 20) continue;
      if (width < NARROW_CONTAINER_THRESHOLD) {
        findings.push({
          kind: 'narrow-container',
          tag: el.tagName.toLowerCase() +
               (el.className && typeof el.className === 'string'
                 ? '.' + el.className.split(/\s+/)[0]
                 : ''),
          width: width,
          ancestors: ancestorChain(el)
        });
      }
    }
    return findings;
  }

  function checkLineCounts() {
    var findings = [];
    var nodes = document.querySelectorAll(TEXT_LEAF_SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var lines = textLineCount(el);
      if (lines === null) continue;
      var text = (el.textContent || '').trim();
      if (text.length < 3) continue;

      // A. Short text wrapping to many lines.
      if (text.length <= SHORT_TEXT_MAX_CHARS && lines > SHORT_TEXT_MAX_LINES) {
        findings.push({ kind: 'short-text-many-lines', ...describe(el, lines) });
        if (findings.length > 50) break;
      }
      // B. Heading wrapping too many lines.
      else if (/^h[1-6]$/i.test(el.tagName) && lines > HEADING_MAX_LINES) {
        findings.push({ kind: 'heading-many-lines', ...describe(el, lines) });
      }
      // C. Caterpillar — any element with text wrapping > 12 lines.
      else if (lines > CATERPILLAR_LINES) {
        findings.push({ kind: 'caterpillar-element', ...describe(el, lines) });
      }
    }
    return findings;
  }

  // ----------------------------------------------------------------------- run

  function runCheck(opts) {
    opts = opts || {};
    var findings = [];
    var multiplier = opts.nuclearMultiplier || NUCLEAR_SCROLL_MULTIPLIER;

    var bodyIssue = checkBodyScroll(multiplier);
    if (bodyIssue) findings.push(bodyIssue);

    findings = findings.concat(checkNarrowContainers());
    findings = findings.concat(checkLineCounts());

    var byKind = {};
    findings.forEach(function (f) { byKind[f.kind] = (byKind[f.kind] || 0) + 1; });

    var report = {
      ok: findings.length === 0,
      viewport: { w: window.innerWidth, h: window.innerHeight },
      bodyScrollHeight: document.body.scrollHeight,
      findings: findings,
      findingsByKind: byKind,
      url: location.href,
      ts: new Date().toISOString(),
      probeVersion: '0.1.2'
    };

    if (!opts.silent) {
      if (report.ok) {
        console.log('%c[wrapcheck] OK', 'color: #2f5b50; font-weight: 600;', report);
      } else {
        console.group('%c[wrapcheck] ' + findings.length + ' finding(s) — ' +
                      Object.keys(byKind).map(function (k) { return k + ':' + byKind[k]; }).join(' · '),
                      'color: #c45a3a; font-weight: 600;');
        findings.forEach(function (f, i) {
          console.log('#' + (i + 1) + ' ' + f.kind, f);
        });
        console.log('Full report:', report);
        console.groupEnd();
      }
    }

    return report;
  }

  window.__wrapcheck = runCheck;

  if (/[?&]wrapcheck=1\b/.test(location.search)) {
    if (document.readyState === 'complete') {
      runCheck();
    } else {
      window.addEventListener('load', function () { runCheck(); });
    }
  }
})();
