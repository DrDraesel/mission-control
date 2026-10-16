"""Smoke-test rhubarb-lip-sync Windows CLI: download release zip -> extract -> --version."""
import os, glob, subprocess
import requests

URL = "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip"
scratch = os.path.join(os.environ.get("TMPDIR", r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch"), "rhubarb")
os.makedirs(scratch, exist_ok=True)
dest = os.path.join(scratch, "rhubarb.zip")

r = requests.get(URL, headers={"User-Agent": "mission-control-research/1.0"}, timeout=240, stream=True)
r.raise_for_status()
with open(dest, "wb") as f:
    for chunk in r.iter_content(1 << 20):
        f.write(chunk)
print("downloaded bytes:", os.path.getsize(dest))

import zipfile
with zipfile.ZipFile(dest) as z:
    z.extractall(scratch)

exes = glob.glob(os.path.join(scratch, "**", "rhubarb*.exe"), recursive=True)
print("exes found:", [os.path.relpath(e, scratch) for e in exes])
if exes:
    out = subprocess.run([exes[0], "--version"], capture_output=True, text=True, timeout=90)
    print("exit:", out.returncode)
    print("stdout:", (out.stdout or "")[:400].strip())
    print("stderr:", (out.stderr or "")[:400].strip())
