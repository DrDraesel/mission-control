import requests, time, json, sys

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

def probe(q):
    url = "https://api.github.com/search/repositories"
    p = {"q": q, "sort": "stars", "order": "desc", "per_page": 5}
    try:
        r = requests.get(url, headers=HEADERS, params=p, timeout=30)
        if r.status_code != 200:
            return {"q": q, "status": r.status_code, "total": None}
        d = r.json()
        return {"q": q, "status": 200, "total": d.get("total_count"),
                "top": [(i["full_name"], i["stargazers_count"]) for i in d.get("items", [])[:5]]}
    except Exception as e:
        return {"q": q, "status": "ERR", "err": str(e)}

queries = [
    "programmatic video",
    "3d web design webgpu",
    "webgpu 3d editor",
]
out = []
for q in queries:
    res = probe(q)
    out.append(res)
    print(json.dumps(res, ensure_ascii=False), flush=True)
    time.sleep(7)
