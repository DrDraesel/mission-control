import json, time
import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = ["KlingAIResearch/LivePortrait", "nadermx/backgroundremover",
         "bookwjitchieni1986/blender-ai-mcp-addon", "hitkeeen/blender-ai-mcp-addon",
         "bgleeson180-afk/cinema-4d-sacerin-motion-studio",
         "frankxai/awesome-motion-design-agent-skills", "mojomast/open-higgsfield-skills"]
out = {}
for r in REPOS:
    d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25)
    if d.status_code != 200:
        print(f"{r}: HTTP {d.status_code}"); time.sleep(1); continue
    j = d.json()
    lic = (j.get("license") or {}).get("spdx_id")
    print(f"{j['full_name']}: {j['stargazers_count']}* lic={lic} pushed={j['pushed_at'][:10]} created={j['created_at'][:10]} fork={j['fork']} lang={j.get('language')} archived={j['archived']}")
    print(f"   desc: {(j.get('description') or '')[:150]}")
    if j.get("fork"):
        pr = j.get("parent") or {}
        print(f"   PARENT: {pr.get('full_name')} {pr.get('stargazers_count')}*")
    out[r] = dict(full_name=j["full_name"], stars=j["stargazers_count"], license=lic,
                  pushed=j["pushed_at"], created=j["created_at"], fork=j["fork"],
                  desc=j.get("description"), parent=(j.get("parent") or {}).get("full_name"),
                  homepage=j.get("homepage"))
    rel = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=25)
    if rel.status_code == 200:
        rj = rel.json()
        print(f"   rel {rj.get('tag_name')} {str(rj.get('published_at'))[:10]} assets={[a['name'] for a in rj.get('assets', [])][:6]}")
    time.sleep(1.0)
json.dump(out, open("research/daily/2026-11-21-new-meta.json", "w", encoding="utf-8"), indent=1)
