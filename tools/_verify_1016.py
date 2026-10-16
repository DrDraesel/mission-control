"""Verify 2026-10-16 key repos via GitHub REST API (stars/license/pushed_at). Only report verified numbers."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # --- 10-16 sweep NEW ---
    "scenario-labs/blender-plugin",
    # --- 10-16 web finds (video-gen / digital-human) ---
    "FlashML-org/FreeVideo",
    "kandinskylab/kandinsky-s2v",
    "hao-ai-lab/fastvideo",
    "kandinskylab/kvae-audio",
    "TaoLiveAIGC/TaoMate-H3",
    # --- 10-16 web finds (misc / unknown-inlane) ---
    "jub0t/concat",
    "morluto/rea",
    "xerj-org/xerj",
    "wmarceau/instagram-creator-mcp",
    "Niko1221/Strata",
    "Thysrael/Horizon",
    "GCWing/OpenBitFun",
    "lexmount/moli",
    # --- momentum refresh (top pipeline repos) ---
    "heygen-com/hyperframes",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "academa-labs/manimgx",
    "kajisho5/ffmpeg-skill",
    "feitangyuan/onetake",
    "liyupi/ai-promo-video-maker",
    "ziplab/ATAS",
    "Lightricks/LTX-Desktop",
    "kandinskylab/kandinsky-6",
    "WeftCut/WeftCut",
    "openfilm/openfilm",
    "vincentsch/explainroo",
    "KyaniteLabs/kinocut",
    "nexu-io/open-design",
    "mutonby/openshorts",
    "Tencent-Hunyuan/Prism",
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
                "description": (d.get("description") or "")[:220],
                "topics": d.get("topics", []),
                "homepage": d.get("homepage"),
                "archived": d.get("archived"),
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} lang={meta[repo]['language']}")
            print(f"    desc: {meta[repo]['description'][:150]}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

(OUT / f"{today}-repo-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nsaved meta for {len(meta)} repos -> {today}-repo-meta.json")
