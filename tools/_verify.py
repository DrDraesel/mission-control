"""Verify key repos of today via GitHub REST API (stars/license/pushed_at). Only report verified numbers."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # --- 11-25 sweep-new (topic:product-video / kinetic-typography / fresh-month-movers) ---
    "haziqahmedqasmi/PeakCut",
    "arla6ka/design.how",
    "hridaya423/silkreel",
    "jitOffice/jit-motion",
    "display-dev/product-film",
    "EGSECDA/vocaloid-style-mv-pipeline",
    # --- 11-25 web/curated lane ---
    "Hao0321/Editkin",
    "Hao0321/video-autopilot-kit",
    "kleZ799/clipmint",
    "frankShan001/CutVoke",
    "MemeCalculate/moyin-creator",
    "NarratorAI-Studio/narrator-ai-cli-skill",
    "vrgamegirl19/comfyui-vrgamedevgirl",
    "emircesur/Linnea",
    "AnIntellectualBeing/GTA-Auto-Clipper",
    # --- 11-25 momentum refresh ---
    "heygen-com/hyperframes",
    "zhouxiaoka/autoclip",
    "jub0t/Concat",
    "OpenMontageInc/OpenMontage",
    "Vincentwei1021/video-shotcraft",
    "nexu-io/openmotion",
    "KyaniteLabs/kinocut",
    "edigeh/broll-mcp",
]

meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            meta[repo] = {
                "stars": d.get("stargazers_count"),
                "forks": d.get("forks_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "description": (d.get("description") or "")[:200],
                "topics": d.get("topics", []),
                "homepage": d.get("homepage"),
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} lang={meta[repo]['language']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

(OUT / f"{today}-repo-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta for {len(meta)} repos")
