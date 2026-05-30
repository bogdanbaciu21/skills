#!/usr/bin/env python3
"""reskin.py — apply a repo's design system across its pages (pagecraft bundle).

Detects the design system a repo has (an installed *-design / *-brand skill, a
tokens stylesheet, or a reskin.json manifest), syncs its tokens + assets into the
served dir, and reframes the site's HTML with the design system's nav / hero /
footer — stripping each page's old chrome and injecting the brand frame,
idempotently (already-framed pages are skipped).

HYBRID model: if the repo declares a bespoke applier (`apply_command` in
reskin.json) or one is detected (e.g. apply-brand-frame-*.py), reskin RUNS that
per page. Otherwise it uses the built-in generic injector driven by the design
system's frame/ templates. Either way it's one command: `reskin apply`.

In reskin.json, `tokens_css`, `assets`, and `frame` are all relative to
`design_system.source` (the dir holding the brand). See SKILL.md.

Commands:
  reskin detect [--repo .]                          what design system + applier exists here?
  reskin init   [--repo .]                          scaffold a reskin.json from what's detected
  reskin apply  [--repo .] [--page P ...] [--dry-run]
  reskin verify [--repo .]                          pagecraft keystone + brand-asset checks
"""
import argparse, glob, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Proven strip patterns from apply-brand-frame-v3.py — the "old chrome" removed
# before injecting the new frame. Overridable per-repo via reskin.json.
DEFAULT_STRIP = [
    r'\s*<nav class="[a-z-]+">.*?</nav>\s*',
    r'\s*<div class="[a-z]+-nav">.*?</div>\s*',
    r'\s*<div class="page-header">.*?</div>\s*</div>\s*',
    r'\s*<div class="page-header">.*?</div>\s*',
    r'\s*<header class="[a-z]+-(?:head|hero)">.*?</header>\s*',
    r'\s*<div class="[a-z]+-(?:head|hero|eyebrow|byline)"[^>]*>.*?</div>\s*',
    r'\s*<h1[^>]*>.*?</h1>\s*',
    r'\s*<p class="(?:lede|sub)"[^>]*>.*?</p>\s*',
    r'\s*<div class="[a-z]+-meta"[^>]*>.*?</div>\s*',
]
DEFAULT_MARKER = 'class="brand-nav"'   # presence => already framed (idempotency)


def _src_base(repo, ds):
    """Absolute dir that design-system relative paths resolve against."""
    s = ds.get("source")
    if not s or s == ".":
        return repo
    return s if os.path.isabs(s) else os.path.join(repo, s)


# ----------------------------------------------------------------- detection

def detect(repo):
    f = {"manifest": None, "source": None, "design_skill": None, "tokens_css": None,
         "assets_dir": None, "frame_dir": None, "bespoke_applier": None, "design_md": None}

    if os.path.isfile(os.path.join(repo, "reskin.json")):
        f["manifest"] = "reskin.json"

    # Installed design/brand skill (LJB ljbcpa-design, SLG slg-brand, …).
    # tokens/assets/frame are recorded RELATIVE TO the skill dir (= source).
    for pat in (".claude/skills/*-design", ".claude/skills/*-brand", ".claude/skills/*design*"):
        for d in sorted(glob.glob(os.path.join(repo, pat))):
            if not os.path.isdir(d):
                continue
            f["design_skill"] = f["source"] = os.path.relpath(d, repo)
            for tok in ("colors_and_type.css", "tokens.css"):
                if os.path.isfile(os.path.join(d, tok)):
                    f["tokens_css"] = tok
            if os.path.isdir(os.path.join(d, "assets")):
                f["assets_dir"] = "assets"
            if os.path.isdir(os.path.join(d, "frame")):
                f["frame_dir"] = "frame"
            break
        if f["design_skill"]:
            break

    # No skill: a tokens stylesheet in the repo (source = repo root, repo-relative path).
    if not f["tokens_css"]:
        for cand in ("assets/css/flourishes.css", "colors_and_type.css",
                     "assets/colors_and_type.css", "styles.css", "assets/css/app.css"):
            if os.path.isfile(os.path.join(repo, cand)):
                f["tokens_css"], f["source"] = cand, "."
                break

    if os.path.isfile(os.path.join(repo, "design.md")):
        f["design_md"] = "design.md"

    # Bespoke applier already in the repo (hybrid run-path). Prefer a full-frame
    # applier over a nav-only one.
    hits = [h for h in glob.glob(os.path.join(repo, "**", "apply-brand*.py"), recursive=True)
            if "node_modules" not in h and "/.git/" not in h]
    hits.sort(key=lambda h: (0 if "frame" in os.path.basename(h) else 1, h))
    if hits:
        f["bespoke_applier"] = os.path.relpath(hits[0], repo)
    return f


def has_design_system(f):
    return any(f[k] for k in ("manifest", "design_skill", "tokens_css", "design_md"))


# ----------------------------------------------------------------- manifest

def load_manifest(repo):
    mf = os.path.join(repo, "reskin.json")
    return json.load(open(mf)) if os.path.isfile(mf) else None


def scaffold(f):
    ds = {}
    if f["source"]:      ds["source"] = f["source"]
    if f["tokens_css"]:  ds["tokens_css"] = f["tokens_css"]
    if f["assets_dir"]:  ds["assets"] = f["assets_dir"]
    if f["frame_dir"]:   ds["frame"] = f["frame_dir"]
    m = {
        "design_system": ds or {"source": "TBU", "tokens_css": "TBU", "assets": "TBU"},
        "served_root": "TBU — dir whose HTML pages get reskinned (e.g. brian-portal or .)",
        "assets_target": "TBU — where assets land under served_root (e.g. assets/<brand>)",
        "framed_marker": DEFAULT_MARKER,
        "pages": [{"path": "TBU/page.html", "eyebrow": "section", "headline_pre": "Title",
                   "headline_em": "", "subhead": "One-line deck.", "page_label": "Page"}],
    }
    if f["bespoke_applier"]:
        m["apply_command"] = ('python3 ' + f["bespoke_applier"] +
                              ' {page} "{eyebrow}|{headline_pre}|{headline_em}|{subhead}|{page_label}"')
    return m


# ----------------------------------------------------------------- reskin core

def _render(tpl, page):
    for k in ("eyebrow", "headline_pre", "headline_em", "subhead", "page_label", "page_file", "page_path"):
        tpl = tpl.replace("{{%s}}" % k, str(page.get(k, "")))
    return tpl


def generic_frame(repo, m, page, dry):
    """Built-in injector — mirrors apply-brand-frame-v3.py, but nav/hero/footer
    come from the design system's frame/ templates instead of being hardcoded."""
    ds = m["design_system"]
    frame_dir = ds.get("frame")
    if not frame_dir:
        return ("ERR", "no design_system.frame templates and no apply_command — nothing to inject")
    fdir = frame_dir if os.path.isabs(frame_dir) else os.path.join(_src_base(repo, ds), frame_dir)
    parts = {n: (open(os.path.join(fdir, n + ".html")).read() if os.path.isfile(os.path.join(fdir, n + ".html")) else "")
             for n in ("nav", "hero", "footer")}
    if not parts["nav"] and not parts["hero"]:
        return ("ERR", f"{frame_dir} has no nav.html / hero.html")

    path = os.path.join(repo, page["path"])
    if not os.path.isfile(path):
        return ("ERR", "page not found")
    s = open(path).read()
    if m.get("framed_marker", DEFAULT_MARKER) in s:
        return ("SKIP", "already framed")
    bm = re.search(r"(<body[^>]*>)", s)
    if not bm:
        return ("ERR", "no <body>")
    page = {**page, "page_file": os.path.basename(path), "page_path": page["path"]}
    cut = bm.end()
    head_zone, rest = s[cut:cut + 6000], s[cut + 6000:]
    for pat in m.get("strip_patterns", DEFAULT_STRIP):
        head_zone = re.sub(pat, "\n  ", head_zone, count=1, flags=re.DOTALL)
    body = "\n\n" + _render(parts["nav"], page) + "\n\n" + _render(parts["hero"], page) + "\n" + head_zone + rest
    if parts["footer"]:
        body = re.sub(r"</body>", "\n" + _render(parts["footer"], page) + "\n\n</body>", body, count=1)
    if not dry:
        open(path, "w").write(s[:cut] + body)
    return ("FRAMED", "")


def bespoke_frame(repo, m, page, dry):
    rendered = m["apply_command"].format(
        page=os.path.join(repo, page["path"]),
        eyebrow=page.get("eyebrow", ""), headline_pre=page.get("headline_pre", ""),
        headline_em=page.get("headline_em", ""), subhead=page.get("subhead", ""),
        page_label=page.get("page_label", ""))
    if dry:
        return ("WOULD-RUN", rendered)
    r = subprocess.run(rendered, shell=True, cwd=repo, capture_output=True, text=True)
    return (("RAN" if r.returncode == 0 else "FAIL"), (r.stdout + r.stderr).strip()[:200])


def sync_assets(repo, m, dry):
    ds = m["design_system"]
    base = _src_base(repo, ds)
    target = os.path.join(repo, m.get("served_root", "."), m.get("assets_target", "assets"))
    moved = []
    if ds.get("assets"):
        srca = os.path.join(base, ds["assets"])
        if os.path.isdir(srca):
            moved.append(f"{ds['assets']}/ -> {os.path.relpath(target, repo)}/")
            if not dry:
                os.makedirs(target, exist_ok=True)
                shutil.copytree(srca, target, dirs_exist_ok=True)
    if ds.get("tokens_css"):
        srct = os.path.join(base, ds["tokens_css"])
        if os.path.isfile(srct):
            dstt = os.path.join(target, os.path.basename(ds["tokens_css"]))
            moved.append(f"{os.path.basename(ds['tokens_css'])} -> {os.path.relpath(dstt, repo)}")
            if not dry:
                os.makedirs(target, exist_ok=True)
                shutil.copy2(srct, dstt)
    return moved


# ----------------------------------------------------------------- commands

def cmd_detect(repo, _a):
    f = detect(repo)
    print(f"reskin: scanning {os.path.abspath(repo)}\n")
    for label, val in [("reskin.json manifest", f["manifest"]), ("design system dir (source)", f["source"]),
                       ("design/brand skill", f["design_skill"]), ("tokens stylesheet", f["tokens_css"]),
                       ("brand assets", f["assets_dir"]), ("frame templates", f["frame_dir"]),
                       ("bespoke applier", f["bespoke_applier"]), ("design.md", f["design_md"])]:
        print(f"  {'✓' if val else '·'} {label:26} {val or '—'}")
    print()
    if not has_design_system(f):
        print("  No design system detected. Install a *-design/*-brand skill or add a tokens stylesheet.")
        return 1
    frame_src = "bespoke applier" if f["bespoke_applier"] else ("frame templates" if f["frame_dir"] else "NONE — add frame/ templates or apply_command")
    print(f"  Frame source: {frame_src}")
    print("  Next: " + ("`reskin apply --dry-run`" if f["manifest"] else "`reskin init` to scaffold reskin.json"))
    return 0


def cmd_init(repo, _a):
    if os.path.isfile(os.path.join(repo, "reskin.json")):
        print("reskin.json already exists — not overwriting."); return 1
    f = detect(repo)
    if not has_design_system(f):
        print("No design system detected; nothing to scaffold."); return 1
    open(os.path.join(repo, "reskin.json"), "w").write(json.dumps(scaffold(f), indent=2) + "\n")
    print("Wrote reskin.json (starter). Fill in served_root, assets_target, and pages[], then `reskin apply --dry-run`.")
    return 0


def cmd_apply(repo, a):
    m = load_manifest(repo)
    if not m:
        print("No reskin.json — run `reskin detect` then `reskin init`."); return 1
    bespoke = bool(m.get("apply_command"))
    pages = m.get("pages", [])
    if a.page:
        named = [p for p in pages if p["path"] in a.page]
        pages = named or [{"path": pp, "page_label": os.path.basename(pp)} for pp in a.page]
    if not pages:
        print("No pages to reskin (manifest pages[] empty and no --page given)."); return 1

    moved = sync_assets(repo, m, a.dry_run)
    print(f"{'[dry-run] ' if a.dry_run else ''}assets: " + ("; ".join(moved) if moved else "(none)"))
    print(f"frame via: {'bespoke apply_command' if bespoke else 'generic frame templates'}\n")
    counts = {}
    for page in pages:
        status, note = (bespoke_frame if bespoke else generic_frame)(repo, m, page, a.dry_run)
        counts[status] = counts.get(status, 0) + 1
        print(f"  {status:10} {page['path']}" + (f"   ({note})" if note else ""))
    print("\n" + ("[dry-run] " if a.dry_run else "") + "reskin: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if (counts.get("ERR") or counts.get("FAIL")) else 0


def cmd_verify(repo, _a):
    m = load_manifest(repo) or {}
    served = os.path.join(repo, m.get("served_root", "."))
    keystone = os.path.normpath(os.path.join(HERE, "..", "verify-text-wrap", "check-keystone.py"))
    if os.path.isfile(keystone):
        print("=== wrap-safe keystone guard ===")
        subprocess.run([sys.executable, keystone, "--portal", served])
    else:
        print(f"(keystone guard not found at {keystone})")
    tgt = os.path.join(served, m.get("assets_target", "assets"))
    print(f"\nbrand assets present at {os.path.relpath(tgt, repo)}: {'YES' if os.path.isdir(tgt) else 'NO'}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Apply a repo's design system across its pages.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("detect", "init", "apply", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--repo", default=".")
        if name == "apply":
            s.add_argument("--page", action="append", help="reskin only this page (repeatable)")
            s.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    return {"detect": cmd_detect, "init": cmd_init, "apply": cmd_apply, "verify": cmd_verify}[a.cmd](repo, a)


if __name__ == "__main__":
    sys.exit(main())
