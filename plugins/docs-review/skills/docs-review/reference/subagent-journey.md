# Journey reviewer brief

Fill the placeholders, write this to `{workdir}/JOURNEY_BRIEF.md`, then launch one
subagent per batch of journeys (at most three journeys per subagent, one team per
batch) with the prompt: "Read `{workdir}/JOURNEY_BRIEF.md` and follow it for journeys
<numbers>. Everything is read-only."

---

You follow the documentation the way a specific reader would, to find where they
would get stuck. READ-ONLY: do not edit, commit, push, or create issues or PRs. Do not
install software or run the commands; read them and check them against the code.

## Where things are

- Work dir: `{workdir}`. `config.json` has `journeys` (numbered from 1 in list order),
  taken from the user stories: each an `id`, a `reader`, a `goal`, `starts_at` (repo
  and path, in order) and optionally `done_when`. When `done_when` is given, the goal
  is reached only if every item is.
- Clones in `{workdir}/repos/<name>/`. Docs at each source's `docs` paths; the code
  is the rest of the repo.
- Findings format and severity: `{skill_dir}/reference/findings.md`. Read it first.

Today is {today}.

## Method, per journey

1. Start at the given page. Read it as the reader: someone with that role and no
   inside knowledge of the team.
2. Follow the path they would take: "next" links, the obvious next page in the nav,
   links in the text, and READMEs of repos they are sent to. Write the path down as
   you go.
3. At every step ask: is it clear what to do next? Is a prerequisite assumed but not
   explained or linked (an account, an installed tool, a running service, data)? Do
   the commands and file names match what the code and the previous step produced?
   Does the path send the reader somewhere outdated or circular?
4. Stop when the goal is reached or the reader would be stuck. A dead end that
   cannot be completed from the docs is High.

## Output

Write `{workdir}/findings_journey_<first number>.json` (findings format,
`check: "journey"`, `rule` such as `journey-gap`, `journey-dead-end`,
`journey-missing-prereq`, `journey-outdated-step`). Put the step in `where` and,
in `evidence`, the path taken so far as one string ("newcomer.md -> minimalist_example
README -> ..."). Set `journey` to the journey's number
on every finding. Add one finding with `rule: "journey-summary"`, `severity: "Low"`,
per journey, with `outcome` set to `reached`, `reached with gaps` or `stuck`, a title
that says the outcome and where, and the full path as evidence. The report opens with
these summaries. Validate that it parses.

Reply with only: per journey, reached or stuck and the number of findings, plus any
problems. Do not paste the findings.
