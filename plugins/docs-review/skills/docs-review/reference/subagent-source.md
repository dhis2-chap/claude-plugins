# Source reviewer brief

Fill the placeholders, write this to `{workdir}/SOURCE_BRIEF.md`, then launch one
subagent per group with the prompt: "Read `{workdir}/SOURCE_BRIEF.md` and follow it
for group <group>. Everything is read-only." Without subagents, follow the brief
yourself for each group in turn; "you" below then means you.

---

You review the documentation of one group of repos against their code. READ-ONLY: do
not edit, commit, push, or create issues or PRs.

## Where things are

- Work dir: `{workdir}`. `config.json` lists every selected source (`sources`); yours
  are the ones whose `group` is your group. Each has `docs` paths, `published` and
  `audience`.
- Shallow clones of every selected repo are in `{workdir}/repos/<name>/`. Code
  outside the `docs` paths is the truth the docs are checked against. When a page
  documents another repo (e.g. chap-core docs describing chapkit), check against that
  clone if it is there.
- `{workdir}/findings_structure.json` already covers broken links, dead repo links and
  pages missing from the nav. Do not repeat those.
- Findings format and severity: `{skill_dir}/reference/findings.md`. Read it first.

Today is {today}.

## What to check

Checks selected for this run: {checks}. Do only those of the two below that are
selected.

**code: docs against code.** For each page in your sources:

1. Pick out concrete claims a reader would act on: shell and CLI commands and their
   flags, config keys and file formats, REST endpoints, environment variables, make
   targets, file and module paths, function and class names, install commands,
   version requirements, default values, and "X does Y" statements about behaviour.
2. Check each against the code with grep (CLI definitions, routers, settings
   classes, Makefiles, pyproject, DESCRIPTION, Dockerfiles, compose files). Report
   claims that are wrong or no longer true.
3. The other direction: list the user-facing surface in the code (CLI commands,
   public endpoints, config options, public API of SDKs, make targets meant for
   users) and report significant parts that no page in any selected source
   documents. Check the other clones before calling something undocumented. Skip
   internal and test-only code.
4. Also flag pages that are clearly obsolete: they describe a removed flow, say
   "deprecated", "old", "TODO", "coming soon" without context, or contradict the
   current README of the same repo.

**structure (judgement part).** Beyond what the script found: pages that are
placeholders or near empty, a section whose title promises something the pages do
not cover, and READMEs that do not say what the repo is for or how to start.

For the `examples` group (many small repos): check that each README's run
instructions match the repo (files, commands, MLproject or chapkit config) and say
which chap-core version or workflow they target if the repo depends on one. Note
examples that use a flow the main docs no longer recommend.

## Budget

Work page by page; do not read whole code bases. Roughly 2-6 tool calls per page,
more for reference pages full of commands. If your group has more than about 60
pages, cover reference and getting-started pages first and list what you skipped in
your reply.

## Output

Write `{workdir}/findings_src_<group>.json` (a JSON list in the findings format, `check`
set to `code` or `structure`). Set `effort` and `confidence` on every finding as
`findings.md` defines them. Validate that it parses. Name any helper script
`src_<group>_*.py`.

Reply with only: counts by check and severity, pages reviewed, pages skipped, and any
problems. Do not paste the findings.
