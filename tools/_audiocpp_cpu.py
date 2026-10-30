"""CPU-portable audio.cpp build: download, extract, smoke-test CLI."""
import os, subprocess, time, zipfile
import requests

SCRATCH = r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch\audiocpp"
OUT = os.path.join(SCRATCH, "cpu")
os.makedirs(OUT, exist_ok=True)
url = "https://github.com/0xShug0/audio.cpp/releases/download/v0.9.3/audio-v0.9.3-bin-windows-x64-cpu-portable.zip"
zpath = os.path.join(SCRATCH, "cpu.zip")

if not os.path.exists(zpath):
    t0 = time.time()
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(zpath, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    print(f"downloaded {os.path.getsize(zpath)/1e6:.1f} MB in {time.time()-t0:.0f}s", flush=True)

with zipfile.ZipFile(zpath) as z:
    z.extractall(OUT)
print("extracted", flush=True)

exes = []
for root, _, files in os.walk(OUT):
    for f in files:
        if f.lower().endswith(".exe"):
            exes.append(os.path.join(root, f))
for p in exes:
    print("EXE", p, round(os.path.getsize(p) / 1e6, 1), "MB", flush=True)

cli = next((p for p in exes if "cli" in os.path.basename(p).lower()), None)
if cli:
    cwd = os.path.dirname(cli)
    for args in (["--help"], ["-h"], []):
        try:
            p = subprocess.run([cli] + args, capture_output=True, text=True, timeout=60, cwd=cwd)
            out = (p.stdout or "") + (p.stderr or "")
            print(f"\n=== {' '.join(args) or '(no args)'} rc={p.returncode} len={len(out)} ===", flush=True)
            print("\n".join(out.splitlines()[:28]), flush=True)
        except Exception as e:
            print("ERR", args, e, flush=True)
