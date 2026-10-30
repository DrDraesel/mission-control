"""Probe candidate query phrasings for the code-rendered-film lane (2026-10-18)."""
import json
import time

import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
CANDS = [
    ("code-rendered-film", "code rendered video"),
    ("agent-film-skill", "agent film skill"),
    ("programmatic-video", "programmatic video"),
    ("claude-video-skill", "claude video skill"),
]

for slug, q in CANDS:
    r = requests.get(
        "https://api.github.com/search/repositories",
        headers=HEADERS,
        params={"q": q, "sort": "stars", "order": "desc", "per_page": 8},
        timeout=30,
    )
    if r.status_code != 200:
        print(slug, r.status_code, r.text[:150])
    else:
        d = r.json()
        print(f"== {slug}: '{q}' total={d.get('total_count')}")
        for it in d.get("items", []):
            print(f"   {it['full_name']} {it['stargazers_count']}* {str(it.get('created_at'))[:10]} {(it.get('description') or '')[:90]}")
    time.sleep(7)
