import requests
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
for r in ["imputnet/cobalt", "yt-dlp/yt-dlp", "SandAI-org/MAGI-2-preview", "SandAI-org/MAGI-2"]:
    d = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=30)
    if d.status_code == 200:
        j = d.json()
        print(f"{r:30s} {j['stargazers_count']:>7} {(j.get('license') or {}).get('spdx_id')} {j['pushed_at'][:10]} | {(j.get('description') or '')[:90]}")
    else:
        print(r, d.status_code)
