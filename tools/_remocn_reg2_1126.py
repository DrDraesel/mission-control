import json, requests, collections

r = requests.get("https://remocn.dev/r/registry.json", timeout=60)
reg = r.json()
items = reg.get("items") or reg
print("registry keys:", list(reg.keys())[:6] if isinstance(reg, dict) else type(reg))
print("items:", len(items))
types = collections.Counter(i.get("type") for i in items)
print("types:", dict(types))
cats = collections.Counter((i.get("categories") or ["?"])[0] for i in items)
print("top categories:", cats.most_common(12))
names = [i["name"] for i in items]
print("has counter-reveal:", "counter-reveal" in names)
print("sample names:", names[:8])

# get the one item, in both plausible shapes
for u in ["https://remocn.dev/r/counter-reveal.json"]:
    rr = requests.get(u, timeout=30)
    print(u, "->", rr.status_code, len(rr.content), "B")
    if rr.status_code == 200:
        d = rr.json()
        print("  item name:", d.get("name"), "| type:", d.get("type"), "| deps:", d.get("dependencies"))
        for f in d.get("files", []):
            print("  file:", f.get("path"), "| target:", f.get("target"), "| chars:", len(f.get("content", "")))
        src = (d.get("files") or [{}])[0].get("content", "")
        print("  source head:\n", src[:500])
        # check key remotion idioms
        for kw in ["useCurrentFrame", "interpolate", "spring", "Math.random", "Sequence"]:
            print(f"   {kw}:", kw in src)
