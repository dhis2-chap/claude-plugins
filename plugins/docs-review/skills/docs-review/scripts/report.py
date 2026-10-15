"""Merge findings_*.json into report.html.

Usage: python report.py
Reads config.json for the selection. `where` entries of the form <repo name>/<path>:<line>
become links to the default branch on GitHub.
"""
import glob
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date

cfg = json.load(open("config.json"))
repo_of = {s["name"]: s["repo"] for s in cfg["sources"]}
CHECKS = {"journey": "Reader journeys", "code": "Docs vs code", "overlap": "Overlap between sources",
          "structure": "Structure and links"}
SEV = ["High", "Medium", "Low"]
ENTRY_PAGE = re.compile(r"(README\.md|index\.md|getting[-_]started|newcomer|install|quickstart|setup|intro)", re.I)

findings, seen, bad_files = [], {}, []
for path in sorted(glob.glob("findings_*.json")):
    try:
        items = json.load(open(path))
    except json.JSONDecodeError:
        bad_files.append(path)
        continue
    for f in items:
        key = (f.get("check"), f.get("source"), f.get("title"))
        if key in seen:  # same problem reported twice: keep one, with every location
            seen[key]["where"] += [w for w in f.get("where", []) if w not in seen[key]["where"]]
            continue
        f.setdefault("severity", "Low")
        f.setdefault("where", [])
        f.setdefault("effort", "")
        f.setdefault("confidence", "")
        f["easy"] = f["effort"] == "small" and f["confidence"] == "confirmed"
        seen[key] = f
        findings.append(f)
findings.sort(key=lambda f: (list(CHECKS).index(f["check"]) if f["check"] in CHECKS else 9,
                             f.get("journey") or 0, f.get("source", ""),
                             SEV.index(f["severity"]) if f["severity"] in SEV else 9))
for i, f in enumerate(findings):
    f["id"] = f"f{i + 1}"


def journey_label(n):
    try:
        j = cfg["journeys"][int(n) - 1]
        return f"Journey {n}: {j['reader']}"
    except (TypeError, ValueError, IndexError):
        return f"Journey {n}"


def esc(s):
    return html.escape(str(s or ""))


def where_link(w):
    m = re.match(r"^([^/\s]+)/(.+?)(?::(\d+))?$", w)
    if w.startswith(("http://", "https://")):
        return f'<a href="{esc(w)}" target="_blank" rel="noopener">{esc(w)}</a>'
    if m and m.group(1) in repo_of:
        url = f"https://github.com/{repo_of[m.group(1)]}/blob/HEAD/{m.group(2)}" + (f"#L{m.group(3)}" if m.group(3) else "")
        return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(w)}</a>'
    return esc(w)


def linkify(s):
    s = esc(s)
    return re.sub(r"(https?://[^\s'\")\]<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)


counts = Counter((f["check"], f["severity"]) for f in findings)
summary_rows = "".join(
    f'<tr><th scope="row">{esc(CHECKS.get(c, c))}</th>'
    + "".join(f'<td class="num">{counts.get((c, s), 0) or "&middot;"}</td>' for s in SEV)
    + f'<td class="num total">{sum(counts.get((c, s), 0) for s in SEV)}</td></tr>'
    for c in CHECKS if c in cfg["checks"])

by_check = defaultdict(lambda: defaultdict(list))
for f in findings:
    key = journey_label(f["journey"]) if f["check"] == "journey" and f.get("journey") else f.get("source", "")
    by_check[f["check"]][key].append(f)

def tags(f):
    t = [x for x in (f.get("effort"), f.get("confidence")) if x]
    if f["easy"]:
        t.append("easy fix")
    return "".join(f' <span class="tag">{esc(x)}</span>' for x in t)


def short_where(f):
    w = f.get("where", [])
    return (where_link(w[0]) + (f' <span class="muted">+{len(w) - 1}</span>' if len(w) > 1 else "")) if w else ""


def item(f):
    return (f'<li><a class="sev sev-{esc(f["severity"]).lower()}" href="#{f["id"]}">{esc(f["severity"])}</a> '
            f'{esc(f["title"])} <span class="paths">{short_where(f)}</span></li>')


# Journey table: one row per journey-summary finding
journey_rows = ""
if "journey" in cfg["checks"]:
    summaries = {f.get("journey"): f for f in findings if f.get("rule") == "journey-summary"}
    for n, j in enumerate(cfg["journeys"], 1):
        sm = summaries.get(n)
        blockers = [f for f in findings if f["check"] == "journey" and f.get("journey") == n
                    and f.get("rule") != "journey-summary" and f["severity"] in ("High", "Medium")]
        outcome = (sm or {}).get("outcome") or ("not reviewed" if not sm else "see summary")
        oc = "stuck" if outcome.startswith("stuck") else ("gaps" if "gap" in outcome else "ok")
        anchor = journey_label(n).replace(" ", "-").replace(":", "")
        journey_rows += (f'<tr><td><a href="#{esc(anchor)}">{esc(j["reader"])}</a></td><td>{esc(j["goal"])}</td>'
                         f'<td><span class="outcome outcome-{oc}">{esc(outcome)}</span></td>'
                         f'<td class="num">{len(blockers) or "&middot;"}</td></tr>')

# Fix first: High findings ranked by reach
def rank(f):
    score = 0
    if f["check"] == "journey":
        score += 3
    if any(ENTRY_PAGE.search(w) for w in f.get("where", [])):
        score += 2
    if len(f.get("where", [])) >= 3:
        score += 1
    return -score


highs = sorted((f for f in findings if f["severity"] == "High" and f.get("rule") != "journey-summary"), key=rank)
fix_first = highs[:10]
fix_first_html = "".join(item(f) for f in fix_first)
more_high = f'<p class="muted">{len(highs) - len(fix_first)} more High findings in the sections below.</p>' if len(highs) > len(fix_first) else ""

# Easy fixes: small effort, confirmed
easy = sorted((f for f in findings if f["easy"] and f.get("rule") != "journey-summary"),
              key=lambda f: (SEV.index(f["severity"]) if f["severity"] in SEV else 9, f.get("source", "")))
easy_html = "".join(item(f) for f in easy)
untagged = sum(1 for f in findings if not f.get("effort") or not f.get("confidence"))

sections = []
for c in CHECKS:
    if c not in cfg["checks"]:
        continue
    groups = by_check.get(c, {})
    n = sum(len(v) for v in groups.values())
    body = []
    for src, items in groups.items():
        rows = []
        for f in items:
            wheres = f.get("where", [])
            shown = "".join(f"<li>{where_link(w)}</li>" for w in wheres[:8])
            more = f'<li class="muted">and {len(wheres) - 8} more</li>' if len(wheres) > 8 else ""
            ev = "".join(f"<li>{linkify(e)}</li>" for e in f.get("evidence", []))
            rows.append(f"""
<article class="finding" id="{f['id']}" data-sev="{esc(f['severity'])}" data-check="{esc(c)}" data-source="{esc(f.get('source', ''))}" data-easy="{'1' if f['easy'] else ''}">
  <header><span class="sev sev-{esc(f['severity']).lower()}">{esc(f['severity'])}</span>
  <h4>{esc(f['title'])}</h4><span class="rule">{esc(f.get('rule', ''))}{tags(f)}</span></header>
  <div class="detail">
    {f'<div><span class="label">Where</span><ul class="paths">{shown}{more}</ul></div>' if wheres else ''}
    {f'<div><span class="label">Evidence</span><ul>{ev}</ul></div>' if ev else ''}
    {f'<div><span class="label">Suggestion</span><p>{linkify(f.get("suggestion"))}</p></div>' if f.get('suggestion') else ''}
  </div>
</article>""")
        body.append(f'<div class="source-group"><h3 id="{esc(src).replace(" ", "-").replace(":", "")}">{esc(src)}</h3>{"".join(rows)}</div>')
    empty = '<p class="muted empty">Nothing found.</p>' if not n else ""
    sections.append(f'<section id="{c}"><h2>{esc(CHECKS[c])} <span class="count">{n}</span></h2>{empty}{"".join(body)}</section>')

source_opts = "".join(f'<option value="{esc(s["name"])}">{esc(s["name"])}</option>'
                      for s in cfg["sources"] if any(f.get("source") == s["name"] for f in findings))
groups_txt = ", ".join(cfg["groups"])
teams_txt = " and ".join(cfg["teams"])
warn = f'<p class="warn">Could not read: {esc(", ".join(bad_files))}</p>' if bad_files else ""

page = f"""<title>Chap Docs Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
<style>
:root {{
  --ground: #f6f7f5; --surface: #ffffff; --ink: #1c2320; --muted: #5d6762; --rule: #d9dfdb;
  --accent: #1f6a85; --high: #b42318; --high-bg: #fde8e6; --med: #9a5b00; --med-bg: #fdf0db;
  --low: #4f5b56; --low-bg: #e9edeb;
  --sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  --serif: "Source Serif 4", Georgia, serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --ground: #141917; --surface: #1c2220; --ink: #e4e9e6; --muted: #9aa49f; --rule: #2f3834;
    --accent: #6fb7d1; --high: #ff8a7e; --high-bg: #3a1d1a; --med: #f0b45c; --med-bg: #3a2c15;
    --low: #b5bfba; --low-bg: #26302c;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --ground: #141917; --surface: #1c2220; --ink: #e4e9e6; --muted: #9aa49f; --rule: #2f3834;
  --accent: #6fb7d1; --high: #ff8a7e; --high-bg: #3a1d1a; --med: #f0b45c; --med-bg: #3a2c15;
  --low: #b5bfba; --low-bg: #26302c;
}}
body {{ background: var(--ground); color: var(--ink); font: 15px/1.55 var(--sans); padding: 0 16px; }}
main {{ max-width: 980px; margin: 0 auto; padding-block: 32px 64px; display: grid; gap: 32px; }}
a {{ color: var(--accent); text-underline-offset: 2px; }}
a:focus-visible, select:focus-visible, input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
h1 {{ font: 600 2rem/1.15 var(--serif); margin: 0; text-wrap: balance; }}
h2 {{ font-size: 1.25rem; margin: 0 0 12px; display: flex; gap: 10px; align-items: baseline; }}
h3 {{ font: 500 .85rem var(--mono); color: var(--muted); margin: 20px 0 8px; }}
h4 {{ font-size: 1rem; font-weight: 500; margin: 0; flex: 1 1 20rem; text-wrap: pretty; }}
.lede {{ color: var(--muted); max-width: 65ch; margin: 8px 0 0; }}
.count {{ font: 500 .85rem var(--mono); color: var(--muted); }}
.muted {{ color: var(--muted); }}
.warn {{ color: var(--high); }}
.table-wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; min-width: 420px; background: var(--surface); border: 1px solid var(--rule); }}
th, td {{ padding: 8px 14px; border-bottom: 1px solid var(--rule); text-align: left; }}
thead th {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); font-weight: 500; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; font-family: var(--mono); }}
td.total {{ font-weight: 500; }}
.filters {{ display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; padding: 12px 0;
  border-block: 1px solid var(--rule); position: sticky; top: env(safe-area-inset-top, 0px); background: var(--ground); z-index: 1; }}
.filters label {{ display: inline-flex; gap: 6px; align-items: center; font-size: .9rem; }}
.filters select {{ font: inherit; padding: 4px 8px; background: var(--surface); color: var(--ink); border: 1px solid var(--rule); border-radius: 4px; }}
.finding {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }}
.finding header {{ display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: baseline; }}
.sev {{ font: 500 .72rem var(--mono); text-transform: uppercase; letter-spacing: .05em; padding: 2px 8px; border-radius: 999px; }}
.sev-high {{ color: var(--high); background: var(--high-bg); }}
.sev-medium {{ color: var(--med); background: var(--med-bg); }}
.sev-low {{ color: var(--low); background: var(--low-bg); }}
.rule {{ font: .78rem var(--mono); color: var(--muted); }}
.detail {{ display: grid; gap: 8px; margin-top: 8px; font-size: .9rem; }}
.detail ul {{ margin: 2px 0 0; padding-left: 18px; }}
.detail p {{ margin: 2px 0 0; max-width: 75ch; }}
.paths {{ font: .82rem var(--mono); overflow-wrap: anywhere; }}
.label {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }}
.empty {{ margin: 0; }}
.top {{ display: grid; gap: 10px; }}
.top h2 {{ margin: 0; }}
.top .lede {{ margin: 0; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 24px; margin: 0; font-size: .9rem; }}
.legend div {{ display: flex; gap: 8px; align-items: baseline; }}
.legend dd {{ margin: 0; color: var(--muted); }}
.tag {{ font: .72rem var(--mono); color: var(--muted); border: 1px solid var(--rule); border-radius: 4px; padding: 0 5px; margin-left: 6px; }}
.list {{ margin: 0; padding-left: 22px; display: grid; gap: 6px; }}
.list li {{ text-wrap: pretty; }}
.list .sev {{ text-decoration: none; margin-right: 4px; }}
.list .paths {{ display: block; }}
.outcome {{ font: 500 .78rem var(--mono); white-space: nowrap; }}
.outcome-ok {{ color: var(--accent); }}
.outcome-gaps {{ color: var(--med); }}
.outcome-stuck {{ color: var(--high); }}
.finding:target {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
</style>
<main>
  <header>
    <h1>Documentation review</h1>
    <p class="lede">{esc(teams_txt.capitalize())} documentation, {date.today().isoformat()}. Groups: {esc(groups_txt)}.
    {len(cfg['sources'])} repos{f", {len(cfg['journeys'])} reader journeys" if 'journey' in cfg['checks'] else ''}.
    Paths link to the default branch on GitHub.</p>
    {warn}
  </header>
  {f"""<section class="top">
    <h2>Reader journeys</h2>
    <p class="lede">A reviewer followed the docs as each reader would, without running anything. Stuck means the goal cannot be reached from the docs.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Reader</th><th>Goal</th><th>Outcome</th><th>Blockers</th></tr></thead>
      <tbody>{journey_rows}</tbody>
    </table></div>
  </section>""" if journey_rows else ""}
  <section class="top">
    <h2>All findings</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Check</th><th>High</th><th>Medium</th><th>Low</th><th>Total</th></tr></thead>
      <tbody>{summary_rows}</tbody>
    </table></div>
    <dl class="legend">
      <div><dt class="sev sev-high">High</dt><dd>a reader who follows the docs fails or gets a wrong result</dd></div>
      <div><dt class="sev sev-medium">Medium</dt><dd>misleading or out of date, but a careful reader recovers</dd></div>
      <div><dt class="sev sev-low">Low</dt><dd>worth tidying</dd></div>
    </dl>
    <p class="lede">Severity is impact on the reader. Each finding also carries <span class="tag">effort</span> (small, medium, large) and <span class="tag">confidence</span> (confirmed against code or a live resource, or likely from reading).</p>
  </section>
  {f"""<section class="top">
    <h2>Fix first <span class="count">{len(fix_first)}</span></h2>
    <p class="lede">High findings with the widest reach: journey blockers, entry pages, and the same problem in several places.</p>
    <ol class="list">{fix_first_html}</ol>{more_high}
  </section>""" if fix_first else ""}
  <section class="top">
    <h2>Easy fixes <span class="count">{len(easy)}</span></h2>
    <p class="lede">Small effort and confirmed against the code or a live resource: a one-place edit with a known correct value.{f" {untagged} findings have no effort or confidence set and are not listed." if untagged else ""}</p>
    {f'<ol class="list">{easy_html}</ol>' if easy else '<p class="muted empty">None.</p>'}
  </section>
  <div class="filters">
    <label><input type="checkbox" id="f-high" data-sev="High" checked> High</label>
    <label><input type="checkbox" id="f-medium" data-sev="Medium" checked> Medium</label>
    <label><input type="checkbox" id="f-low" data-sev="Low" checked> Low</label>
    <label><input type="checkbox" id="f-easy"> Easy fixes only</label>
    <label>Source <select id="f-source"><option value="">All</option>{source_opts}</select></label>
  </div>
  {"".join(sections)}
</main>
<script>
const boxes = [...document.querySelectorAll('.filters input[type=checkbox]')];
const sourceSel = document.getElementById('f-source');
const easyBox = document.getElementById('f-easy');
function apply() {{
  const sev = new Set(boxes.filter(b => b.checked && b.dataset.sev).map(b => b.dataset.sev));
  const src = sourceSel.value;
  document.querySelectorAll('.finding').forEach(el => {{
    el.hidden = !sev.has(el.dataset.sev) || (src && el.dataset.source !== src) || (easyBox.checked && !el.dataset.easy);
  }});
  document.querySelectorAll('.source-group').forEach(g => {{
    g.hidden = ![...g.querySelectorAll('.finding')].some(el => !el.hidden);
  }});
}}
boxes.forEach(b => b.addEventListener('change', apply));
sourceSel.addEventListener('change', apply);
</script>
"""
open("report.html", "w").write(page)
by_sev = Counter(f["severity"] for f in findings)
print(f"report.html: {len(findings)} findings ("
      + ", ".join(f"{s}={by_sev.get(s, 0)}" for s in SEV) + f"), {len(easy)} easy fixes"
      + (f", {untagged} without effort/confidence" if untagged else "") + (f"; unreadable: {bad_files}" if bad_files else ""))
