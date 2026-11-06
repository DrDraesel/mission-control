import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mc-research"}
REPOS = [
    "harlixay7/Kinoloom",
    "haiderfarooq3/paper-reel",
    "ConardLi/garden-skills",
    "Theoxmotion/story-video-studio",
    "JuneYaooo/rea-video",
]
out = []
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1.5)
            continue
        d = resp.json()
        lic = (d.get("license") or {}).get("spdx_id")
        print(f"{d['full_name']}: {d['stargazers_count']}* {lic} pushed {d['pushed_at'][:10]} created {d['created_at'][:10]} lang={d.get('language')} fork={d.get('fork')}")
        print(f"   {(d.get('description') or '')[:250]}")
        out.append({"full_name": d["full_name"], "stars": d["stargazers_count"], "license": lic,
                    "pushed_at": d["pushed_at"], "created_at": d["created_at"], "language": d.get("language"),
                    "desc": d.get("description"), "topics": d.get("topics")})
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.3)

json.dump(out, open("research/daily/2026-11-05-repo-meta2.json", "w", encoding="utf-8"), indent=1)
print("saved", len(out))
