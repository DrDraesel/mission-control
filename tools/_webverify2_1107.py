"""11-07 web-lane verification batch 2."""
import json, time
from pathlib import Path
import requests

ROOT = Path(r"C:\Users\GAMEPOWER\projects\mission-control")
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
ledger = json.loads((ROOT / "research/daily/seen-repos.json").read_text(encoding="utf-8"))
lr = {k.lower() for k in ledger["repos"]}

REPOS = ["jnMetaCode/openshorts", "Auto-Vio/autovio", "mkamranr/reelforge", "Blizaine/Maestro", "konecz/kodecz"]
out = []
for full in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{full}", headers=H, timeout=25, allow_redirects=True)
        if r.status_code != 200:
            out.append({"full_name": full, "error": r.status_code}); print(full, r.status_code, flush=True); time.sleep(1.2); continue
        d = r.json()
        rec = {"full_name": d["full_name"], "stars": d["stargazers_count"], "license": (d.get("license") or {}).get("spdx_id"),
               "created": d["created_at"][:10], "pushed": d["pushed_at"][:10], "language": d.get("language"),
               "desc": (d.get("description") or "")[:260], "in_ledger": d["full_name"].lower() in lr}
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=H, timeout=25)
        if rel.status_code == 200:
            rd = rel.json()
            rec["release"] = {"tag": rd.get("tag_name"), "published": (rd.get("published_at") or "")[:10],
                              "assets": [(a["name"], round(a["size"] / 1e6, 1)) for a in rd.get("assets", [])][:6]}
        else:
            rec["release"] = rel.status_code
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    except Exception as e:
        out.append({"full_name": full, "error": str(e)})
    time.sleep(1.2)

(ROOT / "research/daily/2026-11-07-webverify2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved")
