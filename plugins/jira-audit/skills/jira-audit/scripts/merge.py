"""Merge mechanical, reviewer and duplicate findings into merged.json.

A mechanical status hint (S1/S2/S3/S5/E1) on an issue a reviewer looked at is
dropped: the reviewer either confirmed it (and wrote their own finding) or
refuted it. Notes and rules the reviewers do not cover (H*, E4, S4, E2, C1) are kept.
"""
import glob
import json
from collections import Counter

mech = json.load(open("findings_mechanical.json"))
sub, clean, reviewed = [], set(), set()
for f in sorted(glob.glob("findings_batch_*.json")):
    sub += json.load(open(f))
for f in glob.glob("clean_batch_*.json"):
    clean |= set(json.load(open(f)))
for f in glob.glob("batch_*.json"):
    b = json.load(open(f))
    reviewed |= set(b["issues"]) | set(b["epics"])
dups = json.load(open("findings_dups.json")) if glob.glob("findings_dups.json") else []

KEEP_ALWAYS = {"E4", "C1", "S4", "E2"}
kept = [m for m in mech if m["rule"][0] == "H" or m["rule"] in KEEP_ALWAYS or m["confidence"] == "Note" or m["key"] not in reviewed]
dropped = len(mech) - len(kept)

json.dump({"sub": sub, "dups": dups, "mech": kept, "reviewed": sorted(reviewed), "clean": sorted(clean)}, open("merged.json", "w"), indent=1)
print(f"reviewer findings {len(sub)} {dict(Counter(x['rule'] for x in sub))}")
print(f"duplicates {len(dups)}, mechanical kept {len(kept)}, dropped as refuted {dropped}")
print(f"reviewed {len(reviewed)}, clean {len(clean)}, unaccounted {len(reviewed - clean - {x['key'] for x in sub})}")
