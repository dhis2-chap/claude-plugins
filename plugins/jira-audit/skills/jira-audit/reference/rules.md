# Rules, confidence and tiers

## Rules

| ID | Rule | Who decides | Default |
|---|---|---|---|
| S1 | Open issue; a merged PR that references it (not partially) delivers it; no open PR | script hints, reviewer confirms by reading the PR | Medium → High if the PR covers the whole issue |
| S2 | In Review, but no open PR references it | script, reviewer checks for an unpushed branch or a PR without the key | High |
| S3 | In Progress, no issue or PR activity for `stale_days`, no open PR | script | High |
| S4 | Done, but every referenced PR was closed unmerged or is still open | script only (Done issues are not reviewed) | Low |
| S5 | Backlog / To Do / Selected for Development, but an open or merged PR references it | script, reviewer confirms | Medium |
| S6 | Delivered by a merged PR or commit that never cited the key | reviewer only: keyword search in `unlinked_prs.json` and the master clone, confirmed in the diff | Medium/High |
| E1 | Epic open, every child Done | script; **a note, not an action**, when the epic carries an umbrella label or calls itself a placeholder | Medium |
| E2 | Epic Done, children open | script | High |
| E3 | Epic description no longer matches its children | reviewer | Medium |
| E4 | Open epic with no children | script, note only | Note |
| R1 | Open epic not listed under any initiative on the roadmap page (`roadmap.md`) | script; adding it to the page is up to the team | Medium |
| R2 | Open epic that no idea in the ROADMAP project links (`roadmap_ideas.jsonl`); the evidence names ideas with similar text | script (`roadmap.py`); a strong match proposes `link_implements:<idea>` | Medium with a strong match, Low with weak candidates, Note with none |
| R3 | ROADMAP idea with no CLIM epic linked. Ideas in `roadmap_delivery_statuses` (taken onto the roadmap) should have one; earlier-stage ideas are only listed when a similar open epic exists | script; a strong match proposes `link_implements:<epic>` | Medium / Low |
| R4 | ROADMAP idea linked to a CLIM epic with `Relates` or another type instead of the delivery link (`roadmap_delivery_link`), so the idea shows no delivery progress | script | High |
| D1 | Description claims (paths, endpoints, commands, "currently X") no longer match master or merged PRs | reviewer, with a `file:line` or PR as evidence | Medium/High |
| D2 | Description empty or too thin to pick up | reviewer | Low/Medium |
| D3 | Approach superseded by a later issue, PR or decision | reviewer, citing it | Medium |
| U1 | Duplicate: same work | duplicates reviewer, both issues read | High/Medium |
| U2 | Overlap, split, or follow-up with no Jira link | duplicates reviewer or any reviewer who notices | Medium |
| C1 | Open issue with no component, but keyword match or parent epic in scope | script | Medium |
| H1 | Assignee is not a PR author (after mapping display names to GitHub logins) | script, note | Note |
| H2 | In Progress / In Review with no assignee | script, note | Note |
| H3 | Open, only in closed sprints | script, note | Note |
| H4 | Open Task/Story/Bug with no epic | script, note | Note |

Mechanical S1/S2/S3/S5/E1 hits on an issue a reviewer read are dropped at merge
time: the reviewer either wrote their own finding or refuted the hint.

## Confidence

- **High**: direct evidence and no other sensible reading.
- **Medium**: strong evidence; someone with context should confirm.
- **Low**: a signal worth a glance.
- **Note**: hygiene, no action proposed.

## Tiers of proposed changes

| Tier | What | Rule |
|---|---|---|
| 1 | Apply on one approval. Reversible in one click, backed by a PR or an existing epic, nobody loses work. | S1/S6 High → Done; S5 with an open PR → In Progress; U2 "relates to" links; C1 where the parent epic has the component; R4 delivery links (the pair is already linked, only the type is wrong) |
| 2 | One glance per item. | Medium closes; In Review → In Progress; stale → Backlog; close/link as duplicate; C1 by keyword; E1; R2/R3 links suggested by text similarity |
| 3 | Needs the ticket owner. | Every description edit (D1, D2, D3, E3) |

**No transition reaches tier 1 on a count alone.** E1 (all children done) sits
in tier 2 because long-running epics legitimately stay open; S1 needs the
reviewer to have read the PR against the issue text.

## Lessons from the first run (2026-10-02)

- Display names vs GitHub logins: `ivar`/`ivargr`, `Knut Dagestad Rand`/`knutdrand` are the
  same person. Keep `gh_logins` in config up to date or H1 produces noise.
- Placeholder epics (`ch-initiative` label, "placeholder" in the text) must not be closed
  because their children happen to be done.
- The first full run found ~110 proposed changes; most were backlog accumulated over months.
  A sprint-scoped rerun after applying tier 1 should produce a short list.
- The duplicate script needed loose thresholds (TF-IDF 0.22, Jaccard 0.34) to surface anything,
  and the reviewer dropped ~90% of candidates. Most useful U2 hits came from reviewers noticing
  unlinked follow-ups while reading, not from the similarity pass.

## Lessons from adding the roadmap-idea rules (2026-11-11)

- Jira has no Initiative type in CLIM. "Initiatives" are headings on the Confluence roadmap page
  (R1) and ideas in the Product Discovery project ROADMAP (R2-R4). The `ch-initiative` label marks
  umbrella epics, nothing more.
- Only `Polaris work item link` (epic "implements" idea) counts as delivery on an idea. Of the
  Chap and Open Climate Service ideas on 2026-11-11, 9 had it, 6 were linked with `Relates`
  only, and 28 had no CLIM link at all.
- Epic-to-idea similarity uses character n-grams (3-5) on summary plus the first 300 characters
  of the description. On the 2026-11-11 data every already-linked pair scored 0.34 or more
  except three (0.10-0.20), and the best unlinked pairs scored 0.20-0.24 and were all real
  matches on reading, while pairs at 0.15-0.17 were mostly noise. Hence `STRONG` 0.30 (propose
  the link, tier 2) and `WEAK` 0.18 (list as a candidate). Word TF-IDF separated the two groups
  worse. Expect a Low R2/R3 row for most unlinked epics and ideas; the candidates are there to
  be read, not applied.
- Ideas are selected by Product Areas (`cf[10216]`) or Domain (`cf[10566]`), which
  `write-roadmap-idea` always sets. An idea without either field is invisible to R3 and R4.
