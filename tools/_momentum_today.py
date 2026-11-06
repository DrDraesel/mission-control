"""Print stars for a watchlist of repos present in today's raw sweep (no extra API calls)."""
import json
from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-11-06-github.json")
d = json.loads(p.read_text(encoding="utf-8"))
stars = {}
for q, payload in d["queries"].items():
    for it in payload.get("items", []):
        n = (it.get("full_name") or "").lower()
        stars[n] = max(stars.get(n, 0), it.get("stars") or 0)

WATCH = [
    "heygen-com/hyperframes", "jub0t/concat", "storytold/filmcraft", "storytold/effectcraft",
    "storytold/photocraft", "0xs4n4tg/kinetograph", "veedstudio/open-edit", "codewithameer/meercut",
    "moneyprinterturbo", "calesthio/openmontage", "lemomo-ai/lemo-opuscar", "pbakaus/impeccable",
    "tt-a1i/archify", "leonxlnx/taste-skill", "chaiNNer-org/chaiNNer", "toyxyz/toyxyz_rgbmocap",
    "andrew-babo/muse4ai", "d3voz/openjutsu", "rk0neki/openkatana", "theploggy/creatoros-studio",
    "0xshug0/audio.cpp", "k2-fsa/sherpa-onnx", "wyattblue/auto-editor", "mifi/lossless-cut",
    "open-pencil/open-pencil", "tangency-labs/solidcraft", "comfy-org/comfyui",
]
print("repo | stars (today's sweep, 0 = not surfaced today)")
for w in WATCH:
    print(f"{w:38s} {stars.get(w, 0):>8}")
