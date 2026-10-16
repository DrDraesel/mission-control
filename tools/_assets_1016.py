"""2026-10-16: check releases/latest + Windows assets for today's key candidates."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "FlashML-org/FreeVideo",
    "WeftCut/WeftCut",
    "Lightricks/LTX-Desktop",
    "zhuifengshen/anything2explainer",  # sanity (noncommercial, skip if gone)
]

for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"{repo}: releases HTTP {r.status_code}")
            continue
        d = r.json()
        print(f"\n== {repo} latest: {d.get('tag_name')} published={d.get('published_at','')[:10]}")
        for a in d.get("assets", []):
            name = a.get("name")
            size = round((a.get("size") or 0) / 1e6, 1)
            url = a.get("browser_download_url")
            mark = ""
            low = (name or "").lower()
            if any(k in low for k in ["win", "windows", ".exe", ".msi", "x64", "portable"]):
                mark = " <-- WIN?"
            print(f"   {name}  {size}MB{mark}")
            if mark:
                try:
                    h = requests.head(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=25, allow_redirects=True)
                    print(f"      HEAD: {h.status_code} len={h.headers.get('Content-Length')}")
                except Exception as e:
                    print(f"      HEAD ERR {e}")
    except Exception as e:
        print(f"{repo}: ERR {e}")
