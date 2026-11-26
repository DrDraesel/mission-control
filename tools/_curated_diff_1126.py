import json, re, pathlib

base = pathlib.Path(r"C:\Users\GAMEPOWER\projects\mission-control")
cur = (base / "research/daily/2026-11-26-curated-projects.md").read_text(encoding="utf-8", errors="replace")
led = json.loads((base / "research/daily/seen-repos.json").read_text(encoding="utf-8"))
repos = {k.lower(): v for k, v in led["repos"].items()}

# find owner/repo mentions, both bare and in github links
names = set(re.findall(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", cur))
names |= set(re.findall(r"^\|\s*\[?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]?", cur, re.M))
names = {n.rstrip('.') for n in names if not n.lower().startswith(('docs/', 'assets/'))}
print("unique names in index:", len(names))

new = sorted(n for n in names if n.lower() not in repos)
print("NOT IN LEDGER:", len(new))
for n in new:
    # grab the surrounding line for context
    m = re.search(r"^.*" + re.escape(n) + r".*$", cur, re.M)
    line = (m.group(0)[:220] if m else "")
    print(f"  {n}  ::  {line.strip()}")
