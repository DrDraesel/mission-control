"""Download + extract audio.cpp Windows CUDA 13.3 build for a smoke test."""
import json, os, sys, time, zipfile
import requests

SCRATCH = r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch\audiocpp"
os.makedirs(SCRATCH, exist_ok=True)

H = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control"}
rel = requests.get("https://api.github.com/repos/0xShug0/audio.cpp/releases/latest", headers=H, timeout=30).json()
asset = next(a for a in rel["assets"] if "windows-x64-cuda13.3.zip" in a["name"])
url, size = asset["browser_download_url"], asset["size"]
zpath = os.path.join(SCRATCH, asset["name"])
print("asset", asset["name"], round(size / 1e6, 1), "MB", flush=True)

if not os.path.exists(zpath) or os.path.getsize(zpath) != size:
    t0 = time.time()
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        done = 0
        with open(zpath, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
        print(f"downloaded {done/1e6:.1f} MB in {time.time()-t0:.0f}s", flush=True)

with zipfile.ZipFile(zpath) as z:
    z.extractall(os.path.join(SCRATCH, "extracted"))
print("extracted", flush=True)

EXTS = (".exe",)
for root, dirs, files in os.walk(os.path.join(SCRATCH, "extracted")):
    for f in files:
        if f.lower().endswith(EXTS) and ("cli" in f.lower() or "audio" in f.lower() or "server" in f.lower()):
            p = os.path.join(root, f)
            print("EXE", p, round(os.path.getsize(p) / 1e6, 1), "MB", flush=True)
