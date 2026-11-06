import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mc-research"}
REPOS = [
    "inclusionAI/Ming-3.0-tts",
    "shinshin86/mesh-avatar-studio",
    "AirsupHQ/machine-skill",
    "ahujasid/camera-to-blender",
    "elvarofficial/teardown",
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
        print(f"{d['full_name']}: {d['stargazers_count']}* {lic} pushed {d['pushed_at'][:10]} created {d['created_at'][:10]} lang={d.get('language')}")
        print(f"   {(d.get('description') or '')[:230]}")
        out.append({"full_name": d["full_name"], "stars": d["stargazers_count"], "license": lic,
                    "pushed_at": d["pushed_at"], "created_at": d["created_at"], "language": d.get("language"),
                    "desc": d.get("description")})
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.3)

json.dump(out, open("research/daily/2026-11-05-repo-meta3.json", "w", encoding="utf-8"), indent=1)
print("saved", len(out))
