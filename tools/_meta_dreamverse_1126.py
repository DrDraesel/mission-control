import requests, json
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
r = requests.get("https://api.github.com/search/repositories", headers=H, timeout=30,
                 params={"q": "dreamverse harness", "sort": "stars", "order": "desc", "per_page": 8})
for it in r.json().get("items", []):
    print(it["full_name"], it["stargazers_count"], (it.get("license") or {}).get("spdx_id"), (it.get("pushed_at") or "")[:10], "|", it.get("description"))
print("---- yt-dlp check ----")
for q in ["yt-dlp", "cobalt"]:
    d = requests.get("https://api.github.com/search/repositories", headers=H, timeout=30,
                     params={"q": q, "sort": "stars", "order": "desc", "per_page": 3}).json()
    print(q, [(i["full_name"], i["stargazers_count"]) for i in d.get("items", [])][:3])
