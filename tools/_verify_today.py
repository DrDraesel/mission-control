"""Verify today's candidate repos + latest release asset names via GitHub REST (unauth, ~1 req/s)."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "chaiNNer-org/chaiNNer",
    "toyxyz/toyxyz_RGBMocap",
    "andrew-babo/muse4ai",
    "d4niel-fr/shdw-video-editor",
    "thePloggy/CreatorOS-Studio",
    "chenthedesignmaker/ComfyUI-Picky",
    "0xS4N4TG/kinetograph",
    "OpenShot/openshot-qt",
    "RickBL99/gobo",
    "apsolut/one-shot-multicam",
    "TusharTechs/platelock",
    "grzenio22/cue-the-boom",
    "TransparentLC/realesrgan-gui",
]

meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 301:
            r = requests.get(r.json().get("url", ""), headers=HEADERS, timeout=20)
        if r.status_code != 200:
            meta[repo] = {"error": r.status_code, "body": r.text[:160]}
            print(f"{repo}: HTTP {r.status_code}")
            time.sleep(1.2)
            continue
        d = r.json()
        rel = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20)
        assets = []
        tag = None
        if rel.status_code == 200:
            rd = rel.json()
            tag = rd.get("tag_name")
            assets = [(a["name"], a.get("size")) for a in rd.get("assets", [])]
        elif rel.status_code == 404:
            # maybe no releases at all
            pass
        meta[repo] = {
            "stars": d["stargazers_count"],
            "forks": d["forks_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "pushed_at": d["pushed_at"][:10],
            "created_at": d["created_at"][:10],
            "archived": d.get("archived"),
            "language": d.get("language"),
            "description": (d.get("description") or "")[:200],
            "default_branch": d.get("default_branch"),
            "latest_tag": tag,
            "assets": assets,
            "rel_status": rel.status_code,
        }
        print(f"{repo}: {d['stargazers_count']}* lic={(d.get('license') or {}).get('spdx_id')} pushed={d['pushed_at'][:10]} rel={rel.status_code} {tag} assets={len(assets)}")
        for a, s in assets[:8]:
            print(f"    - {a} ({round((s or 0)/1048576,1)}MB)")
    except Exception as e:  # noqa: BLE001
        meta[repo] = {"error": str(e)}
        print(f"{repo}: EXC {e}")
    time.sleep(1.2)

out = OUT / f"{today}-repo-meta.json"
out.write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("saved", out)
