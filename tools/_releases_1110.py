import requests, time
H = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
for r in ["Comfy-Org/ComfyUI", "heygen-com/hyperframes", "storytold/effectcraft", "storytold/filmcraft", "jub0t/Concat", "nexu-io/open-design"]:
    try:
        j = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=20).json()
        print(f"{r}: {j.get('tag_name')} published {str(j.get('published_at'))[:10]} assets={len(j.get('assets') or [])}")
        names = [a['name'] for a in (j.get('assets') or [])]
        win = [n for n in names if 'win' in n.lower() or 'setup' in n.lower()]
        print("   win:", win[:4] if win else "none", "| all:", names[:4])
    except Exception as e:
        print(r, "ERR", e)
    time.sleep(0.8)
