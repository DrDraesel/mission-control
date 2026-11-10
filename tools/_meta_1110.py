import requests, json, time
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
repos = [
    "Comfy-Org/ComfyUI", "heygen-com/hyperframes", "storytold/effectcraft", "storytold/filmcraft",
    "jub0t/Concat", "nexu-io/open-design", "harry0703/MoneyPrinterTurbo", "meta/astryx",
    "Lightricks/LTX-Desktop", "OpenCut-app/OpenCut", "kandinskylab/kandinsky-6",
    "shinyobjectz/raea", "voyager-so/vork", "ismael-joffroy-chandoutis/spritz",
]
out = []
for r in repos:
    try:
        j = requests.get(f"https://api.github.com/repos/{r}", headers=H, timeout=20).json()
        row = dict(full_name=j.get("full_name"), stars=j.get("stargazers_count"),
                   lic=(j.get("license") or {}).get("spdx_id"), pushed=str(j.get("pushed_at"))[:10])
        out.append(row)
        print(f"{row['full_name']}: {row['stars']}* {row['lic']} pushed {row['pushed']}")
    except Exception as e:
        print(r, "ERR", e)
    time.sleep(0.8)

for r in ["Lightricks/LTX-Desktop", "shinyobjectz/raea"]:
    try:
        j = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=20).json()
        print(f"\n{r} latest: {j.get('tag_name')} published {str(j.get('published_at'))[:10]}")
        for a in (j.get("assets") or [])[:8]:
            print(f"   {a['name']} {a['size']/1e6:.1f} MB")
        body = (j.get("body") or "")[:700]
        print("   body:", body.replace("\n", " | ")[:650])
    except Exception as e:
        print(r, "REL ERR", e)
    time.sleep(0.8)
json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-11-10-repo-meta.json", "w"), indent=1)
