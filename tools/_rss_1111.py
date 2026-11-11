import re, sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
items = re.findall(
    r"<item><title>(.*?)</title><link>(.*?)</link>.*?<pubDate>(.*?)</pubDate><description>(.*?)</description>",
    s,
    re.S,
)
print("items", len(items))
for t, l, d, desc in items[:14]:
    print("---", d[:16], "|", t[:120])
    print("   ", desc[:300].replace("&#39;", "'").replace("&amp;", "&"))
    print("   ", l)
