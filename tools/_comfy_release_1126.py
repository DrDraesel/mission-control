import requests
H = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-research"}
for r in ["Comfy-Org/ComfyUI", "Lightricks/LTX-Video", "heygen-com/hyperframes", "zhouxiaoka/autoclip"]:
    try:
        d = requests.get(f"https://api.github.com/repos/{r}/releases/latest", headers=H, timeout=30).json()
        print(r, "->", d.get("tag_name"), "|", (d.get("published_at") or "")[:10], "|", [a["name"] for a in d.get("assets", [])][:6])
    except Exception as e:
        print(r, "ERR", e)
