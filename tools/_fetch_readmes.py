"""Fetch READMEs for a repo list, save to research/daily/readmes/.
Usage: python tools/_fetch_readmes.py <repos.txt|repos.json>  (one full_name per line, or JSON array of names/objects with full_name)
"""
import json
import sys
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\readmes")
OUT.mkdir(parents=True, exist_ok=True)

cands = []
if len(sys.argv) > 1:
    src = Path(sys.argv[1])
    txt = src.read_text(encoding="utf-8")
    if src.suffix == ".json":
        data = json.loads(txt)
        cands = [d["full_name"] if isinstance(d, dict) else d for d in data]
    else:
        cands = [l.strip() for l in txt.splitlines() if l.strip() and not l.startswith("#")]
print(f"{len(cands)} candidates")

NAMES = ["README.md", "readme.md", "README.MD", "README.rst"]
BRANCHES = ["main", "master"]

with requests.Session() as s:
    s.headers["User-Agent"] = "mission-control-research/1.0"
    for repo in cands:
        slug = repo.replace("/", "__")
        dest = OUT / f"{slug}.md"
        if dest.exists() and dest.stat().st_size > 50:
            print("skip (cached)", repo)
            continue
        got = False
        for br in BRANCHES:
            for name in NAMES:
                url = f"https://raw.githubusercontent.com/{repo}/{br}/{name}"
                try:
                    r = s.get(url, timeout=20)
                    if r.status_code == 200 and len(r.text) > 50:
                        dest.write_text(r.text[:40000], encoding="utf-8")
                        print(f"OK {repo} -> {len(r.text)} chars ({br})")
                        got = True
                        break
                    if r.status_code == 404:
                        continue
                except Exception as e:
                    print("err", repo, e)
            if got:
                break
        if not got:
            print("NO README", repo)
print("done")
