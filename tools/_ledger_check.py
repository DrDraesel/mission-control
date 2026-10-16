"""Check candidate names against the seen-repos ledger. Usage: python tools/_ledger_check.py names.txt"""
import json
import sys
from pathlib import Path

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
ledger = json.loads((D / "seen-repos.json").read_text(encoding="utf-8"))
repos = ledger["repos"]

names = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
for n in names:
    if n in repos:
        e = repos[n]
        print(f"SEEN  {n}  ^ first={e.get('first_seen')} stars={e.get('stars')} q={e.get('queries')}")
    else:
        print(f"NEW   {n}")
print(f"\nledger total: {len(repos)}")
