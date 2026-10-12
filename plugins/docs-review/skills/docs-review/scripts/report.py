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
CHECKS = {"code": "Docs vs code", "overlap": "Overlap between sources", "journey": "Reader journeys",
          "structure": "Structure and links"}
SEV = ["High", "Medium", "Low"]

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
        seen[key] = f
        findings.append(f)
findings.sort(key=lambda f: (list(CHECKS).index(f["check"]) if f["check"] in CHECKS else 9,
                             f.get("source", ""), SEV.index(f["severity"]) if f["severity"] in SEV else 9))


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
    by_check[f["check"]][f.get("source", "")].append(f)

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
<article class="finding" data-sev="{esc(f['severity'])}" data-check="{esc(c)}" data-source="{esc(src)}">
  <header><span class="sev sev-{esc(f['severity']).lower()}">{esc(f['severity'])}</span>
  <h4>{esc(f['title'])}</h4><span class="rule">{esc(f.get('rule', ''))}</span></header>
  <div class="detail">
    {f'<div><span class="label">Where</span><ul class="paths">{shown}{more}</ul></div>' if wheres else ''}
    {f'<div><span class="label">Evidence</span><ul>{ev}</ul></div>' if ev else ''}
    {f'<div><span class="label">Suggestion</span><p>{linkify(f.get("suggestion"))}</p></div>' if f.get('suggestion') else ''}
  </div>
</article>""")
        body.append(f'<div class="source-group" data-source="{esc(src)}"><h3>{esc(src)}</h3>{"".join(rows)}</div>')
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
</style>
<main>
  <header>
    <h1>Documentation review</h1>
    <p class="lede">{esc(teams_txt.capitalize())} documentation, {date.today().isoformat()}. Groups: {esc(groups_txt)}.
    {len(cfg['sources'])} repos{f", {len(cfg['journeys'])} reader journeys" if 'journey' in cfg['checks'] else ''}.
    Paths link to the default branch on GitHub.</p>
    {warn}
  </header>
  <div class="table-wrap"><table>
    <thead><tr><th>Check</th><th>High</th><th>Medium</th><th>Low</th><th>Total</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table></div>
  <div class="filters">
    <label><input type="checkbox" id="f-high" data-sev="High" checked> High</label>
    <label><input type="checkbox" id="f-medium" data-sev="Medium" checked> Medium</label>
    <label><input type="checkbox" id="f-low" data-sev="Low" checked> Low</label>
    <label>Source <select id="f-source"><option value="">All</option>{source_opts}</select></label>
  </div>
  {"".join(sections)}
</main>
<script>
const boxes = [...document.querySelectorAll('.filters input[type=checkbox]')];
const sourceSel = document.getElementById('f-source');
function apply() {{
  const sev = new Set(boxes.filter(b => b.checked).map(b => b.dataset.sev));
  const src = sourceSel.value;
  document.querySelectorAll('.finding').forEach(el => {{
    el.hidden = !sev.has(el.dataset.sev) || (src && el.dataset.source !== src);
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
      + ", ".join(f"{s}={by_sev.get(s, 0)}" for s in SEV) + ")" + (f"; unreadable: {bad_files}" if bad_files else ""))
