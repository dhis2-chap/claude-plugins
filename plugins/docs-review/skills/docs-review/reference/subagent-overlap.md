# Overlap reviewer brief

Fill the placeholders, write this to `{workdir}/OVERLAP_BRIEF.md`, then launch one
subagent per selected team with the prompt: "Read `{workdir}/OVERLAP_BRIEF.md` and
follow it for team <team>. Everything is read-only." Without subagents, follow the
brief yourself for each team in turn; "you" below then means you.

---

You look for the same topic covered in more than one place across the selected
documentation sources. READ-ONLY: do not edit, commit, push, or create issues or PRs.

## Where things are

- Work dir: `{workdir}`. `config.json` lists the selected sources. Yours are those of
  your team plus any `shared` ones. If the other team's sources are in `config.json`
  too, also compare against them where a topic crosses over (e.g. OCS feeding climate
  data into Chap). Only use sources listed in `config.json`.
- Clones in `{workdir}/repos/<name>/`, docs at each source's `docs` paths.
- Findings format and severity: `{skill_dir}/reference/findings.md`. Read it first.

Today is {today}.

## Method

1. Build a topic map: for every page, its title and headings
   (`grep -n '^#' ...`). Write it to `{workdir}/overlap_<team>_topics.tsv` (source,
   path, headings) so you can work from it.
2. Find topics covered in two or more places: installation and setup, data formats,
   model configuration, MLproject and chapkit, evaluation and metrics, DHIS2
   connection, deployment, workshop and webinar material, and anything else that
   appears more than once. Known example: the webinar series exists in both
   chap-site `docs/2026-webinar-series` and chap-core
   `docs/kigali-workshop/kigali-webinar-series`.
3. For each overlap, read the copies and decide:
   - **contradiction** (Medium, High if following one copy fails): they disagree on a
     command, version, step or recommendation. Quote both, and say which matches the
     code if you can tell with a quick grep.
   - **diverged copy** (Medium): the same page copied into two places and edited
     separately. Say which looks newer (git log on the clone is shallow, so compare
     content).
   - **duplicate** (Low): agree today, but two places to maintain. Suggest which
     should be the single home and where the other should link.
   Same-topic pages for different audiences (a tutorial and a reference) are not a
   problem unless they contradict.

4. **Terminology.** If `{workdir}/brain/Vault-overviews/terminology.md` exists (from
   chap-first-brain, the team's knowledge base), read it and check the pages of your
   sources against it: a name written in a form it calls outdated (such as "CHAP"),
   or a term used in a sense it does not list or mixing two senses it keeps apart
   (such as "template" or "model"). Skip entries marked **To confirm**. Report each
   term once, with every page in `where` and the terminology entry quoted in
   `evidence` (rule `terminology`; Low, or Medium when the mix-up can lead the reader
   to the wrong thing). Without the file, skip this step.

5. **Principles.** If `{workdir}/brain/Human-input/principles.md` exists (from
   chap-first-brain: what the team believes and has decided, one numbered entry
   each with a Source and a Status), read it and check it against the pages of your
   sources, in both directions:
   - **A page contradicts an entry** (rule `principle-conflict`): the page tells the
     reader to do, or states as fact, something an entry rules out, for example
     sending data out of the country, or a step where the HISP Centre approves what a
     country runs. Medium; High when a reader following the page would act against
     the entry. Quote the page and the entry in `evidence`.
   - **An entry looks wrong** (rule `principle-doubt`): the docs or the code describe,
     as current and deliberate, something an entry says we do not do (a documented
     feature, a default, a documented process), or the entry's Source is a page that
     no longer says it. Low. Quote both sides; the suggestion is to confirm or change
     the entry, not the docs. This is the one place the review questions the team's
     own material rather than the product docs.
   Skip entries whose Status is `proposal`. For entries marked `to confirm`, report
   as usual but set `confidence: likely` and name the status in `evidence`. Report
   each entry once, with every page in `where`. Without the file, skip this step.

Report disagreements between pages (within one source or across sources). Leave
"one page is wrong about the code" to the source reviewers, who check docs against
code; if both pages are wrong, or only the code settles it, report it once as a
contradiction and say which side the code supports.

## Output

Write `{workdir}/findings_overlap_<team>.json` (findings format, `check: "overlap"`,
`where` listing every copy). Set `effort` and `confidence` on every finding as
`findings.md` defines them. Validate that it parses.

Reply with only: number of topics mapped, counts by rule and severity, whether the
terminology and principles files were used, and any problems. Do not paste the
findings.
