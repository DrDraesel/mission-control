"""Assemble 2026-10-15-repo-meta.json from verified artifacts."""
import json
from datetime import date
from pathlib import Path

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
meta = {}

# sweep new candidates (search-API verified)
nc = json.loads((D / f"{date.today().isoformat()}-new-candidates.json").read_text(encoding="utf-8"))
items = nc if isinstance(nc, list) else nc.get("repos", nc.get("new", []))
for r in items:
    lic = r.get("license")
    meta[r["full_name"]] = {
        "stars": r.get("stars"),
        "license": (lic.get("spdx_id") if isinstance(lic, dict) else lic),
        "created_at": (r.get("created_at") or "")[:10],
        "pushed_at": (r.get("pushed_at") or "")[:10],
        "desc": (r.get("description") or "")[:140],
        "source": "sweep",
    }

# web verification (search bucket)
for f in (f"{date.today().isoformat()}-webverify-meta.json", f"{date.today().isoformat()}-webverify-direct.json"):
    p = D / f
    if p.exists():
        for k, v in json.loads(p.read_text(encoding="utf-8")).items():
            slug = v.get("full_name", k)
            meta[slug] = {
                "stars": v.get("stars"),
                "license": v.get("license"),
                "created_at": v.get("created_at"),
                "pushed_at": v.get("pushed_at"),
                "desc": v.get("desc", v.get("description", ""))[:140],
                "source": "web-verified",
            }

# manual adds verified this run (repos probe / releases)
manual = {
    "deepbeepmeep/Wan2GP": {"stars": 10517, "license": "NOASSERTION (WanGP Community License 2.0)", "pushed_at": "2026-10-12", "created_at": "2025-02-27",
                            "desc": "GPU-poor super app: Wan/LTX-2/H3/Hunyuan/Kandinsky + TTS; 6GB min, LTX-2@10GB; Win .bat installer"},
    "beziointeractive/morphable-desktop": {"stars": 4, "license": "GPL-3.0", "pushed_at": "2026-09-28", "created_at": "2026-08-31",
                                           "desc": "Morphable Community motion designer; Win x64 setup.exe 30.6MB v26.1.0 (09-02)", "source": "web-verified"},
    "WeftCut/WeftCut": {"release": "v0.4.0 (10-12): WeftCut-win-x64.exe 237.2MB + mac dmg + linux deb/AppImage", "source": "web-verified"},
    "notepower2k1/CapCap": {"release": "LocalUIV8.6 (10-14): CapCapV86.zip 815.8MB", "source": "sweep"},
    "johnnyang0612/bearcarousel": {"release": "v0.2.0 (07-23): BearCarousel.exe 29.9MB + mac tars", "source": "web-verified"},
    "xuanyustudio/LocalMiniDrama": {"release": "v1.2.8 (07-01): LocalMiniDrama(-Lite).1.2.8.exe 109/187.4MB", "source": "sweep"},
    "kyogreultima/tramme": {"release": "v0.6.0 (10-11): tramme-windows-x64-setup.exe 21.3MB + mac dmg + linux", "source": "web-verified"},
}
for slug, extra in manual.items():
    if slug in meta:
        meta[slug].update({k: v for k, v in extra.items() if v is not None})
    else:
        meta[slug] = extra

out = D / f"{date.today().isoformat()}-repo-meta.json"
out.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", out.name, "entries:", len(meta))
