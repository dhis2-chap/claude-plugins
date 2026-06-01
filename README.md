# DHIS2 CHAP — Claude Code plugins

Internal [Claude Code](https://code.claude.com) plugin marketplace for people
working on the DHIS2 CHAP modeling platform. Add it once, then install the
plugins you want.

## Use the marketplace

In Claude Code, add this repo as a marketplace (one time):

```
/plugin marketplace add dhis2-chap/claude-plugins
```

Then browse and install plugins:

```
/plugin install hello-world@dhis2-chap
```

Useful management commands:

```
/plugin list                              # what's installed
/plugin marketplace update dhis2-chap     # pull the latest plugin list
/plugin disable <plugin>@dhis2-chap       # turn off without uninstalling
/plugin uninstall <plugin>@dhis2-chap     # remove
```

### Auto-suggest the marketplace to a whole repo (optional)

Add this to a project's `.claude/settings.json` so anyone opening that repo in
Claude Code is prompted to enable the marketplace and listed plugins:

```json
{
  "extraKnownMarketplaces": {
    "dhis2-chap": {
      "source": { "source": "github", "repo": "dhis2-chap/claude-plugins" }
    },
    "enabledPlugins": {
      "hello-world@dhis2-chap": true
    }
  }
}
```

## Repository layout

```
.
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest — lists every plugin
├── plugins/
│   └── hello-world/            # one directory per plugin
│       ├── .claude-plugin/
│       │   └── plugin.json      # plugin manifest
│       ├── commands/            # slash commands (.md files)
│       │   └── hello.md
│       └── skills/              # skills (one folder each, with SKILL.md)
│           └── chap-greeting/
│               └── SKILL.md
└── README.md
```

## Add a new plugin

1. Copy `plugins/hello-world/` to `plugins/<your-plugin>/`.
2. Edit `plugins/<your-plugin>/.claude-plugin/plugin.json` — set `name`,
   `description`, `version`.
3. Add your own commands, skills, agents, hooks, or MCP servers. A plugin can
   contain any of:
   - `commands/` — slash commands (`.md` files with a `description` frontmatter).
   - `skills/<skill-name>/SKILL.md` — skills (auto-triggered by their `description`).
   - `agents/` — subagent definitions.
   - `hooks/hooks.json` — event hooks.
   - `.mcp.json` — MCP server config.
4. Register it in `.claude-plugin/marketplace.json` by adding an entry to the
   `plugins` array (`name` + `source: "./plugins/<your-plugin>"`).
5. Validate, commit, and open a PR:

   ```
   /plugin validate .
   ```

6. Once merged, teammates run `/plugin marketplace update dhis2-chap` to see it.

## Notes

- **Versioning:** bump `version` in the plugin's `plugin.json` on each change so
  installs pick up updates. (Omit `version` entirely to version by git commit
  instead.)
- **Don't** put `commands/`, `skills/`, `agents/`, or `hooks/` inside
  `.claude-plugin/` — only the manifest (`plugin.json`) goes there.
