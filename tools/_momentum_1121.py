import json, time
import requests

REPOS = [
    "Comfy-Org/ComfyUI",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "zhouxiaoka/autoclip",
    "nexu-io/openmotion",
    "shinyobjectz/raea",
    "0xS4N4TG/kinetograph",
    "MoneyPrinterTurbo/MoneyPrinterTurbo",
    "keyline-dev/keyline",
    "ifm-ai/PAN2",
    "kajisho5/ffmpeg-skill",
    "CutWire-Studios/Drift",
]
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
rows = []
for r in REPOS:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25)
        if d.status_code != 200:
            print(f"{r}: HTTP {d.status_code}")
            time.sleep(0.8)
            continue
        j = d.json()
        rel = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=25)
        tag = pub = None
        assets = []
        if rel.status_code == 200:
            rj = rel.json()
            tag = rj.get("tag_name")
            pub = str(rj.get("published_at"))[:10]
            assets = [a["name"] for a in rj.get("assets", [])][:4]
        print(f"{j['full_name']}: {j['stargazers_count']}* {((j.get('license') or {}).get('spdx_id'))} pushed={j['pushed_at'][:10]} rel={tag} ({pub}) assets={assets}")
        rows.append(dict(full_name=j["full_name"], stars=j["stargazers_count"], pushed=j["pushed_at"], tag=tag, published=pub, assets=assets))
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(0.9)
json.dump(rows, open("research/daily/2026-11-21-momentum.json", "w", encoding="utf-8"), indent=1)
