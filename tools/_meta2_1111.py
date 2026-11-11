"""11-11 verify the new-candidate repos + find slugs for the two web-only finds."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "google-labs-code/design.md",
    "projectM-visualizer/projectm",
    "jeffstric/ZJT",
    "tsoding/musializer",
    "foobar404/wave.js",
    "nomadoor/ComfyUI-Panorama-Stickers",
    "SonderSaid/ComfyUI-Sonder-Editor",
    "creativevideotips/cvt-ltx-alpha-gen",
    "jayfunc/BetterLyrics",
    "VoltAgent/awesome-design-md",
]
SEARCHES = ["imagination studio film", "spede splat edit engine"]

meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f"{repo}: HTTP {r.status_code}")
            meta[repo] = {"error": r.status_code}
            time.sleep(1)
            continue
        d = r.json()
        meta[repo] = {
            "stars": d["stargazers_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "pushed_at": d["pushed_at"][:10],
            "created_at": d["created_at"][:10],
            "language": d.get("language"),
            "archived": d.get("archived"),
            "description": (d.get("description") or "")[:200],
        }
        print(f"{repo}: {d['stargazers_count']}* {meta[repo]['license']} {meta[repo]['language']} pushed {meta[repo]['pushed_at']} created {meta[repo]['created_at']}")
    except Exception as e:
        print(f"{repo}: ERR {e}")
        meta[repo] = {"error": str(e)}
    time.sleep(1)

for q in SEARCHES:
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            headers=HEADERS,
            params={"q": q, "sort": "stars", "order": "desc", "per_page": 5},
            timeout=30,
        )
        if r.status_code == 200:
            print(f"SEARCH {q!r}: total={r.json().get('total_count')}")
            for it in r.json().get("items", [])[:5]:
                print(f"   {it['full_name']} {it['stargazers_count']}* {(it.get('description') or '')[:90]}")
                meta[f"search:{it['full_name']}"] = {
                    "stars": it["stargazers_count"],
                    "license": (it.get("license") or {}).get("spdx_id"),
                    "pushed_at": it["pushed_at"][:10],
                    "description": (it.get("description") or "")[:200],
                }
        else:
            print(f"SEARCH {q!r}: HTTP {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"SEARCH {q!r}: ERR {e}")
    time.sleep(8)

path = OUT / f"{date.today().isoformat()}-repo-meta.json"
prev = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
prev.update(meta)
path.write_text(json.dumps(prev, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", path, len(prev), "entries")
