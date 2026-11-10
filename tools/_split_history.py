import re, pathlib
p = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-history.md")
t = p.read_text(encoding="utf-8")
print("total chars", len(t))
# split into entries on lines starting with "- "
parts = re.split(r"(?m)^(?=- )", t)
print("blocks", len(parts))
for i, b in enumerate(parts):
    head = b.strip().split("\n")[0][:70]
    print(i, len(b), head)
