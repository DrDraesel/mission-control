import json, re, pathlib, sys

CACHE = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\web")
LEDGER = pathlib.Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\seen-repos.json")
seen = json.load(open(LEDGER, encoding="utf-8"))["repos"]

files = list(CACHE.glob("libreaihub.vercel.app-*.md"))
pat = re.compile(r"\[([^\]]+?)\s*★\s*([\d.]+)([km]?)\]\(\.\./repos/([a-z0-9-]+)\.html\)")
pat2 = re.compile(r"\[([^\]]+?)\]\(\.\./repos/([a-z0-9-]+)\.html\)\s*\n([^\n]*)\n[^\n]*★\s*([\d.]+)([km]?)\s*stars?\s*([A-Za-z0-9.\-]+)?")

def mul(v, suffix):
    v = float(v)
    return int(v * (1000 if suffix == "k" else 1_000_000 if suffix == "m" else 1))

rows = {}
for f in files:
    txt = f.read_text(encoding="utf-8", errors="ignore")
    for m in pat.finditer(txt):
        name, v, suf, slug = m.groups()
        rows.setdefault(slug, (name.strip(), mul(v, suf)))
    for m in pat2.finditer(txt):
        name, slug, desc, v, suf, lic = m.groups()
        rows.setdefault(slug, (name.strip(), mul(v, suf)))

out = []
for slug, (name, stars) in rows.items():
    out.append({"slug": slug, "name": name, "stars": stars,
                "in_ledger": any(slug in k.lower() or name.lower().replace(" ", "-") in k.lower() for k in seen)})
out.sort(key=lambda r: -r["stars"])
print(f"{len(out)} distinct entries parsed from {len(files)} LibreAI pages\n")
for r in out:
    if r["in_ledger"]:
        continue
    print(f'{r["stars"]:>7}  {r["slug"]:<34} {r["name"][:48]}')
json.dump(out, open(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-10-26-libreai-parsed.json", "w", encoding="utf-8"), indent=1)
