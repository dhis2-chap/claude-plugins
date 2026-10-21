"""Shallow-clone every selected repo into repos/ in parallel, and list the repos that
exist in each org (for the dead-repo link check).

Usage: python fetch.py
Clones over HTTPS with the gh credential helper (SSH may wait for a hardware key).
Large blobs are skipped, so binary assets can be missing from the clones.
"""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

cfg = json.load(open("config.json"))
os.makedirs("repos", exist_ok=True)


def clone(src):
    dest = os.path.join("repos", src["name"])
    if os.path.isdir(dest):
        return src["name"], "kept"
    r = subprocess.run(
        ["git", "-c", "credential.helper=!gh auth git-credential", "clone", "-q", "--depth", "1",
         "--filter=blob:limit=2m", f"https://github.com/{src['repo']}.git", dest],
        capture_output=True, text=True, timeout=600)
    return src["name"], "ok" if r.returncode == 0 else r.stderr.strip()[-200:]


def org_repos(org):
    r = subprocess.run(["gh", "repo", "list", org, "--limit", "2000", "--json", "name", "--jq", ".[].name"],
                       capture_output=True, text=True, timeout=300)
    return org, r.stdout.split()


orgs = sorted({s["repo"].split("/")[0] for s in cfg["sources"]} | {"dhis2", "dhis2-chap"})
with ThreadPoolExecutor(max_workers=12) as ex:
    clones = list(ex.map(clone, cfg["sources"]))
    existing = dict(ex.map(org_repos, orgs))

json.dump(existing, open("org_repos.json", "w"))
failed = [(n, s) for n, s in clones if s not in ("ok", "kept")]
print(f"cloned {len(clones) - len(failed)}/{len(clones)}; org repo lists: "
      + ", ".join(f"{o}={len(v)}" for o, v in existing.items()))
for n, s in failed:
    print(f"FAILED {n}: {s}")
if any(not v for v in existing.values()):
    print("WARNING: an org repo list is empty; the dead-repo link check is skipped for it")
