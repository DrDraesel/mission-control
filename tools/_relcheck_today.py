import json, urllib.request, sys

REPOS = [
    "comfyanonymous/ComfyUI",
    "heygen-com/hyperframes",
    "storytold/filmcraft",
    "storytold/effectcraft",
    "jub0t/Concat",
    "opencut-app/opencut",
    "Lightricks/LTX-Desktop",
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-research", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req, timeout=25))

for r in REPOS:
    try:
        rel = get(f"https://api.github.com/repos/{r}/releases/latest")
        assets = [a["name"] for a in rel.get("assets", [])][:4]
        print(f"{r}: {rel.get('tag_name')} published={rel.get('published_at')} assets={assets}")
    except Exception as e:
        print(f"{r}: ERR {e}")
