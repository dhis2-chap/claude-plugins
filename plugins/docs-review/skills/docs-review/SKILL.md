---
name: docs-review
description: Use when the user wants a review of documentation across the chap modeling platform and climate team repos (chap-core, chap-site, chap-frontend, chapkit, SDKs, model examples, open-climate-service, climate-tools, climate-app, climate-sre) to find holes. Checks docs against code, overlap and contradictions between sources, reader journeys, and structure and links, and produces a shareable HTML report. Triggers on "review the docs", "docs review", "find holes in the documentation", "check our documentation", "are the docs up to date".
---

# Docs review

Find holes in the documentation: what is wrong compared to the code, what is
duplicated or contradicts across sources, where a reader gets stuck, and what is
broken or unreachable. The run is read-only and ends in a report; nothing is edited,
and no issues or PRs are created.

The sources live in `sources.md` next to this file. Scripts are in `scripts/`, the
subagent briefs and the findings format in `reference/`.

## Requirements

- `gh` authenticated with read access to the `dhis2` and `dhis2-chap` orgs.
- `uv` (for `structure.py`, which needs PyYAML).
- A work directory: the session scratchpad if there is one, else `mktemp -d`. Called
  `WORKDIR` below. `SKILL_DIR` is the directory of this file.

## 0. Ask

Read `sources.md`. Unless the user already said, ask in one `AskUserQuestion` call:

1. **Teams** (single select): Modeling platform, Climate data, or Both. Shared sources
   (`climate-sre`) are included with either.
2. **Scope** (single select): everything in the selected teams (default), pick
   groups, or name repos.
3. **Checks** (multi-select, all on by default): Docs vs code, Overlap between
   sources, Reader journeys, Structure and links.

If the user chose to pick groups, ask once more with the groups of the selected
teams as a multi-select (from `sources.md`: modeling has `core`, `chapkit`, `sdk`,
`examples`; climate has `ocs`, `climate-tools`, `climate-app`; shared has `sre`). If
they chose to name repos, take the names as free text.

## 1. Select, fetch, mechanical checks

```
cd WORKDIR
cp SKILL_DIR/scripts/*.py .
python3 pick.py SKILL_DIR/sources.md --teams modeling,climate [--groups ...] [--repos ...] --checks code,overlap,journey,structure
python3 fetch.py
uv run --with pyyaml python structure.py
```

`fetch.py` clones every selected repo shallow over HTTPS in parallel (seconds, not
minutes) and lists the repos in each org. If a clone fails, report it and continue
without that repo. Run `structure.py` even when the structure check is not selected:
its output keeps the other reviewers from reporting broken links. Delete
`findings_structure.json` before the report if structure was not selected.

## 2. Review (parallel subagents)

Fill `{workdir}`, `{skill_dir}`, `{today}` and `{checks}` in the briefs, write them to
`WORKDIR`, and launch every subagent in one message:

- **Source reviewers** (if `code` or `structure` is selected): one per group in
  `config.json`, from `reference/subagent-source.md`.
- **Overlap reviewers** (if `overlap`): one per selected team, from
  `reference/subagent-overlap.md`.
- **Journey reviewers** (if `journey`): batches of at most three journeys from
  `config.json`, one team per batch, from `reference/subagent-journey.md`.

Tell the user how many subagents were launched. Do not do their work while waiting
and do not read their transcripts. When all have replied, check that each expected
`findings_*.json` exists and parses; rerun any subagent that failed or reported tool
errors.

## 3. Report

```
python3 report.py
```

The report opens with the journey outcomes (one row per reader), the counts, a
"Fix first" list (High findings with the widest reach) and an "Easy fixes" list
(`effort: small` and `confidence: confirmed`). If `report.py` prints findings
without effort or confidence, a reviewer skipped the fields: send that subagent back
to set them.

Before publishing, verify two or three "Fix first" findings and one or two easy fixes
yourself against the clones (open the file and line, confirm the claim). Drop or
downgrade any that do not hold, in the findings file, and rerun `report.py`.

Load the `artifact-design` skill, as the Artifact tool requires, then publish
`WORKDIR/report.html` with the Artifact tool (icon `book`). The page already follows
the artifact contract; do not redesign it. It starts private; sharing is done from the
page's Share menu.

Reply with: the link, the journey outcomes in one line each, counts per check and
severity, the number of easy fixes, three to five notable findings in one line each,
and what you verified. Do not paste the whole list. If the user
wants issues or fixes from the report, that is a separate step they ask for.

## Principles

- Every finding has evidence a reader can open: a `file:line`, a URL or a quote.
- Neutral wording about the docs, never about people. The report is shared.
- Read-only: no edits, commits, issues or PRs during the review.
- Keep `sources.md` the single place that says what is reviewed. If the user asks to
  add or drop a source permanently, change that file in the plugin repo.
