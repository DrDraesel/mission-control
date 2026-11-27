import json, collections, pathlib
d = json.loads(pathlib.Path("research/daily/2026-11-26-new-candidates.json").read_text(encoding="utf-8"))
items = d if isinstance(d, list) else d.get("candidates", [])
c = collections.Counter()
for it in items:
    for q in it.get("queries") or it.get("matched_queries") or []:
        c[q] += 1
print("queries with new:", c)
print("total queries:", 40, "| with new:", len(c), "| zero-new:", 40 - len(c))
