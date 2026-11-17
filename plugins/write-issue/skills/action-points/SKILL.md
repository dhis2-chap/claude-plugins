---
name: action-points
description: Add, capture, list and close action points (todos) in the Climate team task tracking project (CTI) in Jira. Use for "add an action point for <person> about <thing>", "here are the action points from today's meeting", "capture the todos from these notes", "take the action points from the notes of <meeting>", "turn these into tasks", "what are my action points?", "what does <person> have open?", "which action points are overdue?", "mark CTI-12 as done" and similar.
---

# Action points in CTI

The team's action points are Tasks in the Jira project `CTI`, "Climate team
task tracking" (site `dhis2.atlassian.net`, a business project). This skill
covers all work on them:

1. [Adding one action point](#adding-one-action-point) from a short prompt.
2. [Capturing action points from notes](#capturing-action-points-from-notes),
   pasted or taken from a meeting's notes in Google Drive or Confluence.
3. [Reading action points](#reading-action-points): a person's open ones,
   one meeting's, unassigned, overdue or open longest.
4. [Closing or updating one](#closing-or-updating-one).

All Jira work goes through the Atlassian MCP. If its tools are not in the
session, say so, tell the user to connect it, and offer to write the draft
anyway. Do not fall back to the Jira REST API, `acli` or API tokens.

Some people say "CTT"; the key is `CTI`. Newly created issues can take a
minute to show up in search.

## Fields

| Field | Id | Notes |
|---|---|---|
| Summary | `summary` | Required. See "Summary" below. |
| Description | `description` | First line names the meeting; see "Description". |
| Assignee | `assignee` | One person; see "People". Empty when nobody owns it. |
| Meeting type | `customfield_10677` | Picklist: `Retrospective` (`10952`), `Planning` (`10953`), `Discovery refinement` (`10954`), `Topic meeting` (`10955`), `Thursday steering meeting` (`10956`), `Other` (`10957`). Set as `{"id": "<id>"}`. |
| Meeting date | `customfield_10678` | `YYYY-MM-DD`. |
| Others involved | `customfield_10679` | Jira users, `[{"accountId": "..."}]`. |
| Outcome | `customfield_10680` | Short text: the result, filled in when the action point is closed. |
| Due date | `duedate` | Only from an explicit date; see "Dates". |

Issue type: `Task` (id `10340`). Do not set labels or priority unless the
user gave them. The CLIM component and label rules do not apply here.

Statuses: `To do`, `Proposed`, `Done`, `Won't do`. Transitions: To do `21`,
Proposed `2`, Done `41`, Won't do `3`. Check with the MCP's
get-transitions tool if one fails.

## Writing an action point

### Summary

The user's own words, lightly cleaned:

- Fix spelling and obvious typos.
- Remove list markers (`-`, `*`, `[ ]`), a leading "todo X:", "AP:",
  "action point:", "TODO:", and speaker or owner labels ("Knut:") once the
  owner is recorded as assignee.
- Do not rewrite, expand abbreviations, reword for clarity, or force a
  verb at the start. "Security review for CAPS, OCS and Chap" stays as it
  is.
- Write issue numbers bare (`CLIM-1234`) and add no Jira links unless
  asked.
- One line. Keep names and specifics.

### Description

The first line names the meeting, so the task can be traced back:

- A meeting with a picklist type: `From the <type, lowercase> meeting on
  <D Month YYYY>.`, for example `From the planning meeting on 16 November
  2026.`
- Meeting type `Other`: `From the <meeting name as the user gave it> on <D
  Month YYYY>.`, for example `From the CAPS collaboration meeting on 16
  November 2026.` CTI only stores `Other`, so this line is what keeps the
  name findable.
- No meeting: `From <who asked>, <D Month YYYY>.`

After a blank line, add the extra lines from the notes for that todo
(sub-bullets, a link, a sentence of context), unchanged. Leave the rest out.
Plain text is fine for a sentence or two; use ADF for bullets or links, and
never send Markdown to Jira (see "Writing into Jira" in
[write-issue](../write-issue/SKILL.md)).

Older tasks use `Meeting: <name>` as their first line instead. Read both
forms when searching; write only the new one.

### People

A task has exactly one assignee. Resolve each distinct name once per run
and reuse the result.

1. "Me", "I", "my": the current user (the MCP's user-info tool).
2. Any other name: look it up with `lookupJiraAccountId` (full name if
   given, else first name). First names are often shared (there are
   several Edvins, Knuts and Mortens in Jira), so narrow to people who take
   part in CTI: for each candidate, search
   `project = CTI AND (assignee = "<accountId>" OR reporter = "<accountId>" OR "Others involved" = "<accountId>")`.
   - One CTI candidate: use it, and show the display name in the draft so
     the user can confirm.
   - Several CTI candidates: list them and ask which one.
   - No CTI candidate but exactly one active match in the lookup: propose
     it, say they have no CTI tasks yet, and ask the user to confirm.
   - No match: ask whether to assign it to someone else or leave it
     unassigned, and keep the original name in the description
     (`Owner in the notes: <name> (no Jira account found).`).
3. Several people on one todo ("A and B", "A + B", "A, B and C", or a
   section header naming them): the first is the assignee and the rest go
   in `Others involved`. Say so in the draft so the user can swap them if
   the first is not the owner. People without an account go in the
   description (`Also involved: <names>.`).
4. "We", "someone", "the team", or no name: leave it unassigned and list it
   under "Unclear" so the user can name an owner. Never guess an assignee.

### Dates

- Set `duedate` only when the text gives a date or a deadline that can be
  resolved ("by Thursday", "before 20 November"). Resolve relative dates
  against the meeting date (or today, with no meeting), and show the
  absolute date in the draft for confirmation.
- When the date is unclear ("before next Thursday" could be two dates),
  show both and ask.
- When the date is already past, or before the meeting date, flag it in the
  draft ("this date is before the meeting; is it a typo or already late?")
  instead of setting it silently.
- Leave the deadline text in the summary as the user wrote it.
- Conditions without a date ("before the country rollout") are not due
  dates; keep them in the summary or description.

### Duplicates and related tasks

Before showing any draft, check CTI for two things:

1. **The same meeting captured before** (by this session or a teammate):
   `project = CTI AND "Meeting date" = "<date>" AND "Meeting type" = "<type>"`,
   and for `Other`, keep the ones whose first description line names the
   same meeting (either form above, case-insensitive).
2. **Related open tasks from any meeting:** action points often come back
   at a later meeting. Search open tasks for the main words of each
   proposed summary, for example
   `project = CTI AND statusCategory != Done AND text ~ "Bulletin app"`.

Sort what you find:

- **Same action, same meeting** (near-identical summary): a duplicate.
  Default to skip.
- **Same action on the same thing, other wording or another meeting**:
  possible duplicate or follow-up. Ask: skip, create anyway, or add the
  new detail to the existing task (as a comment, after approval).
- **Different action or different thing**: not related.

Show each match with the existing key, its summary and status, the proposed
summary, and the bucket. Never drop a todo without showing it. When nothing
is found, say so in one line.

## Adding one action point

For prompts like "add an action point for Morten about reviewing CLIM-1904"
or "AP: I'll send the slides to the partners".

1. Take the summary from the user's words (see "Summary"), and resolve the
   owner (see "People").
2. If the user named no meeting, ask once which meeting it came from (type
   and date). If there was none, leave both meeting fields empty.
3. Run the duplicate check.
4. Show a one-line draft, for example:
   `Review CLIM-1904 · assignee <Display Name> · Planning meeting, 16 Nov 2026 · no related open tasks`
   plus any due date or question.
5. Create it when the user says yes, and report the key as a link.

## Capturing action points from notes

### Getting the notes

The notes come in one of three ways:

- **Pasted** into the prompt.
- **A file or link** the user points to.
- **A named meeting** ("take the action points from Monday's status
  meeting notes"). The team's meeting notes are in Google Drive or in
  Confluence; look in both before concluding anything:
  - **Google Drive.** In the team's knowledge vault (`chap-first-brain`),
    selected Drive folders are mirrored as Markdown under
    `Archive/files/gdrive/` (meeting notes in
    `Archive/files/gdrive/meeting-notes/`, each folder with an `index.md`
    linking back to Drive). Run
    `bash AI-internal/useful-scripts/ensure_archive.sh` first, and search
    with `grep -ril <term> Archive/files`: the folder is gitignored, so a
    vault-wide search skips it. Outside the vault, use a Google Drive
    connector if one is in the session, or ask the user for the file.
  - **Confluence.** Search with the Atlassian MCP's CQL search, for example
    `type = page AND title ~ "<meeting name>" ORDER BY lastmodified DESC`
    or `type = page AND text ~ "<meeting name>" AND lastmodified >= now("-2w")`.
  - Many notes are one long running document with a section per meeting.
    Take only the section for the meeting date, and say which document and
    section you used.
  - If neither place has notes for the meeting, say so plainly. The notes
    may be somewhere you cannot reach, or the meeting may have no notes at
    all; ask the user to paste them or to name the action points directly.
    Never treat "not found" as "no action points".

### Meeting fields

A batch is almost always one meeting. Ask once, in one short question, for
the meeting type and date, and apply them to every task in the run:

- Propose the date when the notes have one (a heading like "Status meeting
  16 Nov 2026"); otherwise ask.
- Do not guess the type from the notes. When the user's answer is not a
  picklist value, offer the closest match and `Other`. For `Other`, keep
  the meeting name the user gave for the description line.
- If the user skips one, leave it unset.

### What counts as an action point

An action point is something someone should do. Signals: imperative verbs
("write", "email", "ask", "fix", "check with"); "TODO:", "AP:", "action:",
"follow up", `- [ ]`; "I'll ...", "<name> to ...", "we should ...".

Not action points: decisions taken ("we decided X"), agreed ways of
working, observations, questions with no owner, background, reference
links. When a line could be either ("the build is slow"), list it under
"Unclear" and ask.

One action point per todo. Sub-bullets go in its description. Do not split
or merge todos unless the user asks.

### Draft

Start with the meeting and the notes you used:

```
Meeting: Planning, 16 Nov 2026 (notes: <document and section, or "pasted">)
```

Then a numbered list:

```
1. <summary> · assignee: <Display Name> or unassigned
   Others involved: <Display Name>, ...        (when any)
   Due: <YYYY-MM-DD>                           (when set)
   <description lines, if any>
```

Then, each only when it has entries:

```
Possible duplicates and related tasks:
- CTI-31 (To do) "<existing summary>" ↔ "<proposed summary>": <bucket, proposed action>

Unclear (ask before creating):
- "<verbatim line>": <why: action point? owner? date?>

Not action points (will skip):
- <a few words each; "... and N others" when long>
```

Show display names, not account ids.

### After approval

Create nothing until the user says yes ("looks good" and "go ahead"
count; silence does not). Then create the tasks one by one with the
MCP's create-issue tool, project `CTI`, type `Task`, with the assignee,
meeting fields, `Others involved` and due date where set. Report the keys
as a list of links. If a create fails, stop, show which one and why, and
ask before retrying or skipping.

## Reading action points

Use the MCP's JQL search. List key, summary, assignee, status and meeting
date (fields `summary`, `assignee`, `status`, `customfield_10677`,
`customfield_10678`, `duedate`).

| Request | JQL |
|---|---|
| My open ones | `project = CTI AND assignee = currentUser() AND statusCategory != Done` |
| A person's open ones | `project = CTI AND assignee = "<accountId>" AND statusCategory != Done` (resolve the name as in "People") |
| Unassigned | `project = CTI AND assignee is EMPTY AND statusCategory != Done` |
| One meeting | add `AND "Meeting date" = "YYYY-MM-DD"` and `AND "Meeting type" = "Planning"`; for `Other`, also match the meeting name in the description |
| Overdue | `project = CTI AND statusCategory != Done AND duedate < now()` |
| Open longest | `project = CTI AND statusCategory != Done ORDER BY "Meeting date" ASC, created ASC` |

"Me" is the person whose Atlassian login the MCP uses.

For "overdue" or "open longest", also:

- Read the summaries for deadlines written only in the text ("before
  Thursday", "by end of November"), and list them separately from real due
  dates. Do not invent deadlines.
- Remember that CTI started on 16 November 2026. Earlier action points were
  kept in the meeting notes and as `Design` issues on CLIM board 653 (see
  CLIM-250). Moving them to CTI is CTI-21. When the question is about the
  long run, say so and offer to look there.

## Closing or updating one

For "mark CTI-12 as done", "CTI-12 is won't do", "set the outcome of CTI-12
to ...", "assign CTI-30 to Knut", "set a due date on CTI-23":

1. Read the issue first and show its summary and current status, so the
   user can see it is the right one.
2. Move it with the MCP's transition tool: Done `41`, Won't do `3`.
   If the user gave a result, put it in `Outcome` (`customfield_10680`).
   For Won't do, ask for a one-line reason for `Outcome` if none was given.
3. Other edits (assignee, due date, meeting fields, others involved) are
   made with the MCP's edit tool, with names and dates resolved as above.
4. A single change the user asked for directly needs no further approval.
   Several changes at once (for example closing everything from one
   meeting) are shown as a list first and done after approval.

Never delete CTI issues, and never change issues in other projects from
this skill.
