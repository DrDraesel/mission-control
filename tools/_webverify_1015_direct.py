"""10-15 direct /repos probe (core API bucket, ~60/hr) for web-sweep candidates.
Core bucket is separate from the search bucket the sweep uses — safe to run concurrently.
"""
import json
import time
from datetime import date
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

SLUGS = [
    "WeftCut/WeftCut",
    "iterative-computer/powermove",
    "nexu-io/motion-anything",
    "0xsline/OpenChatCut",
    "MartinDelophy/ai-video-editor",
    "sasharun/awesome-faceless",
    "luminalmvm/Lumit",
    "Yuan-ManX/open-motion",
    "diffusionstudio/editor",
    "kyogreultima/tramme",
    "diffusionstudio/dapi",
]

meta = {}
for i, slug in enumerate(SLUGS):
    if i > 0:
        time.sleep(1.5)
    try:
        r = requests.get(f"https://api.github.com/repos/{slug}", headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"ERR {slug}: {e}", flush=True)
        continue
    if r.status_code == 200:
        d = r.json()
        meta[slug] = {
            "full_name": d["full_name"],
            "stars": d["stargazers_count"],
            "pushed_at": d["pushed_at"][:10],
            "created_at": d["created_at"][:10],
            "license": (d.get("license") or {}).get("spdx_id"),
            "desc": (d.get("description") or "")[:160],
            "url": d["html_url"],
            "archived": d.get("archived"),
        }
        print(f"OK {slug}: {d['stargazers_count']}* lic={(d.get('license') or {}).get('spdx_id')} pushed={d['pushed_at'][:10]} created={d['created_at'][:10]} :: {(d.get('description') or '')[:70]}", flush=True)
    else:
        print(f"HTTP {r.status_code} {slug}", flush=True)

out = D / f"{date.today().isoformat()}-webverify-direct.json"
out.write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("saved", out.name, flush=True)
