"""Smoke-test Mirage Tesseract Windows CLI: download, sha256-verify, extract, run --help.
Scratch dir only. Bounded: no install, no PATH changes."""
import hashlib, os, subprocess, sys, zipfile
from pathlib import Path
import requests

SCRATCH = Path(os.environ.get("TMPDIR", r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch")) / "tsrct"
SCRATCH.mkdir(parents=True, exist_ok=True)

BASE = "https://github.com/mirage-hq/Tesseract/releases/download/v0.2.0"
ZIP = "tesseract-0.2.0-windows-x86_64.zip"
zip_path = SCRATCH / ZIP

if not zip_path.exists():
    print("downloading", ZIP, "...", flush=True)
    with requests.get(f"{BASE}/{ZIP}", stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
print("zip size:", round(zip_path.stat().st_size / 1e6, 1), "MB")

# checksum
sha_txt = requests.get(f"{BASE}/{ZIP}.sha256", timeout=30).text
print("sha256 file says:", sha_txt.strip()[:120])
expected = sha_txt.split()[0].strip().lower()
h = hashlib.sha256()
with open(zip_path, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("computed sha256 matches:", h.hexdigest() == expected)

# extract
EX = SCRATCH / "extracted"
if not EX.exists():
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        print("zip entries (first 15):", names[:15])
        z.extractall(EX)
    print("extracted to", EX)

# find exe
exes = [p for p in EX.rglob("*.exe")]
print("exes found:", [str(p.relative_to(EX)) for p in exes][:10])

if exes:
    exe = exes[0]
    for args in (["--help"], ["--version"]):
        try:
            r = subprocess.run([str(exe)] + args, capture_output=True, timeout=60)
            out = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
            print(f"\n$ tesseract {' '.join(args)}  -> exit {r.returncode}")
            print(out[:1500])
            break
        except subprocess.TimeoutExpired:
            print(f"timeout running {' '.join(args)}")
        except Exception as e:
            print("run error:", e)
