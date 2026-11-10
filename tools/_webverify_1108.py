import json, time, sys, urllib.request

LED = 'research/daily/seen-repos.json'
d = json.load(open(LED))
led = {k.lower() for k in d['repos']}

CAND = [
    'sorsama/wabcut',
    'pycodebr/heditor',
    'CloudAI-X/threejs-skills',
    'fahmiwol/tyx-lab',
    'fitchmultz/pi-posthorse',
    'SeniorMatt/kinoklip',
    'nexu-io/html-anything',
    'glumbis/effectcraft',
    'isroil01/premation',
    'Mixddux/Natron-FOSS-After-Effects',
    'SubtitleEdit/SubtitleEdit',
    'gyroflow/gyroflow',
    'medhachim/CapRocket',
]

HEAD = {'User-Agent': 'mission-control-research', 'Accept': 'application/vnd.github+json'}
out = []
for full in CAND:
    rec = {'full_name': full, 'in_ledger': full.lower() in led}
    try:
        req = urllib.request.Request('https://api.github.com/repos/' + full, headers=HEAD)
        j = json.load(urllib.request.urlopen(req, timeout=25))
        rec.update({
            'stars': j.get('stargazers_count'),
            'license': (j.get('license') or {}).get('spdx_id'),
            'created_at': (j.get('created_at') or '')[:10],
            'pushed_at': (j.get('pushed_at') or '')[:10],
            'language': j.get('language'),
            'archived': j.get('archived'),
            'fork': j.get('fork'),
            'desc': (j.get('description') or '')[:220],
            'default_branch': j.get('default_branch'),
            'topics': (j.get('topics') or [])[:8],
        })
    except Exception as e:
        rec['error'] = str(e)[:120]
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    time.sleep(1.2)

json.dump(out, open('research/daily/2026-11-08-webverify.json', 'w'), indent=1, ensure_ascii=False)
print('saved', len(out))
