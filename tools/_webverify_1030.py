"""Verify web-found candidates against GitHub REST API (core, ~1 req/s)."""
import json, time, sys
import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "d3voz/openjutsu",
    "inikolax/Remiqora-Video",
    "heyimjames/tela",
    "AIEraDev/Clypra",
    "chengxs1994/EasyCut",
    "Reubencfernandes/Open-Video-Craft",
    "phucnguyentvp1/frameweaver",
    "Metatransformer/artboard",
    "mir-ashiq/canvix",
    "Augani/openreel-video",
    "deepopen-com/deepopen-3d-webs",
    "FireRedTeam/FireRed-OpenStoryline",
    "haidrrrry/claude-remotion-skill",
    "aqm857886159/Nomi",
    "MartinDelophy/ai-video-editor",
]
WANT_ASSETS = {
    "d3voz/openjutsu", "inikolax/Remiqora-Video", "AIEraDev/Clypra",
    "chengxs1994/EasyCut", "heyimjames/tela", "Metatransformer/artboard",
}

out = {}
for r in REPOS:
    url = f"https://api.github.com/repos/{r}"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        except Exception as e:
            print(f"{r}: net error {e}", flush=True)
            time.sleep(5)
            continue
        if resp.status_code == 200:
            d = resp.json()
            lic = (d.get("license") or {}).get("spdx_id")
            out[r] = {
                "full_name": d["full_name"], "stars": d["stargazers_count"],
                "language": d.get("language"), "license": lic,
                "created_at": d["created_at"][:10], "pushed_at": d["pushed_at"][:10],
                "desc": (d.get("description") or "")[:220],
                "topics": (d.get("topics") or [])[:8],
                "default_branch": d.get("default_branch"),
            }
            print(f"OK {d['full_name']} {d['stargazers_count']}* {lic} push={d['pushed_at'][:10]} lang={d.get('language')}", flush=True)
            if r in WANT_ASSETS:
                time.sleep(1)
                try:
                    rel = requests.get(url + "/releases/latest", headers=HEADERS, timeout=25)
                    if rel.status_code == 200:
                        rd = rel.json()
                        out[r]["latest_release"] = {
                            "tag": rd.get("tag_name"),
                            "published": (rd.get("published_at") or "")[:10],
                            "assets": [(a["name"], round(a["size"] / 1e6, 1)) for a in rd.get("assets", [])][:12],
                        }
                        print("   release", rd.get("tag_name"), [a["name"] for a in rd.get("assets", [])][:6], flush=True)
                    else:
                        out[r]["latest_release"] = {"http": rel.status_code}
                        print("   release", rel.status_code, flush=True)
                except Exception as e:
                    print("   release err", e, flush=True)
            break
        elif resp.status_code in (301, 302):
            url = resp.headers.get("Location", url)
        elif resp.status_code == 404:
            print(f"404 {r}", flush=True)
            out[r] = {"error": 404}
            break
        elif resp.status_code in (403, 429):
            print(f"{r}: {resp.status_code} rate limited, sleeping 60", flush=True)
            time.sleep(60)
        else:
            print(f"{r}: HTTP {resp.status_code}", flush=True)
            out[r] = {"error": resp.status_code}
            break
    time.sleep(1.2)

json.dump(out, open("research/daily/2026-10-30-webmeta.json", "w"), indent=1)
print("saved", len(out))
