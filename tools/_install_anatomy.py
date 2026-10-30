"""Install wheresryan22/anatomy agent skill into Hermes skills dir (creative/anatomy)."""
import io
import shutil
import sys
import tarfile
from pathlib import Path

import requests

DEST = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\creative")
SKILL_DIR = DEST / "anatomy"
URL = "https://codeload.github.com/wheresryan22/anatomy/tar.gz/refs/heads/main"

if (SKILL_DIR / "SKILL.md").exists() and "--force" not in sys.argv:
    print("already installed:", SKILL_DIR)
    sys.exit(0)

r = requests.get(URL, timeout=180)
r.raise_for_status()
print("tarball", round(len(r.content) / 1e6, 2), "MB")

tmp = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch\anatomy-extract")
if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir(parents=True)

SKIP_TOP = {".github", ".git"}
with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
    members = []
    for m in tf.getmembers():
        parts = m.name.split("/")
        if len(parts) < 2:
            continue
        if parts[1] in SKIP_TOP:
            continue
        members.append(m)
    tf.extractall(tmp, members=members, filter="data")
    print("extracted members:", len(members))

src = next(p for p in tmp.iterdir() if p.is_dir())
if SKILL_DIR.exists():
    shutil.rmtree(SKILL_DIR)
DEST.mkdir(parents=True, exist_ok=True)
shutil.copytree(src, SKILL_DIR)
print("installed ->", SKILL_DIR)
print("frontmatter:", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()[:5])
files = sum(1 for _ in SKILL_DIR.rglob("*") if _.is_file())
size = sum(f.stat().st_size for f in SKILL_DIR.rglob("*") if f.is_file())
print(f"files={files} size={size/1e6:.2f} MB")
print("top:", sorted(p.name for p in SKILL_DIR.iterdir()))
