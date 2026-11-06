import json, time
import requests
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = ["storytold/effectcraft", "storytold/filmcraft", "storytold/photocraft", "heygen-com/hyperframes",
         "jub0t/Concat", "storytold/solidcraft", "academa-labs/manimgx", "open-pencil/open-pencil",
         "Lightricks/LTX-Desktop", "wexloops/openfield", "Comfy-Org/ComfyUI"]
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            d = r.json()
            assets = [(a["name"], round(a["size"]/1048576, 1)) for a in d.get("assets", [])]
            win = [a for a in assets if ("win" in a[0].lower() or ".msi" in a[0].lower() or ".exe" in a[0].lower())]
            print(f"{repo}: {d.get('tag_name')} {(d.get('published_at') or '')[:10]} assets={len(assets)} win={win[:4]}")
        else:
            print(f"{repo}: HTTP {r.status_code}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)
