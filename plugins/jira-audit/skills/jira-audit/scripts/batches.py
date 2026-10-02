"""Split the issues to review into batches for the reviewer subagents.

Scope comes from config.json: "sprint" reviews only issues in cfg["sprints"],
"all" reviews every open in-scope issue. C1 hits (no component) are included.
Issues sharing an epic stay in the same batch; the no-epic pile is chunked.
Writes batch_<n>.json with {"issues": [...], "epics": [...]} and prints the count.
"""
import json
import math
from collections import defaultdict

cfg = json.load(open("config.json"))
DONE = set(cfg["done_statuses"])
BATCH_SIZE = 25

issues = json.load(open("jira.json"))
c1 = {f["key"] for f in json.load(open("findings_mechanical.json")) if f["rule"] == "C1"}


def in_scope_for_review(k, d):
    if d["status"] in DONE or d["type"] == "Epic" or not (d["in_scope"] or k in c1):
        return False
    if cfg["scope"] == "sprint":
        return any(s["name"] in cfg["sprints"] for s in d["sprints"])
    return True


groups = defaultdict(list)
for k, d in sorted(issues.items(), key=lambda kv: int(kv[0].split("-")[1])):
    if in_scope_for_review(k, d):
        groups[d["parent"] or "NO_EPIC"].append(k)

units = []
for ep, keys in groups.items():
    if ep == "NO_EPIC":
        units += [(f"NO_EPIC_{i}", keys[i:i + 20]) for i in range(0, len(keys), 20)]
    else:
        units.append((ep, keys))
units.sort(key=lambda u: -len(u[1]))

total = sum(len(u[1]) for u in units)
n = max(1, math.ceil(total / BATCH_SIZE))
batches = [[] for _ in range(n)]
for u in units:
    min(batches, key=lambda b: sum(len(x[1]) for x in b)).append(u)

for i, b in enumerate(batches):
    keys = [k for _, ks in b for k in ks]
    epics = [ep for ep, _ in b if ep in issues and issues[ep]["status"] not in DONE]
    json.dump({"issues": keys, "epics": epics}, open(f"batch_{i}.json", "w"), indent=1)
    print(f"batch_{i}: {len(keys)} issues, epics {epics}")
print(f"{n} batches, {total} issues to review")
