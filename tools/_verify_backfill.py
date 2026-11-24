import json, time, requests
from datetime import date
from pathlib import Path

OUT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = [
    "Lightricks/LTX-Video",
    "Wan-Video/Wan2.2",
    "Tencent-Hunyuan/HunyuanVideo",
    "genmoai/mochi",
    "hpcaitech/Open-Sora",
    "zai-org/CogVideo",
    "OpenTalker/SadTalker",
    "FFmpeg/FFmpeg",
    "yt-dlp/yt-dlp",
]
meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            meta[repo] = {
                "stars": d.get("stargazers_count"),
                "license": (d.get("license") or {}).get("spdx_id"),
                "language": d.get("language"),
                "created_at": (d.get("created_at") or "")[:10],
                "pushed_at": (d.get("pushed_at") or "")[:10],
                "description": (d.get("description") or "")[:200],
            }
            print(f"OK {repo}: {meta[repo]['stars']}* lic={meta[repo]['license']} pushed={meta[repo]['pushed_at']}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

p = OUT / f"{date.today().isoformat()}-backfill-meta.json"
p.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
print("saved", p.name, len(meta))
