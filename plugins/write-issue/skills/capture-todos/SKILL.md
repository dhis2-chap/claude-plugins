---
name: capture-todos
description: Find todos in a pasted list of text and create one Jira task per todo in the Climate team task tracking project (CTI). Use when asked to "capture todos", "turn these into tasks", "make CTI tasks from this", "add these todos to Jira" or similar, usually with a block of pasted notes.
---

# Capturing todos into CTI

Turn a pasted block of notes into one CTI task per todo. The pasted text is
usually meeting notes, a brain dump, a Slack thread or a voice-memo transcript,
mixed with things that are not todos (observations, decisions, background).

## Project

- Site: `dhis2.atlassian.net`. Project: `CTI` ("Climate team task tracking"),
  a business project. Issue type: `Task`. Only `Summary` is required.
- Reporter defaults to the current user. Set `Assignee` when the pasted text
  names an owner — see "Assignee" below. Do not set labels or priority unless
  the human gave them.
- Several CTI custom fields describe the meeting the todos came from or the
  task itself — ask for them before showing the draft; see "Shared fields
  for this meeting" below.

## Shared fields for this meeting

A pasted block is almost always one meeting's notes. These fields are the
same for every todo in that paste, so ask once up front and apply the
answers to every task created in this run:

| Field | Id | How to ask |
|---|---|---|
| Meeting type | `customfield_10677` | Pick one: `Retrospective`, `Planning`, `Discovery refinement`, `Topic meeting`, `Thursday steering meeting`, `Other`. Required for the draft — do not guess from the notes. When the human's answer does not match a picklist value, offer the closest match and `Other` and let them choose. |
| Meeting date | `customfield_10678` | A date (YYYY-MM-DD). If the notes have a heading like "Standup 2026-11-14", propose that date; otherwise ask. |

Ask for both in one short question before the draft. Once answered, show
them at the top of the draft as the "Meeting:" header. If the human skips
one, leave it unset and carry on.

**When the meeting type is `Other`:** record whatever the human originally
typed as the meeting name (for example "CAPS collaboration meeting") and
put it as the first line of every task's description, formatted as
`Meeting: <name>`. This keeps the name findable on each task even though
CTI itself only stores `Other`. Show the meeting name in the draft's
"Meeting:" header alongside the picklist value (for example
`Meeting: Other — CAPS collaboration meeting on 2026-11-16`).

Two more fields may apply per task, not per meeting, so ask only when
relevant:

- **Outcome** (`customfield_10680`, short text): a one-line result when a
  todo captures what was decided rather than what to do. Rare for todos;
  skip unless the pasted item clearly names an outcome.
- **Due date** (`duedate`) and **Start date** (`customfield_10015`): set
  only when the todo has an explicit date ("by Thursday the 20th", "next
  Friday"). Resolve relative dates against the meeting date and show the
  absolute date in the draft for confirmation. Never guess a due date.

## Assignee

When the pasted text names an owner for a todo (a section header like "Knut",
a prefix like "Knut:", "Knut to ...", or "I'll ..." when the current user is
clearly meant), try to set `Assignee`:

1. **Match the name to a CTI member.** Call `lookupJiraAccountId` for the
   first name (or full name if given). Only consider candidates who are
   members of the CTI project — that is, who have reported, been assigned
   to, or commented on a CTI issue. A quick way is
   `project = CTI AND (assignee = "<accountId>" OR reporter = "<accountId>")`
   via `searchJiraIssuesUsingJql`; if nothing comes back, treat the
   candidate as not in CTI.
2. **Several CTI candidates share the name.** List them in "Unclear" with
   their display names and ask which one.
3. **One clear CTI match.** Use that account id in the draft, and show the
   display name next to the proposed assignee so the human can confirm.
4. **No CTI match** (e.g. "Allen" or "Boshe" are not in CTI). List the
   todo in "Unclear" with the original name and ask whether to assign it
   to someone who is in CTI (for example the current user, or whoever
   raised the todo), or to leave it unassigned.

Resolve each distinct name once per run and reuse the result.

### One main owner, collaborators in "Others involved"

A task has exactly one assignee. When a todo lists several people:

- **"A + B" or "A and B" (shared):** the first name is the main owner and
  the assignee; the other(s) go in the `Others involved` field
  (`customfield_10679`), a multi-user picker. Resolve each name the same
  way as the assignee (lookup + CTI check). Ask if the order looks wrong
  ("the first name may not be the owner").
- **"A, B (and C)" (reviewers, attendees):** the same — first name is the
  assignee, the rest go in `Others involved`.
- **The section header names the owner** (e.g. "Allen + Knut (shared)")
  and the todo body does not override it: use the section's first name.

Collaborators who do not match a CTI member cannot go in `Others
involved`. Mention those names in the description instead (one line,
"Collaborators (not in CTI): ..."), and ask whether to drop them or wait
until they are added to the project.

If no name in the group matches a CTI member, follow step 4 above for the
group as a whole.

## Rules

1. **Do not substantially rewrite.** Keep the human's words. Fixing
   misspellings and obvious typos is fine. Do not expand abbreviations,
   reword for "clarity", add context, split one todo into several, or merge
   several into one.
2. **Ask when unsure.** If a line might or might not be a todo, list it
   under "Unclear" and ask. If the text suggests an assignee for a task
   but it is ambiguous (first name shared by several CTI members,
   "someone should", "we", or no CTI member matches the name), ask. Do
   not guess an assignee.
3. **One task per todo.** A todo with sub-bullets becomes one task with
   the sub-bullets in its description, unless the human says to split it.
4. **Draft first, never submit before approval.** Show the full list
   (summary and any description, grouped: Todos, Unclear, Possible
   duplicates, Not todos) and wait for an explicit yes before creating
   anything in Jira. "Looks good" or "go ahead" counts; silence does not.
5. **Nothing else in CTI.** Only create tasks. Do not edit existing issues,
   add comments, change statuses, or create anything in other projects from
   this skill.

## What counts as a todo

A todo is an action someone should take. Signals:

- Imperative verbs: "write", "email", "ask", "fix", "set up", "check with".
- "TODO:", "AP:", "action:", "follow up", "- [ ]" checkboxes.
- "I'll ...", "<name> to ...", "we should ..." (ask about the "we").

Not todos: decisions already taken ("we decided X"), observations ("the
build is slow"), questions without an owner, background notes, links
pasted as reference. If the same line is both an observation and an
implied action ("the build is slow" → "someone should look at the build"),
put it under Unclear and ask.

## Writing each task

- **Summary:** the todo, lightly cleaned. Start with a verb. One line.
  Trim list markers (`-`, `*`, `[ ]`), "TODO:" prefixes, trailing
  punctuation, and speaker labels ("Jen:"). Keep names and specifics.
- **Description:** only if the pasted text has extra detail for that todo
  (sub-bullets, a link, a quoted sentence of context). Otherwise leave it
  empty. Plain text is fine for one or two sentences; use ADF for anything
  with bullets or links. Never send Markdown to Jira; see "Writing into
  Jira" in [write-issue](../write-issue/SKILL.md) for the formats.
- **Source:** when the pasted text has a heading or date (e.g. "Standup
  2026-11-14"), include it as the first line of the description so the
  task can be traced back. Skip if there is no obvious source.

## Duplicate detection

Before showing the draft, check whether the same meeting has already been
captured — the notes may have been pasted here before, or by someone else
on the team. Query CTI for existing tasks that look like they belong to
the same meeting:

```
project = CTI AND "Meeting type" = "<type>" AND "Meeting date" = "<date>"
```

(Use the picklist id for the type and ISO date for the date.) When the
type is `Other`, also narrow by the meeting name the human typed: fetch
the matching issues' descriptions and keep the ones whose first line is
`Meeting: <same name>` (case-insensitive, ignoring trailing punctuation).

Compare each proposed todo's summary against those existing tasks:

- **Exact or near-exact summary match** (same verb and object, ignoring
  minor differences in wording or punctuation): treat as a duplicate.
- **Clearly overlapping intent** (same action on the same thing,
  different phrasing): flag as a possible duplicate, do not decide.
- **Different enough** (different verb or different object): not a
  duplicate.

Show matches in a `Possible duplicates` section of the draft, each with
the existing CTI key, the existing summary, the proposed summary, and
which bucket it falls in. Default to **skip** for exact matches and
**ask** for possible matches. Never silently drop a todo without showing
it here.

When the first search returns nothing, say so in one line ("no earlier
tasks found for this meeting") and carry on — do not widen the query by
dropping the date or the type, because that would surface unrelated
tasks.

## Draft format

Start the draft with a one-line "Meeting:" header showing the shared
fields the human confirmed:

```
Meeting: <type> on <YYYY-MM-DD>
```

Then a numbered list the human can skim. For each todo:

```
1. <summary>  — assignee: <Display Name>, or "unassigned"
   Others involved: <Display Name>, <Display Name>   (when any)
   Due: <YYYY-MM-DD>                                 (when set)
   (description, if any)
```

Show display names in the draft, not account ids — the ids go into the
create call. Omit each per-task field line that is empty.

Then, separately:

```
Unclear (ask before creating):
- "<verbatim line>" — <why unclear: todo? assignee?>

Not todos (will skip):
- <one or two words each>
```

Keep "Not todos" short — just enough that the human can spot a miss. If
the pasted text is long and most lines are not todos, it is fine to list
only the first few and say "... and N others".

## After approval

Create the tasks one by one with `createJiraIssue`, project `CTI`, issue
type `Task`, the resolved `Assignee` account id where one was set, and
the shared meeting fields (`customfield_10677` meeting type and
`customfield_10678` meeting date) plus per-task `Others involved`,
`Outcome` or dates where they apply. Report the created keys back as a
list the human can click. If a create fails, stop, show which one failed
and why, and ask before retrying or skipping.
