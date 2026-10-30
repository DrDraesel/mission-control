"""Core watchlist release check for 2026-10-23 report table."""
import time

import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "heygen-com/hyperframes",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "storytold/photocraft",
    "storytold/artcraft",
    "jub0t/Concat",
    "Lightricks/LTX-Desktop",
    "academa-labs/manimgx",
    "Comfy-Org/ComfyUI",
    "open-pencil/open-pencil",
    "gatewai-dev/framefields",
    "tangency-labs/solidcraft",
    "lemomo-ai/lemo-opuscar",
    "alexgreensh/anidoodle",
    "KDE/kdenlive",
    "OpenCut-app/OpenCut",
]
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            print(f"{repo}: HTTP {r.status_code}")
            time.sleep(1.2)
            continue
        d = r.json()
        assets = d.get("assets", [])
        win = [f"{a['name']} {a['size']/1e6:.1f}MB" for a in assets if "win" in a["name"].lower()]
        print(f"{repo}: {d.get('tag_name')} ({(d.get('published_at') or '')[:10]}) assets={len(assets)} WIN={win[:4] if win else 'none'}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1.2)
