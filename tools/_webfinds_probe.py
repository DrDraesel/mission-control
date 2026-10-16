"""Verify web-found repos found outside the API sweep. Reads one full_name per line.
Usage: python tools/_webfinds_probe.py <list.txt>
Prints + writes JSON to research/daily/<date>-webfinds-meta.json
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

src = Path(sys.argv[1])
REPOS = [l.strip() for l in src.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
print(f"{len(REPOS)} repos to verify")

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
                "homepage": d.get("homepage"),
                "archived": d.get("archived", False),
                "full_name": d.get("full_name"),
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} lang={meta[repo]['language']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1.2)

(OUT / f"{today}-webfinds-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta for {len(meta)} repos -> {today}-webfinds-meta.json")
