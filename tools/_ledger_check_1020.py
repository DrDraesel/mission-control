import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
led = json.load(open(os.path.join(BASE, "research", "daily", "seen-repos.json"), encoding="utf-8"))
repos = led.get("repos", {})
names = [
    "ZeroLu/awesome-seedance", "AKCodez/higgsfield-claude-skills",
    "UnderleveledBuilder/awesome-short-drama-skills", "dansugc/reelclaw",
    "charlesdove977/UGC-Factory", "jasonlee-breadcrumb/silent-ugc",
    "TheMattBerman/scrollclaw", "dean9703111/ig-card-generator",
    "Anil-matcha/Open-AI-UGC", "xixihhhh/clipforge",
    "SamurAIGPT/AI-Faceless-Video-Generator", "oneworks-ai/avatar",
    "barefootford/buttercut", "Upload-Post/avatar-mix",
    "DeathKnight88/jianying-bridge", "cclank/jevclip", "YeJe-cpu/SeeCut",
    "V0ightt/CutFrame", "webadderallorg/Recordly", "BusyBee3333/code-to-reels",
    "akshinmrv/Voxa", "yukitorido/short-video-generator-AI",
    "Kemerd/OpenOSV", "opusvideo/awesome-claude-video",
    "lemberalla/ave-releases", "deepbeepmeep/Wan2GP",
    "pireel/pireel", "blixvip/NullMotion",
]
for n in names:
    k = n.lower()
    hit = None
    for key in repos:
        if key.lower() == k:
            hit = key
            break
    if hit:
        v = repos[hit]
        first = v.get("first_seen") if isinstance(v, dict) else None
        print(f"IN-LEDGER  {n}  first_seen={first}")
    else:
        print(f"MISSING    {n}")
