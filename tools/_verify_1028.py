"""Verify 2026-10-28 key repos via GitHub REST API (stars/license/pushed_at)."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # web-lane finds today
    "tomasmach/nuzky",
    "ronak-create/FableCut",
    "friction2d/friction",
    "majedphotos/video-ad-editor",
    "charlie947/motion-graphics-skills",
    "appariciojunior/video-editor-skills",
    "rahlquist/hermes-video-toolchain",
    # ledger-gap backfill (famous tools never verified)
    "excalidraw/excalidraw",
    "jgraph/drawio-desktop",
    "mermaid-js/mermaid",
    "GrapesJS/grapesjs",
    "onlook-dev/onlook",
    "webstudio-is/webstudio",
    "k4yt3x/video2x",
    # momentum anchors
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "tt-a1i/archify",
    "Nutlope/hallmark",
    "alchaincyf/huashu-design",
    "tangency-labs/solidcraft",
    "open-pencil/open-pencil",
]

meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200:
            d = r.json()
            meta[repo] = {
                "full_name": d.get("full_name"),
                "stars": d.get("stargazers_count"),
                "forks": d.get("forks_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "description": (d.get("description") or "")[:220],
                "topics": d.get("topics", []),
                "homepage": d.get("homepage"),
                "archived": d.get("archived"),
            }
            m = meta[repo]
            print(f"OK {repo} -> {m['full_name']}: {m['stars']}* lic={m['license']} created={m['created_at']} pushed={m['pushed_at']} lang={m['language']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

(OUT / f"{today}-repo-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta for {len(meta)} repos")
