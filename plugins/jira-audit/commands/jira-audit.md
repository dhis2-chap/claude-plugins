---
description: Audit CLIM Jira against the chap repos (statuses, descriptions, duplicates) and produce a report with tiered proposed changes.
---

Invoke the `jira-audit` skill and begin its workflow now.

If the user already said what to audit (components, repos, "sprint" or "all"),
or asked to apply changes from an earlier report ("apply tier 1", "apply P03
P07"), pass that along to the skill. Otherwise the skill asks.

Do not reimplement the workflow here; the skill is the single source of truth.
