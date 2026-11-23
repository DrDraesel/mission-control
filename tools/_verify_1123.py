import json, time, sys, requests

REPOS = [
    "iamajmeena/neonclipping",
    "AIEraDev/Clypra",
    "rk0neki/OpenKatana",
    "0xsline/OpenChatCut",
    "Theorvane/OpenScene",
    "Forget-C/Jellyfish",
    "HaD0Yun/CozyClay",
    "Aepzie/cutline",
    "FernandoAbishai/ScriptCut",
    "ThinkFlowLab/OpenDirector",
    "shijue-aid/aid-studio",
    "Augani/openreel-video",
    "yeates/Aurora",
    "browser-use/video-use",
    "Tencent/WeVisCut",
    "win4r/video-director",
    "openfilm/openfilm",
    "JuneYaooo/rea-video",
    "kajisho5/ffmpeg-skill",
]
RELEASES = ["AIEraDev/Clypra", "rk0neki/OpenKatana", "Theorvane/OpenScene",
            "0xsline/OpenChatCut", "iamajmeena/neonclipping", "Augani/openreel-video"]

H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}

rl = requests.get("https://api.github.com/rate_limit", headers=H, timeout=20).json()
core = rl["resources"]["core"]
print("core remaining", core["remaining"], "of", core["limit"])

out = {"repos": {}, "releases": {}}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=20)
        if resp.status_code == 200:
            d = resp.json()
            out["repos"][r] = {
                "full_name": d["full_name"],
                "stars": d["stargazers_count"],
                "license": (d.get("license") or {}).get("spdx_id"),
                "pushed_at": d["pushed_at"][:10],
                "created_at": d["created_at"][:10],
                "language": d.get("language"),
                "archived": d.get("archived"),
                "forks": d["forks_count"],
                "description": (d.get("description") or "")[:200],
            }
            print(f"{r:35s} {d['stargazers_count']:>7d}  {(d.get('license') or {}).get('spdx_id')}  pushed {d['pushed_at'][:10]}  created {d['created_at'][:10]}")
        else:
            out["repos"][r] = {"error": resp.status_code}
            print(f"{r:35s} HTTP {resp.status_code}")
    except Exception as e:
        out["repos"][r] = {"error": str(e)}
        print(f"{r:35s} ERR {e}")
    time.sleep(1.2)

for r in RELEASES:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=20)
        if resp.status_code == 200:
            d = resp.json()
            assets = [{"name": a["name"], "size": a["size"]} for a in d.get("assets", [])]
            out["releases"][r] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "assets": assets}
            print(f"REL {r} {d.get('tag_name')} {[a['name'] for a in assets][:6]}")
        else:
            out["releases"][r] = {"http": resp.status_code}
            print(f"REL {r} HTTP {resp.status_code}")
    except Exception as e:
        out["releases"][r] = {"error": str(e)}
    time.sleep(1.0)

json.dump(out, open(sys.argv[1], "w"), indent=1)
print("saved", sys.argv[1])
