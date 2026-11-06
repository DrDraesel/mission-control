"""Verify a batch of repos via the GitHub SEARCH API (separate 10/min bucket).
Usage: python tools/_verify_1031.py name1 name2 ...  or reads tools/_verify_1101.txt
Prints full_name, stars, license, pushed, created, language, archived, desc.
"""
import json
import sys
import time
from pathlib import Path

import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
OUT = Path("research/daily/2026-11-02-repo-meta.json")


def probe(full_name: str) -> dict:
    url = "https://api.github.com/search/repositories"
    params = {"q": f"repo:{full_name}", "per_page": 1}
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"  net error {e}; retry")
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code == 200:
            items = r.json().get("items", [])
            if not items:
                return {"full_name": full_name, "error": "not found via search"}
            it = items[0]
            return {
                "full_name": it["full_name"],
                "url": it["html_url"],
                "stars": it["stargazers_count"],
                "forks": it["forks_count"],
                "language": it.get("language"),
                "license": (it.get("license") or {}).get("spdx_id"),
                "created_at": (it.get("created_at") or "")[:10],
                "pushed_at": (it.get("pushed_at") or "")[:10],
                "archived": it.get("archived"),
                "description": (it.get("description") or "")[:220],
            }
        if r.status_code in (403, 429, 500, 502, 503):
            wait = 30 * (attempt + 1)
            print(f"  HTTP {r.status_code}, wait {wait}s")
            time.sleep(wait)
            continue
        return {"full_name": full_name, "error": f"HTTP {r.status_code}"}
    return {"full_name": full_name, "error": "gave up"}


def main() -> None:
    names = sys.argv[1:]
    if not names:
        names = [l.strip() for l in Path("tools/_verify_1101.txt").read_text().splitlines() if l.strip()]
    meta = json.loads(OUT.read_text()) if OUT.exists() else {"date": "2026-11-02", "repos": {}}
    for i, n in enumerate(names):
        if n in meta["repos"] and meta["repos"][n].get("stars") is not None:
            print(f"cached {n}")
            continue
        if i:
            time.sleep(7)
        d = probe(n)
        meta["repos"][n] = d
        OUT.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
        if "error" in d:
            print(f"!! {n}: {d['error']}")
        else:
            print(f"{d['full_name']}: {d['stars']}* {d['license']} lang={d['language']} "
                  f"created={d['created_at']} pushed={d['pushed_at']} arch={d['archived']}")
            print(f"   {d['description']}")
    print("saved", OUT)


if __name__ == "__main__":
    main()
