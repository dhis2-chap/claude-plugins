#!/usr/bin/env bash
# SessionStart hook for the chap-brain plugin.
#
# Finds the user's clone of the team vault (dhis2-chap/chap-first-brain) and keeps a
# read-only copy of origin/main next to it, as a detached git worktree in
# ~/.cache/chap-brain/vault. The clone itself is never changed: people edit the vault
# there, on any branch and with local changes, so this hook only fetches into it.
# Prints one line telling the agent where the copy is. Whatever it prints becomes
# session context, so it stays short. It never fails the session: every path ends in
# exit 0.
#
# Where the clone is looked for, in order:
#   1. $CHAP_BRAIN_DIR
#   2. a chap-first-brain folder next to the current repo or any folder above it
#      (for example ~/code/chap/chap-first-brain when working in ~/code/chap/chap-core)
#   3. ~/chap-first-brain

set -u

is_vault() { [ -f "$1/AGENTS.md" ] && [ -f "$1/Vault-overviews/terminology.md" ]; }

start="${CLAUDE_PROJECT_DIR:-$PWD}"
clone=""
if [ -n "${CHAP_BRAIN_DIR:-}" ] && is_vault "$CHAP_BRAIN_DIR"; then
  clone="$CHAP_BRAIN_DIR"
else
  d="$start"
  while [ "$d" != "/" ] && [ -n "$d" ]; do
    if is_vault "$d/chap-first-brain"; then clone="$d/chap-first-brain"; break; fi
    d=$(dirname "$d")
  done
  [ -z "$clone" ] && is_vault "$HOME/chap-first-brain" && clone="$HOME/chap-first-brain"
fi

if [ -z "$clone" ]; then
  echo "chap-brain: no clone of the team vault (dhis2-chap/chap-first-brain) found. Clone it next to your Chap repos or set CHAP_BRAIN_DIR."
  exit 0
fi
clone=$(cd "$clone" && pwd -P)

cache="${XDG_CACHE_HOME:-$HOME/.cache}/chap-brain"
copy="$cache/vault"

# Inside the vault (or the copy), the vault's own AGENTS.md and hook apply instead.
here="$(cd "$start" 2>/dev/null && pwd -P)/"
case "$here" in
  "$clone"/*|"$copy"/*) exit 0 ;;
esac

limit=""
command -v timeout >/dev/null 2>&1 && limit="timeout 30"
[ -z "$limit" ] && command -v gtimeout >/dev/null 2>&1 && limit="gtimeout 30"

notes=""
changed=""
git_dir=$(git -C "$clone" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)

# Fetch at most every 10 minutes, so starting many sessions does not hit GitHub each
# time. Fetching only updates origin/main; the clone's branches and files stay as they are.
if [ -z "$(find "$git_dir/FETCH_HEAD" -mmin -10 2>/dev/null)" ]; then
  if ! out=$(GIT_TERMINAL_PROMPT=0 $limit git -C "$clone" fetch --quiet origin main 2>&1); then
    [ -z "$out" ] && out="no answer from the remote within 30 seconds"
    notes="$notes git fetch failed (${out##*$'\n'}), so the vault may be out of date."
  fi
fi

# The copy must be a worktree of this clone. If it belongs to another clone or is broken
# (for example after the clone was moved), remove it and make a new one.
if [ -e "$copy" ]; then
  copy_git=$(git -C "$copy" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
  if [ "$copy_git" != "$git_dir" ]; then
    rm -rf "$copy"
    git -C "$clone" worktree prune 2>/dev/null
  fi
fi
if [ ! -e "$copy" ]; then
  mkdir -p "$cache"
  if ! out=$(git -C "$clone" worktree add --quiet --detach "$copy" origin/main 2>&1); then
    echo "chap-brain: could not make a read-only copy of the team vault (${out##*$'\n'}). Read the clone at $clone instead; it may have local changes or be out of date."
    exit 0
  fi
  changed=1
fi

# Move the copy to origin/main, and undo any edits made to it by mistake. Nobody is
# meant to edit it, so a forced checkout loses nothing.
if [ "$(git -C "$copy" rev-parse HEAD 2>/dev/null)" != "$(git -C "$clone" rev-parse origin/main 2>/dev/null)" ] \
  || [ -n "$(git -C "$copy" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
  if ! out=$(git -C "$copy" checkout --quiet --force --detach origin/main 2>&1); then
    notes="$notes Updating the copy failed (${out##*$'\n'}), so it may be out of date."
  fi
  changed=1
fi

# DVC archive (Archive/files/, gitignored). The copy uses the clone's DVC settings and
# cache, so whatever the clone has downloaded is reused without going online.
if command -v dvc >/dev/null 2>&1; then
  if [ -f "$clone/.dvc/config.local" ] && [ "$clone/.dvc/config.local" -nt "$copy/.dvc/config.local" ]; then
    cp "$clone/.dvc/config.local" "$copy/.dvc/config.local"
  fi
  if ! grep -qF "$clone/.dvc/cache" "$copy/.dvc/config.local" 2>/dev/null; then
    (cd "$copy" && dvc config --local cache.dir "$clone/.dvc/cache" >/dev/null 2>&1)
    changed=1
  fi
  [ -n "$changed" ] && (cd "$copy" && dvc checkout --quiet Archive/files.dvc >/dev/null 2>&1)
fi
# The vault's own script: pulls from the DVC remote only when the cache did not have it.
if [ -f "$copy/AI-internal/useful-scripts/ensure_archive.sh" ]; then
  out=$(bash "$copy/AI-internal/useful-scripts/ensure_archive.sh" 2>&1)
  [ -n "$out" ] && notes="$notes $out"
fi

echo "chap-brain: the Chap team vault (origin/main, read-only copy) is at $copy. Read it, never write to it (see the chap-brain skill). Changes not yet pushed to the vault are only in the clone at $clone.${notes}"
exit 0
