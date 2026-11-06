"""Verify an explicit list of repos via GitHub core REST API -> <today>-repo-meta.json.

Usage: python tools/_verify_list.py research/daily/<date>-verify-list.txt [--releases]

Why: core API gives authoritative stars/licence/pushed_at/created_at; unauthenticated
60 req/hr so keep the list tight. --releases also records the latest release tag and
asset names (Windows fit check) for the same repos.
Appends to today's meta file instead of overwriting (repeat runs are safe).
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

if len(sys.argv) < 2:
    print("usage: _verify_list.py <names-file> [--releases]")
    sys.exit(1)

names_file = Path(sys.argv[1])
with_releases = "--releases" in sys.argv
repos = [ln.strip() for ln in names_file.read_text(encoding="utf-8").splitlines()
         if ln.strip() and not ln.strip().startswith("#")]

meta_path = OUT / f"{today}-repo-meta.json"
meta = {}
if meta_path.exists():
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        meta = {}

for repo in repos:
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
                "description": (d.get("description") or "")[:220],
                "topics": d.get("topics", []),
                "homepage": d.get("homepage"),
                "archived": d.get("archived", False),
                "default_branch": d.get("default_branch"),
            }
            if with_releases:
                try:
                    rel = requests.get(
                        f"https://api.github.com/repos/{repo}/releases/latest",
                        headers=HEADERS, timeout=20)
                    if rel.status_code == 200:
                        rj = rel.json()
                        meta[repo]["latest_release"] = {
                            "tag": rj.get("tag_name"),
                            "published_at": (rj.get("published_at") or "")[:10],
                            "assets": [{"name": a.get("name"), "mb": round((a.get("size") or 0) / 1048576, 1)}
                                       for a in rj.get("assets", [])][:25],
                        }
                except Exception as e:
                    meta[repo]["latest_release"] = {"error": str(e)[:120]}
                time.sleep(1)
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} "
                  f"created={meta[repo]['created_at']} pushed={meta[repo]['pushed_at']} "
                  f"lang={meta[repo]['language']}", flush=True)
        else:
            print(f"HTTP {r.status_code} {repo}", flush=True)
    except Exception as e:
        print("err", repo, e, flush=True)
    time.sleep(1)

meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta for {len(meta)} repos -> {meta_path}")
