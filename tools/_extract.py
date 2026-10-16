"""Extract key signals from fetched READMEs (compact). Usage: python tools/_extract.py [names.txt]
Names file = one repo full_name per line; default: all files in readmes/ modified in last 24h."""
import re
import sys
import time
from pathlib import Path

RD = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\readmes")

if len(sys.argv) > 1:
    names = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
    files = [RD / (n.replace("/", "__") + ".md") for n in names]
    files = [f for f in files if f.exists()]
else:
    cutoff = time.time() - 86400
    files = [f for f in sorted(RD.glob("*.md")) if f.stat().st_mtime > cutoff]

for f in files:
    t = f.read_text(encoding="utf-8", errors="replace")
    t2 = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t2 = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", t2)
    t2 = re.sub(r"<[^>]+>", "", t2)
    t2 = re.sub(r"\n{3,}", "\n\n", t2)
    head = t2.strip()[:420].replace("\n", " ")
    print(f"\n{'='*70}\n# {f.stem}\n  {head}")
    seen = []
    for line in t2.splitlines():
        low = line.lower()
        if any(k in low for k in ["windows", "pip install", "ffmpeg", "license", "python ", "python3", "requirement", "gpu", "vram", "cuda", "comfyui", "node ", "download"]):
            s = line.strip()[:150]
            if s and s not in seen and len(seen) < 5:
                seen.append(s)
                print("  |", s)
