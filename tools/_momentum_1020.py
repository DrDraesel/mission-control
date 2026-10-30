import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
PREV = {  # values from 2026-10-19 report
    "heygen-com/hyperframes": 67414,
    "jub0t/Concat": 9384,
    "storytold/filmcraft": 15025,
    "storytold/effectcraft": 7392,
    "OpenCut-app/OpenCut": 95352,
    "academa-labs/manimgx": 1868,
}
REPOS = list(PREV) + [
    "tangency-labs/solidcraft", "FlashML-org/FreeVideo", "Lightricks/LTX-Desktop",
    "dmtrKovalenko/fframes", "open-pencil/open-pencil", "lemomo-ai/lemo-opuscar",
    "alexgreensh/anidoodle", "walterlow/freecut", "gatewai-dev/framefields",
    "nexu-io/open-design", "remotion-dev/remotion", "pireel/pireel",
]
out = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=25)
        if r.status_code != 200:
            print(repo, "HTTP", r.status_code)
            out[repo] = {"http": r.status_code}
        else:
            d = r.json()
            s = d.get("stargazers_count")
            delta = s - PREV[repo] if repo in PREV and s is not None else None
            out[repo] = {"stars": s, "pushed_at": (d.get("pushed_at") or "")[:10], "delta": delta}
            print(f"{repo}: {s}*  {('+%d' % delta) if delta is not None else ''}  pushed={out[repo]['pushed_at']}")
    except Exception as e:
        print(repo, "ERR", e)
    time.sleep(1.0)

open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-20-momentum.json", "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
print("saved")
