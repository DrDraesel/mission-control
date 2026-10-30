"""Verify 2026-10-23 candidates (web lane) via GitHub REST API."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # gittrend / trendshift video-editing catches
    "nikopueringer/CorridorKey2.0",
    "jd-opensource/JoyAI-Video-Edit",
    "KnifeLemon/Filee",
    "majedphotos/video-ad-editor",
    "AmitDigga/fabric-video-editor",
    "amirmushichge/VibeMotion",
    "VenturiVideo/Venturi",
    "Theorvane/openscene",
    "webadderallorg/Recordly",
    "dlsandy/Transub-Player",
    "mcncarl/jianying-headless",
    # agent-skill lane (only the ones with real pipelines)
    "bestagentkits/motion-video-skill",
    "alchaincyf/huashu-art-motion",
    "wheresryan22/anatomy",
    # brand-kit lane
    "fabriziosalmi/brandkit",
    # status refresh / momentum
    "storytold/artcraft",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "OpenCut-app/OpenCut",
    "Comfy-Org/ComfyUI",
    "yikart/AiToEarn",
    "presenton/presenton",
    "lemomo-ai/lemo-opuscar",
    "alexgreensh/anidoodle",
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
    time.sleep(1.1)

p = OUT / f"{today}-repo-meta.json"
p.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print("saved", p, len(meta))
