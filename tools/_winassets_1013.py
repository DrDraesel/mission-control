"""Print Windows/macOS asset names from latest releases of the 6 new ArtCraft apps."""
import requests
import time

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "storytold/wordcraft",
    "storytold/soundcraft",
    "storytold/deckcraft",
    "storytold/cadcraft",
    "storytold/gridcraft",
    "storytold/figcraft",
]
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20)
    if r.status_code == 200:
        d = r.json()
        assets = [a["name"] for a in d.get("assets", [])]
        win = [a for a in assets if ("windows" in a.lower() or "win" in a.lower() or a.lower().endswith(".msi") or a.lower().endswith(".exe"))]
        mac = [a for a in assets if "macos" in a.lower() or "darwin" in a.lower()]
        print(f"{repo} {d.get('tag_name')}: WIN={win}")
        print(f"   MAC={mac}")
    else:
        print(f"{repo}: HTTP {r.status_code}")
    time.sleep(1)
