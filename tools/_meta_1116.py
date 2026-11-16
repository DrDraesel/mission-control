import json, sys, time
import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

REPOS = [
    "ersinkoc/AI-Video-Factory",
    "dughogan/DUGCO_Tools",
    "jplenio/Plenio-Music-Production-System",
    "Comfy-Org/ComfyUI",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "dughogan/nuke-alphagen-ofx",
]

out = {}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            out[r] = {"error": resp.status_code, "body": resp.text[:120]}
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1)
            continue
        d = resp.json()
        lic = (d.get("license") or {}).get("spdx_id")
        out[r] = {
            "stars": d.get("stargazers_count"),
            "license": lic,
            "created": (d.get("created_at") or "")[:10],
            "pushed": (d.get("pushed_at") or "")[:10],
            "lang": d.get("language"),
            "desc": (d.get("description") or "")[:110],
        }
        print(f"{r}: {d.get('stargazers_count')}* {lic} created {(d.get('created_at') or '')[:10]} pushed {(d.get('pushed_at') or '')[:10]} {d.get('language')}")
        time.sleep(1)
    except Exception as e:
        out[r] = {"error": str(e)}
        print(f"{r}: ERR {e}")

# ComfyUI latest release
try:
    rel = requests.get("https://api.github.com/repos/Comfy-Org/ComfyUI/releases/latest", headers=HEADERS, timeout=30).json()
    print("ComfyUI latest release:", rel.get("tag_name"), (rel.get("published_at") or "")[:10])
    print("  assets:", [a["name"] for a in rel.get("assets", [])][:6])
    out["_comfy_release"] = {"tag": rel.get("tag_name"), "published": (rel.get("published_at") or "")[:10]}
except Exception as e:
    print("comfy release err", e)

json.dump(out, open("research/daily/2026-11-16-repo-meta.json", "w", encoding="utf-8"), indent=2)
print("saved -> research/daily/2026-11-16-repo-meta.json")
