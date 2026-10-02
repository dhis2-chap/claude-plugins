---
name: jira-audit
description: Use when the user wants to audit, clean up or sanity-check CLIM Jira against what has actually been done in the chap repos: wrong statuses (done but open, In Review without a PR, stale In Progress), outdated epic/issue descriptions, duplicates, missing components. Produces a shareable HTML report with tiered proposed changes and applies the ones the user approves. Triggers on "audit jira", "go through jira", "check jira against PRs", "jira cleanup", "sprint audit", "apply tier 1".
---

# Jira audit

Compare Jira with the code and report what is wrong, with evidence. The run is
read-only until the user names what to apply. Everything below is a plan the
scripts and reference briefs make concrete; do not improvise a lighter version.

Scripts live in `scripts/` next to this file; briefs in `reference/`. Read
`reference/rules.md` once per session so findings use the same rule ids and tiers.

## Requirements

- **Atlassian MCP** (`mcp__atlassian__*` tools). This skill does not use acli. If the
  tools are missing, stop and tell the user to connect the Atlassian MCP first.
- `gh` authenticated with access to the GitHub org.
- `uv` (for `dups.py`, which needs scikit-learn).
- A scratch directory for the run: use the session scratchpad if there is one, else
  `mktemp -d`. Call it `WORKDIR` below. Subagents all write there; every helper file
  gets a unique prefix.

## 0. Ask, then set config

Ask in one `AskUserQuestion` call unless the user already said it:

1. **Scope**: `sprint` (default) = the active sprint plus the most recently closed one,
   or `all` = every open issue in the components.
2. **Components** (multi-select; default `Chap Modeling Platform`, `Modeling App`, `Modeling`).
   Offer the others from `listJiraProjectComponents` (via `discover` + `executeRead`).
3. **Repos**: default code repos `chap-core, chap-frontend, chapkit, model-marketplace,
   chap-checker`; supporting repos `chap-site, climate-sre`. Offer to add or drop.

Then resolve the rest without asking:

- `cloudId` from `getAccessibleAtlassianResources` (dhis2.atlassian.net).
- Sprint names for scope `sprint`: `discover` "list sprints for board", board `686`,
  take the active sprint and the latest closed one.
- Snapshot time: `date -Iseconds` now.

Write `WORKDIR/config.json`:

```json
{
  "cloud_id": "...", "jira_url": "https://dhis2.atlassian.net", "project": "CLIM",
  "components": ["Chap Modeling Platform", "Modeling App", "Modeling"],
  "scope": "sprint", "sprints": ["<active>", "<last closed>"],
  "org": "dhis2-chap",
  "code_repos": ["chap-core", "chap-frontend", "chapkit", "model-marketplace", "chap-checker"],
  "support_repos": ["chap-site", "climate-sre"],
  "snapshot": "<ISO timestamp>", "stale_days": 28,
  "done_statuses": ["Done", "Closed"],
  "todo_statuses": ["Backlog", "To Do", "Selected for Development"],
  "keywords": ["chap", "chap-core", "chapkit", "modeling app", "modelling app", "modeling platform", "backtest", "prediction", "evaluation", "model template", "marketplace", "benchmark"],
  "umbrella_labels": ["ch-initiative"],
  "gh_logins": {"ivar": ["ivargr"], "Knut Dagestad Rand": ["knutdrand"], "Edvin Aamot Stava": ["edvinstava"], "Morten Hansen": ["mortenoh"], "Boris Simovski": ["bsimovski"], "Eirik Haugstulen": ["eirikhaugstulen"], "Abyot Asalefew Gizaw": ["abyot"]}
}
```

Copy `scripts/*.py` into `WORKDIR` so everything runs from one directory.

Tell the user what will happen and roughly how long: a sprint run is 2-3 reviewer
subagents and about 10 minutes; a full run of ~200 open issues is 7-8 subagents and
about 20 minutes.

## 1. Snapshot (parallel)

Launch, in one message:

- **Jira subagents**, one per slice from `reference/subagent-snapshot.md`. Scope does
  not change the snapshot: always fetch open and done issues for every component
  (done ones feed the duplicate and epic checks), the open no-component issues, and
  the project-wide summaries. Typical: 4 subagents.
- **PRs**, yourself in Bash, for every code and supporting repo:
  `gh pr list --repo ORG/REPO --state all --limit 3000 --json number,title,body,state,mergedAt,closedAt,createdAt,updatedAt,headRefName,author,url > WORKDIR/pr_REPO.json`
- **Clones**, shallow, into `WORKDIR/repos/`:
  `git -c credential.helper='!gh auth git-credential' clone -q --depth 1 https://github.com/ORG/REPO.git`
  (HTTPS; SSH may need a hardware key touch and hang). For repos that push straight to
  main (no PRs), also `gh api repos/ORG/REPO/commits?per_page=100 --paginate` into
  `commits_REPO.jsonl` with `{sha, date, msg}` per line.

When every subagent has reported, check line counts against
`searchResultMode: "count"` for each slice. A mismatch means a page was lost: rerun that slice.

## 2. Link, check, candidates, batches

```
cd WORKDIR
python3 link.py
python3 checks.py
uv run --with scikit-learn python dups.py
python3 batches.py
```

`batches.py` prints how many reviewer batches the scope produced. If it is more than
8, tell the user and offer to narrow the scope rather than launching more.

## 3. Review (parallel subagents)

Fill the placeholders in `reference/subagent-review.md` and `reference/subagent-dups.md`,
write them to `WORKDIR/REVIEW_BRIEF.md` and `WORKDIR/DUPS_BRIEF.md`, and launch one
subagent per batch plus one for duplicates, all in one message. Do not do their work
yourself while waiting, and do not read their transcripts; wait for the hand-backs.

Each hand-back reports counts and problems only. If one reports MCP or gh errors, rerun
that batch before merging.

## 4. Merge, verify, report

```
python3 merge.py
python3 report.py --save
```

Before publishing, re-check every tier-1 and High-confidence transition against live
Jira with one JQL `key in (...)` and `fields: ["status"]`. Any issue whose status
changed since the snapshot is dropped from the proposed changes (edit `merged.json`,
rerun `report.py --save`). Spot-read two or three High findings' evidence yourself.

Publish `WORKDIR/report.html` as an artifact (load the `artifact-design` skill first,
title `CLIM Sprint Audit` or `CLIM Jira Audit`, icon `clipboard`). The artifact starts
private; sharing is done from the page's Share menu, say so. Also keep the local
`report.html` path in the reply for people who want the file.

Reply with: the link, the counts per category, how many tier-1 items there are, three
to five notable findings in one line each, and what you re-checked. Offer "apply tier 1"
or IDs. Do not paste the whole findings list.

## 5. Apply (only on request)

Follow `reference/apply.md`. The user names a tier or IDs; nothing else is touched.
Every change gets a short Jira comment with the evidence and the audit date, and the
touched issues are re-read afterwards.

## Rerunning

History lives in `~/.cache/chap-jira-audit/`. With `--save`, `report.py` marks
findings not seen in the previous run as `new` and lists resolved ones in the header.
Delete `latest.json` there to start fresh.

## Principles

- Every finding cites evidence a reader can open: a PR URL, a `file:line` on master,
  or a quote from the issue. No evidence, no finding.
- Neutral wording about tickets, never about people. The report is shared with the team.
- A count is never enough for a transition. Reviewers read the PR against the issue
  text, and umbrella epics stay open.
- Read-only until the user says what to apply; then one issue at a time, each verified.
