import json, pathlib
led = json.loads(pathlib.Path("research/daily/seen-repos.json").read_text(encoding="utf-8"))
for p in ["dreamverse", "magi-2", "magi2", "hyperflow", "hy-nomas", "hynomas", "fastvideo",
          "vidbee", "cobalt", "lux", "you-get", "streamlink", "open-ai-ugc", "printfilm", "higgsfield-claude"]:
    hits = [k for k in led["repos"] if p in k.lower()]
    print(f"{p:16s} -> {hits if hits else 'ABSENT'}")
