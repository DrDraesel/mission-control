import requests, json, time
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
repos = [
    "shinyobjectz/raea",
    "voyager-so/vork",
    "hodgemann/mondo-music-video",
    "NickPittas/Keyloom",
    "Ltamann/ComfyUI-TBG-RevealLayer",
    "EtienneLescot/shouldercut",
    "360CVGroup/RevealLayer",
]
rows = []
for r in repos:
    try:
        j = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=20).json()
        row = dict(full_name=j.get("full_name"), stars=j.get("stargazers_count"), lang=j.get("language"),
                   lic=(j.get("license") or {}).get("spdx_id"), created=str(j.get("created_at"))[:10],
                   pushed=str(j.get("pushed_at"))[:10], desc=(j.get("description") or "")[:150])
        rows.append(row)
        print(f"{r}: {row['stars']}* {row['lic']} {row['lang']} created {row['created']} pushed {row['pushed']}")
        print("   ", row["desc"])
    except Exception as e:
        print(r, "ERR", e)
    time.sleep(1)
json.dump(rows, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-11-10-webverify.json", "w"), indent=1)
