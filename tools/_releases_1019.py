import requests, json

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

for repo in ["bridge-mind/bridgeclip", "omni-media/omniclip", "Sportinger/MasterSelects", "BintzGavin/helios", "dmtrKovalenko/fframes", "Gitruck/cli"]:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(repo, "HTTP", r.status_code)
            continue
        d = r.json()
        print(f"{repo} | {d.get('tag_name')} | {d.get('published_at','')[:10]} | {d.get('name')}")
        for a in d.get("assets", [])[:12]:
            print(f"   - {a['name']}  {round(a['size']/1048576,1)} MB  dl={a['download_count']}")
    except Exception as e:
        print(repo, "ERR", e)
