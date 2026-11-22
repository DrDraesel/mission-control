import json, time, sys, requests

REPOS = [
    "lovisdotio/motion2code",
    "TMElyralab/MuseTalk",
    "motiondivision/motion",
    "motion-canvas/motion-canvas",
    "eternityspring/reelbench-skills",
    "LudwigKienle/ai-video-production-editor",
    "ChrisHKAI/ChrisHKAI-Video",
    "givemotion/givemotion",
    "Downvid/downvid",
    "yeates/Aurora",
    "Melvynx/video-agent-skills",
    "MakeMyClip/editor",
    "FernandoAbishai/ScriptCut",
    "Aepzie/cutline",
    "ZanePoe/awesome_ai_video_creation",
    "kleZ799/clipmint",
    "haidrrrry/claude-remotion-skill",
    "nateherkai/herk-edit-kit",
]
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}

rl = requests.get("https://api.github.com/rate_limit", headers=H, timeout=20).json()
core = rl["resources"]["core"]
print("core remaining", core["remaining"], "of", core["limit"])
if core["remaining"] < len(REPOS) + 3:
    print("WARNING: core budget low; will use search bucket fallback")

out = {}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=20)
        if resp.status_code == 200:
            d = resp.json()
            out[r] = {
                "full_name": d["full_name"],
                "stars": d["stargazers_count"],
                "license": (d.get("license") or {}).get("spdx_id"),
                "pushed_at": d["pushed_at"][:10],
                "created_at": d["created_at"][:10],
                "language": d.get("language"),
                "archived": d.get("archived"),
                "forks": d["forks_count"],
                "open_issues": d["open_issues_count"],
                "description": (d.get("description") or "")[:200],
            }
            print(f"{r:45s} {d['stargazers_count']:>7d}  {(d.get('license') or {}).get('spdx_id')}  pushed {d['pushed_at'][:10]}")
        else:
            out[r] = {"error": resp.status_code}
            print(f"{r:45s} HTTP {resp.status_code}")
    except Exception as e:
        out[r] = {"error": str(e)}
        print(f"{r:45s} ERR {e}")
    time.sleep(1.2)

json.dump(out, open(sys.argv[1], "w"), indent=1)
print("saved", sys.argv[1])
