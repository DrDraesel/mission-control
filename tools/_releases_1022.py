"""Probe releases/latest for 2026-10-22 candidates (tag + asset names for Windows fit)."""
import requests, time

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "sitor-ai/frametell",
    "soumatheusgomes/editonny",
    "yikart/AiToEarn",
    "bazodev/open-vids",
    "SupercmoHQ/superCMO-skills",
    "shaongitbd/doory",
    "Quentincls/localmesh-engine",
    "pixelartistry/PixelArtistry-Watertight-Meshes",
    "riecodes/free247editor",
    "KDE/kdenlive",
]
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200:
            d = r.json()
            assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in d.get("assets", [])]
            print(f"{repo}: {d.get('tag_name')} ({d.get('published_at','')[:10]}) assets({len(assets)}): {assets[:8]}")
        else:
            print(f"{repo}: HTTP {r.status_code}")
    except Exception as e:
        print(repo, "err", e)
    time.sleep(1.2)
