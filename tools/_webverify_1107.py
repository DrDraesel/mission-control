"""11-07 web-lane verification: resolve candidate slugs via search API then verify core API + releases."""
import json, time, sys
from pathlib import Path
import requests

ROOT = Path(r"C:\Users\GAMEPOWER\projects\mission-control")
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

ledger = json.loads((ROOT / "research/daily/seen-repos.json").read_text(encoding="utf-8"))
lr = {k.lower() for k in ledger["repos"]}

KEYWORD_SEARCHES = [
    ("opendirector", "opendirector in:name"),
    ("weviscut", "weviscut in:name"),
    ("openstoryline", "openstoryline in:name"),
    ("maestro wan", "maestro in:name video wan"),
]
KNOWN = ["konecz/kodecz", "Hhz0823/YoloCut", "niklaus-ai-yt/stickframe", "jub0t/Concat"]

out = {"known": [], "searched": []}


def core(full):
    try:
        r = requests.get(f"https://api.github.com/repos/{full}", headers=H, timeout=25, allow_redirects=True)
        if r.status_code != 200:
            return {"full_name": full, "error": r.status_code}
        d = r.json()
        rec = {
            "full_name": d["full_name"], "stars": d["stargazers_count"],
            "license": (d.get("license") or {}).get("spdx_id"),
            "created": d["created_at"][:10], "pushed": d["pushed_at"][:10],
            "language": d.get("language"), "fork": d.get("fork"),
            "desc": (d.get("description") or "")[:220],
            "in_ledger": d["full_name"].lower() in lr,
        }
        rel = requests.get(f"https://api.github.com/repos/{d['full_name']}/releases/latest", headers=H, timeout=25)
        if rel.status_code == 200:
            rd = rel.json()
            rec["release"] = {"tag": rd.get("tag_name"), "published": (rd.get("published_at") or "")[:10],
                              "assets": [(a["name"], round(a["size"] / 1e6, 1)) for a in rd.get("assets", [])][:8]}
        else:
            rec["release"] = {"error": rel.status_code}
        return rec
    except Exception as e:
        return {"full_name": full, "error": str(e)}


for full in KNOWN:
    print("core:", full, flush=True)
    out["known"].append(core(full))
    time.sleep(1.5)

for label, q in KEYWORD_SEARCHES:
    print("search:", q, flush=True)
    try:
        r = requests.get("https://api.github.com/search/repositories", headers=H,
                         params={"q": q, "sort": "stars", "order": "desc", "per_page": 5}, timeout=25)
        items = [{"full_name": i["full_name"], "stars": i["stargazers_count"], "license": (i.get("license") or {}).get("spdx_id"),
                  "pushed": i["pushed_at"][:10], "created": i["created_at"][:10],
                  "desc": (i.get("description") or "")[:160]} for i in r.json().get("items", [])]
        out["searched"].append({"query": q, "status": r.status_code, "items": items})
    except Exception as e:
        out["searched"].append({"query": q, "error": str(e)})
    time.sleep(7)

p = ROOT / "research/daily/2026-11-07-webverify.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("\n=== KNOWN ===")
for r in out["known"]:
    print(json.dumps(r, ensure_ascii=False))
print("\n=== SEARCH ===")
for r in out["searched"]:
    print(r["query"], r.get("status"))
    for i in r.get("items", []):
        print("  ", i["full_name"], i["stars"], i["license"], i["created"], i["pushed"], "-", i["desc"][:90])
print("\nsaved", p)
