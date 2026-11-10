#!/usr/bin/env bash
# SessionStart hook for the chap-brain plugin.
#
# Finds the local clone of the team vault (dhis2-chap/chap-first-brain), brings it up to
# date with a fast-forward pull and the vault's own archive check, and prints one line
# telling the agent where the vault is. Whatever it prints becomes session context, so
# it stays short. It never fails the session: every path ends in exit 0.
#
# Where the vault is looked for, in order:
#   1. $CHAP_BRAIN_DIR
#   2. a chap-first-brain folder next to the current repo or any folder above it
#      (for example ~/code/chap/chap-first-brain when working in ~/code/chap/chap-core)
#   3. ~/chap-first-brain

set -u

is_vault() { [ -f "$1/AGENTS.md" ] && [ -f "$1/Vault-overviews/terminology.md" ]; }

start="${CLAUDE_PROJECT_DIR:-$PWD}"
vault=""
if [ -n "${CHAP_BRAIN_DIR:-}" ] && is_vault "$CHAP_BRAIN_DIR"; then
  vault="$CHAP_BRAIN_DIR"
else
  d="$start"
  while [ "$d" != "/" ] && [ -n "$d" ]; do
    if is_vault "$d/chap-first-brain"; then vault="$d/chap-first-brain"; break; fi
    d=$(dirname "$d")
  done
  [ -z "$vault" ] && is_vault "$HOME/chap-first-brain" && vault="$HOME/chap-first-brain"
fi

if [ -z "$vault" ]; then
  echo "chap-brain: no clone of the team vault (dhis2-chap/chap-first-brain) found. Clone it next to your Chap repos or set CHAP_BRAIN_DIR."
  exit 0
fi
vault=$(cd "$vault" && pwd -P)

# Inside the vault itself, its own AGENTS.md and SessionStart hook already apply.
case "$(cd "$start" 2>/dev/null && pwd -P)/" in
  "$vault"/*) exit 0 ;;
esac

notes=""

# Pull at most every 10 minutes, so starting many sessions does not hit GitHub each time.
fetch_head="$vault/.git/FETCH_HEAD"
if [ -z "$(find "$fetch_head" -mmin -10 2>/dev/null)" ]; then
  if ! out=$(GIT_TERMINAL_PROMPT=0 git -C "$vault" pull --ff-only --quiet 2>&1); then
    notes="$notes git pull failed (${out##*$'\n'}), so the vault may be out of date."
  fi
fi

# The vault's own script: pulls Archive/files from DVC only when git pull changed it.
if [ -f "$vault/AI-internal/useful-scripts/ensure_archive.sh" ]; then
  out=$(bash "$vault/AI-internal/useful-scripts/ensure_archive.sh" 2>&1)
  [ -n "$out" ] && notes="$notes $out"
fi

echo "chap-brain: the Chap team vault is at $vault. Read it, never write to it, from this session (see the chap-brain skill).${notes}"
exit 0
