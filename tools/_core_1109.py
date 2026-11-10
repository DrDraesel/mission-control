import json, time, sys
import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "Theoxmotion/story-video-studio",
    "Video-Rebirth/hyperflow-infinity",
    "rdh9616/ComfyUI-Open-H3-Regenerate",
    "tazmannner/ComfyUI-H3-RelayHires",
    "10291124jcjc-dotcom/ai-anime-series",
    "andyhuo520/vibe-knowledge",
    "meta/astryx",
    "Hhz0823/YoloCut",
]
out = {}
for r in REPOS:
    try:
        x = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25, allow_redirects=True)
        if x.status_code != 200:
            print(f"{r}: HTTP {x.status_code}")
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
            "desc": (d.get("description") or "")[:200],
            "topics": d.get("topics", []),
        }
        print(f"{r}: {d.get('stargazers_count')}* {(d.get('license') or {}).get('spdx_id')} created {(d.get('created_at') or '')[:10]} pushed {(d.get('pushed_at') or '')[:10]} lang={d.get('language')}")
        print(f"   {(d.get('description') or '')[:160]}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1)
json.dump(out, open("research/daily/2026-11-09-candidates-core.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
