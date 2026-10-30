import requests, time, json, sys

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

CANDIDATES = [
    "mushigaite/short-video-maker",
    "YeJe-cpu/SeeCut",
    "bridge-mind/bridgeclip",
    "Gitruck/cli",
    "majedphotos/video-ad-editor",
    "omni-media/omniclip",
    "renezander030/capcut-cli",
    "kurbaitaev/ghost-editor",
    "mariagorskikh/talking-head-reel",
    "nextwork-projects/ai-video-editor-cooked",
    "Leonxlnx/claude-launchvideo",
    "saeedvaziry/storyboard",
    "deonmenezes/edit-ai",
    "Miftahul-Islam-Efaz/Motion-graphics-skill",
    "Amarel-Taylor-Scott/kinetype",
    "tomastimelock/text-fx",
    "GordenSun/Gorden-vfx-video",
    "zhuyansen/awesome-claude-video-skills",
    "tuzhechen2005/opus-video-skills",
    "HITsz-TMG/VideoClaw",
    "ArcReel/ArcReel",
    "ShadoW-Shinigami/lyric-video-director",
]

def search_repo(full_name):
    url = "https://api.github.com/search/repositories"
    p = {"q": "repo:" + full_name, "per_page": 3}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=p, timeout=30)
        except Exception as e:
            time.sleep(10)
            continue
        if r.status_code == 200:
            items = r.json().get("items", [])
            if not items:
                return {"full_name": full_name, "error": "NOT_FOUND"}
            it = items[0]
            return {
                "full_name": it["full_name"],
                "stars": it["stargazers_count"],
                "forks": it["forks_count"],
                "license": (it.get("license") or {}).get("spdx_id"),
                "created_at": (it.get("created_at") or "")[:10],
                "pushed_at": (it.get("pushed_at") or "")[:10],
                "language": it.get("language"),
                "archived": it.get("archived"),
                "description": (it.get("description") or "")[:200],
                "url": it["html_url"],
                "topics": it.get("topics", []),
            }
        time.sleep(20)
    return {"full_name": full_name, "error": f"HTTP {r.status_code}"}

out = []
for c in CANDIDATES:
    res = search_repo(c)
    out.append(res)
    print(json.dumps(res, ensure_ascii=False), flush=True)
    time.sleep(7)

with open("research/daily/2026-10-19-webverify.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print("SAVED", len(out))
