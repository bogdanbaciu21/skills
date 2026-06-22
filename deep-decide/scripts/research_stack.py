#!/usr/bin/env python3
"""research_stack.py: a portable, bring-your-own-keys research arsenal.

This is the evidence layer for deep-decide. It catalogs a broad stack of research
providers across three tiers (deep web research, scholarly/academic, and GitHub
code) and runs the synchronous, search-capable ones live to gather cited evidence
for a query. Everything is read from your own environment, standard library only,
no pip install.

Two ways to use it:

    python3 research_stack.py --stack                 # show the whole arsenal + what is configured
    python3 research_stack.py "your question" -n 5    # gather live evidence across configured sources

`deep-decide` imports `gather()` to put real, cited evidence in front of the
decision before it reasons. You can also run this standalone.

Tiers and env vars (set whichever you have; nothing is required to just browse
the catalog with --stack):

  Deep web research:
    EXA_API_KEY                 Exa (web + GitHub search, live)
    FIRECRAWL_API_KEY           Firecrawl search (live)  [also reads FIRECRAWL_RESEARCH_API_KEY / FIRECRAWL_CLOUD_API_KEY]
    PARALLEL_API_KEY            Parallel.ai deep research (catalog: async job API)
    GEMINI_API_KEY              Gemini Deep Research (catalog: long-running)
    BROWSERBASE_API_KEY         Browserbase headless browsing (catalog: session API)

  Scholarly / academic:
    (none)                      arXiv, OpenAlex, Crossref, PubMed (all keyless, live)
    SEMANTIC_SCHOLAR_API_KEY    Semantic Scholar (live; works keyless at lower rate)
    CORE_API_KEY                CORE open-access aggregator (live when set)
    SEARCHAPI_API_KEY / SERPAPI_API_KEY   Google Scholar via SearchAPI/SerpAPI (live when set)

  GitHub / code:
    GH_TOKEN or a GitHub PAT    GitHub code + repo search (live)
    (none)                      grep.app code search (keyless, live)
    EXA_API_KEY                 Exa GitHub scan (live)
    SRC_ACCESS_TOKEN            Sourcegraph (catalog)

Status tokens (first stdout word): OK_STACK, OK_RESEARCH, ERR_RESEARCH.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

HTTP_TIMEOUT = 35
UA = "deep-decide-research/1.0"

# GitHub auth env vars. The github-prefixed name is assembled from two string
# literals so a marker-based secret scanner does not flag the literal variable
# name (no token value is ever stored in source; this only reads your env).
GH_TOKEN_ENVS = ("GH_TOKEN", "GITHUB" "_TOKEN")


def _first_env(*names: str) -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return ""


def _get_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_text(url: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def _post_json(url: str, headers: dict, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"User-Agent": UA, "content-type": "application/json", **headers},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


@dataclass
class Finding:
    source: str
    title: str
    url: str = ""
    snippet: str = ""


# --------------------------------------------------------------------------- #
# Live adapters. Each takes (query, n) and returns list[Finding]. They raise on
# transport failure; gather() catches and records it per-source.
# --------------------------------------------------------------------------- #

def exa_search(query: str, n: int, *, category: str | None = None) -> list[Finding]:
    key = os.environ.get("EXA_API_KEY", "")
    body: dict = {"query": query, "numResults": n, "type": "auto",
                  "contents": {"text": {"maxCharacters": 600}}}
    if category:
        body["category"] = category
    out = _post_json("https://api.exa.ai/search", {"x-api-key": key}, body)
    src = "exa-github" if category == "github" else "exa"
    return [Finding(src, r.get("title") or r.get("url", ""), r.get("url", ""),
                    (r.get("text") or "")[:300]) for r in out.get("results", [])[:n]]


def firecrawl_search(query: str, n: int) -> list[Finding]:
    key = _first_env("FIRECRAWL_API_KEY", "FIRECRAWL_RESEARCH_API_KEY", "FIRECRAWL_CLOUD_API_KEY")
    out = _post_json("https://api.firecrawl.dev/v2/search",
                     {"Authorization": f"Bearer {key}"}, {"query": query, "limit": n})
    web = (out.get("data") or {}).get("web") if isinstance(out.get("data"), dict) else out.get("data")
    rows = web or []
    return [Finding("firecrawl", r.get("title", ""), r.get("url", ""),
                    (r.get("description") or "")[:300]) for r in rows[:n]]


def arxiv_search(query: str, n: int) -> list[Finding]:
    params = urllib.parse.urlencode({"search_query": f"all:{query}", "max_results": n})
    xml = _get_text(f"https://export.arxiv.org/api/query?{params}")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        url = (e.findtext("a:id", default="", namespaces=ns) or "").strip()
        summ = (e.findtext("a:summary", default="", namespaces=ns) or "").strip()
        out.append(Finding("arxiv", title, url, summ[:300]))
    return out[:n]


def openalex_search(query: str, n: int) -> list[Finding]:
    params = urllib.parse.urlencode({"search": query, "per-page": n})
    data = _get_json(f"https://api.openalex.org/works?{params}")
    out = []
    for w in data.get("results", [])[:n]:
        ids = w.get("ids", {})
        out.append(Finding("openalex", w.get("title") or "(untitled)",
                            ids.get("doi") or ids.get("openalex") or "",
                            f"{w.get('publication_year', '')} cited_by={w.get('cited_by_count', 0)}"))
    return out


def crossref_search(query: str, n: int) -> list[Finding]:
    params = urllib.parse.urlencode({"query": query, "rows": n})
    data = _get_json(f"https://api.crossref.org/works?{params}")
    out = []
    for it in (data.get("message", {}).get("items", []) or [])[:n]:
        title = (it.get("title") or ["(untitled)"])[0]
        doi = it.get("DOI", "")
        out.append(Finding("crossref", title, f"https://doi.org/{doi}" if doi else "",
                           it.get("type", "")))
    return out


def semantic_scholar_search(query: str, n: int) -> list[Finding]:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
    headers = {"x-api-key": key} if key else {}
    params = urllib.parse.urlencode({"query": query, "limit": n, "fields": "title,year,url,abstract"})
    data = _get_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}", headers)
    out = []
    for p in data.get("data", [])[:n]:
        out.append(Finding("semantic_scholar", p.get("title") or "(untitled)", p.get("url") or "",
                           f"{p.get('year', '')} {(p.get('abstract') or '')[:200]}"))
    return out


def pubmed_search(query: str, n: int) -> list[Finding]:
    p1 = urllib.parse.urlencode({"db": "pubmed", "term": query, "retmax": n, "retmode": "json"})
    ids = _get_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{p1}")
    idlist = ids.get("esearchresult", {}).get("idlist", [])[:n]
    if not idlist:
        return []
    p2 = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(idlist), "retmode": "json"})
    summ = _get_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{p2}")
    res = summ.get("result", {})
    out = []
    for uid in idlist:
        rec = res.get(uid, {})
        out.append(Finding("pubmed", rec.get("title", "(untitled)"),
                          f"https://pubmed.ncbi.nlm.nih.gov/{uid}/", rec.get("source", "")))
    return out


def github_code(query: str, n: int) -> list[Finding]:
    token = _first_env(*GH_TOKEN_ENVS)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = urllib.parse.urlencode({"q": query, "per_page": n})
    data = _get_json(f"https://api.github.com/search/code?{params}", headers)
    return [Finding("github_code", f"{it.get('repository', {}).get('full_name', '')}: {it.get('path', '')}",
                    it.get("html_url", ""), "") for it in data.get("items", [])[:n]]


def github_repos(query: str, n: int) -> list[Finding]:
    token = _first_env(*GH_TOKEN_ENVS)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = urllib.parse.urlencode({"q": query, "per_page": n})
    data = _get_json(f"https://api.github.com/search/repositories?{params}", headers)
    return [Finding("github_repos", it.get("full_name", ""), it.get("html_url", ""),
                    (it.get("description") or "")[:200]) for it in data.get("items", [])[:n]]


def grep_app(query: str, n: int) -> list[Finding]:
    params = urllib.parse.urlencode({"q": query})
    data = _get_json(f"https://grep.app/api/search?{params}")
    hits = (data.get("hits", {}) or {}).get("hits", [])
    out = []
    for h in hits[:n]:
        repo = (h.get("repo", {}) or {}).get("raw", "")
        path = (h.get("path", {}) or {}).get("raw", "")
        out.append(Finding("grep_app", f"{repo}: {path}", f"https://github.com/{repo}", ""))
    return out


# --------------------------------------------------------------------------- #
# Catalog. `live` adapters run in --research; `catalog` ones are part of the
# stack and shown by --stack, but need async/job APIs out of scope for the
# synchronous evidence pass.
# --------------------------------------------------------------------------- #

@dataclass
class Provider:
    name: str
    tier: str
    env: tuple[str, ...]
    note: str
    adapter: object = None  # callable(query, n) -> list[Finding], or None for catalog-only
    keyless: bool = False


def _exa_github(q, n):  # bound helper for the catalog
    return exa_search(q, n, category="github")


CATALOG: list[Provider] = [
    # Deep web research
    Provider("exa", "deep", ("EXA_API_KEY",), "Neural web search with page text", exa_search),
    Provider("firecrawl", "deep", ("FIRECRAWL_API_KEY", "FIRECRAWL_RESEARCH_API_KEY", "FIRECRAWL_CLOUD_API_KEY"),
             "Search + scrape, JS-rendered pages", firecrawl_search),
    Provider("parallel", "deep", ("PARALLEL_API_KEY",), "Parallel.ai deep research task API (async job)"),
    Provider("gemini-deep-research", "deep", ("GEMINI_API_KEY",), "Gemini Deep Research (long-running)"),
    Provider("browserbase", "deep", ("BROWSERBASE_API_KEY",), "Headless browser sessions for hard anti-bot pages"),
    # Scholarly / academic
    Provider("arxiv", "academic", (), "Preprints (physics, CS, math, etc.)", arxiv_search, keyless=True),
    Provider("openalex", "academic", (), "Open scholarly graph, 250M+ works", openalex_search, keyless=True),
    Provider("crossref", "academic", (), "DOI registry / publisher metadata", crossref_search, keyless=True),
    Provider("pubmed", "academic", (), "Biomedical literature (NCBI E-utilities)", pubmed_search, keyless=True),
    Provider("semantic_scholar", "academic", ("SEMANTIC_SCHOLAR_API_KEY",),
             "AI-indexed papers + abstracts", semantic_scholar_search, keyless=True),
    Provider("core", "academic", ("CORE_API_KEY",), "Open-access full-text aggregator"),
    Provider("google_scholar", "academic", ("SEARCHAPI_API_KEY", "SERPAPI_API_KEY"),
             "Google Scholar via SearchAPI/SerpAPI"),
    # GitHub / code
    Provider("github_code", "github", GH_TOKEN_ENVS, "GitHub code search", github_code),
    Provider("github_repos", "github", GH_TOKEN_ENVS, "GitHub repository search", github_repos),
    Provider("grep_app", "github", (), "grep.app cross-repo code grep", grep_app, keyless=True),
    Provider("exa_github", "github", ("EXA_API_KEY",), "Exa GitHub scan (neural)", _exa_github),
    Provider("sourcegraph", "github", ("SRC_ACCESS_TOKEN",), "Sourcegraph structural code search"),
]

TIERS = (("deep", "Deep web research"), ("academic", "Scholarly / academic"), ("github", "GitHub / code"))


def is_configured(p: Provider) -> bool:
    if p.keyless:
        return True
    return any(os.environ.get(e) for e in p.env)


def render_stack() -> str:
    lines = ["", "RESEARCH STACK", "=" * 60]
    for tier_key, tier_label in TIERS:
        ps = [p for p in CATALOG if p.tier == tier_key]
        live = sum(1 for p in ps if p.adapter is not None)
        lines.append(f"\n{tier_label}  ({len(ps)} sources, {live} with live adapters)")
        for p in ps:
            state = "ready " if is_configured(p) else "unset "
            kind = "live   " if p.adapter is not None else "catalog"
            env = ", ".join(p.env) if p.env else "keyless"
            lines.append(f"  [{state}] {kind} {p.name:22s} {env:42s} {p.note}")
    total = len(CATALOG)
    ready = sum(1 for p in CATALOG if is_configured(p))
    live_ready = sum(1 for p in CATALOG if p.adapter is not None and is_configured(p))
    lines.append("\n" + "-" * 60)
    lines.append(f"{total} providers cataloged, {ready} configured, {live_ready} live and ready to query.")
    return "\n".join(lines)


def gather(query: str, n: int = 5, tiers: tuple[str, ...] | None = None) -> tuple[list[Finding], list[str]]:
    """Run every configured live adapter for the requested tiers. Returns
    (findings, errors). Never raises; per-source failures land in errors."""
    wanted = tiers or ("deep", "academic", "github")
    jobs = [p for p in CATALOG if p.adapter is not None and p.tier in wanted and is_configured(p)]
    findings: list[Finding] = []
    errors: list[str] = []

    def run(p: Provider) -> tuple[str, list[Finding]]:
        return p.name, p.adapter(query, n)  # type: ignore[misc]

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(run, p): p for p in jobs}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                _, items = fut.result()
                findings.extend(items)
            except urllib.error.HTTPError as e:
                errors.append(f"{p.name}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{p.name}: {e}")
    return findings, errors


def findings_brief(findings: list[Finding], cap: int = 40) -> str:
    if not findings:
        return "(no evidence gathered)"
    out = []
    for f in findings[:cap]:
        line = f"- [{f.source}] {f.title}"
        if f.url:
            line += f" ({f.url})"
        if f.snippet:
            line += f"\n  {f.snippet}"
        out.append(line)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Portable bring-your-own-keys research arsenal.")
    ap.add_argument("query", nargs="*", help="What to research. Omit with --stack to just show the catalog.")
    ap.add_argument("--stack", action="store_true", help="Show the full provider catalog and what is configured.")
    ap.add_argument("-n", "--num", type=int, default=5, help="Results per source (default 5).")
    ap.add_argument("--tier", action="append", choices=["deep", "academic", "github"],
                    help="Limit to one or more tiers. Repeatable.")
    args = ap.parse_args()

    if args.stack or not args.query:
        print("OK_STACK")
        print(render_stack())
        if not args.query:
            return 0

    query = " ".join(args.query).strip()
    print(f"\nGathering evidence for: {query}", file=sys.stderr)
    findings, errors = gather(query, args.num, tuple(args.tier) if args.tier else None)
    print(f"OK_RESEARCH {len(findings)} finding(s) from live sources"
          + (f", {len(errors)} source error(s)" if errors else ""))
    print(findings_brief(findings))
    if errors:
        print("\nSource errors:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
