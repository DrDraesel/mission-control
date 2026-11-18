"""Web-lane candidate verification for 2026-11-18."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # faceless / shorts generators found on the open web
    "Chamanrajragu/purffle-shorts",
    "jutsuhq/content-factory",
    "shubhxtech/AutoShorts",
    "samolubukun/NovaClip",
    "AbdullahNaveed/ai-shorts-generator",
    # effectcraft ecosystem (web topic: after-effects-alternative)
    "revsync09-dot/titlekit",
    "caioeo/cadancer-for-effectcraft",
    "cxcmyt/motion-forge",
    "isroil01/premation",
    # momentum / releases refresh
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "Comfy-Org/ComfyUI",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "CutWire-Studios/Drift",
    "nexu-io/openmotion",
    "0xS4N4TG/kinetograph",
    "shinyobjectz/raea",
    "facebookresearch/segment-anything",
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

(OUT / f"{today}-verify-web.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("saved", len(meta))
