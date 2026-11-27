"""11-27 verify: new candidates + momentum + releases + ComfyUI tag."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # new candidates (sweep)
    "ed-asriyan/lottie-converter",
    "trykimu/videoeditor",
    "basmilius/meteocons",
    "LottieFiles/lottie-player",
    # curated-index / web lane
    "robbietilton/Editroom",
    "sirioberati/ai-filmmaking-camera-control-seedance-2-5",
    # momentum
    "heygen-com/hyperframes",
    "zhouxiaoka/autoclip",
    "nexu-io/openmotion",
    "jub0t/Concat",
    "OpenMontageInc/OpenMontage",
    "KyaniteLabs/kinocut",
    "Vincentwei1021/video-shotcraft",
    "Remocn/remocn",
    "Tencent/libpag",
    "iamajmeena/neonclipping",
    "haziqahmedqasmi/PeakCut",
    "academa-labs/manimgx",
    "edenfunf/reelmimic",
    "0xS4N4TG/kinetograph",
    "keyline-dev/keyline",
]

RELEASES = [
    "heygen-com/hyperframes",
    "zhouxiaoka/autoclip",
    "nexu-io/openmotion",
    "jub0t/Concat",
    "Comfy-Org/ComfyUI",
    "academa-labs/manimgx",
    "KyaniteLabs/kinocut",
]

meta, rel = {}, {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=H, timeout=20)
        if r.status_code == 200:
            d = r.json()
            meta[repo] = {
                "stars": d.get("stargazers_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "description": (d.get("description") or "")[:180],
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

print("--- releases ---")
for repo in RELEASES:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20)
        if r.status_code == 200:
            d = r.json()
            rel[repo] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10],
                         "assets": [a["name"] for a in d.get("assets", [])][:6]}
            print(f"REL {repo}: {rel[repo]['tag']} {rel[repo]['published']} assets={rel[repo]['assets']}")
        else:
            print(f"REL HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err rel", repo, e)
    time.sleep(1)

(OUT / f"{today}-repo-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
(OUT / f"{today}-releases.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta {len(meta)} / releases {len(rel)}")
