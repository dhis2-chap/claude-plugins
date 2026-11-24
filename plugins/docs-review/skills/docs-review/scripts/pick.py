"""Pick sources from sources.md and write config.json.

Usage: python pick.py SOURCES_MD [--stories DIR] [--teams modeling,climate] [--groups core,geoservice]
                        [--repos chap-core,climate-app] [--checks code,overlap,journey,structure]
Teams default to both; shared sources are added whenever any team is picked.
--groups and --repos narrow the selection further (a repo is kept if it matches either).
--stories is a clone of dhis2-chap/user-stories; a story becomes a journey when the repo
it starts in (org/name, as in Sources) is selected. Stories with status "planned", or with
no starts_at page, are not journeys: nobody can walk them yet. YAML files that are not a
list of stories (readers.yaml, terminology.yaml) are ignored. Current stories that start
in a repo missing from Sources are printed as a warning. Needs PyYAML.
Prints the selected groups and repos.
"""
import argparse
import glob
import json
import os

import yaml

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
p.add_argument("--stories", default="")
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

def is_story(entry):
    return isinstance(entry, dict) and "id" in entry and "goal" in entry


team_of = {s["repo"].lower(): s["team"] for s in sources}
listed = {r["repo"].lower() for r in table(text, "Sources")}
journeys, skipped, unlisted = [], [], []
for path in sorted(glob.glob(os.path.join(a.stories, "*.yaml"))) if a.stories else []:
    data = yaml.safe_load(open(path))
    # The stories repo also holds other YAML (readers.yaml, terminology.yaml): only
    # files that are a list of stories count.
    if not isinstance(data, list) or not data or not all(is_story(st) for st in data):
        continue
    for st in data:
        if st.get("status", "current") != "current" or not st.get("starts_at"):
            skipped.append(st["id"])
            continue
        first = st["starts_at"][0]["repo"].lower()
        if first in team_of:
            journeys.append({**st, "team": team_of[first]})
        elif first not in listed:
            unlisted.append(f"{st['id']} ({st['starts_at'][0]['repo']})")
checks = [c for c in csv(a.checks) if c in ALL_CHECKS]
bad = set(csv(a.checks)) - set(ALL_CHECKS)
if bad:
    raise SystemExit(f"unknown checks: {sorted(bad)}; use {ALL_CHECKS}")
if not sources:
    raise SystemExit("no sources matched")
if "journey" in checks and not a.stories:
    raise SystemExit("the journey check needs --stories")

cfg = {"sources": sources, "journeys": journeys, "checks": checks,
       "groups": sorted({s["group"] for s in sources}),
       "teams": sorted({s["team"] for s in sources} - {"shared"}) or ["shared"]}
json.dump(cfg, open("config.json", "w"), indent=2)

for g in cfg["groups"]:
    names = [s["name"] for s in sources if s["group"] == g]
    print(f"{g}: {', '.join(names)}")
print(f"{len(sources)} repos, {len(journeys)} journeys, checks: {', '.join(checks)}")
if skipped:
    print(f"not journeys (planned or no starts_at): {', '.join(skipped)}")
if unlisted:
    print(f"WARNING: {len(unlisted)} current stories start in a repo that is not in Sources, "
          f"so no run reviews them (a renamed repo, or a source to add): {', '.join(unlisted)}")
