"""Mechanical checks on jira.json + links.json. Writes findings_mechanical.json.

Rules are documented in reference/rules.md. Every finding here is a hint for the
reviewer subagents, except the hygiene notes (H*, E4) and S4/E2/C1 which go
straight to the report.
"""
import json
import re
from collections import Counter
from datetime import datetime, timedelta

cfg = json.load(open("config.json"))
NOW = datetime.fromisoformat(cfg["snapshot"])
STALE = timedelta(days=cfg["stale_days"])
DONE = set(cfg["done_statuses"])
TODO = set(cfg["todo_statuses"])
KEYWORDS = re.compile(r"\b(" + "|".join(re.escape(w) for w in cfg["keywords"]) + r")\b", re.I)
UMBRELLA = re.compile(r"placeholder|umbrella|ongoing|future work", re.I)
GH = {k.lower(): [v.lower() for v in vs] for k, vs in cfg["gh_logins"].items()}

issues = json.load(open("jira.json"))
links = json.load(open("links.json"))


def same_person(display, login):
    d, l = display.lower(), login.lower()
    if l in GH.get(d, []):
        return True
    parts = d.split()
    return l == "".join(parts) or (parts and l.startswith(parts[0][:4]) and l.endswith(parts[-1][:3]))


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def pr_urls(ps):
    return [f"{p['repo']}#{p['number']} ({p['state'].lower()}) {p['url']}" for p in ps]


findings = []


def add(key, rule, title, evidence, action="none", confidence="Medium"):
    findings.append({"key": key, "rule": rule, "title": title, "evidence": evidence, "suggested_action": action, "confidence": confidence})


children = {}
for d in issues.values():
    if d["parent"]:
        children.setdefault(d["parent"], []).append(d)

for key, d in issues.items():
    prs = links.get(key, [])
    merged = [p for p in prs if p["state"] == "MERGED"]
    merged_full = [p for p in merged if not p["partial"]]
    open_prs = [p for p in prs if p["state"] == "OPEN"]
    st = d["status"]
    is_open = st not in DONE

    if not d["in_scope"]:
        parent_in = d["parent"] in issues and issues[d["parent"]]["in_scope"]
        if is_open and (parent_in or KEYWORDS.search(d["summary"] + " " + d["desc"])):
            why = f"parent epic in scope: {d['parent']}" if parent_in else "keyword match in summary/description"
            add(key, "C1", "No component but looks related", [why], "add_component:?", "Medium")
        continue

    if d["type"] == "Epic":
        kids = children.get(key, [])
        if not kids:
            if is_open:
                add(key, "E4", "open epic with no child issues", [f"last updated {d['updated'][:10]}"], "none", "Note")
            continue
        open_kids = [k for k in kids if k["status"] not in DONE]
        if is_open and not open_kids:
            umbrella = set(d["labels"]) & set(cfg["umbrella_labels"]) or UMBRELLA.search(d["desc"])
            if umbrella:
                add(key, "E1", f"all {len(kids)} children done, but the epic is a placeholder/initiative", [f"children: {', '.join(k['key'] for k in kids)}"], "none", "Note")
            else:
                add(key, "E1", f"Epic open but all {len(kids)} children are done", [f"children: {', '.join(k['key'] for k in kids)}"], "transition:Done", "Medium")
        if not is_open and open_kids:
            add(key, "E2", f"Epic is {st} but {len(open_kids)} children are open", [f"{k['key']} ({k['status']})" for k in open_kids], "none", "High")
        continue

    if is_open and merged_full and not open_prs:
        add(key, "S1", f"{st} but has merged PR(s) and no open PR", pr_urls(merged_full), "transition:Done", "Medium")
    if st == "In Review" and not open_prs:
        add(key, "S2", "In Review but no open PR references it", pr_urls(prs) or ["no PR references this key"], "none", "High")
    if st == "In Progress":
        last = max([ts(d["updated"])] + [ts(p["updatedAt"]) for p in prs])
        if NOW - last > STALE and not open_prs:
            add(key, "S3", f"In Progress, no activity for {(NOW - last).days} days, no open PR", [f"last activity {last.date()}"] + pr_urls(prs), "none", "High")
    if not is_open and prs and not merged:
        add(key, "S4", f"{st} but referenced PRs were never merged", pr_urls(prs), "none", "Low")
    if st in TODO and (open_prs or merged):
        add(key, "S5", f"{st} but has {'open' if open_prs else 'merged'} PR(s)", pr_urls(open_prs or merged), "transition:In Progress" if open_prs else "transition:Done", "Medium")

    if is_open and st in ("In Progress", "In Review"):
        if not d["assignee"]:
            add(key, "H2", f"{st} with no assignee", [], "none", "Note")
        authors = {p["author"] for p in prs}
        if d["assignee"] and authors and not any(same_person(d["assignee"], a) for a in authors):
            add(key, "H1", f"assignee {d['assignee']}, PR author(s) {', '.join(sorted(authors))}", [], "none", "Note")
    if is_open and d["sprints"] and all(s["state"] == "closed" for s in d["sprints"]):
        add(key, "H3", f"open, only in closed sprint(s): {', '.join(s['name'] for s in d['sprints'])}", [], "none", "Note")
    if is_open and d["type"] not in ("Epic", "Sub-task") and not d["parent"]:
        add(key, "H4", "open issue with no epic", [], "none", "Note")

json.dump(findings, open("findings_mechanical.json", "w"), indent=1)
print(Counter(f["rule"] for f in findings))
