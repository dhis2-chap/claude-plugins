---
description: Set up the Discourse MCP server for community.dhis2.org (one-time, per machine).
---

Invoke the `discourse` skill and run its **Setup** section now, step by step.

Check what is already in place before telling the user to do anything: whether
the `discourse` MCP server is registered (`claude mcp list`), whether the
profile file exists, and whether write tools are exposed. Only walk the user
through the steps that are still missing.

Do not reimplement the setup here — the skill is the single source of truth.
