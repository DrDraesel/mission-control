import json, time
import requests

H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "Comfy-Org/ComfyUI",
    "heygen-com/hyperframes",
    "jub0t/Concat",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "0xS4N4TG/kinetograph",
    "veedstudio/open-edit",
    "tangency-labs/solidcraft",
    "MoneyPrinterTurbo/MoneyPrinterTurbo",
    "tt-a1i/archify",
    "pbakaus/impeccable",
    "Leonxlnx/taste-skill",
    "cloudai-x/threejs-skills",
    "kandinskylab/kandinsky-6",
]
out = {}
for r in REPOS:
    rec = {}
    try:
        x = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25, allow_redirects=True)
        if x.status_code == 200:
            d = x.json()
            rec["stars"] = d.get("stargazers_count")
            rec["pushed_at"] = (d.get("pushed_at") or "")[:10]
            rec["license"] = (d.get("license") or {}).get("spdx_id")
            rec["full_name"] = d.get("full_name")
        else:
            rec["repo_http"] = x.status_code
    except Exception as e:
        rec["repo_err"] = str(e)
    time.sleep(0.7)
    try:
        y = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=25, allow_redirects=True)
        if y.status_code == 200:
            rel = y.json()
            rec["latest_tag"] = rel.get("tag_name")
            rec["published"] = (rel.get("published_at") or "")[:10]
            rec["assets"] = [a.get("name") for a in rel.get("assets", [])][:8]
        else:
            rec["rel_http"] = y.status_code
    except Exception as e:
        rec["rel_err"] = str(e)
    time.sleep(0.7)
    out[r] = rec
    print(r, json.dumps(rec, ensure_ascii=False)[:420])
json.dump(out, open("research/daily/2026-11-09-repo-meta.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
