"""Print the actions behind approved IDs or a tier, as JSON for the apply step.

Usage: python approved.py tier1          # every tier-1 item
       python approved.py P03 P07 P12    # specific IDs
Reads proposed.json written by report.py.
"""
import json
import sys

proposed = json.load(open("proposed.json"))
args = sys.argv[1:]
if not args:
    sys.exit("give a tier (tier1/tier2/tier3) or IDs")
if args[0].startswith("tier"):
    sel = [p for p in proposed if p["tier"] == int(args[0][4:])]
else:
    want = {a.upper() for a in args}
    sel = [p for p in proposed if p["id"] in want]
    missing = want - {p["id"] for p in sel}
    if missing:
        print(f"unknown IDs: {sorted(missing)}", file=sys.stderr)
print(json.dumps(sel, indent=1))
