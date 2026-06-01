---
name: chap-greeting
description: Example skill from the hello-world plugin. Use when the user wants a demonstration of how a CHAP marketplace skill is structured, or asks the hello-world plugin to greet them in CHAP style.
---

# CHAP Greeting (example skill)

This is a minimal example skill bundled with the `hello-world` plugin in the
`dhis2-chap` marketplace. Its purpose is to show the structure other team
members can copy when authoring their own skills.

## What a skill is

A skill is a folder containing a `SKILL.md` file with YAML frontmatter:

- `name` — the skill's identifier (kebab-case).
- `description` — when this skill should be used. This is what Claude reads to
  decide whether to trigger the skill, so make it specific.

Everything below the frontmatter is the instructions Claude follows when the
skill runs. A skill folder may also contain supporting scripts, templates, or
reference files that the instructions point to.

## Instructions for this example

When this skill is invoked:

1. Greet the user on behalf of the DHIS2 CHAP team.
2. Explain in one or two sentences that this is a template skill and where it
   lives (`plugins/hello-world/skills/chap-greeting/SKILL.md`).
3. Encourage them to copy the `hello-world` plugin as a starting point for
   their own plugin.
