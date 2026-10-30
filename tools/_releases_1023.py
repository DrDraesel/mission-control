"""Release-asset probe for 2026-10-23 finds (Windows fit check)."""
import time

import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "webadderallorg/Recordly",
    "KnifeLemon/Filee",
    "VenturiVideo/Venturi",
    "jd-opensource/JoyAI-Video-Edit",
    "alchaincyf/huashu-art-motion",
    "bestagentkits/motion-video-skill",
    "wheresryan22/anatomy",
    "nikopueringer/CorridorKey2.0",
]
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            print(f"-- {repo}: releases/latest HTTP {r.status_code}")
            time.sleep(1.2)
            continue
        d = r.json()
        print(f"-- {repo}: {d.get('tag_name')} ({d.get('published_at','')[:10]})")
        for a in d.get("assets", [])[:14]:
            print(f"     {a['name']}  {a['size']/1e6:.1f} MB")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1.2)
