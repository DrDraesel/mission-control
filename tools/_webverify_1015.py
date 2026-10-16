"""10-15 web-find verification via search API (separate rate bucket from core).
Verifies web-sweep candidates + momentum checks + slug hunts. 7s spacing (10/min limit).
"""
import json
import time
from datetime import date
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

QUERIES = [
    ("weftcut", "repo:WeftCut/WeftCut"),
    ("bearcarousel", "repo:johnnyang0612/bearcarousel"),
    ("claude-carruseles", "repo:TonyciencIA/claude-carruseles"),
    ("ucouerbe-carousel", "repo:ucouerbe/instagram-carousel-automation"),
    ("wan2gp", "repo:deepbeepmeep/Wan2GP"),
    ("motion-anything", "repo:nexu-io/motion-anything"),
    ("tramme", "repo:kyogreultima/tramme"),
    ("glaxnimate-upstream", "repo:mbasaglia/glaxnimate"),
    ("morphable-hunt", "morphable motion"),
    ("larryloop-hunt", "larryloop"),
    ("hypit", "repo:hypit-ai/hypit"),
    ("ltx-desktop", "repo:Lightricks/LTX-Desktop"),
    ("kandinsky6", "repo:kandinskylab/kandinsky-6"),
    ("pireel", "repo:pireel/pireel"),
    ("capcap-check", "repo:notepower2k1/CapCap"),
]

meta = {}
for i, (label, q) in enumerate(QUERIES):
    if i > 0:
        time.sleep(7)
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         headers=HEADERS, params={"q": q, "sort": "stars", "order": "desc", "per_page": 3},
                         timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"ERR {label}: {e}", flush=True)
        continue
    if r.status_code == 200:
        items = r.json().get("items", [])
        if not items:
            print(f"EMPTY {label} :: {q}", flush=True)
            continue
        if "hunt" in label:
            for d in items[:3]:
                print(f"HUNT {label}: {d['full_name']} {d['stargazers_count']}* :: {(d.get('description') or '')[:90]}", flush=True)
        d = items[0]
        meta[label] = {
            "full_name": d["full_name"],
            "stars": d["stargazers_count"],
            "pushed_at": d["pushed_at"][:10],
            "created_at": d["created_at"][:10],
            "license": (d.get("license") or {}).get("spdx_id"),
            "desc": (d.get("description") or "")[:140],
            "url": d["html_url"],
        }
        print(f"OK {label}: {d['full_name']} {d['stargazers_count']}* lic={meta[label]['license']} pushed={meta[label]['pushed_at']} created={meta[label]['created_at']}", flush=True)
    else:
        print(f"HTTP {r.status_code} {label}", flush=True)

out = D / f"{date.today().isoformat()}-webverify-meta.json"
out.write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("saved", out.name, flush=True)
