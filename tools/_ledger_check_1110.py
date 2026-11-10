import json
d = json.load(open(r'C:\Users\GAMEPOWER\projects\mission-control\research\daily\seen-repos.json'))['repos']
for n in ["toonflow", "arcreel", "spritz", "maestroai", "hy-nomas", "openshorts", "hy_nomas"]:
    hits = [k for k in d if n in k.lower()]
    print(n, "->", hits if hits else "NOT IN LEDGER")
