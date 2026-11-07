"""11-07 momentum + release state for anchors."""
import json, time
from pathlib import Path
import requests

ROOT = Path(r"C:\Users\GAMEPOWER\projects\mission-control")
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "Comfy-Org/ComfyUI", "heygen-com/hyperframes", "storytold/filmcraft", "storytold/effectcraft",
    "0xS4N4TG/kinetograph", "veedstudio/open-edit", "jub0t/Concat", "OpenCut-app/OpenCut",
    "harry0703/MoneyPrinterTurbo", "tangency-labs/solidcraft",
]
out = []
for full in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{full}", headers=H, timeout=25, allow_redirects=True)
        if r.status_code != 200:
            print(full, "core", r.status_code, flush=True); time.sleep(1.2); continue
        d = r.json()
        rec = {"full_name": d["full_name"], "stars": d["stargazers_count"],
               "pushed": d["pushed_at"][:10], "license": (d.get("license") or {}).get("spdx_id")}
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=H, timeout=25)
        if rel.status_code == 200:
            rd = rel.json()
            rec["release"] = {"tag": rd.get("tag_name"), "published": (rd.get("published_at") or "")[:10],
                              "assets": [a["name"] for a in rd.get("assets", [])][:5]}
        else:
            rec["release"] = rel.status_code
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    except Exception as e:
        print(full, "ERR", e, flush=True)
    time.sleep(1.2)

(ROOT / "research/daily/2026-11-07-repo-meta.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", len(out))
