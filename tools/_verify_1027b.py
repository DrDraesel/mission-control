import json, time
import requests

HEAD = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "kaomei/stickman-video-director",
    "andyhuo520/digital-human-koubo",
    "0xS4N4TG/kinetograph",
    "SamurAIGPT/postiz-cheap",
    "alecs5am/ralphy",
    "Domica/CapRust",
]
out = json.load(open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-27-repo-meta.json", encoding="utf-8"))

for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEAD, timeout=25)
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1.2)
            continue
        d = resp.json()
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=HEAD, timeout=25)
        assets, tag = [], None
        if rel.status_code == 200:
            rj = rel.json()
            tag = rj.get("tag_name")
            assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in rj.get("assets", [])]
        out[d["full_name"]] = {
            "stars": d["stargazers_count"], "forks": d["forks_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "pushed_at": d.get("pushed_at"), "created_at": d.get("created_at"),
            "desc": (d.get("description") or "")[:230],
            "homepage": d.get("homepage"), "language": d.get("language"),
            "archived": d.get("archived"), "topics": (d.get("topics") or [])[:12],
            "latest_tag": tag, "assets": assets[:10],
        }
        print(f"{d['full_name']}: {d['stargazers_count']}* {(d.get('license') or {}).get('spdx_id')} pushed={d.get('pushed_at')} lang={d.get('language')} tag={tag} assets={assets[:6]}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.2)

json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-27-repo-meta.json", "w", encoding="utf-8"), indent=1)
print(f"\ntotal in file: {len(out)}")
