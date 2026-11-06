"""Review raw candidates from one or more <date>-github.json files against the ledger.
Usage: python tools/_review_multi.py <raw1.json> [raw2.json ...]
Unions all items by full_name (max stars wins); prints repos NOT seen in the ledger.
Writes <today>-new-candidates.json. Run BEFORE merging the ledger.
"""
import json
import sys
from datetime import date
from pathlib import Path

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()

files = [Path(a) for a in sys.argv[1:]] or [D / f"{today}-github.json"]
ledger = json.loads((D / "seen-repos.json").read_text(encoding="utf-8"))
seen = {k.lower() for k in ledger["repos"].keys()}  # case-insensitive (renames can change case only)

union = {}
for f in files:
    raw = json.loads(f.read_text(encoding="utf-8"))
    n0 = len(union)
    for slug, q in raw["queries"].items():
        for it in q["items"]:
            name = it["full_name"]
            cur = union.get(name)
            if cur is None:
                cur = dict(it)
                cur["slugs"] = []
                union[name] = cur
            else:
                if (it["stars"] or 0) > (cur["stars"] or 0):
                    slugs = cur["slugs"]
                    cur.update(it)
                    cur["slugs"] = slugs
            if slug not in cur["slugs"]:
                cur["slugs"].append(slug)
    print(f"loaded {f.name}: +{len(union) - n0} unique repos (union {len(union)})")

new = [it for it in union.values() if it["full_name"].lower() not in seen]
SPAM = ("dictat", "dictatorship", "cirosantilli", "setup-guide", "win-guide", "workflow-guide", "shotcut-download")
new = [it for it in new if not any(s in it["full_name"].lower() for s in SPAM)]
new.sort(key=lambda x: -(x["stars"] or 0))
out_path = D / f"{today}-new-candidates.json"
out_path.write_text(json.dumps(new, indent=1, ensure_ascii=False), encoding="utf-8")

print(f"\nUNION {len(union)} repos vs ledger({len(seen)}): {len(new)} NEW (not in ledger)")
print("=" * 78)
for it in new:
    print(f"[{it['stars']}*] {it['full_name']} [{it['language']}] created:{it['created_at']} pushed:{it['pushed_at']} lic={it['license']} slugs={it['slugs']}")
    print(f"     {(it['description'] or '')[:170]}")
print(f"\n-> {out_path}")
