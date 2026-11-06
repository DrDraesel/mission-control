"""Check OpenShot CLI exists in repo tree + latest release tags for the ArtCraft/HyperFrames lane."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

res = {}

# 1) OpenShot repo tree -> does openshot-cli exist?
for br in ("develop", "main", "master"):
    r = requests.get(f"https://api.github.com/repos/OpenShot/openshot-qt/git/trees/{br}?recursive=1", headers=H, timeout=30)
    if r.status_code == 200:
        paths = [t["path"] for t in r.json().get("tree", [])]
        hits = [p for p in paths if "cli" in p.lower()]
        res["openshot_tree"] = {"branch": br, "files": len(paths), "cli_paths": hits[:25]}
        print("OpenShot tree", br, len(paths), "files; cli hits:", hits[:25])
        break
    else:
        print("tree", br, r.status_code)
    time.sleep(1.2)

# 2) latest releases for the daily-watch repos
for repo in ("storytold/effectcraft", "storytold/filmcraft", "storytold/photocraft", "heygen-com/hyperframes", "jub0t/Concat"):
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20)
    if r.status_code == 200:
        d = r.json()
        win = [a["name"] for a in d.get("assets", []) if "win" in a["name"].lower() or "exe" in a["name"].lower() or "msi" in a["name"].lower()]
        res[repo] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "win_assets": win[:6]}
        print(repo, d.get("tag_name"), (d.get("published_at") or "")[:10], win[:6])
    else:
        res[repo] = {"error": r.status_code}
        print(repo, "HTTP", r.status_code)
    time.sleep(1.2)

(OUT / f"{today}-releases.txt").write_text(json.dumps(res, indent=1), encoding="utf-8")
print("saved", OUT / f"{today}-releases.txt")
