"""Pick sources from sources.md and write config.json.

Usage: python pick.py SOURCES_MD [--teams modeling,climate] [--groups core,ocs]
                        [--repos chap-core,climate-app] [--checks code,overlap,journey,structure]
Teams default to both; shared sources are added whenever any team is picked.
--groups and --repos narrow the selection further (a repo is kept if it matches either).
Prints the selected groups and repos.
"""
import argparse
import json
import re

ALL_CHECKS = ["code", "overlap", "journey", "structure"]


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


def csv(s):
    return [x.strip() for x in s.split(",") if x.strip()] if s else []


p = argparse.ArgumentParser()
p.add_argument("sources_md")
p.add_argument("--teams", default="modeling,climate")
p.add_argument("--groups", default="")
p.add_argument("--repos", default="")
p.add_argument("--checks", default=",".join(ALL_CHECKS))
a = p.parse_args()

text = open(a.sources_md).read()
teams = set(csv(a.teams)) | {"shared"}
groups, repos = set(csv(a.groups)), {r.lower() for r in csv(a.repos)}

sources = []
for r in table(text, "Sources"):
    if r["team"] not in teams:
        continue
    name = r["repo"].split("/")[1]
    if (groups or repos) and r["group"] not in groups and name.lower() not in repos:
        continue
    sources.append({
        "repo": r["repo"], "name": name, "team": r["team"], "group": r["group"],
        "docs": csv(r["docs"]), "nav": None if r["nav"] == "-" else r["nav"],
        "published": r["published"], "audience": r["audience"],
    })

names = {s["name"] for s in sources}
journeys = [j for j in table(text, "Journeys") if j["starts at"].split()[0] in names]
checks = [c for c in csv(a.checks) if c in ALL_CHECKS]
bad = set(csv(a.checks)) - set(ALL_CHECKS)
if bad:
    raise SystemExit(f"unknown checks: {sorted(bad)}; use {ALL_CHECKS}")
if not sources:
    raise SystemExit("no sources matched")

cfg = {"sources": sources, "journeys": journeys, "checks": checks,
       "groups": sorted({s["group"] for s in sources}),
       "teams": sorted({s["team"] for s in sources} - {"shared"}) or ["shared"]}
json.dump(cfg, open("config.json", "w"), indent=2)

for g in cfg["groups"]:
    names = [s["name"] for s in sources if s["group"] == g]
    print(f"{g}: {', '.join(names)}")
print(f"{len(sources)} repos, {len(journeys)} journeys, checks: {', '.join(checks)}")
