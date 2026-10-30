import json, sys, time
import requests

HEAD = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

NEW = [
    "tt-a1i/archify",
    "OrellBuehler/kerf",
    "ATH-MaaS/Pixelle-Video",
    "earthtojake/text-to-cad",
    "alchaincyf/huashu-design",
    "Nutlope/hallmark",
    "Anil-matcha/Open-Generative-AI",
]

MOMENTUM = [
    "heygen-com/hyperframes",
    "nexu-io/open-design",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "jub0t/concat",
    "tangency-labs/solidcraft",
    "lemomo-ai/lemo-opuscar",
    "academa-labs/manimgx",
    "cathrynlavery/diagram-design",
    "OpenCut-app/OpenCut",
    "remotion-dev/remotion",
    "wheresryan22/anatomy",
    "webadderallorg/Recordly",
    "getopenscreen/openscreen",
    "deepbeepmeep/WanGP",
    "Comfy-Org/ComfyUI",
    "Lightricks/LTX-Desktop",
    "FlashML-org/FreeVideo",
]

out = {}
errors = []


def fetch(full, want_releases=False):
    resp = requests.get(f"https://api.github.com/repos/{full}", headers=HEAD, timeout=25)
    if resp.status_code != 200:
        print(f"{full}: HTTP {resp.status_code} {resp.text[:100]}")
        errors.append((full, resp.status_code))
        return None
    d = resp.json()
    assets, tag = [], None
    if want_releases:
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=HEAD, timeout=25)
        if rel.status_code == 200:
            rj = rel.json()
            tag = rj.get("tag_name")
            assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in rj.get("assets", [])]
        else:
            print(f"   releases/latest HTTP {rel.status_code}")
    rec = {
        "stars": d["stargazers_count"], "forks": d["forks_count"],
        "license": (d.get("license") or {}).get("spdx_id"),
        "pushed_at": d.get("pushed_at"), "created_at": d.get("created_at"),
        "desc": (d.get("description") or "")[:230],
        "homepage": d.get("homepage"), "language": d.get("language"),
        "archived": d.get("archived"), "topics": (d.get("topics") or [])[:12],
        "latest_tag": tag, "assets": assets[:14],
    }
    out[d["full_name"]] = rec
    print(f"{d['full_name']}: {rec['stars']}* {rec['license']} pushed={rec['pushed_at']} created={(rec['created_at'] or '')[:10]} lang={rec['language']}")
    print(f"   {rec['desc']}")
    if want_releases:
        print(f"   tag={tag} assets={assets[:8]}")
    return rec


for r in NEW:
    fetch(r, want_releases=True)
    time.sleep(1.1)

for r in MOMENTUM:
    fetch(r)
    time.sleep(1.1)

json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-27-repo-meta.json", "w", encoding="utf-8"), indent=1)
print(f"\nsaved 2026-10-27-repo-meta.json ({len(out)} repos, {len(errors)} errors)")
