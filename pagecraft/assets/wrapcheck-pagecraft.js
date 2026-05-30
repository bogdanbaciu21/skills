(function () {
  "use strict";

  var PROSE_SELECTOR = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "td", "th", "caption", "label", "a",
    "dt", "dd", "blockquote", "figcaption"
  ].join(",");

  var NARROW_CONTAINER_SELECTOR = [
    "main", "article", "section", ".doc", ".article", ".prose",
    ".content", ".pc-page", ".pc-prose", "[class$='-page']"
  ].join(",");

  var OVERFLOW_OK_SELECTOR = [
    "table", "pre", "code", ".pc-table-wrap", ".bbt-wrap",
    ".bb-table-wrap", ".table-scroll", ".table-wrap", ".scroll",
    ".overflow-section", "[data-wrap-overflow-ok]"
  ].join(",");

  function text(el) {
    return (el.textContent || "").replace(/\s+/g, " ").trim();
  }

  function shortSelector(el) {
    var tag = el.tagName ? el.tagName.toLowerCase() : "node";
    var cls = "";
    if (typeof el.className === "string" && el.className.trim()) {
      cls = "." + el.className.trim().split(/\s+/).slice(0, 3).join(".");
    }
    return tag + cls;
  }

  function isVisible(el) {
    if (!el || !el.getBoundingClientRect) return false;
    var style = getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") return false;
    var rect = el.getBoundingClientRect();
    return rect.width > 1 && rect.height > 1;
  }

  function isUserText(el) {
    if (!isVisible(el)) return false;
    if (el.closest("script, style, noscript, svg, canvas, [hidden], [aria-hidden='true']")) return false;
    if (el.closest(OVERFLOW_OK_SELECTOR)) return false;
    return text(el).length > 0;
  }

  function hasCompositeChildren(el) {
    return Array.prototype.some.call(el.children || [], function (child) {
      if (!isVisible(child)) return false;
      return !/^(A|ABBR|B|BR|CODE|EM|I|KBD|MARK|S|SAMP|SMALL|SPAN|STRONG|SUB|SUP|TIME|U)$/.test(child.tagName);
    });
  }

  function lineCount(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var tops = [];
    Array.prototype.forEach.call(range.getClientRects(), function (rect) {
      if (rect.width <= 1 || rect.height <= 1) return;
      var top = Math.round(rect.top);
      if (tops.indexOf(top) === -1) tops.push(top);
    });
    range.detach();
    return tops.length;
  }

  function add(findings, kind, el, extra) {
    var rect = el.getBoundingClientRect();
    var payload = {
      kind: kind,
      tag: shortSelector(el),
      cls: typeof el.className === "string" ? el.className : "",
      width: Math.round(rect.width),
      cellWidth: Math.round(rect.width),
      textPreview: text(el).slice(0, 100)
    };
    Object.keys(extra || {}).forEach(function (key) {
      payload[key] = extra[key];
    });
    findings.push(payload);
  }

  function checkPageLength(findings) {
    var height = Math.max(document.body ? document.body.scrollHeight : 0, document.documentElement ? document.documentElement.scrollHeight : 0);
    var viewport = window.innerHeight || 1;
    if (height > viewport * 30) {
      findings.push({
        kind: "nuclear-scroll-height",
        tag: "body",
        width: Math.round(document.documentElement.getBoundingClientRect().width || window.innerWidth || 0),
        bodyScrollHeight: height,
        viewportHeight: viewport,
        ratio: Math.round((height / viewport) * 10) / 10
      });
    }
  }

  function checkNarrowContainers(findings) {
    Array.prototype.forEach.call(document.querySelectorAll(NARROW_CONTAINER_SELECTOR), function (el) {
      if (!isVisible(el)) return;
      if (el.closest(OVERFLOW_OK_SELECTOR)) return;
      var rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.width < 200) {
        add(findings, "narrow-container", el, { containerWidth: Math.round(rect.width) });
      }
    });
  }

  function checkTextLines(findings) {
    Array.prototype.forEach.call(document.querySelectorAll(PROSE_SELECTOR), function (el) {
      if (!isUserText(el)) return;
      if (hasCompositeChildren(el)) return;
      var value = text(el);
      var lines = lineCount(el);
      var width = Math.round(el.getBoundingClientRect().width);
      if (!lines) return;

      if (/^H[1-6]$/.test(el.tagName) && width < 340 && lines > 3) {
        add(findings, "heading-many-lines", el, { textLines: lines });
        return;
      }

      if (width < 260 && value.length <= 40 && lines > 2) {
        add(findings, "short-text-many-lines", el, { textLines: lines });
        return;
      }

      if (width < 260 && value.length <= 180 && lines > 8) {
        add(findings, "caterpillar-element", el, { textLines: lines });
      }
    });
  }

  function checkTypographyAntiPatterns(findings) {
    Array.prototype.forEach.call(document.querySelectorAll(PROSE_SELECTOR), function (el) {
      if (!isUserText(el)) return;
      var style = getComputedStyle(el);
      if (style.wordBreak === "break-all") {
        add(findings, "forced-word-breaking", el, {
          wordBreak: style.wordBreak,
          overflowWrap: style.overflowWrap
        });
      }
      if (style.hyphens === "auto" && !el.closest(".pc-table, .bbt, .bb-table")) {
        add(findings, "auto-hyphenation", el, { hyphens: style.hyphens });
      }
    });
  }

  window.__wrapcheck = function () {
    var findings = [];
    checkPageLength(findings);
    checkNarrowContainers(findings);
    checkTextLines(findings);
    checkTypographyAntiPatterns(findings);
    return {
      version: "pagecraft-2026-05-30",
      bodyScrollHeight: Math.max(document.body ? document.body.scrollHeight : 0, document.documentElement ? document.documentElement.scrollHeight : 0),
      findings: findings
    };
  };
}());
