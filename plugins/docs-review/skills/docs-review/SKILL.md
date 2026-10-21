---
name: docs-review
description: Use when the user wants a review of documentation across the chap modeling platform and climate team repos (chap-core, chap-site, chap-frontend, chapkit, SDKs, model examples, open-climate-service, climate-tools, climate-app, climate-sre) to find holes. Checks docs against code, overlap and contradictions between sources, reader journeys, and structure and links, and produces a shareable HTML report. Triggers on "review the docs", "docs review", "find holes in the documentation", "check our documentation", "are the docs up to date".
---

# Docs review

Find holes in the documentation: what is wrong compared to the code, what is
duplicated or contradicts across sources, where a reader gets stuck, and what is
broken or unreachable. The run is read-only and ends in a report; nothing is edited,
and no issues or PRs are created.

The sources live in `sources.md` next to this file. The reader journeys are the user
stories in [dhis2-chap/user-stories](https://github.com/dhis2-chap/user-stories);
the review also checks that those stories still make sense against the docs, and
that they agree with the user stories open-climate-service keeps in its own
documentation.
Scripts are in `scripts/`, the reviewer briefs and the findings format in
`reference/`.

## Works in any agent

The workflow runs in Claude Code, Codex, Copilot or any agent that can run shell
commands and read files. Three steps use a feature not every agent has, and each
has a fallback:

| Step | With the feature | Without it |
|------|------------------|------------|
| 0. Ask | A question tool (Claude Code: `AskUserQuestion`) | Ask the same questions in one plain message and wait for the answer |
| 2. Review | Subagents, launched in parallel | Follow each brief yourself, one after the other |
| 3. Report | An Artifact tool that publishes HTML (Claude Code) | Hand over the HTML file path |

Decide once at the start which case you are in; do not try a tool you do not have.

## Requirements

- `gh` authenticated with read access to the `dhis2` and `dhis2-chap` orgs.
- `python3`, and `uv` (for `pick.py` and `structure.py`, which need PyYAML).
- A work directory: the agent's scratch or temp directory if it has one, else
  `mktemp -d`. Called `WORKDIR` below. `SKILL_DIR` is the directory of this file.

## 0. Ask

Read `sources.md`. Unless the user already said, ask once, in one question-tool call
or one plain message:

1. **Teams** (single select): Modeling platform, Climate data, or Both. Shared sources
   (`climate-sre`) are included with either.
2. **Scope** (single select): everything in the selected teams (default), pick
   groups, or name repos.
3. **Checks** (multi-select, all on by default): Docs vs code, Overlap between
   sources, Reader journeys (including whether the user stories still make sense),
   Structure and links.

If the user chose to pick groups, ask once more with the groups of the selected
teams as a multi-select (from `sources.md`: modeling has `core`, `chapkit`, `sdk`,
`examples`; climate has `ocs`, `climate-tools`, `climate-app`; shared has `sre`). If
they chose to name repos, take the names as free text.

## 1. Select, fetch, mechanical checks

```
cd WORKDIR
cp SKILL_DIR/scripts/*.py .
git -c credential.helper='!gh auth git-credential' clone -q --depth 1 https://github.com/dhis2-chap/user-stories.git stories
uv run --with pyyaml python pick.py SKILL_DIR/sources.md --stories stories --teams modeling,climate [--groups ...] [--repos ...] --checks code,overlap,journey,structure
python3 fetch.py
uv run --with pyyaml python structure.py
```

Skip the user-stories clone and `--stories` when the journey check is not selected.
`fetch.py` clones every selected repo shallow over HTTPS in parallel (seconds, not
minutes) and lists the repos in each org. If a clone fails, report it and continue
without that repo. Run `structure.py` even when the structure check is not selected:
its output keeps the other reviewers from reporting broken links. Delete
`findings_structure.json` before the report if structure was not selected.

## 2. Review

The review is a set of independent jobs, each described by a brief in `reference/`.
Fill `{workdir}`, `{skill_dir}`, `{today}` and `{checks}` in the briefs and write
them to `WORKDIR`. The jobs are:

- **Source reviewers** (if `code` or `structure` is selected): one per group in
  `config.json`, from `reference/subagent-source.md`.
- **Overlap reviewers** (if `overlap`): one per selected team, from
  `reference/subagent-overlap.md`.
- **Journey reviewers** (if `journey`): batches of at most three journeys from
  `config.json`, one team per batch, from `reference/subagent-journey.md`.
- **Stories reviewer** (if `journey`): one job, from `reference/subagent-stories.md`.
  It checks the user-stories repo itself: stories that no longer fit the docs,
  readers and goals the docs serve but no story covers, and whether the stories
  open-climate-service lists in `docs/project_description.md` still match the
  repo's copy.

Every job writes its own `findings_*.json` in the format in `reference/findings.md`,
so the jobs can run in any order and the report does not care who ran them.

**With subagents:** launch every job at once, in one message if the agent runs
them in parallel. Tell the user how many were launched. Do not do their work while
waiting and do not read their transcripts. When all have replied, check that each
expected `findings_*.json` exists and parses; rerun any subagent that failed or
reported tool errors.

**Without subagents:** do the jobs yourself, one at a time, in the order above.
For each job, read its brief and follow it exactly as a subagent would, including
the budget, the output file name and the "reply with" summary (keep that summary
as a note for the final reply instead of sending it). Finish one job and validate
its file before starting the next, so a long run can be resumed from the last
finished job. Tell the user the job count up front and give a one-line progress
note as each one finishes. If the run is too large to finish, prefer dropping
whole groups or journeys over covering every page thinly, and name what was
skipped in the reply.

## 3. Report

```
python3 report.py
```

The report opens with the journey outcomes (one row per reader), the counts, a
"Fix first" list (High findings with the widest reach) and an "Easy fixes" list
(`effort: small` and `confidence: confirmed`). If `report.py` prints findings
without effort or confidence, a reviewer skipped the fields: send that subagent
back to set them, or set them yourself if you did the job.

Before publishing, verify two or three "Fix first" findings and one or two easy fixes
yourself against the clones (open the file and line, confirm the claim). Drop or
downgrade any that do not hold, in the findings file, and rerun `report.py`.

**With an Artifact tool (Claude Code):** load the `artifact-design` skill, as the
Artifact tool requires, then publish `WORKDIR/report.html` with the Artifact tool
(icon `book`). The page already follows the artifact contract; do not redesign it.
It starts private; sharing is done from the page's Share menu.

**Without one:** the report is `WORKDIR/report.html`, a self-contained page with no
external dependencies that opens in any browser. If `WORKDIR` is a temporary
directory, copy the file to `docs-review-<today>.html` in the user's current
directory so it survives the session, and give that path. Sharing is up to the
user; do not upload it anywhere unless they ask.

Reply with: the link or path, the journey outcomes in one line each, counts per
check and severity, the number of easy fixes, three to five notable findings in one
line each, and what you verified. Do not paste the whole list. If the user wants
issues or fixes from the report, that is a separate step they ask for.

## Principles

- Every finding has evidence a reader can open: a `file:line`, a URL or a quote.
- Neutral wording about the docs, never about people. The report is shared.
- Read-only: no edits, commits, issues or PRs during the review.
- Keep `sources.md` the single place that says which repos are reviewed, and the
  user-stories repo the single place for journeys. The review proposes story
  changes in the report; if the user asks to add or drop a source or a journey
  permanently, change the file there, as a separate step.
