"""Install the diagram-design agent skill into the Hermes skills dir (user-level)."""
import io
import shutil
import sys
import tarfile
from pathlib import Path

import requests

DEST = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\creative")
SKILL_DIR = DEST / "diagram-design"
URL = "https://codeload.github.com/cathrynlavery/diagram-design/tar.gz/refs/heads/main"

if (SKILL_DIR / "SKILL.md").exists() and "--force" not in sys.argv:
    print("already installed:", SKILL_DIR, "use --force to replace")
    sys.exit(0)

r = requests.get(URL, timeout=120)
r.raise_for_status()
print("tarball", round(len(r.content) / 1e6, 2), "MB")

tmp = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch\diagram-design-extract")
if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir(parents=True)

with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
    members = [m for m in tf.getmembers() if "/skills/diagram-design/" in m.name]
    tf.extractall(tmp, members=members)
    print("extracted members:", len(members))

src = next(p for p in tmp.rglob("SKILL.md")).parent
if SKILL_DIR.exists():
    shutil.rmtree(SKILL_DIR)
DEST.mkdir(parents=True, exist_ok=True)
shutil.copytree(src, SKILL_DIR)
print("installed ->", SKILL_DIR)

head = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()[:6]
print("frontmatter:", head)
files = sum(1 for _ in SKILL_DIR.rglob("*") if _.is_file())
size = sum(f.stat().st_size for f in SKILL_DIR.rglob("*") if f.is_file())
print(f"files={files} size={size/1e6:.2f} MB")
print("dirs:", sorted({str(p.relative_to(SKILL_DIR)) for p in SKILL_DIR.iterdir()}))
