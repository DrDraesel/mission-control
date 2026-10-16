"""Refresh remaining repos via search API (separate rate limit): repo:<full_name> queries."""
import json
import time
from datetime import date
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "hassancs91/claude-faceless-shorts-creator",
    "Orkas-AI/Orkas-VideoStudio",
    "friction2d/friction",
    "latent-spaces/brag",
    "pireel/pireel",
    "duixcom/Duix-Avatar",
    "modelscope/FunClip",
    "PurpleDoubleD/locally-uncensored",
]

meta = {}
for i, repo in enumerate(REPOS):
    if i > 0:
        time.sleep(7)
    r = requests.get("https://api.github.com/search/repositories",
                     headers=HEADERS, params={"q": f"repo:{repo}", "per_page": 1}, timeout=30)
    if r.status_code == 200:
        items = r.json().get("items", [])
        if items:
            d = items[0]
            meta[repo] = {"stars": d["stargazers_count"], "pushed_at": d["pushed_at"][:10],
                          "license": (d.get("license") or {}).get("spdx_id")}
            print(f"OK {repo}: {d['stargazers_count']}* lic={meta[repo]['license']} pushed={meta[repo]['pushed_at']}")
        else:
            print(f"EMPTY {repo}")
    else:
        print(f"HTTP {r.status_code} {repo}")

out = D / f"{date.today().isoformat()}-refresh2-meta.json"
out.write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("saved", out.name)
