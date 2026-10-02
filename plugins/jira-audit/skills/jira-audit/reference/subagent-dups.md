# Duplicates subagent brief

Write this to `{workdir}/DUPS_BRIEF.md` with the placeholders filled, then launch one
subagent with: "Read `{workdir}/DUPS_BRIEF.md` and follow it exactly. Everything is read-only."

---

READ-ONLY. Never change anything in Jira.

Work dir: `{workdir}`

Input: `dup_candidates.json`, a list of candidate pairs (`{a, a_summary, a_status, b,
b_summary, b_status, tfidf, jaccard, same_epic}`) found by text similarity. Snapshot
details for in-scope issues are in `jira.json` (dict by key; load with Python, do not
cat). PRs referencing an issue are in `links.json`.

Jira MCP: first ToolSearch `select:mcp__atlassian__getJiraIssue`. cloudId `{cloud_id}`.
Use `getJiraIssue` with `view: "evidence"` to read full descriptions and existing
issue links. Read both issues of a pair before judging; summaries alone are not
enough. Skip reading only when both summaries are obviously about different things
(drop the pair silently).

For each pair decide:

- **U1 duplicate**: same piece of work. Suggest which to keep: the older one by
  default, or the one with more detail, PRs or comments; say why. If one is Done and
  the other open, the open one is usually the one to close unless it adds scope.
- **U2 overlap / split**: same area and should be linked, merged, or one made a child
  of the other; or one is a narrower slice of the other.
- **not related**: drop.

Also check whether the pair is ALREADY linked in Jira. If linked as duplicate and the
open one is still open, that is a finding too.

If while reading you notice a third issue that duplicates one of the pair, include it.

Output `findings_dups.json`: list of

```json
{
  "key": "{project}-aaa",
  "other": "{project}-bbb",
  "rule": "U1|U2",
  "title": "one line",
  "evidence": ["quote or fact from a", "quote or fact from b", "existing link: none / Relates"],
  "suggested_action": "close_duplicate:{project}-bbb (keep {project}-aaa) | link_duplicate:{project}-bbb | link_relates:{project}-bbb | make_child:{project}-bbb",
  "confidence": "High|Medium|Low",
  "note": "optional"
}
```

Tone: neutral, about tickets, never about people. Validate the JSON before finishing.
Reply with only: pairs read, U1 count, U2 count, dropped count, and any problems.
