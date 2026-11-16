import json, time
import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}

REPOS = [
    "leodavincs/kurgu",
    "CutWire-Studios/Drift",
    "Hhz0823/YoloCut",
    "openfilm/openfilm",
    "PedroMarinhoDev/ComfyUI-ReCaVSR",
]

for r in REPOS:
    resp = requests.get(f"https://api.github.com/repos/{r}", headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        print(f"{r}: HTTP {resp.status_code}")
        time.sleep(1)
        continue
    d = resp.json()
    print(f"{r}: {d.get('stargazers_count')}* {(d.get('license') or {}).get('spdx_id')} created {(d.get('created_at') or '')[:10]} pushed {(d.get('pushed_at') or '')[:10]} {d.get('language')}")
    print("   ", (d.get("description") or "")[:150])
    if r in ("CutWire-Studios/Drift", "leodavincs/kurgu"):
        rel = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=HEADERS, timeout=30)
        if rel.status_code == 200:
            rd = rel.json()
            print("    release:", rd.get("tag_name"), (rd.get("published_at") or "")[:10])
            print("    assets:", [a["name"] for a in rd.get("assets", [])][:12])
        else:
            print("    release HTTP", rel.status_code)
        time.sleep(1)
    time.sleep(1)
