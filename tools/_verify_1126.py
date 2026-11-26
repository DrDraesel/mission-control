import json, time, requests, pathlib
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
repos = ["Remocn/remocn", "fastvideo-project/dreamverse-harness", "Tencent/libpag",
         "screenpipe/screenpipe", "Dakkshin/after-effects-mcp", "RxLaboratory/Duik",
         "omnimux-ai/omnimux-client", "Just-Moh-it/Mockoops", "jplenio/Plenio-Music-Production-System"]
out = {}
for r in repos:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=30).json()
        out[r] = {"stars": d.get("stargazers_count"), "lic": (d.get("license") or {}).get("spdx_id"),
                  "pushed": d.get("pushed_at"), "created": d.get("created_at"),
                  "lang": d.get("language"), "desc": d.get("description"), "homepage": d.get("homepage")}
        print(f"{r:42s} {out[r]['stars']:>7} {str(out[r]['lic']):14s} {str(out[r]['pushed'])[:10]} {out[r]['lang']}")
    except Exception as e:
        print(r, "ERR", e)
    time.sleep(1)
pathlib.Path("research/daily/2026-11-26-repo-meta.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

# licence files for the NOASSERTION ones
for r in ["Tencent/libpag", "screenpipe/screenpipe"]:
    for p in ["LICENSE", "LICENSE.txt", "LICENSE.md"]:
        u = f"https://raw.githubusercontent.com/{r}/main/{p}"
        rr = requests.get(u, timeout=25)
        if rr.status_code == 200:
            print(f"\n--- {r}/{p} ({len(rr.text)} chars) ---\n{rr.text[:400]}")
            break
