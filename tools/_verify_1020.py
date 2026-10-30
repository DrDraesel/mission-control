"""10-20 verify: repos of interest -> stars/license/pushed_at. /repos primary, search-API fallback on 403."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    # sweep NEW (ugc-video query debut)
    "ZeroLu/awesome-seedance",
    "AKCodez/higgsfield-claude-skills",
    "UnderleveledBuilder/awesome-short-drama-skills",
    "dansugc/reelclaw",
    "charlesdove977/UGC-Factory",
    "jasonlee-breadcrumb/silent-ugc",
    "TheMattBerman/scrollclaw",
    "dean9703111/ig-card-generator",
    # web lane
    "oneworks-ai/avatar",
    "Upload-Post/avatar-mix",
    "DeathKnight88/jianying-bridge",
    "cclank/jevclip",
    "V0ightt/CutFrame",
    "BusyBee3333/code-to-reels",
    "Kemerd/OpenOSV",
    "opusvideo/awesome-claude-video",
    "lemberalla/ave-releases",
    "graphiteeditor/graphite",
    # momentum / status
    "deepbeepmeep/Wan2GP",
    "Anil-matcha/Open-AI-UGC",
    "SamurAIGPT/AI-Faceless-Video-Generator",
    "barefootford/buttercut",
    "pireel/pireel",
    "heygen-com/hyperframes",
    "storytold/filmcraft",
    "jub0t/Concat",
    "academa-labs/manimgx",
    "OpenCut-app/OpenCut",
    "aqm857886159/Nomi",
]

meta = {}
blocked = False


def from_item(d, key):
    return {
        "stars": d.get("stargazers_count"),
        "forks": d.get("forks_count"),
        "license": (d.get("license") or {}).get("spdx_id"),
        "language": d.get("language"),
        "created_at": (d.get("created_at") or "")[:10],
        "pushed_at": (d.get("pushed_at") or "")[:10],
        "description": (d.get("description") or "")[:220],
        "topics": d.get("topics", []),
        "homepage": d.get("homepage"),
        "full_name": d.get("full_name"),
    }


for repo in REPOS:
    got = None
    if not blocked:
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
            if r.status_code == 200:
                got = from_item(r.json(), repo)
            elif r.status_code in (403, 429):
                blocked = True
                print(f"RATE-LIMIT on /repos, switching to search bucket")
            else:
                print(f"HTTP {r.status_code} {repo}")
                meta[repo] = {"error": r.status_code}
        except Exception as e:
            print("err", repo, e)
    if got is None and blocked:
        # search-API bucket (10/min) — 7s spacing
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=HEADERS,
                params={"q": f"repo:{repo}", "per_page": 1},
                timeout=25,
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    got = from_item(items[0], repo)
                else:
                    print(f"SEARCH-EMPTY {repo}")
                    meta[repo] = {"error": "not_found"}
            else:
                print(f"SEARCH HTTP {r.status_code} {repo}")
                meta[repo] = {"error": r.status_code}
        except Exception as e:
            print("err-search", repo, e)
        time.sleep(7)
    if got:
        meta[repo] = got
        print(f"OK {repo}: {got['stars']}* lic={got['license']} created={got['created_at']} pushed={got['pushed_at']} lang={got['language']}")
    if not blocked:
        time.sleep(1)

(OUT / f"{today}-repo-meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"saved meta for {len(meta)} repos -> {today}-repo-meta.json")
