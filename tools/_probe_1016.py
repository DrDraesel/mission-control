"""2026-10-16 follow-up probes: kandinsky-s2v slug, wmarceau repos, concat releases."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

# 1) find kandinsky-s2v real slug
r = requests.get("https://api.github.com/search/repositories",
                 params={"q": "kandinsky-s2v", "per_page": 10},
                 headers=HEADERS, timeout=25)
print("== search kandinsky-s2v:", r.status_code)
if r.status_code == 200:
    for it in r.json().get("items", []):
        print(f"  {it['full_name']} {it['stargazers_count']}* created={it['created_at'][:10]} lic={(it.get('license') or {}).get('spdx_id')} pushed={it['pushed_at'][:10]}")
        print(f"     {(it.get('description') or '')[:140]}")

# 2) wmarceau public repos (instagram-creator-mcp owner)
r = requests.get("https://api.github.com/users/wmarceau/repos",
                 params={"per_page": 30, "sort": "pushed"}, headers=HEADERS, timeout=25)
print("\n== wmarceau repos:", r.status_code)
if r.status_code == 200:
    for it in r.json():
        print(f"  {it['full_name']} {it['stargazers_count']}* pushed={it['pushed_at'][:10]}")

# 3) concat releases + assets
r = requests.get("https://api.github.com/repos/jub0t/concat/releases/latest", headers=HEADERS, timeout=25)
print("\n== jub0t/concat latest release:", r.status_code)
if r.status_code == 200:
    d = r.json()
    print(f"  tag={d.get('tag_name')} published={d.get('published_at','')[:10]}")
    for a in d.get("assets", []):
        print(f"  asset: {a.get('name')} {round((a.get('size') or 0)/1e6,1)}MB")
    if not d.get("assets"):
        print("  (no assets)")
