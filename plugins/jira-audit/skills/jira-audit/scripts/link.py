"""Merge Jira snapshot slices and link issues to PRs.

Reads config.json, jira_*.jsonl and pr_<repo>.json from the current directory.
Writes jira.json, links.json, unlinked_prs.json and all_prs.json.
"""
import glob
import json
import re

cfg = json.load(open("config.json"))
IN_SCOPE = set(cfg["components"])
KEY = re.compile(rf"{cfg['project']}-(\d+)", re.I)
PARTIAL_WORDS = r"(part of|first step|step (one|1|towards)|towards|follow-?up|related( to)?|prep(aration|ares)? for|groundwork|precursor|see also|refs?)"
PARTIAL = re.compile(rf"{PARTIAL_WORDS}\W{{0,10}}{cfg['project']}-\d+|{cfg['project']}-\d+\W{{0,10}}(\(?(part|partial|first step|step)\b)", re.I)

issues = {}
for f in sorted(glob.glob("jira_*.jsonl")):
    if f == "jira_other_summaries.jsonl":
        continue
    for line in open(f):
        d = json.loads(line)
        prev = issues.get(d["key"])
        if prev:
            prev["components"] = sorted(set(prev["components"]) | set(d["components"]))
        else:
            issues[d["key"]] = d
for d in issues.values():
    d["in_scope"] = bool(set(d["components"]) & IN_SCOPE)
json.dump(issues, open("jira.json", "w"), indent=0)

links, unlinked, all_prs = {}, [], []
for f in sorted(glob.glob("pr_*.json")):
    repo = f[3:-5]
    for p in json.load(open(f)):
        text = " ".join(filter(None, [p["title"], p["body"], p["headRefName"]]))
        keys = {f"{cfg['project']}-{m}" for m in KEY.findall(text)}
        rec = {
            "repo": repo, "number": p["number"], "title": p["title"], "state": p["state"],
            "mergedAt": p["mergedAt"], "closedAt": p["closedAt"], "createdAt": p["createdAt"],
            "updatedAt": p["updatedAt"], "branch": p["headRefName"], "author": p["author"]["login"],
            "url": p["url"], "keys": sorted(keys),
        }
        all_prs.append(rec)
        if not keys:
            unlinked.append({**rec, "body": (p["body"] or "")[:400]})
            continue
        for k in keys:
            partial = any(k.upper() in m.group(0).upper() for m in PARTIAL.finditer(text))
            links.setdefault(k, []).append({**rec, "partial": partial})

json.dump(links, open("links.json", "w"), indent=0)
json.dump(unlinked, open("unlinked_prs.json", "w"), indent=0)
json.dump(all_prs, open("all_prs.json", "w"), indent=0)

n_open = sum(1 for d in issues.values() if d["in_scope"] and d["status"] not in cfg["done_statuses"])
print(f"issues {len(issues)}, in scope {sum(1 for d in issues.values() if d['in_scope'])}, open in scope {n_open}")
print(f"prs {len(all_prs)}, with refs {sum(1 for p in all_prs if p['keys'])}, unlinked {len(unlinked)}")
