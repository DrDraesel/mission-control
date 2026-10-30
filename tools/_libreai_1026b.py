import json, re, pathlib

CACHE = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\web")
LEDGER = pathlib.Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\seen-repos.json")
seen = json.load(open(LEDGER, encoding="utf-8"))["repos"]

files = list(CACHE.glob("libreaihub.vercel.app-*.md"))

def mul(v, suffix):
    v = float(v)
    return int(v * (1000 if suffix == "k" else 1_000_000 if suffix == "m" else 1))

link = re.compile(r"\[([^\]]{1,80}?)\]\(\.\./repos/([a-z0-9-]+)\.html\)")
stars_re = re.compile(r"★\s*\*{0,2}\s*([\d.]+)\s*([km]?)\s*\*{0,2}")
rows = {}
for f in files:
    txt = f.read_text(encoding="utf-8", errors="ignore")
    for m in link.finditer(txt):
        name, slug = m.group(1), m.group(2)
        window = txt[m.start(): m.start() + 300]
        sm = stars_re.search(window)
        stars = mul(sm.group(1), sm.group(2)) if sm else 0
        prev = rows.get(slug)
        if prev is None or stars > prev[1]:
            rows[slug] = (name.strip(" *"), stars)

out = [{"slug": s, "name": n, "stars": st,
        "in_ledger": any(s in k.lower() for k in seen)}
       for s, (n, st) in rows.items()]
out.sort(key=lambda r: -r["stars"])
print(f"{len(out)} distinct entries from {len(files)} pages; {sum(1 for r in out if not r['in_ledger'])} not in ledger\n")
for r in out:
    if not r["in_ledger"]:
        print(f'{r["stars"]:>7}  {r["slug"]:<32} {r["name"][:50]}')
json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-26-libreai-parsed.json", "w", encoding="utf-8"), indent=1)
