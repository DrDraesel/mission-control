import requests, json, time

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "storytold/effectcraft",
    "Lightricks/LTX-Desktop",
    "storytold/filmcraft",
    "jub0t/Concat",
    "heygen-com/hyperframes",
    "academa-labs/manimgx",
    "pireel/pireel",
    "OpenCut-app/OpenCut",
    "deepbeepmeep/Wan2GP",
    "graphiteeditor/graphite",
    "barefootford/buttercut",
]
out = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(repo, "HTTP", r.status_code)
            out[repo] = {"http": r.status_code}
            time.sleep(1)
            continue
        d = r.json()
        assets = [{"name": a["name"], "mb": round(a["size"] / 1048576, 1), "dl": a["download_count"]} for a in d.get("assets", [])]
        out[repo] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "name": d.get("name"), "assets": assets}
        print(f"{repo} | {d.get('tag_name')} | {(d.get('published_at') or '')[:10]} | {d.get('name')} | assets={len(assets)}")
        for a in assets[:10]:
            print(f"   - {a['name']}  {a['mb']} MB  dl={a['dl']}")
    except Exception as e:
        print(repo, "ERR", e)
    time.sleep(1)

open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-20-releases.json", "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
print("saved")
