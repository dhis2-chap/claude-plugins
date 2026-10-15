"""Mechanical structure and link checks over the cloned docs. Writes findings_structure.json.

Usage: uv run --with pyyaml python structure.py

- nav-missing:     a nav entry points to a page that does not exist
- nav-orphan:      pages under the docs root that no nav entry reaches (one finding per source)
- link-broken:     a relative link to a file that does not exist
- link-dead-repo:  a link to a dhis2 or dhis2-chap repo that does not exist
- link-moved-repo: a link to a repo that was renamed or moved (works through a redirect)
- link-github-path: a github.com/.../blob|tree/<main|master>/path link to a path missing
                   on the default branch of a repo that is cloned here
External sites are not fetched.
"""
import fnmatch
import glob
import json
import os
import re
import subprocess
from urllib.parse import unquote

import yaml

cfg = json.load(open("config.json"))
org_repos = {o: {r.lower() for r in v} for o, v in json.load(open("org_repos.json")).items()}
cloned = {s["repo"].lower(): s["name"] for s in cfg["sources"]}
SKIP_DIRS = {"node_modules", ".git", ".github", "site", "_build", "target", "renv", "man"}
SKIP_FILES = {"CLAUDE.md", "AGENTS.md"}
DOC_EXT = (".md", ".mdx", ".ipynb")
findings = []
mounts = {}  # source name -> path prefixes that `!import` fills in on the built site


class AnyTagLoader(yaml.SafeLoader):
    pass


AnyTagLoader.add_multi_constructor("", lambda loader, suffix, node: None)


def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=AnyTagLoader) or {}


def walk(root, exts):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith((".", "_"))]
        out += [os.path.join(d, f) for f in files if f.endswith(exts) and f not in SKIP_FILES]
    return out


def doc_files(src, base):
    out = []
    for p in src["docs"]:
        full = os.path.normpath(os.path.join(base, p))
        if os.path.isfile(full):
            out.append(full)
        elif os.path.isdir(full):
            out += walk(full, (".md", ".mdx"))
    return sorted(set(out))


def rel(src, path):
    return f"{src['name']}/{os.path.relpath(path, os.path.join('repos', src['name']))}"


def add(src, rule, severity, title, where, evidence="", suggestion=""):
    findings.append({"check": "structure", "rule": rule, "source": src["name"], "severity": severity,
                     "title": title, "where": where if isinstance(where, list) else [where],
                     "evidence": [evidence] if evidence else [], "suggestion": suggestion})


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def nav_pages(value, out, mounts, title=""):
    """Collect nav page paths; titles of `!import` entries go to mounts (their slug is
    where the imported docs appear on the built site)."""
    if isinstance(value, str):
        if value.startswith("!import"):
            mounts.add(slug(title))
        elif not value.startswith(("http://", "https://")):
            out.append(value.split("#")[0])
    elif isinstance(value, list):
        for v in value:
            nav_pages(v, out, mounts)
    elif isinstance(value, dict):
        for k, v in value.items():
            nav_pages(v, out, mounts, k)


def myst_files(value, out):
    if isinstance(value, dict):
        if isinstance(value.get("file"), str):
            out.append(value["file"])
        for v in value.values():
            myst_files(v, out)
    elif isinstance(value, list):
        for v in value:
            myst_files(v, out)


def nav_check(src, base):
    kind, _, arg = src["nav"].partition(":")
    exts, ignore = (".md", ".mdx"), []
    if kind == "mkdocs":
        conf_path = os.path.join(base, arg)
        conf = load_yaml(conf_path)
        if "nav" not in conf:
            return
        root = os.path.join(os.path.dirname(conf_path), conf.get("docs_dir", "docs"))
        pages = []
        nav_pages(conf["nav"], pages, mounts.setdefault(src["name"], set()))
        ignore = [ln.strip().lstrip("/") for ln in str(conf.get("not_in_nav") or "").splitlines() if ln.strip()]
        where_nav = rel(src, conf_path)
    elif kind == "myst":
        conf_path = os.path.join(base, arg)
        root = os.path.dirname(conf_path)
        pages = []
        for p in [conf_path] + [os.path.join(root, e) for e in load_yaml(conf_path).get("extends", []) or []]:
            if os.path.isfile(p):
                myst_files(load_yaml(p).get("project", {}).get("toc", []), pages)
        exts, where_nav = DOC_EXT, rel(src, conf_path)
    elif kind == "imports":
        ts_files = glob.glob(os.path.join(base, arg))
        root = os.path.dirname(os.path.join(base, arg))
        pages = []
        for t in ts_files:
            for m in re.finditer(r"""['"](\.{1,2}/[^'"]+\.mdx?)['"]""", open(t).read()):
                pages.append(os.path.relpath(os.path.normpath(os.path.join(os.path.dirname(t), m.group(1))), root))
        where_nav = ", ".join(rel(src, t) for t in ts_files)
    else:
        return
    norm = {os.path.normpath(p) for p in pages}
    for p in sorted(norm):
        if not os.path.exists(os.path.join(root, p)):
            add(src, "nav-missing", "High", f"Navigation points to a missing page: {p}", where_nav,
                suggestion="Fix the path or remove the entry.")
    orphans = []
    for f in walk(root, exts):
        r = os.path.relpath(f, root)
        if os.path.basename(r) == "README.md" or os.path.basename(r).startswith("_") or any(fnmatch.fnmatch(r, g) for g in ignore):
            continue
        if r not in norm:
            orphans.append(rel(src, f))
    if orphans:
        add(src, "nav-orphan", "Low", f"{len(orphans)} page(s) are not in the navigation", sorted(orphans),
            evidence=f"Navigation defined in {where_nav}",
            suggestion="Add them to the nav, move them out of the docs folder, or delete them if obsolete.")


FENCE = re.compile(r"^\s*(```|~~~)")
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)|(?:href|src)=[\"']([^\"']+)[\"']")
GH = re.compile(r"https?://github\.com/([^/#?\s]+)/([^/#?\s]+)(?:/(?:blob|tree)/([^/#?\s]+)/([^#?\s]*))?")


def exists_rel(path):
    cands = [path, path + ".md", os.path.join(path, "index.md"), os.path.join(path, "README.md"), path.rstrip("/") + ".md"]
    return any(os.path.exists(c) for c in cands)


def resolve_repo(org, repo):
    """Current full name of org/repo via the API (follows renames), or None if it is gone."""
    r = subprocess.run(["gh", "api", f"repos/{org}/{repo}", "--jq", ".full_name"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def link_check(src, files):
    dead = {}
    skip_roots = mounts.get(src["name"], set())
    # MyST serves every page at a flat URL named after the file, so `[x](data-engineer)` works
    stems = {os.path.splitext(os.path.basename(f))[0] for f in files} if (src["nav"] or "").startswith("myst:") else set()
    for f in files:
        in_fence = False
        for n, line in enumerate(open(f, errors="replace"), 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = re.sub(r"`[^`]*`", "", line)
            for m in LINK.finditer(line):
                target = (m.group(1) or m.group(2)).strip()
                where = f"{rel(src, f)}:{n}"
                if target.startswith(("#", "mailto:", "tel:", "/", "data:")) or "{{" in target or "{%" in target:
                    continue
                if target.startswith(("http://", "https://")):
                    g = GH.match(target)
                    if not g or g.group(1).lower() not in org_repos:
                        continue
                    org, repo = g.group(1).lower(), re.sub(r"\.git$", "", g.group(2)).lower()
                    if org_repos[org] and repo not in org_repos[org]:
                        dead.setdefault(f"{org}/{repo}", []).append(where)
                    elif g.group(3) in ("main", "master") and g.group(4) and f"{org}/{repo}" in cloned:
                        p = os.path.join("repos", cloned[f"{org}/{repo}"], unquote(g.group(4)).rstrip("/"))
                        if not os.path.exists(p):
                            add(src, "link-github-path", "Medium", f"Link to a path that is not on {g.group(3)}: {target}",
                                where, suggestion="Point the link at the current location.")
                    continue
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                path = unquote(target.split("#")[0].split("?")[0])
                if path.split("/")[0] in skip_roots or ("." not in path and path.strip("/").split("/")[-1] in stems):
                    continue
                if path and not exists_rel(os.path.normpath(os.path.join(os.path.dirname(f), path))):
                    add(src, "link-broken", "Medium", f"Broken relative link: {target}", where,
                        suggestion="Fix the path or remove the link.")
    for repo, wheres in sorted(dead.items()):
        now = resolve_repo(*repo.split("/"))
        if now:
            add(src, "link-moved-repo", "Low", f"Links to github.com/{repo}, which has moved to {now}", wheres,
                suggestion=f"Update the links to github.com/{now}; they work through a redirect today.")
        else:
            add(src, "link-dead-repo", "Medium", f"Links to a repo that does not exist: github.com/{repo}", wheres,
                suggestion="Point the links at the repo that replaced it, or remove them.")


for src in cfg["sources"]:
    base = os.path.join("repos", src["name"])
    if not os.path.isdir(base):
        continue
    if src["nav"]:
        nav_check(src, base)
    link_check(src, doc_files(src, base))

json.dump(findings, open("findings_structure.json", "w"), indent=1)
counts = {}
for f in findings:
    counts[f["rule"]] = counts.get(f["rule"], 0) + 1
print(f"{len(findings)} structure findings: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
