"""10-14 web-find verification via search API (separate rate bucket from core).
Verifies web-sweep candidates + momentum checks. 7s spacing (10/min limit).
"""
import json
import time
from datetime import date
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

# (label, search query) — repo: queries verify exact slugs; plain queries hunt slugs
QUERIES = [
    ("threeui", "repo:MengTo/threeui"),
    ("openvids", "repo:bazodev/open-vids"),
    ("akari", "repo:AkariLabs/akari-video"),
    ("nvidia-vfx-nodes", "repo:Comfy-Org/ComfyUI_Nvidia_VFX_Nodes"),
    ("glaxnimate", "glaxnimate"),
    ("kimo-hunt", "kimo video"),
    ("hypit", "repo:hypit-ai/hypit"),
    ("manimgx", "repo:academa-labs/manimgx"),
    ("openfilm", "repo:openfilm/openfilm"),
    ("effectcraft", "repo:storytold/effectcraft"),
    ("hyperframes", "repo:heygen-com/hyperframes"),
    ("openshorts", "repo:mutonby/openshorts"),
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
        if label == "kimo-hunt":
            for d in items[:3]:
                print(f"HUNT {label}: {d['full_name']} {d['stargazers_count']}* :: {(d.get('description') or '')[:80]}", flush=True)
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
