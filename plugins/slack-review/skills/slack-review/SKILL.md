---
name: slack-review
description: "Review recent activity in the team's approved Slack channels: messages nobody answered, a TL;DR of each thread, and the actions people need to take. Use when asked what was missed in Slack, for a Slack catch-up, a weekly Slack review, unanswered Slack questions, or action items from a Slack channel. Reads Slack through the slack_* tools of the chap-first-brain MCP server."
metadata:
  internal: true
---

# Slack review

Go through recent Slack activity and report three things: messages that still need an answer, what each thread was about, and what people need to do. The review is a draft for the user. Never post it to Slack or anywhere else without their go-ahead.

## 0. Check the tools

Slack is read with the `slack_*` tools of the chap-first-brain MCP server: `slack_channels`, `slack_history`, `slack_thread` and `slack_find`. The tool names may carry a prefix, such as `mcp__chap-first-brain__slack_history`.

If those tools are not available, stop and tell the user to connect the server. Point them to "Use it from Claude Code" in the server's README in dhis2-chap/chap-first-brain (`AI-internal/mcp-server/README.md`). Don't try another way into Slack.

If a tool answers that Slack isn't configured, say so and stop.

## 1. Settle the scope

- **Channel:** use the one the user names. If they name none, review every channel `slack_channels` lists.
- **Period:** the last 7 days, today included, unless the user says otherwise (at most 31 days). Work in UTC dates: the period runs from `start` to `today`.

## 2. Read the messages

For each channel, call `slack_history` with:
- `after` = 30 days before `start`
- `before` = the day after `today`
- `max_messages` = 1000

The extra 30 days are context only. They let you see threads that started earlier but got replies during the period. Report only on messages and replies dated inside the period. If the history says only part of the range was returned, or a thread looks cut short, read the rest with `slack_thread`.

## 3. Write the review

For each channel, write the three parts below. Leave out a part that would be empty.

```
## #<channel>: <start> to <today>

### Unanswered
- <date> <author>: <the message's point in one line> (ts <ts>)

### Threads
- **<topic>** (<date started>, <n> replies, <people>): <TL;DR in one or two sentences>. Status: resolved / open / waiting on <person or thing>.

### Actions
- [ ] <owner, or "unassigned"> — <action> (<date>, <thread topic or message>)
```

**Unanswered:** top-level messages from the period that got no reply in their thread and no answer later in the channel, and that need one: a question, a request, a proposal, a problem report, or a review or decision asked for.
- Leave out greetings, thanks, jokes and social chat, emoji-only posts, join and leave notices, bot posts, and announcements or FYIs that ask nothing.
- When unsure, include it.

**Threads:** one entry per thread with replies in the period, most active first. Say what was discussed and where it landed.

**Actions:** things someone needs to do, taken only from what was said:
- commitments ("I'll…")
- requests to a person or group
- decisions that need follow-up
- questions under Unanswered that someone should answer

Don't invent actions or owners. If nobody is named, write "unassigned".

When there is more than one channel, write one section per channel, then end with a combined `## All actions` list grouped by owner.

If a channel had no messages in the period, say so in one line.

## Rules

- Base everything on the messages. Never fill in from general knowledge.
- Name people as they appear in Slack.
- Quote only short phrases.
- Keep it short enough to read in a couple of minutes.
- The channels can be private. Keep their content out of public repos, issues and pull requests, and don't share it outside the team without the user's go-ahead.
