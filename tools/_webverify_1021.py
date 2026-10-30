import json, sys, time, requests

seen = json.load(open('research/daily/seen-repos.json', encoding='utf-8'))
names = set(seen.keys()) if isinstance(seen, dict) and 'repos' not in seen else set(seen.get('repos', {}).keys())

cands = sys.argv[1:]
out = []
for r in cands:
    tag = 'LEDGERED' if r in names else 'NEW     '
    try:
        resp = requests.get(f'https://api.github.com/repos/{r}', timeout=25,
                            headers={'Accept': 'application/vnd.github+json'})
        if resp.status_code != 200:
            print(f'{tag} {r}  HTTP {resp.status_code}')
            time.sleep(1.2)
            continue
        d = resp.json()
        lic = (d.get('license') or {}).get('spdx_id')
        line = (f"{tag} {d['full_name']}  {d['stargazers_count']}*  {lic}  "
                f"pushed={d['pushed_at'][:10]}  created={d['created_at'][:10]}  {d.get('language')}  "
                f"archived={d.get('archived')}")
        print(line)
        print('    ' + (d.get('description') or '')[:220])
        out.append({'full_name': d['full_name'], 'stars': d['stargazers_count'], 'license': lic,
                    'pushed_at': d['pushed_at'][:10], 'created_at': d['created_at'][:10],
                    'language': d.get('language'), 'archived': d.get('archived'),
                    'description': d.get('description'), 'in_ledger': r in names})
    except Exception as e:
        print(f'{tag} {r}  ERR {e}')
    time.sleep(1.2)

json.dump(out, open('research/daily/2026-10-21-webfinds.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('\nsaved', len(out))
