import json, pathlib
d = json.loads(pathlib.Path("research/daily/2026-11-26-new-candidates.json").read_text(encoding="utf-8"))
items = d if isinstance(d, list) else d.get("candidates", d.get("items", []))
print("count:", len(items))
for it in items:
    print(f"{it.get('full_name'):45s} {it.get('stars'):>7} {str(it.get('license')):14s} {it.get('pushed_at','')[:10]} {(it.get('description') or '')[:110]}")
