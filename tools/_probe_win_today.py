import requests, time

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

for repo in ["aqm857886159/Nomi", "ter-9001/WannaCut", "OpenCut-app/OpenCut"]:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases", headers=HEADERS, params={"per_page": 6}, timeout=20)
    print("==", repo, r.status_code)
    if r.status_code == 200:
        for rel in r.json():
            assets = [a["name"] for a in rel.get("assets", [])]
            win = [a for a in assets if ("win" in a.lower() or a.lower().endswith(".exe") or a.lower().endswith(".msi"))]
            print(f"  {rel.get('tag_name')} {rel.get('published_at','')[:10]} assets={len(assets)} WIN={win[:6]}")
            if repo == "aqm857886159/Nomi" and rel.get("tag_name") == "v0.23.1":
                print("   ALL:", assets)
    time.sleep(1)
