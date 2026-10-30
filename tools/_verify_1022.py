"""Verify repos for 2026-10-22 via GitHub REST API; merges into <date>-repo-meta.json.
Usage: python tools/_verify_1022.py names.txt
Handles renames (follows redirects; records resolved full_name).
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
META_FILE = OUT / f"{today}-repo-meta.json"
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

names = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
         if l.strip() and not l.startswith("#")]

meta = {}
if META_FILE.exists():
    try:
        meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        meta = {}

for repo in names:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200:
            d = r.json()
            full = d.get("full_name")
            meta[repo] = {
                "full_name": full,
                "stars": d.get("stargazers_count"),
                "forks": d.get("forks_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "open_issues": d.get("open_issues_count"),
                "archived": d.get("archived"),
                "description": (d.get("description") or "")[:220],
                "topics": d.get("topics", []),
                "homepage": d.get("homepage"),
            }
            flag = "" if full == repo else f"  [renamed -> {full}]"
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} lang={meta[repo]['language']}{flag}", flush=True)
        else:
            print(f"HTTP {r.status_code} {repo}", flush=True)
    except Exception as e:
        print("err", repo, e, flush=True)
    time.sleep(1.2)

META_FILE.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nwrote {META_FILE} ({len(meta)} repos)")
