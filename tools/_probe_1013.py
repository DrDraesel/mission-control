"""One-off 2026-10-13 probe: ledger membership + API existence for web-found leads and ArtCraft new-app guesses."""
import json
import time
from pathlib import Path

import requests

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
ledger = json.loads((D / "seen-repos.json").read_text(encoding="utf-8"))["repos"]

names = [
    "hypit-ai/hypit",
    "AbdullahNaveed/ai-shorts-generator",
    "IlyassCODEX/Faceless-Reels-AI-Agent-for-Instagram",
    "OpenMontage/OpenMontage",
    "storytold/figcraft",
    "storytold/wordcraft",
    "storytold/soundcraft",
    "storytold/deckcraft",
    "storytold/cadcraft",
    "storytold/gridcraft",
]

print("=== LEDGER CHECK ===")
for n in names:
    tail = n.split("/")[-1].lower()
    hits = [k for k in ledger if tail in k.lower()]
    print(f"{n}: {'IN-LEDGER' if n in ledger else 'not-in-ledger'} | similar: {hits[:6]}")

print("\n=== API CHECK ===")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
for repo in names:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            lic = (d.get("license") or {}).get("spdx_id")
            print(f"OK {repo}: {d['stargazers_count']}* lic={lic} created={d['created_at'][:10]} pushed={d['pushed_at'][:10]} lang={d.get('language')}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1.2)
