"""Review today's raw candidates against the ledger: list repos NOT seen before, per query, by stars.
Writes <date>-new-candidates.json for README fetching."""
import json
import sys
from datetime import date
from pathlib import Path

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
raw = json.loads((D / f"{today}-github.json").read_text(encoding="utf-8"))
ledger = json.loads((D / "seen-repos.json").read_text(encoding="utf-8"))
# case-insensitive: GitHub renames can change case only (jub0t/concat -> jub0t/Concat)
seen = {k.lower(): k for k in ledger["repos"].keys()}

SPAM = ("dictat", "dictatorship", "cirosantilli", "setup-guide", "win-guide", "workflow-guide", "shotcut-download")

new = {}
for slug, q in raw["queries"].items():
    print(f"\n=== {slug} ({q['query']}) total={q['count']} ===")
    for it in q["items"]:
        name = it["full_name"]
        is_spam = any(s in name.lower() for s in SPAM)
        tag = "OLD" if name.lower() in seen else ("SPAM" if is_spam else "NEW")
        if name.lower() not in seen and not is_spam:
            e = new.setdefault(name, dict(it))
            e.setdefault("slugs", [])
            if slug not in e["slugs"]:
                e["slugs"].append(slug)
        print(f"  [{tag}] {name} ({it['stars']}*) [{it['language']}] created:{it['created_at']} pushed:{it['pushed_at']} lic={it['license']}")
        print(f"       {(it['description'] or '')[:160]}")

out = sorted(new.values(), key=lambda x: -(x["stars"] or 0))
(D / f"{today}-new-candidates.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\n#### {len(out)} NEW repos (not in ledger) -> {today}-new-candidates.json")
for it in out[:40]:
    print(f"  {it['full_name']} ({it['stars']}*) {it['slugs']}")
