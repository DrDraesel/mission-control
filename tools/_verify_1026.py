import json, sys, time
import requests

HEAD = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

REPOS = sys.argv[1:] or [
    "tt-a1i/archify",
    "Anil-matcha/Open-Generative-AI",
    "ATH-MaaS/Pixelle-Video",
    "earthtojake/text-to-cad",
]

out = {}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEAD, timeout=25)
        if resp.status_code == 301 or (resp.status_code == 200 and resp.json().get("full_name", "").lower() != r.lower()):
            d = resp.json()
            if resp.status_code == 200:
                r = d["full_name"]
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code} {resp.text[:120]}")
            out[r] = {"error": resp.status_code}
            time.sleep(1.2)
            continue
        d = resp.json()
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=HEAD, timeout=25)
        assets = []
        tag = None
        if rel.status_code == 200:
            rj = rel.json()
            tag = rj.get("tag_name")
            assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in rj.get("assets", [])]
        out[d["full_name"]] = {
            "stars": d["stargazers_count"], "forks": d["forks_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "pushed_at": d.get("pushed_at"), "created_at": d.get("created_at"),
            "desc": (d.get("description") or "")[:220],
            "homepage": d.get("homepage"), "language": d.get("language"),
            "archived": d.get("archived"), "topics": d.get("topics"),
            "latest_tag": tag, "assets": assets[:14],
        }
        a = out[d["full_name"]]
        print(f"{d['full_name']}: {a['stars']}* {a['license']} pushed={a['pushed_at']} created={a['created_at'][:10]} lang={a['language']}")
        print(f"   {a['desc']}")
        print(f"   tag={tag} assets={assets[:8]}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.2)

json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-26-repo-meta-web.json", "w", encoding="utf-8"), indent=1)
print("\nsaved 2026-10-26-repo-meta-web.json")
