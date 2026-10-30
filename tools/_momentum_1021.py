import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
prevdoc = json.load(open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-20-momentum.json", encoding="utf-8"))
PREV = {k: v["stars"] for k, v in prevdoc.items() if isinstance(v, dict) and v.get("stars")}

REPOS = [
    "heygen-com/hyperframes", "jub0t/Concat", "storytold/filmcraft", "storytold/effectcraft",
    "OpenCut-app/OpenCut", "academa-labs/manimgx", "tangency-labs/solidcraft",
    "FlashML-org/FreeVideo", "Lightricks/LTX-Desktop", "dmtrKovalenko/fframes",
    "open-pencil/open-pencil", "lemomo-ai/lemo-opuscar", "alexgreensh/anidoodle",
    "walterlow/freecut", "gatewai-dev/framefields", "nexu-io/open-design",
    "remotion-dev/remotion", "pireel/pireel", "Augani/openreel-video",
    "openspline/openspline", "graphiteeditor/graphite",
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
            print(f"{repo}: {s}*  {('+%d' % delta) if delta is not None else '?'}  pushed={out[repo]['pushed_at']}")
    except Exception as e:
        print(repo, "ERR", e)
    time.sleep(1.0)

open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-21-momentum.json", "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
print("saved")
