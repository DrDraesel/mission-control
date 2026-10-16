"""Extra probes 2026-10-06: find motion-script slug, kandinsky-6 releases, FreeFaceless status."""
import json
import time
from datetime import date
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

# 1) search for motion-script repo
r = requests.get("https://api.github.com/search/repositories",
                 headers=HEADERS, params={"q": "motion-script motion design", "per_page": 6}, timeout=30)
print("== motion-script search ==")
if r.status_code == 200:
    for it in r.json().get("items", []):
        print(f"  {it['full_name']} ({it['stargazers_count']}*) {it['description'][:100] if it['description'] else ''}")
else:
    print("HTTP", r.status_code, r.text[:200])
time.sleep(4)

# 2) kandinsky-6 releases
r = requests.get("https://api.github.com/repos/kandinskylab/kandinsky-6/releases/latest", headers=HEADERS, timeout=30)
print("\n== kandinsky-6 releases/latest ==")
if r.status_code == 200:
    d = r.json()
    print("tag:", d.get("tag_name"), "| published:", d.get("published_at"))
    for a in (d.get("assets") or []):
        print(f"  asset: {a['name']} ({a['size']/1e6:.1f}MB)")
    if not d.get("assets"):
        print("  (no assets)")
else:
    print("HTTP", r.status_code, r.text[:200])
time.sleep(1)

# 3) FreeFaceless status
r = requests.get("https://api.github.com/repos/nils44344/FreeFaceless", headers=HEADERS, timeout=30)
print("\n== FreeFaceless ==")
print("HTTP", r.status_code)
if r.status_code == 200:
    d = r.json()
    print("full_name:", d.get("full_name"), "| stars:", d.get("stargazers_count"),
          "| created:", d.get("created_at"), "| pushed:", d.get("pushed_at"),
          "| default_branch:", d.get("default_branch"), "| archived:", d.get("archived"))
else:
    print(r.text[:200])
time.sleep(1)

# 4) kandinsky-6 repo files at root (check model card / weights link)
r = requests.get("https://api.github.com/repos/kandinskylab/kandinsky-6/contents/", headers=HEADERS, timeout=30)
print("\n== kandinsky-6 root files ==")
if r.status_code == 200:
    for f in r.json()[:25]:
        print(f"  {f['name']} ({f.get('size')} bytes)")
else:
    print("HTTP", r.status_code)
