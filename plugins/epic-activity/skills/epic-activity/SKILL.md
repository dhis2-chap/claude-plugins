---
name: epic-activity
description: Check whether a CLIM Jira epic is actually being worked on, using real evidence (merged/open PRs in the dhis2-chap repos and Jira changelogs) instead of Jira statuses alone. Gives a timeline of when work happened and a short verdict on recent activity. Use when asked "has this epic been worked on", "is CLIM-123 active", "when was this epic last worked on", "is this epic stale", or "epic activity for CLIM-123". Requires the Atlassian MCP connector and the gh CLI.
metadata:
  internal: true
---

# Epic activity check

Answers one question: **has this epic actually been worked on, and is it active now?** Jira statuses are bookkeeping, so compare them with what landed in code.

Input: one or more epic keys (e.g. `CLIM-1349`). If none was given, ask. Default "recent" = the last 14 days (one sprint). Use today's date.

Read-only. Never edit Jira or comment on PRs.

## 1. Epic and children (Jira)

- Fetch the epic: summary, description (note the **Done when** criteria), status, created, and comments.
- Children: JQL `parent = <EPIC> ORDER BY created ASC` with fields `summary, status, assignee, created, updated, statuscategorychangedate, resolutiondate, customfield_10020` (sprints).
- Also note issues the description names as building on or depending on this epic (e.g. "builds on CLIM-1679"), and any "is blocked by" links. Fetch their status.

## 2. Jira changelogs (where the dates matter)

For children that are open, or that closed in the last ~4 weeks, fetch the issue with `expand=changelog` and record:
- Status transitions with dates. Flag items that **skip In Progress** (Backlog → Done), which were logged after the fact.
- Sprint carry-overs (the same item rolled into 3+ sprints).
- Changes that are only bookkeeping (labels, rank, sprint, `SprintCount` automation). These are **not** activity.
- Items **created and resolved within a few hours**: logged after the work was done.

## 3. Code evidence (GitHub)

For the epic key and each child key:

```bash
gh search prs "CLIM-<n>" --owner dhis2-chap --json repository,number,title,state,createdAt,closedAt,updatedAt \
  --jq '.[] | "\(.repository.name)#\(.number) \(.state) created \(.createdAt[:10]) closed \(.closedAt[:10] // "-") \(.title)"'
```

Search results match text, so drop PRs that mention a key only in passing or come from an unrelated epic.

Then look for **untagged** related work: list PRs created in the epic's active window in the likely repos (chap-core, chapkit, chap-frontend, chap-site, open-climate-service, …) and grep titles for the epic's topic keywords. Mark these as "likely related", not confirmed.

If a child links to a Google Doc or Confluence page as its main output, say that its edit history was not checked (or check it if a Drive/Confluence tool is available).

## 4. Output (brief)

1. **Verdict first**, one or two lines: active / tapering / stalled / never started, plus the date of the last real work.
2. **When work actually happened**: bursts by date range, each with the PRs or changes behind it. Short bullets.
3. **Jira vs reality**: skipped In Progress, items marked Done long after their PRs merged, Done items whose PR is still open, carry-overs, and work that only exists as bookkeeping.
4. **What's left**: untouched children (with how long), an unassigned spike, blockers and their status, and how far the **Done when** criteria are met.
5. One suggested next step (e.g. close the epic, pull X into the sprint, ask the assignee about the blocker).

Rules:
- Do not count Closed (decided not to do) as delivered.
- Do not judge people. Describe the work, not individuals' effort.
- Keep it short; tables only for timelines with 5+ rows.
