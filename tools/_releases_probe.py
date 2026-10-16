"""Probe releases/latest for key tools: tag + asset names (Windows fit)."""
import requests, time

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "storytold/wordcraft",
    "storytold/soundcraft",
    "storytold/deckcraft",
    "storytold/cadcraft",
    "storytold/gridcraft",
    "storytold/figcraft",
    "honwee/mynah",
    "hypit-ai/hypit",
]
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20)
    if r.status_code == 200:
        d = r.json()
        assets = [a["name"] for a in d.get("assets", [])]
        print(f"{repo}: {d.get('tag_name')} ({d.get('published_at','')[:10]}) assets({len(assets)}): {assets[:8]}")
    else:
        print(f"{repo}: HTTP {r.status_code}")
    time.sleep(1)
