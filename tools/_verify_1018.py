"""Verify 2026-10-18 candidates via GitHub REST API (stars/license/pushed_at)."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # --- web lane: 3D / CAD / motion ---
    "tangency-labs/solidcraft",
    "bherbruck/solidcraft",
    "Formsmith746/SketchForge-3D",
    "tempblade/creator",
    "AmyangXYZ/reze-design",
    "pascalorg/editor",
    # --- web lane: editors / faceless ---
    "MartinDelophy/ai-video-editor",
    "AkariLabs/akari-video",
    "Ekaanth/OpenCut-AI",
    "IgorShadurin/app.yumcut.com",
    "ZeldoGiQ/aivc-dach",
    # --- new agent film skill lane (code-rendered-film query probe) ---
    "Tejashmakwana/motionmaxxing",
    "smixs/visual-skills",
    "kuhnhomeuk-cell/procedural-film",
    "1weiho/cinematic-shot",
    "machina-exm/film-studio-skills",
    "HRuiCcc/RuiC-motion-reel",
    "ferndesk/no-slop-motion",
    "iart-ai/kinetic-typography-skills",
    "COPPSARY/Motify",
    "gatewai-dev/framefields",
    "joeseesun/opus-video-prompts",
    # --- recheck ---
    "kandinskylab/kandinsky-s2v",
    "storytold/artcraft",
    # --- momentum ---
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "lemomo-ai/lemo-opuscar",
    "alexgreensh/anidoodle",
    "academa-labs/manimgx",
    "storytold/filmcraft",
    "storytold/effectcraft",
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
