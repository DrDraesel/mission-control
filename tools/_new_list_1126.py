import json, pathlib
d = json.loads(pathlib.Path("research/daily/seen-repos.json").read_text(encoding="utf-8"))
print("total", d["total"], "updated", d["updated"])
new = [(k, v) for k, v in d["repos"].items() if v.get("first_seen") == "2026-11-26"]
print("first_seen today:", len(new))
for k, v in sorted(new, key=lambda x: -(x[1].get("stars") or 0)):
    print(f"  {k} ({v.get('stars')}*) {v.get('queries')}")
