---
name: chap-brain
description: Use the Chap team vault (dhis2-chap/chap-first-brain) as read-only context from any Chap repo. Use when work needs what the team calls things, believes, decided or wrote before. That covers naming and wording in UI text, docs, comments, commit messages and PR descriptions; design choices that touch team positions (for example how models are evaluated or configured); questions like "what did we decide about X" or "what did the meeting say"; user stories; partners and countries; and drafting Jira issues, grants, reports or slides. Also use it to check a draft or a diff for wrong terms, conflicts with team principles and claims the vault contradicts.
---

# Chap brain

The team vault, `dhis2-chap/chap-first-brain`, is a private git repository of Markdown
that holds the team's terminology, principles, reports and meeting notes. This skill
lets a session in any other repo (chap-core, chap-frontend, chapkit, ...) read it.

## Find the vault

In Claude Code, the plugin's session-start hook prints a line `chap-brain: the Chap team
vault is at <path>` and has already pulled it. Use that path.

Without that line (other agents, or the hook found nothing), look in this order:
`$CHAP_BRAIN_DIR`, a `chap-first-brain` folder next to the current repo or a folder
above it, then `~/chap-first-brain`. Run `git -C <vault> pull --ff-only` once if it was
not pulled this session. If there is no clone, tell the user to clone
`dhis2-chap/chap-first-brain` next to their Chap repos, and carry on without it.

If the current repo *is* the vault, stop: its own `AGENTS.md` applies instead.

## Read only

Never create, edit, move or delete files in the vault, and never run git or DVC write
commands there (commit, push, `dvc add`, `dvc push`). Pulling is the only exception.
When something should be saved to the vault (a decision, a report, a new term, a
suggestion), say so and suggest the user opens a session in the vault to do it, where
its conventions and scripts apply.

## What to read

Read only what the task needs. The vault's `AGENTS.md` has the full rules; read it when
the task goes beyond a quick lookup.

| Question | Read |
|---|---|
| What is this called, how is it spelled, what does a term mean | `Vault-overviews/terminology.md` |
| What does the team believe or has it decided | `Human-input/principles.md` (each entry has a source and a status) |
| What did a meeting say or decide | `Archive/files/gdrive/meeting-notes/` (start from its `index.md`) |
| Has the team looked into this before | `Human-AI-collaboration/Reports/ReportOverview.md`, then the report |
| Who uses Chap and what they need to do | The user stories in `dhis2-chap/user-stories`, as the vault's `AGENTS.md` describes |
| Which sources are trusted | `Vault-overviews/approved-sources.md` |
| How to file Jira issues and roadmap ideas | The "Jira" and "Roadmap ideas" sections of `AGENTS.md` |

`Archive/files/` is gitignored, so a plain `grep -r` from the vault root skips it. Search
it explicitly: `grep -ril <term> <vault>/Archive/files`. If it is empty, the archive has
not been downloaded yet; don't conclude there is nothing there.

## Flag mistakes

When the work in front of you (code, UI strings, docs, a draft, a diff, the user's own
wording) disagrees with the vault, say so, cite the vault file, and suggest the fix.
Don't change things silently. Look for:

- **Terms**: a name or spelling that differs from `terminology.md`, or one term used in
  two senses.
- **Principles**: a design or text that goes against an entry in `principles.md`. Name
  the entry and let the user decide whether it is a deliberate exception.
- **Facts**: a statement about Chap (partners, deployments, results, funding, decisions)
  that the vault contradicts, or that has no source at all. Facts come from the user or
  the vault, never from general knowledge.

Keep it proportionate: one line per finding, and nothing when nothing is wrong.

## Keep private things private

The vault is private; many Chap repos are public. Don't copy partner names, meeting
content, people's names, unpublished results or vault file paths into code, commits,
PRs, issues or docs of a public repo without the user's explicit go-ahead. Terminology
and the wording of a principle are fine to apply.
