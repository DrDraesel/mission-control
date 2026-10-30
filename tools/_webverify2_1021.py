import json, sys, time, requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
seen = json.load(open('research/daily/seen-repos.json', encoding='utf-8'))
names = set(seen.keys()) if isinstance(seen, dict) else set()

out = []
for r in sys.argv[1:]:
    tag = 'LEDGERED' if r in names else 'NEW     '
    ok = False
    for attempt in range(3):
        resp = requests.get('https://api.github.com/search/repositories',
                            params={'q': f'repo:{r}'}, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            if not items:
                print(f'{tag} {r}  NOT FOUND via search')
            else:
                d = items[0]
                lic = (d.get('license') or {}).get('spdx_id')
                print(f"{tag} {d['full_name']}  {d['stargazers_count']}*  {lic}  "
                      f"pushed={d['pushed_at'][:10]}  created={d['created_at'][:10]}  {d.get('language')}")
                print('    ' + (d.get('description') or '')[:220])
                out.append({'full_name': d['full_name'], 'stars': d['stargazers_count'], 'license': lic,
                            'pushed_at': d['pushed_at'][:10], 'created_at': d['created_at'][:10],
                            'language': d.get('language'), 'description': d.get('description'),
                            'in_ledger': r in names})
            ok = True
            break
        time.sleep(20)
    if not ok:
        print(f'{tag} {r}  FAILED')
    time.sleep(7)

json.dump(out, open('research/daily/2026-10-21-webfinds2.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('\nsaved', len(out))
