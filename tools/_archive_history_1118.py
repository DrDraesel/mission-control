import re, pathlib

base = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references")
live = base / "query-yield-history.md"
arch = base / "query-yield-archive-2026-10a.md"

t = live.read_text(encoding="utf-8")
parts = re.split(r"(?m)^(?=- )", t)
header, entries = parts[0], parts[1:]

keep, moved = [], []
for e in entries:
    head = e.strip().split("\n")[0]
    if any(d in head for d in ("10-13 DONE", "10-14 DONE", "10-15 DONE", "10-16 DONE", "10-17 DONE")):
        moved.append(e)
    else:
        keep.append(e)

print("moved", len(moved), "entries:", [m.strip().split("\n")[0][:40] for m in moved])
new_live = header + "".join(keep)
live.write_text(new_live, encoding="utf-8")

at = arch.read_text(encoding="utf-8")
arch.write_text(at.rstrip() + "\n\n" + "".join(moved).strip() + "\n", encoding="utf-8")

print("live chars", len(new_live), "bytes", len(new_live.encode('utf-8')))
print("archive chars", len(arch.read_text(encoding='utf-8')))
