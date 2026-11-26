import json, pathlib

base = pathlib.Path(r"C:\Users\GAMEPOWER\projects\mission-control")
led = json.loads((base / "research/daily/seen-repos.json").read_text(encoding="utf-8"))
repos = led["repos"]

probes = ["video-factory", "plenio", "nano-edge", "dugco", "remocn", "diagram-design",
          "stitch-skills", "recavsr", "taomate", "nkd", "clipmint", "remotion"]
for p in probes:
    hits = [k for k in repos if p in k.lower()]
    print(f"{p:18s} -> {hits if hits else 'ABSENT'}")
print("\nledger total:", led.get("total"), "updated:", led.get("updated"))
