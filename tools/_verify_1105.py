import json, time, requests, sys

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "veedstudio/open-edit",
    "JuneYaooo/rea-video",
    "openfilm/openfilm",
    "storytold/photocraft",
    "KnifeLemon/Filee",
    "calesthio/OpenMontage",
    "Vincentwei1021/video-shotcraft",
    "getopenscreen/openscreen",
]
out = []
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1.2)
            continue
        d = resp.json()
        lic = (d.get("license") or {}).get("spdx_id")
        rec = {
            "full_name": d["full_name"],
            "stars": d["stargazers_count"],
            "license": lic,
            "pushed_at": d["pushed_at"],
            "created_at": d["created_at"],
            "language": d.get("language"),
            "archived": d.get("archived"),
            "fork": d.get("fork"),
            "desc": (d.get("description") or "")[:220],
            "topics": d.get("topics"),
            "homepage": d.get("homepage"),
        }
        out.append(rec)
        print(f"{rec['full_name']}: {rec['stars']}* {lic} pushed {rec['pushed_at'][:10]} created {rec['created_at'][:10]} lang={rec['language']}")
        print(f"   {rec['desc']}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.2)

json.dump(out, open("research/daily/2026-11-05-repo-meta.json", "w", encoding="utf-8"), indent=1)
print("saved", len(out))
