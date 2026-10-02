# Reviewer subagent brief

Write this to `{workdir}/REVIEW_BRIEF.md` with the placeholders filled, then launch
one subagent per `batch_<n>.json` with the prompt: "Read `{workdir}/REVIEW_BRIEF.md`
and follow it exactly for batch N=<n>. Everything is read-only."

---

You are auditing a batch of open Jira issues against what has actually happened in
code. READ-ONLY: never transition, edit, comment on or link anything in Jira, and do
not push or change anything in git.

## Where things are

Work dir: `{workdir}`

- `batch_<N>.json`: your issue keys (`issues`) and the open epics to review (`epics`).
- `jira.json`: dict key → snapshot record (summary, status, type, parent, assignee,
  dates, components, links, sprints, first 300 chars of description). Load with
  Python and look up your keys; do not cat the whole file.
- `links.json`: dict key → PRs referencing it (`{repo, number, title, state, mergedAt,
  url, author, partial}`). `partial: true` means the PR text said "part of", "first step" etc.
- `unlinked_prs.json`: PRs with no issue reference (`{repo, number, title, state,
  mergedAt, url, branch, body[:400]}`).
- `findings_mechanical.json`: what the rule script flagged (S1-S5, E1-E2, C1, H*).
  Hints only; you confirm, refute or refine.
- `commits_<repo>.jsonl` where present: commit log of repos that push straight to main.
- Shallow clones of master for every repo under `{repos_dir}/<repo>/`. Use grep there
  to verify claims in descriptions.

GitHub repos are `{org}/<repo>`. Use `gh pr view <n> --repo {org}/<repo> --json
title,body,files,mergedAt,state` and `gh pr diff` when you need detail.

Jira MCP: first run ToolSearch with query `select:mcp__atlassian__getJiraIssue`.
cloudId is `{cloud_id}`. Use `getJiraIssue` with `view: "evidence"` to read the full
description (the snapshot only has 300 chars). For comments, `getJiraIssue` with
`view: "full"` and `fields: ["comment"]`. Fetch comments only when a verdict depends
on them.

Today is {today}. Stale threshold is {stale_days} days. Statuses: {statuses}.

## For each issue in `issues`

1. Read the full issue.
2. **Status against PRs.**
   - If `links.json` has PRs: open each merged PR (title, body, files) and decide
     whether together they deliver what the issue asks for: ALL of it (→ should be
     Done), PART of it (stays open; say what is left), or the PR only mentions it
     (no status change).
   - S6, always: search `unlinked_prs.json` and the master clone for the issue's key
     terms (feature names, endpoints, CLI commands, file names). If a merged PR or
     commit clearly delivered the work without citing the key, report it with the
     URL, confirmed in the files changed, not just the title.
   - "In Review" needs an OPEN PR; "In Progress" needs activity within the stale
     threshold.
3. **Description.**
   - D1 outdated/wrong: concrete claims (file paths, module names, endpoints, CLI
     commands, config keys, chosen approach, "currently X does Y") that no longer
     match master or merged PRs. Check with grep in the clones. Docs repos show
     documented behaviour; infra repos show deployment reality.
   - D2 thin: empty, or no goal / no definition of done.
   - D3 superseded: a later issue, PR or decision replaced the approach; say which.
   Only flag D1/D3 with evidence (a `file:line` on master, a PR URL, or a quote from
   another issue). Do not flag style.
4. If the issue clearly belongs under a different epic, say so (`relink_epic`); do
   not hunt for it.

## For each epic in `epics`

Read the epic and list its children (ToolSearch
`select:mcp__atlassian__searchJiraIssuesUsingJql`, JQL `parent = KEY`). E3: does the
epic's description still describe what its children do? Flag if the goal changed,
the scope text is stale, or most children are about something else. Apply D1/D2/D3
to the epic text itself. An epic that calls itself a placeholder or umbrella stays
open even if every child is Done.

## Output

`findings_batch_<N>.json`: a JSON list, one object per finding (an issue can have
several; a clean issue has none):

```json
{
  "key": "{project}-123",
  "rule": "S1|S2|S3|S5|S6|D1|D2|D3|E3|RELINK",
  "title": "one line, what is wrong",
  "evidence": ["https://github.com/{org}/<repo>/pull/600 (merged 2026-08-01) adds X", "<repo>/path/file.py:42 shows Y", "issue says: '...'"],
  "suggested_action": "transition:Done | transition:In Progress | transition:Backlog | edit_description | relink_epic:KEY | none",
  "proposed_text": "for edit_description only: the specific sentence(s) to change or add, short, not a rewrite",
  "confidence": "High | Medium | Low",
  "note": "optional: what remains, caveats"
}
```

`clean_batch_<N>.json`: the keys you reviewed and found nothing to report on.

Confidence: High = direct evidence and no other sensible reading. Medium = strong
evidence, someone with context should confirm. Low = worth a glance.

Tone: neutral, about the ticket, never about a person. Not "X forgot to"; write
"merged in #n, status still Backlog".

Budget: roughly 2-5 tool calls per issue. Do not read entire repos. Name any helper
script `batch<N>_*.py`. Validate the JSON files parse before finishing.

Reply with only: counts per rule, number of clean issues, and any problems. Do not
paste findings in the reply.
