"""Roadmap checks: in-scope CLIM epics against the ideas in the ROADMAP project.

Run with: uv run --with scikit-learn python roadmap.py
Reads config.json, jira.json and roadmap_ideas.jsonl; writes findings_roadmap.json.
Rules R2, R3 and R4 are documented in reference/rules.md. When
roadmap_ideas.jsonl is missing the script writes an empty list and says so.
"""
import json
import os
import re
from collections import Counter

cfg = json.load(open("config.json"))
OUT = "findings_roadmap.json"
if not os.path.exists("roadmap_ideas.jsonl"):
    json.dump([], open(OUT, "w"))
    print("roadmap_ideas.jsonl not found: skipping R2-R4")
    raise SystemExit

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DONE = set(cfg["done_statuses"])
DELIVERY = cfg["roadmap_delivery_link"]
ACTIVE = set(cfg["roadmap_active_statuses"])
NEEDS_EPIC = set(cfg["roadmap_delivery_statuses"])
STRONG, WEAK, TOP = 0.30, 0.18, 3  # character n-gram cosine; see "Lessons" in reference/rules.md

issues = json.load(open("jira.json"))
ideas = {}
for line in open("roadmap_ideas.jsonl"):
    d = json.loads(line)
    ideas[d["key"]] = d
epics = {k: d for k, d in issues.items() if d["type"] == "Epic" and d["in_scope"] and d["status"] not in DONE}

# Which CLIM epics each idea links, split by link type; and the reverse.
idea_delivery, idea_other, epic_ideas, link_summary = {}, {}, {}, {}
for ik, idea in ideas.items():
    for l in idea["links"]:
        if not l["key"].startswith(cfg["project"] + "-") or l.get("issuetype") != "Epic":
            continue
        (idea_delivery if l["type"] == DELIVERY else idea_other).setdefault(ik, {})[l["key"]] = l["type"]
        link_summary[l["key"]] = l.get("summary") or issues.get(l["key"], {}).get("summary", "")
        epic_ideas.setdefault(l["key"], set()).add(ik)

# Text similarity between open in-scope epics and ideas.
ekeys, ikeys = sorted(epics, key=lambda k: int(k.split("-")[1])), sorted(ideas, key=lambda k: int(k.split("-")[1]))
texts = [epics[k]["summary"] + " " + epics[k]["desc"] for k in ekeys] + [ideas[k]["summary"] + " " + ideas[k]["desc"] for k in ikeys]
sim = [[0.0] * len(ikeys) for _ in ekeys]
if ekeys and ikeys:
    X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit_transform(texts)
    sim = cosine_similarity(X[: len(ekeys)], X[len(ekeys):])


def candidates(row, keys, lookup):
    scored = sorted(((float(s), k) for s, k in zip(row, keys) if s >= WEAK), reverse=True)[:TOP]
    return [(k, s, lookup[k]["summary"]) for s, k in scored]


def fmt(cands):
    return [f"candidate {k} (similarity {s:.2f}): {summary}" for k, s, summary in cands]


findings = []


def add(key, rule, title, evidence, action="none", confidence="Medium", other=None):
    f = {"key": key, "rule": rule, "title": title, "evidence": evidence, "suggested_action": action, "confidence": confidence}
    if other:
        f["other"] = other
    findings.append(f)


# R4: idea linked to an epic, but not with the delivery link.
for ik in ikeys:
    for ek, ltype in idea_other.get(ik, {}).items():
        if ek in idea_delivery.get(ik, {}):
            continue
        add(ik, "R4", f"linked to epic {ek} with '{ltype}' instead of the delivery link",
            [f"link type '{ltype}' does not show as delivery on the idea; '{DELIVERY}' (epic implements idea) does", f"{ek}: {link_summary.get(ek, '')}".strip()],
            f"link_implements:{ek}", "High", other=ek)

# R3: active idea with no epic at all.
for j, ik in enumerate(ikeys):
    idea = ideas[ik]
    if idea["status"] not in ACTIVE or idea_delivery.get(ik) or idea_other.get(ik):
        continue
    cands = candidates([sim[i][j] for i in range(len(ekeys))], ekeys, epics)
    other_links = [f"{l['type']} {l['key']} ({l.get('issuetype', '?')}, {l['status']})" for l in idea["links"] if l["key"].startswith(cfg["project"] + "-")]
    ev = [f"status {idea['status']}, no linked {cfg['project']} epic"] + ([f"other {cfg['project']} links: " + ", ".join(other_links)] if other_links else []) + (fmt(cands) or ["no similar open epic in the audited components"])
    if idea["status"] in NEEDS_EPIC:
        best = cands[0] if cands and cands[0][1] >= STRONG else None
        add(ik, "R3", "on the roadmap but no epic delivers it", ev, f"link_implements:{best[0]}" if best else "none", "Medium", other=best[0] if best else None)
    elif cands:
        add(ik, "R3", f"{idea['status']} idea with a similar open epic that is not linked", ev, "none", "Low", other=cands[0][0])

# R2: open epic no idea links to.
for i, ek in enumerate(ekeys):
    if epic_ideas.get(ek):
        continue
    cands = candidates(sim[i], ikeys, ideas)
    if not cands:
        add(ek, "R2", "open epic not linked from any roadmap idea", ["no similar idea found"], "none", "Note")
        continue
    best = cands[0]
    if best[1] >= STRONG:
        add(ek, "R2", f"open epic not linked from any roadmap idea; {best[0]} looks like the one", fmt(cands), f"link_implements:{best[0]}", "Medium", other=best[0])
    else:
        add(ek, "R2", "open epic not linked from any roadmap idea", fmt(cands), "none", "Low", other=best[0])

json.dump(findings, open(OUT, "w"), indent=1)
print(f"ideas {len(ideas)} (active {sum(1 for d in ideas.values() if d['status'] in ACTIVE)}), open epics in scope {len(epics)}, "
      f"epics with an idea {sum(1 for k in epics if epic_ideas.get(k))}")
print(Counter(f"{f['rule']}/{f['confidence']}" for f in findings))
