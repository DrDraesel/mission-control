"""Follow-up verify batch 2 (2026-10-11): reels/social lane web finds."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "ronin1770/reel-quick",
    "Caio-Felice-Cunha/instagram-reels-poster",
    "Jakeschincariol/instagram-agent-skill",
    "mlnjsh/AI-REELS-GENERATOR",
    "IlyassCODEX/Faceless-Reels-AI-Agent-for-Instagram",
]
# search for more social/faceless tools the sweep may have missed
qs = ['faceless video stars:>30 pushed:>2026-09-15', 'reels automation stars:>30 pushed:>2026-09-15']

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

time.sleep(3)
for q in qs:
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         headers=HEADERS, params={"q": q, "sort": "stars", "order": "desc", "per_page": 8}, timeout=25)
        print(f"\nsearch '{q}': HTTP {r.status_code}")
        if r.status_code == 200:
            for it in r.json().get("items", []):
                print(f"  {it['full_name']} ({it['stargazers_count']}*) pushed={(it.get('pushed_at') or '')[:10]} lic={(it.get('license') or {}).get('spdx_id')}")
    except Exception as e:
        print("search err", q, e)
    time.sleep(3)

(OUT / f"{today}-repo-meta-extra.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nsaved extra meta for {len(meta)} repos")
