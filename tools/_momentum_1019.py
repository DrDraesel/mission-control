import requests, time, json

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "heygen-com/hyperframes",
    "jub0t/concat",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "academa-labs/manimgx",
    "OpenCut-app/OpenCut",
    "gatewai-dev/framefields",
    "Lightricks/LTX-Desktop",
    "KyaniteLabs/kinocut",
    "FlashML-org/FreeVideo",
    "deepbeepmeep/Wan2GP",
    "tangency-labs/solidcraft",
]

def q(full):
    url = "https://api.github.com/search/repositories"
    r = None
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params={"q": "repo:" + full, "per_page": 1}, timeout=30)
        except Exception:
            time.sleep(12); continue
        if r.status_code == 200:
            it = (r.json().get("items") or [None])[0]
            if not it:
                return {"full_name": full, "error": "NOT_FOUND"}
            return {"full_name": it["full_name"], "stars": it["stargazers_count"],
                    "pushed_at": (it.get("pushed_at") or "")[:10],
                    "license": (it.get("license") or {}).get("spdx_id")}
        time.sleep(20)
    return {"full_name": full, "error": (r.status_code if r is not None else "ERR")}

out = []
for full in REPOS:
    res = q(full)
    out.append(res)
    print(json.dumps(res), flush=True)
    time.sleep(7)
with open("research/daily/2026-10-19-momentum.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("DONE")
