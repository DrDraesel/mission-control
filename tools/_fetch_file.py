"""Fetch a raw file from a GitHub repo (no API, no rate limit).
Usage: python tools/_fetch_file.py <owner/repo> <path/in/repo> [outfile]
Prints to stdout if no outfile.
"""
import sys
from pathlib import Path

import requests

repo, path = sys.argv[1], sys.argv[2]
out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
for br in ("main", "master"):
    url = f"https://raw.githubusercontent.com/{repo}/{br}/{path}"
    r = requests.get(url, headers={"User-Agent": "mission-control-research/1.0"}, timeout=20)
    if r.status_code == 200 and len(r.text) > 10:
        if out:
            out.write_text(r.text, encoding="utf-8")
            print(f"OK {repo}/{path} ({br}) -> {out} ({len(r.text)} chars)")
        else:
            print(r.text[:3000])
        sys.exit(0)
print(f"NOT FOUND: {repo}/{path}")
sys.exit(1)
