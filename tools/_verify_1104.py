"""Verify 2026-11-04 web-lane candidates + momentum repos via GitHub REST API.
Prints stars/license/language/created/pushed and latest release asset names."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

WEB = [
    "MagoStudio/MagoStudio",
    "sirioberati/YouTube-AI-Motion-Graphics",
    "Moessif/code-video-showcase",
    "andreavolpato/spektrafilm",
    "apekshik/anyscene",
    "YeJe-cpu/easy-jianying",
    "CodeWithAmeer/MeerCut",
    "medhachim/CapRocket",
    "Leonxlnx/napali",
    "blendi-remade/prompt2rig",
    "JayWebtech/autoshorts",
    "harry7557558/spirula-studio",
    "Akillll-DuoHe/fy-code-animation",
    "ersinkoc/AI-Video-Factory",
    "LiamGvchi/gc-minimal-zine-poster",
    "Zeejay0/gathered-scenes-zine-skill",
    "higgsfield-ai/skills",
    "wquguru/shisei",
    "hongye007/open-pose-costume",
    "hyz317/HairDeck",
    "Mayzmei/anime-series-maker",
]
MOMENTUM = [
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "calesthio/OpenMontage",
    "lemomo-ai/lemo-opuscar",
    "mromidev/claude-animated-shorts",
    "wj-sidiss/otopilot",
    "D3voz/openjutsu",
    "Comfy-Org/ComfyUI",
    "open-pencil/open-pencil",
    "tt-a1i/archify",
    "pbakaus/impeccable",
    "Leonxlnx/taste-skill",
    "academa-labs/manimgx",
    "harry0703/MoneyPrinterTurbo",
]

meta = {}
for repo in WEB + MOMENTUM:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            rec = {
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
                "fork": d.get("fork"),
            }
            meta[repo] = rec
            print(f"OK {repo}: {rec['stars']}* lic={rec['license']} lang={rec['language']} created={rec['created_at']} pushed={rec['pushed_at']}")
            print(f"    {rec['description'][:150]}")
        elif r.status_code in (301, 302, 404):
            print(f"HTTP {r.status_code} {repo}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

# release assets for the ones likely to be installed
print("\n--- release assets ---")
for repo in ["MagoStudio/MagoStudio", "CodeWithAmeer/MeerCut", "medhachim/CapRocket",
             "YeJe-cpu/easy-jianying", "JayWebtech/autoshorts", "sirioberati/YouTube-AI-Motion-Graphics",
             "Moessif/code-video-showcase", "Leonxlnx/napali", "andreavolpato/spektrafilm"]:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200:
            d = r.json()
            assets = [f"{a['name']} ({a['size']/1048576:.1f}MB)" for a in d.get("assets", [])]
            meta.setdefault(repo, {})["latest_release"] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "assets": assets}
            print(f"{repo} {d.get('tag_name')} {(d.get('published_at') or '')[:10]} -> {assets[:6]}")
        else:
            print(f"{repo} /releases/latest HTTP {r.status_code}")
    except Exception as e:
        print("rel err", repo, e)
    time.sleep(1)

out = OUT / f"{today}-repo-meta.json"
out.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nwrote {out} ({len(meta)} repos)")
