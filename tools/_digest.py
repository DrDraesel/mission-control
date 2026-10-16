import json
from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-09-25-github.json")
data = json.loads(p.read_text(encoding="utf-8"))
print("fetched_at:", data["fetched_at"])
for slug in ["faceless-video", "video-automation", "motion-graphics"]:
    q = data["queries"][slug]
    print(f"\n=== {slug} ({q['query']}) total={q['count']} ===")
    for it in q["items"]:
        print(f"  {it['full_name']} ({it['stars']}*) [{it['language']}] created:{it['created_at']} pushed:{it['pushed_at']}")
        print(f"     {(it['description'] or '')[:150]}")
