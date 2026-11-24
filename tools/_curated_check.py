import json, re, sys

led = json.load(open('research/daily/seen-repos.json', encoding='utf-8'))
repos = led['repos']

txt = open('research/daily/_tmp-curated.md', encoding='utf-8').read()
links = re.findall(r'\]\(https://github\.com/([^/)]+/[^/)]+)\)', txt)
seen = []
for l in links:
    n = l.strip('/')
    if n not in seen:
        seen.append(n)

absent = []
for n in seen:
    low = n.lower()
    match = [k for k in repos if k.lower() == low]
    if not match:
        absent.append(n)

print("curated repos:", len(seen))
print("absent from ledger:", len(absent))
for n in absent:
    print(n)
print("\n--- categories head ---")
cats = re.findall(r'分类：([^；\n]+)', txt)
from collections import Counter
for c, k in Counter(cats).most_common(20):
    print(k, c)
