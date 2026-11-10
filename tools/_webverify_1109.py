import json, time
import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "Leonxlnx/escapement",
    "suhas-svg/hermes_explainer",
    "skeptical-agency/shorts-factory",
    "niklaus-ai-yt/stickframe",
    "dhruvthakur11/youtube-ai-video-editing-system",
    "james-see/ltx-video-mac",
    "nexu-io/open-design",
    "JimLiu/baoyu-design",
]
out = {}
for r in REPOS:
    try:
        x = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25, allow_redirects=True)
        if x.status_code != 200:
            print(f"{r}: HTTP {x.status_code}")
            out[r] = {"http": x.status_code}
            continue
        d = x.json()
        out[r] = {
            "full_name": d.get("full_name"),
            "stars": d.get("stargazers_count"),
            "license": (d.get("license") or {}).get("spdx_id"),
            "created_at": (d.get("created_at") or "")[:10],
            "pushed_at": (d.get("pushed_at") or "")[:10],
            "language": d.get("language"),
            "archived": d.get("archived"),
            "desc": (d.get("description") or "")[:220],
        }
        print(f"{r}: {d.get('stargazers_count')}* {(d.get('license') or {}).get('spdx_id')} created {(d.get('created_at') or '')[:10]} pushed {(d.get('pushed_at') or '')[:10]} lang={d.get('language')}")
        print(f"   {(d.get('description') or '')[:170]}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1)
json.dump(out, open("research/daily/2026-11-09-webverify.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
