import json, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mc-research"}
REPOS = [
    "Comfy-Org/ComfyUI",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "storytold/photocraft",
    "tangency-labs/solidcraft",
    "heygen-com/hyperframes",
    "jub0t/concat",
    "Lightricks/LTX-Desktop",
    "remotion-dev/remotion",
]
out = {}
for r in REPOS:
    try:
        resp = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            out[r] = {"error": resp.status_code}
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1.5)
            continue
        d = resp.json()
        assets = [(a["name"], round(a["size"] / 1048576, 1)) for a in d.get("assets", [])]
        out[r] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "assets": assets}
        print(f"{r}: {d.get('tag_name')} @ {(d.get('published_at') or '')[:10]}")
        win = [a for a in assets if any(k in a[0].lower() for k in ("win", ".exe", ".msi", "windows"))]
        if win:
            print("   WIN:", ", ".join(f"{n} {s}MB" for n, s in win[:6]))
        elif assets:
            print("   assets:", ", ".join(f"{n} {s}MB" for n, s in assets[:4]))
    except Exception as e:
        out[r] = {"error": str(e)}
        print(f"{r}: ERR {e}")
    time.sleep(1.5)

json.dump(out, open("research/daily/2026-11-05-releases.txt", "w", encoding="utf-8"), indent=1)
print("done")
