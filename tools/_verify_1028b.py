import json, time, requests
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = ["konlu/story-studio", "patch-gg/anymove", "bangtutorial/bang-motion",
         "SiddharthFulia/kinetic-text-ffmpeg", "Freespirits/social-auto-engine",
         "alsk1992/instagram-ai-agent"]
out = {}
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{repo}", headers=H, timeout=20, allow_redirects=True)
    if r.status_code == 200:
        d = r.json()
        out[repo] = {"full_name": d["full_name"], "stars": d["stargazers_count"],
                     "license": (d.get("license") or {}).get("spdx_id"),
                     "created_at": d["created_at"][:10], "pushed_at": d["pushed_at"][:10],
                     "language": d.get("language"), "description": (d.get("description") or "")[:200]}
        print("OK", repo, "->", d["full_name"], d["stargazers_count"], "lic=", out[repo]["license"],
              "created=", out[repo]["created_at"], "pushed=", out[repo]["pushed_at"], "lang=", out[repo]["language"])
    else:
        print("HTTP", r.status_code, repo)
    time.sleep(1)
p = r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-28-repo-meta2.json"
open(p, "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
print("saved", len(out))
