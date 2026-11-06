"""Close the ledger gaps the image-upscaling probe exposed (name-match hole): Upscayl / Real-ESRGAN etc."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = ["upscayl/upscayl", "xinntao/Real-ESRGAN", "NatronGitHub/Natron", "jliljebl/flowblade", "KDE/kdenlive"]
meta = {}
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{repo}", headers=H, timeout=20)
    if r.status_code != 200:
        print(repo, "HTTP", r.status_code, r.text[:90].replace("\n", " "))
        meta[repo] = {"error": r.status_code}
        time.sleep(1.2)
        continue
    d = r.json()
    rel = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20)
    assets = []
    tag = None
    if rel.status_code == 200:
        tag = rel.json().get("tag_name")
        assets = [(a["name"], round((a.get("size") or 0) / 1048576, 1)) for a in rel.json().get("assets", [])]
    meta[repo] = {
        "stars": d["stargazers_count"], "license": (d.get("license") or {}).get("spdx_id"),
        "created": d["created_at"][:10], "pushed": d["pushed_at"][:10], "language": d.get("language"),
        "desc": (d.get("description") or "")[:180], "tag": tag, "assets": assets[:8], "rel": rel.status_code,
    }
    print(f"{repo}: {d['stargazers_count']}* lic={(d.get('license') or {}).get('spdx_id')} pushed={d['pushed_at'][:10]} lang={d.get('language')} rel={rel.status_code} {tag}")
    for a, s in assets[:6]:
        print(f"    - {a} ({s}MB)")
    time.sleep(1.2)
out = OUT / f"{today}-repo-meta3.json"
out.write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("saved", out)
