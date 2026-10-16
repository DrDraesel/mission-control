"""Check releases/latest assets for Windows fit of today's top candidates."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "xixihhhh/hotclip",
    "elevenyellow/handcrafted-persona-engine",
    "Tenney95/AI-Canvas-tauri",
    "fagenorn/handcrafted-persona-engine",
]
for r in REPOS:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=HEADERS, timeout=20).json()
        assets = [(a["name"], round(a["size"] / 1048576, 1)) for a in d.get("assets", [])]
        print(f"{r}: tag={d.get('tag_name')} published={str(d.get('published_at'))[:10]} assets={assets[:8]}")
    except Exception as e:
        print(f"{r}: ERR {e}")
