---
name: sprint-review
description: Produce the end-of-sprint review reports for the CLIM team, one for Chap and one for Data — what got done and how it serves the 6-month objectives, unplanned work, unfinished and languishing items, demo candidates, and improvement suggestions. Use when asked for a "sprint review", "sprint report", "what did we get done this sprint", or the Friday report for the Monday meeting.
---

# Sprint review report

Run Friday end of day; the team goes through it in the Monday meeting. Sprints are 2 weeks. The report is a **draft for me** — never post it to Jira, Confluence or Slack without my OK.

## 0. Two reports: Chap and Data

Produce **one report per group**, split by Jira component:

| Report | Components |
|---|---|
| **Chap** | Modeling App, Modeling, ChapKit, Chap Modeling Platform |
| **Data** | Geo Service (formerly Climate Service), Climate Tools, Climate App |

- **Geo Service** = Open Geo Service (formerly OCS / Open Climate Service; renamed Nov 2026). Its epics use the O2 label `ch-obj-open-geo-service`.
- **Single-component report**: when I ask for a report for one component (e.g. "Geo Service"), produce only that report, scoped to that component, in `reports/sprint-review-<YYYY-MM-DD>-<component-slug>.md`. Same sections and rules.

- If an issue has no component, use its epic's components.
- An issue with components from both groups goes in **both** reports and is listed under "Cross-team".
- **Ignore issues with the CAPS component for now**: leave them out of both reports entirely, including Cross-team. (Mentions of CAPS inside Chap or Data issues are fine.)
- Issues in neither group (e.g. Maps App, Other, or no component at all) go in neither report's numbers. Mention any that are languishing or blocking under "Cross-team".
- An epic follows the same rule: components from both groups → it appears in both reports' epic checklist.
- All sections cover that group only, except section 9 ("Cross-team"), which is the same in both reports: dependencies, shared items, overlaps, and work that falls between the groups.

## 1. Gather data

- **Sprint**: the active sprint on CLIM board 686 (or the sprint I name). If the dashboard is running, `GET http://localhost:3001/api/sprint-data?sprintId=<id>` already returns completed / incomplete / added-mid-sprint keys (via the GreenHopper sprint report). Otherwise use the Jira MCP / REST API directly; see `server.js` for the API quirks.
- **Per issue**: summary, type, status, assignee, epic (`customfield_10014` or `parent`), components (for the Chap / Data split), created date, and the **changelog** (status transitions and Sprint field changes) — needed for the languishing checks.
- **6-month objectives**: from the link in `CLAUDE.md`. If it's missing or stale, say so in the report and ask me; don't invent objectives.
- Epics are the bridge from issues to objectives. Map issue → epic → objective; flag issues with no epic.
- **Work outside the sprint**: JQL `project = CLIM AND issuetype != Epic AND status CHANGED DURING ("<sprint start>", "<sprint end>")`, from the exact sprint start time, minus every issue that was in the sprint at any point: all GreenHopper sets (including removed) and issues whose Sprint field lists this sprint. Don't use "issues fetched for the report" as the sprint list, since epic children get fetched too. For each: status changes inside the sprint window (changelog), epic, components (epic's if none). Apply the same Chap / Data / CAPS split.
- **Epics closed during the sprint**, whether or not they were in the sprint: JQL `project = CLIM AND issuetype = Epic AND status CHANGED TO (Done, Closed) DURING ("<previous sprint's complete time>", "<sprint end>")` (from the previous sprint's close, so epics closed between sprints aren't missed). For each, get the description (find its "Done when" section), components, when and to which status it was closed (changelog), current status (it may have been reopened), and its child issues with their statuses (`parent = <key>`).

## 2. Report sections

1. **Headline** (3–5 bullets): the group's sprint in one glance. Include how many epics were closed and how many had a "Done when".
2. **Epics in this sprint, by objective.** The report's main section: every epic with at least one item in the sprint, grouped under its **main objective**.
   - **Main objective**: the objective the objectives page lists the epic under (first one if several); otherwise its first `ch-obj-*` label that's on the page. Other objectives it serves go in the Epic cell as `<br>_also O5_`. Flag labels that aren't on the objectives page, and epics the page lists but that have no label.
   - One `### O4 <name> (`ch-obj-model-quality`)` heading per objective, in order O1–O8, with a line `n epics · n items done`. Objectives with no epic get one line: "No epic in the sprint has this as its main objective." **Exception, Data / Geo Service reports:** show only objectives that have at least one epic in the sprint (most objectives are Chap-focused), with one line at the top of the section naming the objectives left out (e.g. "Not in this sprint: O1, O3–O6, O8"). Then `### No objective` (epics without one), then `### No epic`: a short summary of sprint items with no epic (done / open bullets), since they need an epic or a decision that they don't.
   - Table columns: Epic | Time in progress | This sprint | What moved | Flags.
     - **Epic**: key link + title.
     - **Time in progress**: weeks since the epic first moved to In Progress / In Review (epic changelog). If it never did, use the first time one of its child issues started, and say so in the section intro. For a Done epic, count until it was done. Show one `■` per week (rounded to the nearest week, at least 1, at most 12, then `+`), each block wrapped in `<span style="color:…">` with a colour that gets more intense each week: `#fde2c4, #fcc896, #fbab68, #f88d3e, #f06e1e, #dc5414, #c03f0e, #a1300b`, then `#7f2408` from week 9 on. Follow the blocks with `n wk` (`<1 wk` under a week). Explain the bar in one line under the section heading, with a 1-week and a 9-week example.
     - **This sprint**: `done of in sprint`, with `(+n)` for items that came in after day 1. Don't count items removed from the sprint; mention them under Flags instead.
     - **What moved**: 1–3 bullets as `• item<br>• item`, with Jira links.
     - **Flags**: `✅ Done <date>`; red `no "Done when"` (same red style as section 3); `⚠ all child issues done, epic still open`; `⚠ epic still in Backlog` (when work has started); items not started; items removed from the sprint; `—` if none.
   - Don't show child-issue counts or progress as a percentage of tasks; time in progress is the measure.
3. **Epics marked Done or Closed: verify together.** The team's rule: no epic is Done until the team has checked its "Done when" together. The team does the checking **in Jira**, so this section is only a list, not a checklist. Open with a short reminder of the rule and of Done vs Closed, then three lists:
   - `**Done** (n)`: one bullet per epic, key link + title. If the epic has **no "Done when"** section, show the whole line in red with a marker: `🔴 <span style="color:red">[CLIM-123](…) Title — no "Done when"</span>`.
   - `**Closed** (n)`: one bullet per epic, key link + title, then "— reason recorded" if a comment explains the closing (see `CLAUDE.md`: Done = completed, Closed = decided not to do it). If there's no such comment, use the same red style with "— no reason for closing recorded".
   - `**Ready to close?** (n)`: open epics (with items in the sprint or not) whose child issues are all done. Same line format, red if there's no "Done when". One line above saying: check the "Done when" together, then mark it Done.
   - Don't list criteria, child-issue counts or proposed checks. Epics outside both groups go under Cross-team (CAPS epics are ignored, see above).
4. **Unplanned work**: issues added after sprint start. Section 2 already shows how many landed in each epic (+n), so here only cover the bigger new streams as a table: Stream | Source | Why now. For each: what it was, who/where it came from (leadership, collaborator, other DHIS2 team, bug), and *why it was important to do now* — take this from the issue description/comments; if it isn't recorded, say "reason not recorded" rather than guessing. Note what it likely displaced.
5. **Worked on outside the sprint**: issues from the "work outside the sprint" query. This work is invisible in the sprint numbers, so it gets its own section.
   - **Done or started**: table Issue | Epic | Change (`Backlog → Done, 6 Nov`). Group several issues from the same epic that moved together in one row. Note when items went straight from Backlog to Done (tracked after the fact) or many moved in the same minute (bulk clean-up).
   - **Closed (not done)**: one bullet per epic with the issue links and a short note (e.g. closed with the epic, had sat In Progress since an earlier sprint). This is housekeeping, not delivered work; never count it as done.
   - Flag an epic marked Done while a large share of its children were Closed: its scope was dropped, not delivered, so the team should check its "Done when" with that in mind.
   - Add a headline bullet with the counts (done, started, closed).
6. **Not finished**: incomplete issues, with status and a one-line reason if visible.
7. **Languishing** — flag any issue that:
   - has been in **more than 3 sprints** (count distinct sprints in the Sprint field history), or
   - has been in an **In Progress / In Review** status for **more than 6 weeks** (cumulative, from the changelog).
   Show sprint count / weeks-in-status, assignee, and a suggested action (split, unblock, re-scope, drop, pair up).
8. **Demo candidates**: 2–4 items that make a good demo — user-visible, finished, explainable in ~5 minutes, interesting to people outside the team. Skip refactors, infra, dependency bumps and half-finished UI. Say in one line why each is a good pick and who'd present it.
9. **Cross-team** (same text in both reports): dependencies one group is waiting on, items shared by both groups, duplicated work, items that fell between the groups or outside both, one group getting most of the attention.
10. **Suggestions for next sprint**: 3–5 concrete, actionable suggestions (e.g. finish X before pulling new work, close or re-scope a languishing item, route a recurring side-request into the backlog, rebalance attention to an objective with no progress). These feed sprint planning.

## 3. Output

- Write the two reports to `reports/sprint-review-<YYYY-MM-DD>-chap.md` and `reports/sprint-review-<YYYY-MM-DD>-data.md` (Friday's date), and give me a short summary of each in chat.
- Link Jira keys with a hover title giving the issue type and summary: `[CLIM-123](https://dhis2.atlassian.net/browse/CLIM-123 "Task: Add a model promotion checklist")`. Every link gets one, including short range links like `[1629]`. In the title, replace `"` with `'` and `|` with `/` so the link and tables don't break.
- **People matters stay private**: report on work, not on individuals' performance. No personal details.
- Keep it scannable — it's read aloud in a meeting. Tables for lists, bullets for the rest.
