"""DICOM/PACS infrastructure stack check for the newly-opened clinical lane (2026-11-18)."""
import json
import time
from datetime import date
from pathlib import Path

import requests

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

REPOS = [
    "orthanc-server/orthanc",
    "dcm4che/dcm4che",
    "pydicom/pydicom",
    "SimpleITK/SimpleITK",
    "Project-MONAI/MONAI",
    "MIC-DKFZ/nnUNet",
    "gdevilla/nnUNet",
    "Nicholas-Steele/pydicom-seg",
    "pydicom/pydicom-seg",
    "razorx89/dicomtls",
]

meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=H, timeout=20)
        if r.status_code == 200:
            d = r.json()
            meta[repo] = {
                "stars": d.get("stargazers_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "description": (d.get("description") or "")[:160],
            }
            print(f"OK {repo}: {d.get('stargazers_count')}* lic={meta[repo]['license']} pushed={meta[repo]['pushed_at']} lang={d.get('language')}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

# PyPI availability for the Python side
for pkg in ["pydicom", "SimpleITK", "monai", "nnunetv2", "pydicom-seg"]:
    try:
        r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=20)
        if r.status_code == 200:
            d = r.json()
            files = [f["filename"] for f in d["urls"]]
            print(f"PYPI {pkg} {d['info']['version']} :: {len(d['releases'])} releases :: {files[:2]}")
        else:
            print(f"PYPI {pkg} HTTP {r.status_code}")
    except Exception as e:
        print("err pypi", pkg, e)

(OUT / f"{today}-dicom-stack.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
