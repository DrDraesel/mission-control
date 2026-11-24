import json
from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\seen-repos.json")
d = json.loads(p.read_text(encoding="utf-8"))
repos = d["repos"]

old = "calesthio/OpenMontage"
new = "OpenMontageInc/OpenMontage"
prev = repos.pop(old, None)
if prev:
    cur = repos.get(new, {})
    cur["first_seen"] = prev.get("first_seen", "2026-09-25")
    q = list(dict.fromkeys((prev.get("queries") or []) + (cur.get("queries") or [])))
    cur["queries"] = q
    repos[new] = cur
    print("renamed", old, "->", new, "first_seen", cur["first_seen"], "stars", cur.get("stars"), "queries", cur["queries"])
else:
    print("old slug absent; nothing to rename")

d["total"] = len(repos)
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
print("total", d["total"], "updated", d["updated"])
print("check:", [k for k in repos if "montage" in k.lower()])
