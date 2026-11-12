"""11-12 run: API-verify key repos (core API, ~1 req/s). Outputs research/daily/2026-11-12-repo-meta.json"""
import json, time, requests
from datetime import datetime
from pathlib import Path

OUT = Path("research/daily/2026-11-12-repo-meta.json")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}

REPOS = [
    "ifm-ai/PAN2",
    "UnlimitedEditing/ComfyUI-PAN2",
    "yiboz2001/UltraTex",
    "visualbruno/ComfyUI-UltraTex",
    "pixelartistry/PixelArtistry-UltraTex",
    "Comfy-Org/ComfyUI",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "nexu-io/open-design",
    "harry0703/MoneyPrinterTurbo",
    "tangency-labs/solidcraft",
    "0xS4N4TG/kinetograph",
    "shinyobjectz/raea",
    "kane50613/takumi",
    "google-labs-code/design.md",
    "meta/astryx",
    "veedstudio/open-edit",
    "edenfunf/reelmimic",
]

out = {}
for r in REPOS:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}", headers=HEADERS, timeout=30).json()
        if "full_name" not in d:
            out[r] = {"error": d.get("message"), "status": d.get("status")}
            print(r, "ERR", d.get("message"))
        else:
            out[r] = {
                "full_name": d["full_name"],
                "stars": d["stargazers_count"],
                "license": (d.get("license") or {}).get("spdx_id"),
                "pushed_at": d["pushed_at"][:10],
                "created_at": d["created_at"][:10],
                "language": d.get("language"),
                "archived": d.get("archived"),
                "desc": (d.get("description") or "")[:160],
            }
            print(f"{d['full_name']:45s} {d['stargazers_count']:>8} {(d.get('license') or {}).get('spdx_id')} {d['pushed_at'][:10]}")
    except Exception as e:
        out[r] = {"error": str(e)}
        print(r, "EXC", e)
    time.sleep(1.2)

if OUT.exists():
    try:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        if isinstance(prev, dict) and prev.get("date") == str(datetime.now().date()):
            prev["repos"].update(out)
            out = prev["repos"]
    except Exception:
        pass
OUT.write_text(json.dumps({"date": str(datetime.now().date()), "checked_at": datetime.now().isoformat(), "repos": out}, indent=1), encoding="utf-8")
print("saved", OUT)
