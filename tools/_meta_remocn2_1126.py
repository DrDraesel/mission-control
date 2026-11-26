import requests
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
for r in ["Remocn/remocn", "Remocn/remocn-studio"]:
    d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=30).json()
    print(r, "|", d.get("stargazers_count"), "|", (d.get("license") or {}).get("spdx_id"), "|", d.get("pushed_at"), "|", d.get("created_at"), "| fork:", d.get("fork"), "|", d.get("homepage"))
    print("   ", d.get("description"))
