# Findings format

Every subagent and script writes a JSON list of findings to `WORKDIR/findings_<id>.json`.
`report.py` merges all `findings_*.json` files.

```json
{
  "check": "code | overlap | journey | structure",
  "rule": "short kebab-case kind, e.g. cli-flag-missing, undocumented-command, contradiction, duplicate, journey-gap",
  "source": "repo name the finding is about, e.g. chap-core (for overlap: the first repo involved)",
  "severity": "High | Medium | Low",
  "title": "one line: what is wrong, specific enough to act on",
  "where": ["chap-core/docs/chap-cli/eval-reference.md:42", "https://chap.dhis2.org/..."],
  "evidence": ["chap-core/chap_core/cli_endpoints/evaluate.py:88 defines --backtest-params, not --params", "page says: '...'"],
  "suggestion": "short: what to change, not a rewrite"
}
```

`where` entries are `<repo name>/<path>:<line>` (the report turns them into GitHub
links) or full URLs. Line numbers are on the default branch of the shallow clone.

## Severity

- **High**: a reader who follows the docs fails or gets a wrong result. A command,
  flag, endpoint, config key or file that does not exist; a required step missing; a
  journey that cannot be completed; a nav entry pointing at nothing.
- **Medium**: misleading or out of date, but a careful reader can recover. Outdated
  descriptions of behaviour, contradictions between pages or sources, a significant
  user-facing feature with no docs, broken links.
- **Low**: worth tidying. Duplicated content that agrees, pages missing from the nav,
  links that work only through a redirect, dated wording.

## Rules for every finding

- Evidence a reader can open: a `file:line` in a clone, a URL, or a quote. No
  evidence, no finding.
- Verify before reporting. For "does not exist" claims, grep the code; for
  contradictions, quote both sides.
- For High, confirm the failure would really happen to a reader following the docs:
  not commented-out config, not an optional path, not an example the docs never tell
  them to run. Otherwise it is Medium at most.
- For version and release claims, check what is actually released (PyPI, CRAN,
  GitHub releases, image tags), not only the version on the default branch.
- One finding per problem. If the same wrong command appears on five pages, make one
  finding with five `where` entries.
- Neutral wording about the docs, never about people.
- Do not report style, tone or grammar unless it changes the meaning.
