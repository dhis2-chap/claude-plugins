"""List repos in the orgs that sources.md neither reviews nor explicitly leaves out, so the
skill's list of sources can be kept up to date. Run after fetch.py.

Usage: python coverage.py SOURCES_MD
Candidates: every non-archived, non-fork repo in dhis2-chap, and the repos in dhis2 whose
name, description or topics match CLIMATE (dhis2 holds the whole DHIS2 product, most of it
out of scope). Repos in the Sources or Not reviewed tables are skipped. Writes coverage.json,
which report.py turns into a section, and prints a short summary.
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

CLIMATE = re.compile(r"climate|chap|weather|earth|dhis2eo", re.I)
NEW_DAYS = 90
DOC_MARKERS = {"docs", "doc", "vignettes", "mkdocs.yml", "myst.yml", "_quarto.yml", "_pkgdown.yml"}


def table(text, heading):
    """Rows of the first markdown table after `## heading`, as dicts."""
    lines = []
    for ln in text.split(f"## {heading}", 1)[1].splitlines():
        if ln.startswith("|"):
            lines.append(ln)
        elif lines:
            break
    split = lambda ln: [c.strip() for c in ln.strip().strip("|").split("|")]  # noqa: E731
    header = split(lines[0])
    return [dict(zip(header, split(ln))) for ln in lines[2:]]


def top_level(full):
    """Names at the root of the default branch, or [] for an empty or unreadable repo."""
    r = subprocess.run(["gh", "api", f"repos/{full}/contents", "--jq", ".[].name"],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.split() if r.returncode == 0 else []


text = open(sys.argv[1]).read()
known = {r["repo"].lower() for r in table(text, "Sources") + table(text, "Not reviewed")}
meta = json.load(open("org_repos_meta.json"))
new_since = (date.today() - timedelta(days=NEW_DAYS)).isoformat()

candidates = []
for org, repos in meta.items():
    for r in repos:
        full = f"{org}/{r['name']}"
        if r["isArchived"] or r["isFork"] or full.lower() in known:
            continue
        topics = " ".join(t["name"] for t in r.get("repositoryTopics") or [])
        if org != "dhis2-chap" and not CLIMATE.search(f"{r['name']} {r['description'] or ''} {topics}"):
            continue
        candidates.append({"repo": full, "description": r["description"] or "",
                           "visibility": r["visibility"].lower(), "created": r["createdAt"][:10],
                           "pushed": r["pushedAt"][:10], "new": r["createdAt"][:10] >= new_since})

with ThreadPoolExecutor(max_workers=12) as ex:
    for c, names in zip(candidates, ex.map(top_level, [c["repo"] for c in candidates])):
        c["docs"] = sorted(n for n in names if n.lower() in DOC_MARKERS)
        c["readme"] = any(n.lower().startswith("readme") for n in names)

candidates.sort(key=lambda c: c["pushed"], reverse=True)  # then new first, then those with docs
candidates.sort(key=lambda c: (not c["new"], not c["docs"]))
json.dump({"new_days": NEW_DAYS, "candidates": candidates}, open("coverage.json", "w"), indent=2)

if not any(meta.values()):
    print("WARNING: no org repo lists; run fetch.py first, with gh authenticated")
new = [c for c in candidates if c["new"]]
print(f"{len(candidates)} repos not in sources.md ({len(new)} created in the last {NEW_DAYS} days, "
      f"{sum(bool(c['docs']) for c in candidates)} with a docs folder or site config)")
for c in new:
    print(f"NEW {c['repo']} ({c['created']}{', docs: ' + ','.join(c['docs']) if c['docs'] else ''}) {c['description']}")
