"""Build the HTML report from merged.json. Writes report.html and proposed.json.

Usage: python report.py [--save]
  --save  also record this run under ~/.cache/chap-jira-audit/ so the next run
          can mark findings as new / still open / resolved.
Scope (sprint/all), sprint names, components and the snapshot time come from config.json.
"""
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

cfg = json.load(open("config.json"))
m = json.load(open("merged.json"))
issues = json.load(open("jira.json"))
JIRA = cfg["jira_url"].rstrip("/") + "/browse/"
DONE = set(cfg["done_statuses"])
SPRINT = cfg["scope"] == "sprint"
HIST_DIR = os.path.expanduser("~/.cache/chap-jira-audit")

RULES = {
    "S1": "Open, but a merged PR delivers it", "S2": "In Review without an open PR", "S3": "In Progress and stale",
    "S4": "Done, but referenced PRs never merged", "S5": "Not started, but has a PR", "S6": "Delivered by a PR that never cited the key",
    "E1": "Epic open, all children done", "E2": "Epic done, children open", "E3": "Epic text no longer matches children", "E4": "Epic with no children",
    "D1": "Description outdated or wrong", "D2": "Description empty or too thin", "D3": "Description superseded",
    "U1": "Duplicate", "U2": "Overlap or unlinked follow-up", "C1": "No component",
    "H1": "Assignee differs from PR author", "H2": "Active but unassigned", "H3": "Open, only in closed sprints", "H4": "No epic",
}
CONF_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Note": 3}
TIER_TXT = {
    1: "Apply on one approval: reversible in one click, hard evidence, no one loses work. Each change gets a Jira comment naming the PR or this audit.",
    2: "One glance each: transitions without a PR to point at, duplicate closes, component by keyword only.",
    3: "For the ticket owner: description edits. The proposed text is in the Descriptions section.",
}

if SPRINT:
    in_sprint = {k for k, d in issues.items() if any(s["name"] in cfg["sprints"] for s in d["sprints"])}
    for part in ("sub", "dups", "mech"):
        m[part] = [f for f in m[part] if f["key"] in in_sprint]
    m["reviewed"] = [k for k in m["reviewed"] if k in in_sprint]
    m["clean"] = [k for k in m["clean"] if k in in_sprint]


def esc(s):
    return html.escape(str(s or ""))


def short(u):
    mo = re.match(r"https://github\.com/[^/]+/([^/]+)/pull/(\d+)", u)
    return f"{mo.group(1)}#{mo.group(2)}" if mo else (u if len(u) < 60 else u[:57] + "...")


def linkify(s):
    s = esc(s)
    s = re.sub(r"(https?://[^\s'\")\]]+)", lambda mo: f'<a href="{mo.group(1)}" target="_blank" rel="noopener">{short(mo.group(1))}</a>', s)
    return re.sub(rf"\b({cfg['project']}-\d+)\b", lambda mo: f'<a href="{JIRA}{mo.group(1)}" target="_blank" rel="noopener">{mo.group(1)}</a>', s)


def key_cell(k):
    return f'<a class="key" href="{JIRA}{k}" target="_blank" rel="noopener">{k}</a><div class="sum">{esc(issues.get(k, {}).get("summary", ""))}</div>'


def status_pill(k):
    st = issues.get(k, {}).get("status", "?")
    cls = "done" if st in DONE else ("prog" if st in ("In Progress", "In Review") else "todo")
    return f'<span class="pill {cls}">{esc(st)}</span>'


def conf_pill(c):
    return f'<span class="conf {c.lower()}">{c}</span>'


def action_cell(a):
    return '<span class="muted">none</span>' if not a or a == "none" else f"<code>{esc(a)}</code>"


def tier(f):
    a, r, c = f.get("suggested_action", "none"), f["rule"], f["confidence"]
    if a == "none":
        return None
    if r in ("S1", "S6") and a == "transition:Done" and c == "High":
        return 1
    if r == "S5" and a == "transition:In Progress":
        return 1
    if r == "U2" and a.startswith("link_relates"):
        return 1
    if r == "C1" and "parent epic" in f["evidence"][0]:
        return 1
    if a.startswith(("transition", "close_duplicate", "link_duplicate")) or r == "C1":
        return 2
    return 3


# ---- history ----
prev = {}
hist_latest = os.path.join(HIST_DIR, "latest.json")
if os.path.exists(hist_latest):
    prev = json.load(open(hist_latest))
prev_set = {tuple(x) for x in prev.get("findings", [])}

sub, dups, mech = m["sub"], m["dups"], m["mech"]
allf = sub + dups + mech
for f in allf:
    f["_id"], f["_tier"] = "", tier(f)
    f["_new"] = (f["key"], f["rule"]) not in prev_set if prev else False
pid = 0
for f in sorted(allf, key=lambda f: ((f["_tier"] or 9), CONF_ORDER.get(f["confidence"], 9), int(f["key"].split("-")[1]))):
    if f["_tier"]:
        pid += 1
        f["_id"] = f"P{pid:02d}"

cur_set = {(f["key"], f["rule"]) for f in allf if not f["rule"].startswith("H")}
resolved = sorted(prev_set - cur_set) if prev else []
n_new = sum(1 for f in allf if f["_new"] and not f["rule"].startswith("H"))


def rows(findings, cols):
    out = []
    for f in sorted(findings, key=lambda f: (CONF_ORDER.get(f["confidence"], 9), int(f["key"].split("-")[1]))):
        ev = "".join(f"<li>{linkify(e)}</li>" for e in f.get("evidence", []))
        note = f'<p class="note">{linkify(f["note"])}</p>' if f.get("note") else ""
        prop = f'<p class="prop"><b>Proposed text:</b> {linkify(f["proposed_text"])}</p>' if f.get("proposed_text") else ""
        other = f'<td>{key_cell(f["other"])}{status_pill(f["other"])}</td>' if "other" in cols else ""
        idc = f'<td class="pid">{f["_id"]}</td>' if "id" in cols else ""
        new = ' <span class="new">new</span>' if f["_new"] else ""
        out.append(f'<tr>{idc}<td>{key_cell(f["key"])}{status_pill(f["key"])}</td>{other}'
                   f'<td><span class="rule" title="{esc(RULES.get(f["rule"], ""))}">{f["rule"]}</span> {esc(f["title"])}{new}'
                   f'<details><summary>evidence</summary><ul>{ev}</ul>{prop}{note}</details></td>'
                   f'<td>{action_cell(f.get("suggested_action"))}</td><td>{conf_pill(f["confidence"])}</td></tr>')
    return "\n".join(out)


def table(findings, cols=("id", "key", "finding", "action", "conf")):
    if not findings:
        return '<p class="muted">Nothing found.</p>'
    ths = {"id": "ID", "key": "Issue", "other": "Related issue", "finding": "Finding", "action": "Suggested action", "conf": "Confidence"}
    return f'<div class="tw"><table><thead><tr>{"".join(f"<th>{ths[c]}</th>" for c in cols)}</tr></thead><tbody>{rows(findings, cols)}</tbody></table></div>'


status_f = [f for f in sub if f["rule"][0] == "S"] + [f for f in mech if f["rule"] == "S4"]
epic_f = [f for f in sub if f["rule"] == "E3"] + [f for f in mech if f["rule"] in ("E1", "E2") and f["confidence"] != "Note"]
desc_f = [f for f in sub if f["rule"][0] == "D"]
comp_f = [f for f in mech if f["rule"] == "C1"]
hyg = [f for f in mech if f["rule"][0] == "H" or f["rule"] == "E4" or (f["rule"] == "E1" and f["confidence"] == "Note")]
by_conf = Counter(f["confidence"] for f in sub + dups)
by_cat = {"Status": len(status_f), "Epics": len(epic_f), "Descriptions": len(desc_f), "Duplicates": len(dups), "Component": len(comp_f)}
proposed = [f for f in allf if f["_id"]]


def prop_table(t):
    fs = sorted([f for f in proposed if f["_tier"] == t], key=lambda f: (f["rule"], int(f["key"].split("-")[1])))
    r = "".join(f'<tr><td class="pid">{f["_id"]}</td><td>{key_cell(f["key"])}</td><td>{action_cell(f["suggested_action"])}</td>'
                f'<td><span class="rule">{f["rule"]}</span> {esc(f["title"])}</td><td>{conf_pill(f["confidence"])}</td></tr>' for f in fs)
    return (f'<h3>Tier {t}<span class="cnt">{len(fs)}</span></h3><p class="lead muted">{TIER_TXT[t]}</p>'
            f'<div class="tw"><table><thead><tr><th>ID</th><th>Issue</th><th>Action</th><th>Why</th><th>Confidence</th></tr></thead><tbody>{r}</tbody></table></div>')


hyg_by = defaultdict(list)
for f in hyg:
    hyg_by[f["rule"]].append(f)
hyg_html = ""
for r in ("E4", "E1", "H2", "H1", "H3", "H4"):
    fs = sorted(hyg_by.get(r, []), key=lambda f: int(f["key"].split("-")[1]))
    if fs:
        items = ", ".join(f'<a href="{JIRA}{f["key"]}" target="_blank" rel="noopener">{f["key"]}</a>' + (f' <span class="muted">({esc(f["title"])})</span>' if r in ("H1", "H3", "E1") else "") for f in fs)
        hyg_html += f'<details class="hyg"><summary><b>{RULES[r]}</b> <span class="muted">{len(fs)}</span></summary><p>{items}</p></details>'

open_in_scope = [k for k, d in issues.items() if d["in_scope"] and d["status"] not in DONE]
n_done = sum(1 for d in issues.values() if d["in_scope"] and d["status"] in DONE)
n_prs = sum(len(json.load(open(f"pr_{r}.json"))) for r in cfg["code_repos"] + cfg["support_repos"] if os.path.exists(f"pr_{r}.json"))
snap = datetime.fromisoformat(cfg["snapshot"]).strftime("%Y-%m-%d %H:%M")
title = f"{cfg['project']} Sprint Audit" if SPRINT else f"{cfg['project']} Jira Audit"
h1 = f"{cfg['project']} Jira audit: sprints {', '.join(cfg['sprints'])}" if SPRINT else f"{cfg['project']} Jira audit: {', '.join(cfg['components'])}"
scope_txt = (f"Scope: issues in the sprints <b>{'</b> and <b>'.join(cfg['sprints'])}</b> within the components {', '.join(cfg['components'])}. "
             if SPRINT else f"Scope: every open issue in the components <b>{'</b>, <b>'.join(cfg['components'])}</b>, plus open issues with no component. ")
hist_txt = ""
if prev:
    hist_txt = (f'<p class="meta">Compared with the run of <b>{prev["snapshot"][:10]}</b>: <b>{n_new}</b> new findings, '
                f'<b>{len(resolved)}</b> resolved since then' + (f' ({", ".join(k for k, _ in resolved[:12])}{"..." if len(resolved) > 12 else ""})' if resolved else "") + ".</p>")

page = f"""<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#f6f7f9;--panel:#fff;--ink:#1c2230;--ink2:#5b6474;--line:#e1e5ec;--accent:#3b5bdb;--accent-soft:#e8edfb;
--high:#b42318;--high-bg:#fde8e6;--med:#9a5b00;--med-bg:#fdf1dc;--low:#3b5bdb;--low-bg:#e8edfb;--note:#5b6474;--note-bg:#eef0f4;
--done:#1b7f4c;--done-bg:#e3f5ea;--prog:#8a5a00;--prog-bg:#fff3d6;--todo:#4b5565;--todo-bg:#eceff3}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#13161c;--panel:#1b1f27;--ink:#e6e9ef;--ink2:#9aa3b2;--line:#2b313c;--accent:#8da2ff;--accent-soft:#232a3f;
--high:#ff8a80;--high-bg:#3a1d1b;--med:#ffc766;--med-bg:#3a2e14;--low:#8da2ff;--low-bg:#232a3f;--note:#9aa3b2;--note-bg:#242933;--done:#6fd39a;--done-bg:#173426;--prog:#ffcf6b;--prog-bg:#3a2e14;--todo:#aab3c2;--todo-bg:#262c37}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#13161c;--panel:#1b1f27;--ink:#e6e9ef;--ink2:#9aa3b2;--line:#2b313c;--accent:#8da2ff;--accent-soft:#232a3f;
--high:#ff8a80;--high-bg:#3a1d1b;--med:#ffc766;--med-bg:#3a2e14;--low:#8da2ff;--low-bg:#232a3f;--note:#9aa3b2;--note-bg:#242933;--done:#6fd39a;--done-bg:#173426;--prog:#ffcf6b;--prog-bg:#3a2e14;--todo:#aab3c2;--todo-bg:#262c37}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif;padding-inline:16px;padding-block:32px 64px}}
.wrap{{max-width:1180px;margin:0 auto}} h1{{font-size:28px;font-weight:600;margin:0 0 4px;text-wrap:balance}}
h2{{font-size:19px;font-weight:600;margin:40px 0 12px;padding-top:16px;border-top:1px solid var(--line)}} h3{{font-size:16px;font-weight:600;margin:24px 0 6px}}
.cnt{{color:var(--ink2);font-weight:400;margin-left:6px}} .meta{{color:var(--ink2);font-size:14px}} .meta b{{color:var(--ink);font-weight:500}}
.tiles{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}} .tile{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px 16px;min-width:110px}}
.tile .n{{font:500 26px/1.1 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}} .tile .l{{font-size:12px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em;margin-top:4px}}
.tw{{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:6px}} table{{border-collapse:collapse;width:100%;font-size:14px}}
th{{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2);font-weight:500;padding:10px 12px;border-bottom:1px solid var(--line)}}
td{{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}} tr:last-child td{{border-bottom:0}} td:first-child{{white-space:nowrap}}
.key{{font:500 13px "IBM Plex Mono",monospace;color:var(--accent);text-decoration:none}} .key:hover{{text-decoration:underline}}
.sum{{font-size:12.5px;color:var(--ink2);max-width:240px;line-height:1.35;margin:2px 0 4px}}
.pill,.conf,.new{{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:999px;font-weight:500;white-space:nowrap}}
.pill.done{{color:var(--done);background:var(--done-bg)}} .pill.prog{{color:var(--prog);background:var(--prog-bg)}} .pill.todo{{color:var(--todo);background:var(--todo-bg)}}
.conf.high{{color:var(--high);background:var(--high-bg)}} .conf.medium{{color:var(--med);background:var(--med-bg)}} .conf.low{{color:var(--low);background:var(--low-bg)}} .conf.note{{color:var(--note);background:var(--note-bg)}}
.new{{color:var(--done);background:var(--done-bg);margin-left:4px}}
.rule{{font:500 11.5px "IBM Plex Mono",monospace;color:var(--accent);background:var(--accent-soft);padding:1px 5px;border-radius:3px;margin-right:4px}}
.pid{{font:500 13px "IBM Plex Mono",monospace;color:var(--ink2)}} code{{font:13px "IBM Plex Mono",monospace;background:var(--accent-soft);padding:1px 5px;border-radius:3px;white-space:nowrap}}
details{{margin-top:4px}} summary{{cursor:pointer;color:var(--ink2);font-size:13px}} details ul{{margin:6px 0 4px;padding-left:18px;font-size:13px;color:var(--ink2)}} details li{{margin:2px 0}}
.prop,.note{{font-size:13px;margin:6px 0 0;padding:8px 10px;border-left:3px solid var(--accent);background:var(--accent-soft);border-radius:0 4px 4px 0}} .note{{border-color:var(--line);background:transparent;color:var(--ink2)}}
a{{color:var(--accent)}} .muted{{color:var(--ink2)}} .hyg{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:8px 14px;margin:6px 0}} .hyg p{{font-size:13px;line-height:1.8;margin:6px 0 2px}}
p.lead{{max-width:72ch}} .method{{max-width:76ch}} .method li{{margin:4px 0}} :focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
@media (max-width:600px){{.sum{{max-width:none}} td,th{{padding:8px}}}}
</style>
<div class="wrap">
<h1>{h1}</h1>
<p class="meta">Snapshot <b>{snap}</b>. {scope_txt}Checked against PRs in {", ".join(cfg["code_repos"])}, with {", ".join(cfg["support_repos"]) or "no supporting repos"} as supporting evidence.</p>
<p class="meta">In scope: <b>{len(open_in_scope)}</b> open issues, <b>{n_done}</b> done, <b>{n_prs}</b> PRs. Reviewed one by one: <b>{len(m["reviewed"])}</b> issues and epics, of which <b>{len(m["clean"])}</b> had nothing to report. Nothing in Jira was changed; the last section lists proposed changes for approval.</p>
{hist_txt}
<div class="tiles">{"".join(f'<div class="tile"><div class="n">{v}</div><div class="l">{k}</div></div>' for k, v in by_cat.items())}</div>
<div class="tiles">{"".join(f'<div class="tile"><div class="n">{by_conf.get(c, 0)}</div><div class="l">{conf_pill(c)}</div></div>' for c in ("High", "Medium", "Low"))}</div>
<p class="lead muted">High: direct evidence, no other sensible reading. Medium: strong evidence, someone with context should confirm. Low: worth a glance. Each row expands to its evidence.</p>

<h2>Proposed changes<span class="cnt">{len(proposed)}</span></h2>
<p class="lead muted">Grouped by how much attention each needs. Approve a whole tier ("apply tier 1") or single IDs. Nothing has been applied.</p>
{prop_table(1)}{prop_table(2)}{prop_table(3)}

<h2>Status mismatches<span class="cnt">{len(status_f)}</span></h2>
<p class="lead muted">S1 open but a merged PR delivers it. S2 In Review with no open PR. S3 In Progress and no activity for {cfg["stale_days"]} days. S4 Done, but its PRs were never merged. S5 not started but has a PR. S6 delivered by a PR that never cited the key.</p>
{table(status_f)}
<h2>Epics<span class="cnt">{len(epic_f)}</span></h2>
{table(epic_f)}
<h2>Descriptions<span class="cnt">{len(desc_f)}</span></h2>
<p class="lead muted">D1 claims that no longer match master or merged PRs. D2 too thin to pick up. D3 superseded by a later decision. The proposed text is the minimal edit, not a rewrite.</p>
{table(desc_f)}
<h2>Duplicates and overlaps<span class="cnt">{len(dups)}</span></h2>
<p class="lead muted">U1 same work twice. U2 overlapping or follow-up work with no Jira link between them. Candidates came from text similarity across the whole project, then each pair was read.</p>
{table(dups, ("id", "key", "other", "finding", "action", "conf"))}
<h2>Missing component<span class="cnt">{len(comp_f)}</span></h2>
<p class="lead muted">Open issues with no component whose text or parent epic points at the audited area. They are invisible on component-filtered boards.</p>
{table(comp_f)}
<h2>Hygiene notes<span class="cnt">{len(hyg)}</span></h2>
<p class="lead muted">Mechanical only, no judgement applied. Listed for completeness.</p>
{hyg_html}

<h2>Method</h2>
<div class="method"><ol>
<li>Snapshot of the in-scope Jira issues via the Atlassian MCP, and of all PRs via <code>gh</code>.</li>
<li>Issue-to-PR links from <code>{cfg["project"]}-n</code> references in PR title, body and branch; "part of" / "first step" references count as partial.</li>
<li>Mechanical rules on the snapshot (status, epics, component, hygiene).</li>
<li>Reviewer subagents, grouped by epic, read every in-scope open issue in full, checked its PRs, and searched unlinked PRs and master for work that never cited the key. Description claims were checked against the code on master.</li>
<li>Duplicate candidates from text similarity across the whole project, then read in pairs.</li>
<li>Mechanical hints a reviewer refuted were dropped. High-confidence transitions were re-checked against live Jira before publishing.</li>
</ol>
<p><b>Blind spots.</b> Work done without a PR (design, research, server config) can look undone; such signals stay Low. The keyword search for unlinked PRs can miss work described in other words. Done issues are only read when part of a duplicate pair. Jira moves during a run.</p></div>
</div>
"""
open("report.html", "w").write(page)
json.dump([{"id": f["_id"], "tier": f["_tier"], "key": f["key"], "rule": f["rule"], "action": f["suggested_action"], "title": f["title"],
            "evidence": f.get("evidence", []), "proposed_text": f.get("proposed_text", ""), "other": f.get("other"), "confidence": f["confidence"]}
           for f in sorted(proposed, key=lambda f: int(f["_id"][1:]))], open("proposed.json", "w"), indent=1)

if "--save" in sys.argv:
    os.makedirs(HIST_DIR, exist_ok=True)
    rec = {"snapshot": cfg["snapshot"], "scope": cfg["scope"], "components": cfg["components"],
           "findings": sorted(cur_set), "proposed": [[f["_id"], f["key"], f["suggested_action"]] for f in proposed]}
    for name in (f"{cfg['snapshot'][:10]}-{cfg['scope']}.json", "latest.json"):
        json.dump(rec, open(os.path.join(HIST_DIR, name), "w"), indent=1)
    print(f"history saved to {HIST_DIR}")

print(f"report.html {len(page)} bytes; {len(proposed)} proposed "
      f"(tier1 {sum(1 for f in proposed if f['_tier'] == 1)}, tier2 {sum(1 for f in proposed if f['_tier'] == 2)}, tier3 {sum(1 for f in proposed if f['_tier'] == 3)}); "
      f"{dict(by_conf)}; new since last run {n_new if prev else 'n/a'}")
