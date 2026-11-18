"""Medical-imaging lane: release assets + package availability (2026-11-18)."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

out = {}
for repo in ["OHIF/Viewers", "nroduit/Weasis", "cornerstonejs/cornerstone3D",
             "TorchIO-project/torchio", "ivmartel/dwv", "suyashkumar/dicom"]:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=H, timeout=20)
        if r.status_code == 200:
            d = r.json()
            assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in d.get("assets", [])][:8]
            out[repo] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "assets": assets}
            print(f"{repo} -> {d.get('tag_name')} ({out[repo]['published']}) assets={len(d.get('assets', []))}")
            for a in assets:
                print("   ", a)
        else:
            print(f"{repo} -> releases HTTP {r.status_code}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

# package availability
for pkg, kind in [("torchio", "pypi"), ("@cornerstonejs/core", "npm"), ("dicom", "pypi")]:
    try:
        if kind == "pypi":
            r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=20)
            if r.status_code == 200:
                d = r.json()
                rel = d["info"]["version"]
                files = [f["filename"] for f in d["urls"]]
                win = [f for f in files if "win" in f.lower() or f.endswith("none-any.whl") or "py3-none-any" in f]
                print(f"PYPI {pkg} {rel} :: {len(d['releases'])} releases; win/any={win[:3]}")
            else:
                print(f"PYPI {pkg} HTTP {r.status_code}")
        else:
            r = requests.get(f"https://registry.npmjs.org/{pkg.replace('/', '%2F')}", timeout=20)
            if r.status_code == 200:
                d = r.json()
                print(f"NPM {pkg} {d['dist-tags']['latest']} :: {d['license']} :: {len(d['versions'])} versions")
            else:
                print(f"NPM {pkg} HTTP {r.status_code}")
    except Exception as e:
        print("err pkg", pkg, e)

(OUT / f"{today}-medical-assets.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
