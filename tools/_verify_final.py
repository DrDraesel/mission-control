"""Final spot-verify for late leads 2026-10-04."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "Anil-matcha/AI-Youtube-Shorts-Generator",
    "Phantom-video/HuMo",
    "SamurAIGPT/Text-To-Video-AI",
    "scenario-labs/skills",
    "Colafornia/short-video-generator-AI",
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
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} lang={meta[repo]['language']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

p = OUT / f"{today}-repo-meta-extra.json"
old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
old.update(meta)
p.write_text(json.dumps(old, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved extra meta for {len(meta)} repos (total file: {len(old)})")
