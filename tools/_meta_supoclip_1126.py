import json, pathlib, requests
base = pathlib.Path("research/daily")
led = json.loads((base/"seen-repos.json").read_text(encoding="utf-8"))
print("supoclip in ledger:", [k for k in led["repos"] if "supoclip" in k.lower()] or "ABSENT")
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
for r in ["FujiwaraChoki/supoclip"]:
    d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=30).json()
    print(r, "|", d.get("stargazers_count"), "|", (d.get("license") or {}).get("spdx_id"), "|", d.get("pushed_at"), "|", d.get("created_at"), "|", d.get("language"))
    print("   ", d.get("description"))
    rl = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=30).json()
    print("   latest release:", rl.get("tag_name"), "| assets:", [a["name"] for a in rl.get("assets", [])] or "none")
