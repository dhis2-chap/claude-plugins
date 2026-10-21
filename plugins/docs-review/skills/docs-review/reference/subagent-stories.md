# Stories reviewer brief

Fill the placeholders, write this to `{workdir}/STORIES_BRIEF.md`, then launch one
subagent with the prompt: "Read `{workdir}/STORIES_BRIEF.md` and follow it.
Everything is read-only." Without subagents, follow the brief yourself; "you"
below then means you.

---

You check that the user stories the team keeps in
[dhis2-chap/user-stories](https://github.com/dhis2-chap/user-stories) still make
sense against the documentation, and whether the documentation shows readers or
goals the stories do not cover yet. READ-ONLY: do not edit, commit, push, or create
issues or PRs. Propose changes to the stories as findings; applying them in the
user-stories repo is a separate step the team decides on.

## Where things are

- Work dir: `{workdir}`. The stories repo is cloned at `{workdir}/stories/`: a
  `README.md` with the format and a status section, and one YAML file per domain
  (`modeling.yaml`, `climate-data.yaml`, `cross-domain.yaml`).
- `config.json` has `journeys`: the stories whose starting repo is selected for
  this run, numbered from 1 in list order, and `sources`: the selected repos with
  their `docs` paths and `audience`.
- Clones of the selected repos in `{workdir}/repos/<name>/`.
- open-climate-service keeps its own user stories in its documentation, in
  `docs/project_description.md` (and a product description in `PRD.md`). The
  climate stories in the stories repo were copied from there, so the two drift
  apart unless someone compares them. That comparison is part of this job when
  `open-climate-service` is in `config.json`; if it is not, skip it and say so.
- Findings format and severity: `{skill_dir}/reference/findings.md`. Read it first.

Today is {today}.

## What to check

Limit yourself to the stories in `config.json` plus the whole file of any domain
that has at least one selected story, so a story is not judged without its
neighbours.

**Stories that no longer make sense.** For each story: do the `starts_at` paths
exist in the clone, and is the page still the natural place for that reader to
start? Does the goal describe something the docs and code still offer, in the
flow they now recommend? Is the reader still a real audience of the selected
sources (compare with `audience` in `config.json` and with who the READMEs and
getting-started pages address)? Report stories to retire, reword or repoint, and
`done_when` items that are no longer checkable. Do not repeat what the journey
reviewers report: they say where a reader gets stuck, you say whether the story
itself is still right.

**Stories that are missing.** Read the entry pages of the selected sources (README,
index, getting started, tutorials) and the status section of the stories README.
List readers and goals the documentation clearly serves that no story covers, for
example a reader type with its own guide, a tutorial with an end state, or a flow
the docs spend many pages on. Suggest each as one story in the repo's format: an
`id`, a `reader`, a one-sentence `goal` and the `starts_at` page. Prefer a few
stories the team would plausibly adopt over an exhaustive list.

**open-climate-service stories against the repo.** Read the user stories in
`docs/project_description.md` (and `PRD.md` if it adds any) and compare with
`climate-data.yaml` and `cross-domain.yaml` in the stories repo:

- a story in the OCS docs with no counterpart in the stories repo: `story-ocs-missing`;
- a story in the stories repo that the OCS docs no longer have, or whose reader
  or goal the OCS docs now state differently: `story-ocs-diverged`. Quote both
  sides and say which looks newer from the content.

If the two sets agree, say so in your reply; that is a useful result and needs no
finding.

## Severity

Impact on the review and on the team's picture of its readers, since no end user
reads the stories repo:

- **Medium**: a story that cannot be walked any more (a `starts_at` page gone, a
  goal the product dropped), or an OCS story that contradicts the repo copy.
- **Low**: wording to update, a `done_when` to add, a missing story to consider,
  an OCS story to copy over.

Set `effort` and `confidence` as `findings.md` defines them. A proposed new story
is `effort: small` only when the suggestion contains the full story.

## Output

Write `{workdir}/findings_stories.json` (findings format, `check: "journey"`, no
`journey` number unless the finding is about one selected story, then its number).
Use `rule` values `story-outdated`, `story-broken-start`, `story-missing`,
`story-ocs-missing`, `story-ocs-diverged`. Set `source` to `user-stories`, or to
`open-climate-service` when the fix belongs in the OCS docs. `where` entries such as
`user-stories/climate-data.yaml:12` and `open-climate-service/docs/project_description.md:40`
become links in the report. Validate that it parses.

Reply with only: stories checked, counts by rule and severity, whether the OCS
stories agree with the repo, and any problems. Do not paste the findings.
