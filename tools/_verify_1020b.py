import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "howseen-ai/claude-motion-design",
    "iart-ai/motion-design-skills",
    "kangarooking/director-skills",
    "Hype-yolo/claude-motion-skill",
    "dev-isaacmello/extreme-motion-design",
    "ZLHad/OpenVideoHarness",
    "charlesdove977/carousel-builder",
    "iart-ai/b-roll-skills",
    "zhuyansen/awesome-claude-video-skills",
]
out = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=25)
        if r.status_code != 200:
            print(repo, "HTTP", r.status_code)
            out[repo] = {"http": r.status_code}
        else:
            d = r.json()
            out[repo] = {
                "stars": d.get("stargazers_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "language": d.get("language"),
                "description": (d.get("description") or "")[:200],
                "full_name": d.get("full_name"),
            }
            print(f"OK {repo}: {out[repo]['stars']}* lic={out[repo]['license']} created={out[repo]['created_at']} pushed={out[repo]['pushed_at']}")
    except Exception as e:
        print(repo, "ERR", e)
    time.sleep(1.2)

p = r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-20-repo-meta.json"
cur = json.load(open(p, encoding="utf-8"))
cur.update(out)
open(p, "w", encoding="utf-8").write(json.dumps(cur, indent=1, ensure_ascii=False))
print("merged into", p)
