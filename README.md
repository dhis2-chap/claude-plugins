# DHIS2 CHAP — Claude Code plugins

Internal [Claude Code](https://code.claude.com) plugin marketplace for people
working on the DHIS2 CHAP modeling platform.

A "marketplace" is just this GitHub repo. You add it to Claude Code once, then
install any plugins you want from it. Plugins can add slash commands, skills,
subagents, hooks, and MCP servers to your Claude Code.

---

## Prerequisites

- [Claude Code](https://code.claude.com) installed and signed in.
- Access to GitHub (this repo is public, so no extra setup is needed).

---

## 1. Add the marketplace (once)

Run this inside Claude Code:

```
/plugin marketplace add dhis2-chap/claude-plugins
```

Claude Code fetches the repo and registers it under the name **`dhis2-chap`**.
You only need to do this once per machine.

---

## 2. Find and install a plugin

Browse everything available, then install what you want:

```
/plugin
```

This opens the plugin manager UI where you can see the marketplace's plugins and
install them interactively.

Or install directly by name, using the `<plugin>@dhis2-chap` form:

```
/plugin install hello-world@dhis2-chap
```

After installing, the plugin's commands and skills are available immediately.
For example, the `hello-world` plugin adds a `/hello` command — try it to
confirm everything works.

### Install scope (optional)

By default a plugin is installed for you only (user scope). You can also share
an install through a repo's checked-in settings:

```
/plugin install <plugin>@dhis2-chap --scope project   # shared via .claude/settings.json
/plugin install <plugin>@dhis2-chap --scope local      # this repo only, gitignored
```

---

## 3. Manage installed plugins

```
/plugin list                                # show installed plugins
/plugin disable <plugin>@dhis2-chap         # turn off without uninstalling
/plugin enable  <plugin>@dhis2-chap         # turn back on
/plugin uninstall <plugin>@dhis2-chap       # remove completely
```

---

## 4. Get updates

New plugins and new versions land in this repo over time. Refresh your local
copy of the marketplace to see them:

```
/plugin marketplace update dhis2-chap
```

Then install or update plugins as usual. Installed plugins pick up new versions
when the plugin's `version` is bumped (or, for unversioned plugins, when the
git commit changes).

---

## Auto-suggest plugins to a whole repo (optional)

If you want everyone who opens a particular CHAP code repo in Claude Code to be
prompted to enable this marketplace and a set of plugins, add this to that
repo's `.claude/settings.json` and commit it:

```json
{
  "extraKnownMarketplaces": {
    "dhis2-chap": {
      "source": { "source": "github", "repo": "dhis2-chap/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "hello-world@dhis2-chap": true
  }
}
```

---

## Available plugins

| Plugin | Description |
|--------|-------------|
| `hello-world` | Example plugin — a `/hello` command and an example skill. Copy it as a template for new plugins. |

---

## Contributing a plugin

Want to share a plugin with the team? See **[CONTRIBUTING.md](./CONTRIBUTING.md)**
for the repo layout and a step-by-step guide.

---

## Troubleshooting

- **A new command/skill doesn't show up after installing.** Run
  `/plugin list` to confirm it's installed and enabled. If you just published a
  change, run `/plugin marketplace update dhis2-chap` first, then reinstall.
- **The marketplace name.** Plugins are always referenced as
  `<plugin>@dhis2-chap`, regardless of the repo name (`claude-plugins`). The
  `dhis2-chap` part comes from the `name` field in `.claude-plugin/marketplace.json`.
