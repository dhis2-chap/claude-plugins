# Contributing a plugin

This repo is the `dhis2-chap` Claude Code plugin marketplace. To share a plugin
with the team, add it here and open a PR.

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
├── CONTRIBUTING.md
└── README.md
```

## Steps

1. **Copy the template.** Duplicate `plugins/hello-world/` to
   `plugins/<your-plugin>/`.

2. **Edit the manifest.** In `plugins/<your-plugin>/.claude-plugin/plugin.json`
   set `name`, `description`, and `version`.

3. **Add your components.** A plugin can contain any of:
   - `commands/` — slash commands (`.md` files with a `description` frontmatter).
   - `skills/<skill-name>/SKILL.md` — skills (auto-triggered by their `description`).
   - `agents/` — subagent definitions.
   - `hooks/hooks.json` — event hooks.
   - `.mcp.json` — MCP server config.

   Do **not** put `commands/`, `skills/`, `agents/`, or `hooks/` inside
   `.claude-plugin/` — only the manifest (`plugin.json`) goes there.

4. **Register the plugin.** Add an entry to the `plugins` array in
   `.claude-plugin/marketplace.json`:

   ```json
   {
     "name": "<your-plugin>",
     "source": "./plugins/<your-plugin>",
     "description": "What it does.",
     "version": "0.1.0"
   }
   ```

5. **Validate.** From the repo root:

   ```
   /plugin validate .
   ```

   (or `claude plugin validate .` from a terminal).

6. **Open a PR.** Once it's merged, teammates run
   `/plugin marketplace update dhis2-chap` to see it, then
   `/plugin install <your-plugin>@dhis2-chap`.

## Versioning

Bump `version` in the plugin's `plugin.json` on each change so existing installs
pick up the update. Alternatively, omit `version` entirely to version the plugin
by its git commit instead.

## Also update the README

Add your plugin to the "Available plugins" table in
[README.md](./README.md) so people can discover it.
