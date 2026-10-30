import requests, time, json
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
for full in ["heyimjames/tela", "open-pencil/open-pencil"]:
    r = requests.get("https://api.github.com/search/repositories", headers=HEADERS,
                     params={"q": "repo:" + full, "per_page": 1}, timeout=30)
    if r.status_code == 200:
        items = r.json().get("items") or []
        if items:
            it = items[0]
            print(json.dumps({"full_name": it["full_name"], "stars": it["stargazers_count"],
                              "license": (it.get("license") or {}).get("spdx_id"),
                              "created": it["created_at"][:10], "pushed": it["pushed_at"][:10],
                              "lang": it.get("language"), "desc": it.get("description")}, ensure_ascii=False))
        else:
            print(full, "NOT_FOUND")
    else:
        print(full, "HTTP", r.status_code)
    time.sleep(7)
