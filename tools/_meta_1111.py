"""11-11 core-API metadata: new repos + upstream versions."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "edenfunf/reelmimic",
    "SonderSaid/ComfyUI-Sonder-Editor",
    "nomadoor/ComfyUI-Panorama-Stickers",
    "kane50613/takumi",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/effectcraft",
    "storytold/filmcraft",
]
RELEASES = ["comfyanonymous/ComfyUI", "heygen-com/hyperframes"]

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
            "full_name": d["full_name"],
            "stars": d["stargazers_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "pushed_at": d["pushed_at"][:10],
            "created_at": d["created_at"][:10],
            "language": d.get("language"),
            "archived": d.get("archived"),
            "description": (d.get("description") or "")[:220],
        }
        print(f"{repo}: {d['stargazers_count']}* {meta[repo]['license']} pushed {meta[repo]['pushed_at']}")
    except Exception as e:
        print(f"{repo}: ERR {e}")
        meta[repo] = {"error": str(e)}
    time.sleep(1)

for repo in RELEASES:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=30)
        if r.status_code == 200:
            d = r.json()
            meta[f"release:{repo}"] = {
                "tag": d.get("tag_name"),
                "published": (d.get("published_at") or "")[:10],
                "assets": [a["name"] for a in d.get("assets", [])][:12],
            }
            print(f"release {repo}: {d.get('tag_name')} {meta['release:' + repo]['published']}")
        else:
            print(f"release {repo}: HTTP {r.status_code}")
            meta[f"release:{repo}"] = {"error": r.status_code}
    except Exception as e:
        print(f"release {repo}: ERR {e}")
    time.sleep(1)

out = OUT / f"{date.today().isoformat()}-repo-meta.json"
out.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", out)
