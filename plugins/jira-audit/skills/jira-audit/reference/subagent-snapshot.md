# Snapshot subagent brief

Fill in the placeholders in `{}` before launching. One subagent per slice. All read-only.

---

You are taking a read-only snapshot of Jira issues via the Atlassian MCP (not acli).
Never modify Jira.

Load the tool first: ToolSearch with query `select:mcp__atlassian__searchJiraIssuesUsingJql`.
cloudId: `{cloud_id}`

JQL: `{jql}`

Call `searchJiraIssuesUsingJql` with `view: "full"`, `maxResults: 50`, and
`fields: ["summary","status","issuetype","parent","assignee","created","updated","resolutiondate","components","issuelinks","labels","description","customfield_10020"]`.
Page with `nextPageToken` until `isLast` is true. `view: "full"` plus explicit
fields is required; the compact view drops fields.

Large pages do not come back inline: the tool saves them to a file and tells you
where. Parse that file with a small Python script. Name every helper script you
create `{slice}_*.py` so it does not collide with other subagents writing to the
same directory.

Write one JSON object per line to `{workdir}/jira_{slice}.jsonl` with keys:
`key, summary, status` (name), `type` (issuetype name), `parent` (key or null),
`parent_summary, assignee` (displayName or null), `created, updated, resolved`
(resolutiondate or null), `components` (list of names), `labels, sprints` (list of
`{name, state}`), `links` (list of `{type, direction "in"/"out", key, status}`),
`desc` (first 300 characters of the description with HTML tags stripped and newlines
replaced by spaces, `""` if none), `desc_len` (approx length of the full description).

Every issue exactly once. Validate with
`python3 -c "import json;[json.loads(l) for l in open(PATH)]"` and count lines.

Reply only with the number of issues written and any problems. Do not echo the data.

---

## Slices

Detailed slices (the brief above), one subagent each. Split a component with more
than ~250 issues into open and done:

| slice | JQL |
|---|---|
| `{comp}_open` | `project = {project} AND component = "{component}" AND statusCategory != Done ORDER BY key ASC` |
| `{comp}_done` | `project = {project} AND component = "{component}" AND statusCategory = Done ORDER BY key ASC` |
| `nocomp_open` | `project = {project} AND component is EMPTY AND statusCategory != Done ORDER BY key ASC` |

Summaries slice (for the duplicate comparison), same subagent as `nocomp_open`,
compact view with `fields: ["summary","status","issuetype","created"]`, `maxResults: 100`:

| file | JQL |
|---|---|
| `jira_other_summaries.jsonl` | `project = {project} AND component not in ({components}) ORDER BY key ASC`, plus `project = {project} AND component is EMPTY AND statusCategory = Done ORDER BY key ASC` |

Keys: `key, summary, status, type, created, group` ("other_component" or "no_component_done").

Roadmap ideas slice (for the R2-R4 checks in `roadmap.py`), same subagent as
`nocomp_open`, `view: "full"`, `maxResults: 100`, with
`fields: ["summary","status","updated","labels","issuelinks","description","customfield_10216","customfield_10566"]`:

| file | JQL |
|---|---|
| `roadmap_ideas.jsonl` | `{roadmap_idea_jql}` from config |

Keys: `key, summary, status, updated, product_areas` (list of the
`customfield_10216` option values), `links` (list of `{type, direction, key,
status, issuetype, summary}` for every issue link, with the linked issue's type
name and summary), `desc` (first 600 characters, tags stripped), `desc_len`.
Ideas from other DHIS2 teams are not fetched; the JQL selects by Product Areas
and Domain.
