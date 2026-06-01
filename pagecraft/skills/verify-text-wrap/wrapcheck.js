/* ============================================================================
 * wrapcheck.js — v0.2.3
 *
 * Runtime probe for caterpillar-text and container-collapse bugs.
 * Exposes window.__wrapcheck() for manual use; auto-runs on ?wrapcheck=1.
 *
 * Source: https://github.com/bogdanbaciu21/skills/tree/main/wrap-safe
 * License: MIT
 *
 * v0.2.3 — STRICTER DISPLAY TAIL RATCHET.
 *   - Treats visibly undersized three-word final lines as line-quality
 *     failures when they are short relative to both the prior line and box.
 *
 * v0.2.2 — LINE QUALITY + CLIPPING RATCHET.
 *   - Extends display-text checks beyond one-word orphans to very short
 *     final lines that are visibly disproportionate to the prior line.
 *   - Flags visible text clipped by overflow-hidden boxes when the text is
 *     not using intentional ellipsis.
 *
 * v0.2.1 — DISPLAY-TEXT ORPHAN RATCHET.
 *   - Flags headline/lede/display text whose final visual line is a stranded
 *     one-word orphan, including elements with inline children such as <b> and
 *     <em>. This catches "Harvest your own / margin."-class failures.
 *
 * v0.2.0 — TYPOGRAPHY RATCHET.
 *   - Flags CSS typography anti-patterns that create visible word fragments:
 *     `hyphens:auto`, `text-wrap:pretty`, `text-wrap:balance` on prose, and
 *     `word-break:break-all`.
 *   - Flags dense long prose trapped in narrow card/sidebar columns on
 *     tablet/desktop widths.
 *   - Flags horizontal overflow at body and element level.
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
 *   <script src="https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/wrap-safe/wrapcheck.js" defer></script>
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
  var NARROW_CONTAINER_SELECTOR = 'article, main, section, .doc, .article, .prose, .news-item, .ma-section, .pa-section, .ts-section, [class$="-page"]';
  var NARROW_CONTAINER_THRESHOLD = 200; // px
  var SHORT_TEXT_MAX_CHARS = 40;        // chars considered "short"
  var SHORT_TEXT_MAX_LINES = 2;         // ≥ 3 lines for short text triggers
  var HEADING_MAX_LINES = 3;            // > 3 lines for any heading triggers
  var CATERPILLAR_LINES = 12;           // > 12 lines triggers regardless of length
  var DENSE_BLOCK_MAX_WIDTH = 320;       // px, only enforced above mobile widths
  var DENSE_BLOCK_MIN_CHARS = 90;
  var DENSE_BLOCK_MIN_LINES = 4;
  var HORIZONTAL_OVERFLOW_TOLERANCE = 2; // px
  var ORPHAN_TEXT_MAX_CHARS = 220;
  var ORPHAN_LAST_LINE_MAX_WORDS = 1;
  var ORPHAN_LAST_LINE_MAX_CHARS = 14;
  var SHORT_FINAL_LINE_MAX_WORDS = 3;
  var SHORT_FINAL_LINE_MAX_CHARS = 32;
  var SHORT_FINAL_LINE_PREV_RATIO = 0.36;
  var SHORT_FINAL_LINE_BOX_RATIO = 0.25;
  var CLIPPED_TEXT_TOLERANCE = 3;

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

  var PROSE_SELECTOR = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'li', 'dd', 'dt', 'blockquote', 'figcaption', 'summary',
    'label', 'td', 'th', 'caption'
  ].join(', ');

  var OVERFLOW_SELECTOR = [
    'main', 'section', 'article',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'li', 'dd', 'dt', 'blockquote', 'figcaption',
    'label', 'td', 'th', 'caption',
    'pre', 'code', 'table',
    'div', 'span', 'a'
  ].join(', ');

  var ORPHAN_SELECTOR = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p',
    '[class*="title"]',
    '[class*="target"]',
    '[class*="headline"]',
    '[class*="heading"]',
    '[class*="headtext"]',
    '[class*="lede"]',
    '[class*="sub"]',
    '[class*="hero"]',
    '[class*="kicker"]'
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

  function textPreview(el, n) {
    return (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, n || 80);
  }

  function shortSelector(el) {
    var out = el.tagName.toLowerCase();
    if (el.id) out += '#' + el.id;
    if (el.className && typeof el.className === 'string') {
      var cls = el.className.split(/\s+/).filter(Boolean).slice(0, 4);
      if (cls.length) out += '.' + cls.join('.');
    }
    return out;
  }

  function isVisible(el) {
    var cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return false;
    var r = el.getBoundingClientRect();
    return r.width >= 1 && r.height >= 1;
  }

  function skipTypographyCheck(el) {
    return !!el.closest('pre, code, kbd, samp, script, style, noscript, svg, canvas, .sr-only, [aria-hidden="true"]');
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

  function visualWordLines(el) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !/\S/.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
        var parent = node.parentElement;
        if (!parent || skipTypographyCheck(parent) || !isVisible(parent)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var words = [];
    var range = document.createRange();
    var node;
    while ((node = walker.nextNode())) {
      var text = node.nodeValue || '';
      var match;
      var re = /\S+/g;
      while ((match = re.exec(text))) {
        range.setStart(node, match.index);
        range.setEnd(node, match.index + match[0].length);
        var rect = range.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1) continue;
        words.push({
          text: match[0],
          top: rect.top,
          left: rect.left,
          right: rect.right,
          width: rect.width
        });
      }
    }
    range.detach && range.detach();
    if (!words.length) return [];

    words.sort(function (a, b) {
      if (Math.abs(a.top - b.top) > 2) return a.top - b.top;
      return a.left - b.left;
    });

    var lines = [];
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      var line = null;
      for (var j = lines.length - 1; j >= 0; j--) {
        if (Math.abs(lines[j].top - w.top) <= 2) {
          line = lines[j];
          break;
        }
      }
      if (!line) {
        line = { top: w.top, left: w.left, right: w.right, words: [] };
        lines.push(line);
      }
      line.words.push(w);
      line.left = Math.min(line.left, w.left);
      line.right = Math.max(line.right, w.right);
    }

    lines.sort(function (a, b) { return a.top - b.top; });
    for (var k = 0; k < lines.length; k++) {
      lines[k].words.sort(function (a, b) { return a.left - b.left; });
      lines[k].text = lines[k].words.map(function (w) { return w.text; }).join(' ');
      lines[k].wordCount = lines[k].words.length;
      lines[k].charCount = lines[k].text.replace(/\s+/g, '').length;
      lines[k].width = Math.round(lines[k].right - lines[k].left);
      lines[k].top = Math.round(lines[k].top);
    }
    return lines;
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
      selector: shortSelector(el),
      textPreview: textPreview(el),
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

  function checkTypographyAntiPatterns() {
    var findings = [];
    var seen = Object.create(null);
    var nodes = document.querySelectorAll(PROSE_SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isVisible(el) || skipTypographyCheck(el)) continue;
      var text = textPreview(el, 100);
      if (text.length < 8) continue;
      var cs = getComputedStyle(el);
      var r = el.getBoundingClientRect();
      var bad = [];

      if (cs.hyphens === 'auto' || cs.webkitHyphens === 'auto') {
        bad.push('hyphens:auto');
      }
      if (cs.wordBreak === 'break-all') {
        bad.push('word-break:break-all');
      }
      if (cs.textWrap === 'pretty') {
        bad.push('text-wrap:pretty');
      } else if (cs.textWrap === 'balance') {
        bad.push('text-wrap:balance');
      }

      if (!bad.length) continue;
      var key = bad.join('|') + '|' + shortSelector(el);
      if (seen[key]) continue;
      seen[key] = 1;
      findings.push({
        kind: 'typography-anti-pattern',
        selector: shortSelector(el),
        tag: el.tagName.toLowerCase(),
        cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
        cellWidth: Math.round(r.width),
        textLen: text.length,
        rules: bad,
        textPreview: text,
        ancestors: ancestorChain(el)
      });
      if (findings.length >= 80) break;
    }
    return findings;
  }

  function checkDenseNarrowTextBlocks() {
    var findings = [];
    var viewportW = window.innerWidth || document.documentElement.clientWidth;
    if (viewportW < 700) return findings;

    var nodes = document.querySelectorAll('p, li, dd, blockquote, figcaption, summary, td, th');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isVisible(el) || skipTypographyCheck(el)) continue;
      var text = textPreview(el, 160);
      if (text.length < DENSE_BLOCK_MIN_CHARS) continue;
      var r = el.getBoundingClientRect();
      if (r.width > DENSE_BLOCK_MAX_WIDTH) continue;
      var lines = textLineCount(el);
      if (lines === null || lines < DENSE_BLOCK_MIN_LINES) continue;
      findings.push({
        kind: 'dense-prose-in-narrow-column',
        selector: shortSelector(el),
        tag: el.tagName.toLowerCase(),
        cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
        cellWidth: Math.round(r.width),
        textLines: lines,
        textLen: (el.textContent || '').trim().length,
        textPreview: text,
        ancestors: ancestorChain(el)
      });
      if (findings.length >= 50) break;
    }
    return findings;
  }

  function checkVisualOrphans() {
    var findings = [];
    var nodes = document.querySelectorAll(ORPHAN_SELECTOR);
    var seen = Object.create(null);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isVisible(el) || skipTypographyCheck(el)) continue;

      var selector = shortSelector(el);
      if (seen[selector]) continue;
      seen[selector] = 1;

      var text = textPreview(el, ORPHAN_TEXT_MAX_CHARS + 1);
      if (text.length < 12 || text.length > ORPHAN_TEXT_MAX_CHARS) continue;

      var cs = getComputedStyle(el);
      var fontSize = parseFloat(cs.fontSize) || 0;
      var cls = (el.className && typeof el.className === 'string') ? el.className : '';
      var displayText = /^h[1-6]$/i.test(el.tagName) ||
        fontSize >= 18 ||
        /(title|target|headline|heading|headtext|lede|sub|hero|kicker)/i.test(cls);
      if (!displayText) continue;

      var r = el.getBoundingClientRect();
      if (r.width < 80) continue;

      var lines = visualWordLines(el);
      if (lines.length < 2) continue;

      var last = lines[lines.length - 1];
      var prev = lines[lines.length - 2];
      if (!last || !prev) continue;

      var priorLines = lines.slice(0, -1);
      var avgPriorWords = priorLines.reduce(function (sum, line) {
        return sum + line.wordCount;
      }, 0) / priorLines.length;
      if (prev.wordCount < 3 && avgPriorWords < 2) continue;

      var lastCleanChars = last.text.replace(/[^A-Za-z0-9$%]/g, '').length;
      if (last.wordCount <= ORPHAN_LAST_LINE_MAX_WORDS &&
          lastCleanChars <= ORPHAN_LAST_LINE_MAX_CHARS) {
        findings.push({
          kind: 'display-text-orphan-line',
          selector: selector,
          tag: el.tagName.toLowerCase(),
          cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
          cellWidth: Math.round(r.width),
          fontSize: Math.round(fontSize),
          textLines: lines.length,
          orphanText: last.text,
          previousLineText: prev.text,
          lineTexts: lines.map(function (line) { return line.text; }),
          textPreview: text,
          ancestors: ancestorChain(el)
        });
        if (findings.length >= 60) break;
        continue;
      }

      var lastWidthRatioToPrev = prev.width > 0 ? last.width / prev.width : 1;
      var lastWidthRatioToBox = r.width > 0 ? last.width / r.width : 1;
      if (last.wordCount <= SHORT_FINAL_LINE_MAX_WORDS &&
          lastCleanChars <= SHORT_FINAL_LINE_MAX_CHARS &&
          lastWidthRatioToPrev <= SHORT_FINAL_LINE_PREV_RATIO &&
          lastWidthRatioToBox <= SHORT_FINAL_LINE_BOX_RATIO) {
        findings.push({
          kind: 'display-text-short-final-line',
          selector: selector,
          tag: el.tagName.toLowerCase(),
          cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
          cellWidth: Math.round(r.width),
          fontSize: Math.round(fontSize),
          textLines: lines.length,
          finalLineText: last.text,
          previousLineText: prev.text,
          finalLineWidth: last.width,
          previousLineWidth: prev.width,
          finalToPreviousRatio: Number(lastWidthRatioToPrev.toFixed(2)),
          finalToBoxRatio: Number(lastWidthRatioToBox.toFixed(2)),
          lineTexts: lines.map(function (line) { return line.text; }),
          textPreview: text,
          ancestors: ancestorChain(el)
        });
        if (findings.length >= 60) break;
      }
    }
    return findings;
  }

  function checkClippedText() {
    var findings = [];
    var nodes = document.querySelectorAll(TEXT_LEAF_SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isVisible(el) || skipTypographyCheck(el)) continue;
      var text = textPreview(el, 120);
      if (text.length < 8) continue;
      var cs = getComputedStyle(el);
      var clipsX = /(hidden|clip)/.test(cs.overflowX);
      var clipsY = /(hidden|clip)/.test(cs.overflowY);
      if (!clipsX && !clipsY) continue;
      if (cs.textOverflow === 'ellipsis' && cs.whiteSpace === 'nowrap') continue;

      var hiddenX = el.scrollWidth - el.clientWidth;
      var hiddenY = el.scrollHeight - el.clientHeight;
      if (hiddenX <= CLIPPED_TEXT_TOLERANCE && hiddenY <= CLIPPED_TEXT_TOLERANCE) continue;

      var r = el.getBoundingClientRect();
      findings.push({
        kind: 'clipped-text',
        selector: shortSelector(el),
        tag: el.tagName.toLowerCase(),
        cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
        cellWidth: Math.round(r.width),
        cellHeight: Math.round(r.height),
        hiddenX: Math.max(0, Math.round(hiddenX)),
        hiddenY: Math.max(0, Math.round(hiddenY)),
        overflowX: cs.overflowX,
        overflowY: cs.overflowY,
        textPreview: text,
        ancestors: ancestorChain(el)
      });
      if (findings.length >= 50) break;
    }
    return findings;
  }

  function checkHorizontalOverflow() {
    var findings = [];
    var viewportW = window.innerWidth || document.documentElement.clientWidth;
    var bodyOverflow = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) - viewportW;
    if (bodyOverflow > HORIZONTAL_OVERFLOW_TOLERANCE) {
      findings.push({
        kind: 'body-horizontal-overflow',
        overflowPx: Math.round(bodyOverflow),
        scrollWidth: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth),
        viewportWidth: viewportW
      });
    }

    var nodes = document.querySelectorAll(OVERFLOW_SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (!isVisible(el)) continue;
      if (el.closest('svg, canvas, script, style, noscript')) continue;
      var overflow = el.scrollWidth - el.clientWidth;
      if (overflow <= HORIZONTAL_OVERFLOW_TOLERANCE) continue;
      var r = el.getBoundingClientRect();
      if (r.width < 20 || r.height < 8) continue;
      findings.push({
        kind: 'element-horizontal-overflow',
        selector: shortSelector(el),
        tag: el.tagName.toLowerCase(),
        cls: (el.className && typeof el.className === 'string') ? el.className.split(/\s+/).filter(Boolean).slice(0, 4).join('.') : '',
        overflowPx: Math.round(overflow),
        clientWidth: el.clientWidth,
        scrollWidth: el.scrollWidth,
        textPreview: textPreview(el, 100),
        ancestors: ancestorChain(el)
      });
      if (findings.length >= 50) break;
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
    findings = findings.concat(checkTypographyAntiPatterns());
    findings = findings.concat(checkDenseNarrowTextBlocks());
    findings = findings.concat(checkVisualOrphans());
    findings = findings.concat(checkClippedText());
    findings = findings.concat(checkHorizontalOverflow());

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
      probeVersion: '0.2.3'
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
