---
name: write-roadmap-idea
description: Write a roadmap idea for Chap or the Open Climate Service in the DHIS2 Roadmap (Jira Product Discovery project ROADMAP), or revise one. Use whenever asked to post, add, propose, suggest or write a roadmap idea, "put this on the roadmap", "make a ROADMAP idea for X" or "update ROADMAP-123". For CLIM epics and issues, use write-issue instead.
---

# Writing roadmap ideas

A roadmap idea is a pitch: it says why something is worth doing, what the
result would be and who it is for, so it can be weighed against other ideas.
It is not an implementation plan. Once an idea is taken onto the roadmap, the
work is planned as CLIM epics and issues with the write-issue skill, and those
epics are linked back to the idea.

The rules from write-issue apply here too: only write what you know, keep
undecided things as open questions, ask before drafting, show a full draft
and wait for approval before creating or editing anything, and check every
issue key and claim you cite. Never write Markdown into Jira (see "Writing
into Jira" in write-issue): send the description as ADF.

## Where ideas go

- Site: `dhis2.atlassian.net`. Project: `ROADMAP` ("DHIS2 Roadmap"), a Jira
  Product Discovery project. Issue type: `Idea` (the only type).
- Board: https://dhis2.atlassian.net/jira/polaris/projects/ROADMAP/ideas/view/ef470a7e-7499-48e1-8043-ca1e306e04f6
- The project is shared by all DHIS2 product teams (Maps, Capture, Android
  and others). Only create and edit Chap and Open Climate Service ideas.
  Never change another team's idea.

## Before drafting

1. Ask the human for whatever context they have: discussions, Slack threads,
   related CLIM issues or earlier ideas.
2. Search for existing ideas on the same topic, for example
   `project = ROADMAP AND text ~ "<keyword>" ORDER BY created DESC`, and
   read the close matches. If one already covers it, say so and offer to
   revise or comment on it instead of creating a duplicate.
3. Ask short batches of questions until Why, What, Done and Who below are
   answered, or the human says they are open.

## Format

Use these sections, as level-3 headings in ADF. This is the format of the
team's existing ideas (for example ROADMAP-686, ROADMAP-700 and ROADMAP-703;
read one for tone):

```
### Why     the problem today and who has it; concrete, a short paragraph
### What    what we would build or do, as a paragraph or bullets,
            ending with a line starting "Done means:" with checkable outcomes
### Who     the users or groups who benefit, and how
```

Add `### Open questions` when something is undecided. Keep the whole
description readable in a minute or two; leave out design detail that
belongs in the CLIM epic.

Title: one line saying the outcome, optionally with a short "noun: what it
gives" form, for example "Show uncertainty intervals for evaluation metrics
and model comparisons in the Modelling App". Do not prefix it with a team or
product name in brackets.

## Fields

Field ids are for `dhis2.atlassian.net` as of 2026-11-03. Option names are
exact; check them with `getJiraIssueTypeMetaWithFields` (project `ROADMAP`,
issue type id `10141`) if a create fails.

| Field | Id | What to set |
|---|---|---|
| Product Areas | `customfield_10216` | `Chap`, `Open Climate Service`, or both. Always set. |
| Domain | `customfield_10566` | `Climate`. Always set. |
| App | `customfield_10218` | `Modelling App` or `Climate App` when the idea is about that app; otherwise leave empty. |
| Origin | `customfield_10226` | Where the idea came from. The team mostly uses `Climate Domain`; others are `Community`, `HISP`, `Product`, `Technical`, `Implementation`. Ask if unclear. |

Leave these to product management and do not set them unless the human
asks: Objective, Strategic Priority, Teams, Target release, Priority, the
impact and effort ratings, Goals and Assignee. Do not add labels.

## Status

A new idea gets the project's starting status. Do not transition ideas:
moving an idea to Analysing, Roadmap Candidate, Assigned to Roadmap, Not
Prioritised or Already Supported is a product management decision.

## Links

Use issue links, not a "Related" list in the description. Put the proposed
links in the draft for approval and create them after the idea exists:

- `Relates` to other ROADMAP ideas or CLIM issues on the same topic.
- `Polaris work item link` ("implements" / "is implemented by") from a CLIM
  epic to the idea it delivers. Add it when the human says an epic
  implements the idea, or when an epic is created for an idea with
  write-issue. The epic is the outward side ("CLIM-123 implements
  ROADMAP-456").

## Revising an idea

Read the current description as ADF, change only what was discussed, and
write it back as ADF. Show the changed sections in the draft. If others have
commented on the idea, mention the comments to the human before editing.
