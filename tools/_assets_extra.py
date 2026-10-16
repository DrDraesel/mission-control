"""One-off: full asset lists for LTX-Desktop/Astrofox, staxrip repo lookup, extra license lines."""
import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

for repo in ["Lightricks/LTX-Desktop", "astrofox-io/astrofox"]:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20)
    d = r.json()
    print(f"\n=== {repo} {d.get('tag_name')} ({str(d.get('published_at'))[:10]}) ===")
    for a in d.get("assets", []):
        print(f"   {a['name']}  {a['size']//1024//1024}MB  dl={a['download_count']}")

r = requests.get("https://api.github.com/search/repositories", headers=H,
                 params={"q": "staxrip", "sort": "stars", "per_page": 3}, timeout=20)
print("\n=== staxrip search ===")
for it in r.json().get("items", []):
    print(f"   {it['full_name']} {it['stargazers_count']}* pushed={it['pushed_at'][:10]} lic={(it.get('license') or {}).get('spdx_id')}")

for repo, fname in [("CapSoftware/Cap", "LICENSE"), ("opentoonz/opentoonz", "LICENSE.txt")]:
    r = requests.get(f"https://raw.githubusercontent.com/{repo}/main/{fname}", timeout=20)
    if r.status_code != 200:
        r = requests.get(f"https://raw.githubusercontent.com/{repo}/master/{fname}", timeout=20)
    lines = [l for l in r.text.split("\n") if l.strip()][:18]
    print(f"\n=== {repo}/{fname} ===")
    for l in lines[:18]:
        print("   ", l[:160])
