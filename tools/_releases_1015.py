"""10-15: /repos + releases/latest probes for top new tools (core bucket)."""
import time
from pathlib import Path

import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = ["deepbeepmeep/Wan2GP", "beziointeractive/morphable-desktop"]
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
    if r.status_code == 200:
        d = r.json()
        print(f"REPO {repo}: {d['stargazers_count']}* lic={(d.get('license') or {}).get('spdx_id')} pushed={d['pushed_at'][:10]} created={d['created_at'][:10]} :: {(d.get('description') or '')[:90]}", flush=True)
    else:
        print(f"REPO {repo}: HTTP {r.status_code}", flush=True)
    time.sleep(1)

RELEASES = ["WeftCut/WeftCut", "notepower2k1/CapCap", "johnnyang0612/bearcarousel",
            "xuanyustudio/LocalMiniDrama", "beziointeractive/morphable-desktop", "kyogreultima/tramme"]
for repo in RELEASES:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20)
    if r.status_code == 200:
        d = r.json()
        assets = [(a["name"], round(a["size"] / 1048576, 1)) for a in d.get("assets", [])]
        print(f"REL {repo}: {d.get('tag_name')} ({d.get('published_at', '')[:10]}) assets({len(assets)}): {assets[:9]}", flush=True)
    else:
        print(f"REL {repo}: HTTP {r.status_code}", flush=True)
    time.sleep(1)
