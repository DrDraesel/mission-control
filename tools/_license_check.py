"""Fetch first lines of LICENSE/LICENSE.md for repos with NOASSERTION/None license (or unknown).
Usage: python tools/_license_check.py <list.txt>   (one full_name per line; raw fetch only, no API)
"""
import sys
from pathlib import Path

import requests

HEADERS = {"User-Agent": "mission-control-research/1.0"}
REPOS = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
NAMES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "license", "COPYING", "LICENSE-MIT", "LICENSE-APACHE"]
BRANCHES = ["main", "master"]
print(f"{len(REPOS)} repos")
for repo in REPOS:
    print(f"\n=== {repo} ===")
    got = False
    for br in BRANCHES:
        for name in NAMES:
            url = f"https://raw.githubusercontent.com/{repo}/{br}/{name}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
            except Exception as e:
                print("err", e)
                continue
            if r.status_code == 200 and len(r.text) > 20:
                lines = [l for l in r.text.splitlines() if l.strip()][:5]
                print(f"[{br}/{name}] " + " | ".join(lines)[:420])
                got = True
                break
        if got:
            break
    if not got:
        print("NO LICENSE FILE FOUND")
