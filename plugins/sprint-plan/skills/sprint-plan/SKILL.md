---
name: sprint-plan
description: Draft the start-of-sprint email to the head of the project — a very brief, non-technical summary of what the CLIM team (Chap and Geo Service) is working on this sprint. Use when asked for the "sprint plan email", "email about the new sprint", or "what are we doing this sprint" for leadership.
---

# Sprint plan email

Sent after sprint planning: **Chap plans Monday, Geo Service plans Tuesday**. Run it Tuesday after Geo Service planning. The email is a **draft for me** — never send it.

## Rules

- **Very, very brief.** One line per item. No intro paragraph, no closing summary.
- **Non-technical.** Written for the head of the project: what users get or why it matters, not how. No library, repo, file or API names. No Jira jargon.
- Report on work, not people. No names of team members.

## Gather

Active sprint on CLIM board 686 (or the one I name): Jira MCP or REST (`/rest/agile/1.0/sprint/<id>/issue`, credentials in `.env`, see `server.js`). Ignore CAPS-only items.

- **Chap** (components Modeling App, Modeling, ChapKit, Chap Modeling Platform): every **epic** that is in the sprint or has a child item in it. Read each epic's description (Goal / Why / Done when).
- **Geo Service** (component Geo Service): the user-facing items are **User Stories**, not epics. Use the User Stories in the sprint. Read each description (user story / Goal).
- Being in the sprint is what counts. Ignore status (a Backlog item in the sprint is planned work); don't mention status in the email.
- Sprints are 2 weeks; the email's dates are the sprint's start and end.
- An epic shared by both groups is listed once, marked "(Chap + Geo Service)".
- **Group by primary objective**, not by group. Objectives page: link in `CLAUDE.md`; each objective has an epic label `ch-obj-*`.
  - **Primary objective**: the objective the page lists the item under; otherwise its first `ch-obj-*` label that isn't `ch-obj-platform-maturity`. Use O5 (platform maturity) only when it's the item's only objective — most epics carry that label, so it's treated as secondary.
  - Items with no `ch-obj-*` label go under "Other".
  - Objectives in order O1–O8; skip objectives with no items. Mark Geo Service items "(Geo Service)" outside O2 and Chap items "(Chap)" inside O2.
- Users are fairly technical: phrase each item by what it unlocks for them (e.g. performance that makes facility-level predictions possible).
- Fold only pure cleanup and team-internal tooling (refactoring, team AI assistant) into one "Also:" line at the end of their objective. Never fold an epic that others can build on: e.g. CLIM-1694 (Chap frontend building blocks) gets its own line, because it lets others build custom apps faster with Chap's business logic built in, and is meant as a shared resource the community contributes back to.

## Output

Write to `reports/sprint-plan-email-<YYYY-MM-DD>.md` (date sent) and show it in chat:

```
Subject: Climate team — sprint <dates>

Hi <name>,

What the team is working on this sprint (<dates>):

**Objective 1 · <short objective name>**
- <Plain-language summary> — <why it matters, a few words>.

**Objective 2 · <short objective name>**
- <Plain-language user story summary> — <why it matters>.
- <Chap item> (Chap) — <why it matters>.

**Objective 5 · <short objective name>**
- <Plain-language summary> — <why it matters>.
- Also: <small internal epics>.

Jennifer
```

- Headings spell out "Objective N" (e.g. "Objective 4 · …"); never "O4" anywhere in the email.
- Each line: under ~20 words. Optional Jira link on the item (`[CLIM-123](https://dhis2.atlassian.net/browse/CLIM-123)`).
- Within each objective, most visible / most important first.
- **Before finalising, ask me whether to remove anything from the list.** Show the item titles and wait for my answer; then write the final file.
