# Applying approved changes

Only after the user has named a tier or IDs from the report. Never apply anything the
user has not named, and never widen "apply tier 1" to tier 2 items.

1. `python3 approved.py tier1` (or `python3 approved.py P03 P07`) prints the selected
   actions from `proposed.json`.
2. For each action, in order, using the Atlassian MCP:

| action | how |
|---|---|
| `transition:<status>` | ToolSearch `select:mcp__atlassian__transitionJiraIssue`. Transition ids differ per status and workflow; get them from `discover` → `listJiraIssueTransitions` → `executeRead` for the issue, then pass the id. If the target status is not offered, skip the item and report it. |
| `add_component:?` | Resolve `?` first: use the parent epic's component when the evidence says "parent epic in scope", otherwise the first component in config. `editJiraIssue` with `components: [{"name": "..."}]`, keeping existing components. |
| `link_relates:KEY` | `discover` "link jira issues", then `executeWrite` with type `Relates`. |
| `link_duplicate:KEY` | Same, type `Duplicate`. Does not change status. |
| `close_duplicate:KEY (keep OTHER)` | Link as Duplicate, then transition the named issue to Done. |
| `relink_epic:KEY` | `editJiraIssue` with `parent: {"key": KEY}`. |
| `edit_description` | Tier 3 only. Apply the `proposed_text` as a minimal edit to the existing description (read it first with `responseContentFormat: html`, change only the sentence named, write back with `contentFormat: html`). Never replace a whole description. |

3. After each change add a comment with `addOrEditJiraIssueComment`, one or two lines:
   what changed and why, with the PR URL from the evidence, and "Jira audit
   <snapshot date>". Example: "Moved to Done: delivered by
   https://github.com/dhis2-chap/chap-core/pull/374 (merged 2026-05-27). Jira audit 2026-10-02."

4. Verify: one JQL `key in (...)` over every touched issue with `fields: ["status",
   "components", "parent"]`, and compare with what was intended. Report any mismatch.

5. Report to the user: a table of ID, issue, action, result (done / skipped and why).
   Append the applied IDs to the history record if `--save` was used
   (`~/.cache/chap-jira-audit/latest.json`, field `applied`).

Rules: one issue at a time, no bulk operations; stop and ask if a transition is
refused or an issue has changed since the snapshot (status differs from
`jira.json`); never delete anything.
