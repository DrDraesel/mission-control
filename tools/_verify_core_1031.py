"""Verify repos via the CORE REST API (/repos/<name>) - separate 60/hr bucket.
Avoids clashing with the search-API sweep. Follows 301 redirects (renames).
"""
import json
import sys
import time
from pathlib import Path

import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
OUT = Path("research/daily/2026-10-31-repo-meta.json")


def probe(full_name: str) -> dict:
    url = f"https://api.github.com/repos/{full_name}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    except requests.exceptions.RequestException as e:
        return {"full_name": full_name, "error": f"net {e}"}
    if r.status_code != 200:
        return {"full_name": full_name, "error": f"HTTP {r.status_code}"}
    it = r.json()
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


def main() -> None:
    names = sys.argv[1:]
    if not names:
        names = [l.strip() for l in Path("tools/_verify_1031.txt").read_text().splitlines() if l.strip()]
    meta = json.loads(OUT.read_text()) if OUT.exists() else {"date": "2026-10-31", "repos": {}}
    for i, n in enumerate(names):
        if meta["repos"].get(n, {}).get("stars") is not None:
            print(f"cached {n}")
            continue
        if i:
            time.sleep(1.5)
        d = probe(n)
        meta["repos"][d["full_name"]] = d
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
