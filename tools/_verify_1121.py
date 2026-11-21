import json, time
import requests

REPOS = [
    "kajisho5/motion-graphics-skill",
    "kajisho5/ffmpeg-skill",
    "KyaniteLabs/kinocut",
    "radityama/motion-studio",
    "sanT-0/facelesspro",
    "delexw/motion-graphics-agent",
    "JEMA-Software-Ltd/faceless-video-pipeline",
]
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
out = {}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=25)
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code} {resp.text[:120]}")
            time.sleep(1.2)
            continue
        d = resp.json()
        lic = (d.get("license") or {}).get("spdx_id")
        row = dict(full_name=d["full_name"], stars=d["stargazers_count"], license=lic,
                   pushed=d["pushed_at"], created=d["created_at"], lang=d.get("language"),
                   forks=d["forks_count"], archived=d["archived"], desc=(d.get("description") or "")[:140],
                   branch=d.get("default_branch"))
        out[r] = row
        print(f"{row['full_name']}: {row['stars']}* lic={lic} pushed={row['pushed'][:10]} created={row['created'][:10]} lang={row['lang']} archived={row['archived']}")
        # latest release
        rel = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=25)
        if rel.status_code == 200:
            rj = rel.json()
            assets = [a["name"] for a in rj.get("assets", [])][:8]
            out[r]["release"] = dict(tag=rj.get("tag_name"), published=rj.get("published_at"), assets=assets)
            print(f"   release {rj.get('tag_name')} {str(rj.get('published_at'))[:10]} assets={assets}")
        else:
            print(f"   releases/latest HTTP {rel.status_code}")
    except Exception as e:
        print(f"{r}: ERR {e}")
    time.sleep(1.2)

json.dump(out, open("research/daily/2026-11-21-repo-meta.json", "w", encoding="utf-8"), indent=1)
print("saved", len(out))
