"""Release + momentum probe for 2026-11-01 (core API, ~1 req/s)."""
import json
import time
from pathlib import Path

import requests

H = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control"}
REPOS = [
    "storytold/filmcraft",
    "jub0t/concat",
    "OpenCut-app/OpenCut",
    "Comfy-Org/ComfyUI",
    "Lightricks/LTX-Desktop",
    "Twixtor",  # placeholder removed below if 404
]
OUT = Path("research/daily/2026-11-01-releases.json")
res = {}

with requests.Session() as s:
    s.headers.update(H)
    for r in REPOS:
        try:
            j = s.get(f"https://api.github.com/repos/{r}/releases/latest", timeout=30).json()
        except Exception as e:
            print(r, "ERR", e)
            continue
        if "tag_name" not in j:
            print(f"{r}: {j.get('message')}")
            res[r] = {"error": j.get("message")}
            continue
        assets = [a["name"] for a in j.get("assets", [])]
        win = [a for a in assets if "win" in a.lower() or "setup" in a.lower() or "-x64" in a.lower()]
        res[r] = {"tag": j["tag_name"], "published": j.get("published_at"), "win": win, "n": len(assets)}
        print(f"{r}: {j['tag_name']} {j.get('published_at')} assets={len(assets)} win={win[:4]}")
        time.sleep(1)

OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
print("saved", OUT)
