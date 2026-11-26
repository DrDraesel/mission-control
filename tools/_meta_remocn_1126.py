import json, requests
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
for r in ["Remocn/remocn", "AtlasCloudAI/atlas-explainer"]:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=30).json()
        print(r, "|", d.get("stargazers_count"), "|", (d.get("license") or {}).get("spdx_id"), "|", d.get("pushed_at"), "|", d.get("created_at"), "|", d.get("description"))
    except Exception as e:
        print(r, "ERR", e)
