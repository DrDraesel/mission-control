import json, time, urllib.request

HEAD = {'User-Agent': 'mission-control-research', 'Accept': 'application/vnd.github+json'}

def get(url):
    req = urllib.request.Request(url, headers=HEAD)
    return json.load(urllib.request.urlopen(req, timeout=25))

REPOS = ['heygen-com/hyperframes', 'sarpstar/cinecode', 'sorsama/wabcut',
         'Comett1225/AbsentMotion', 'mifi/editly', 'TypesettingTools/Aegisub']
out = {}
for full in REPOS:
    rec = {}
    try:
        j = get('https://api.github.com/repos/' + full)
        rec.update(stars=j.get('stargazers_count'), pushed_at=(j.get('pushed_at') or '')[:10],
                   license=(j.get('license') or {}).get('spdx_id'),
                   created_at=(j.get('created_at') or '')[:10], lang=j.get('language'))
    except Exception as e:
        rec['repo_error'] = str(e)[:90]
    try:
        rel = get('https://api.github.com/repos/%s/releases/latest' % full)
        rec['release'] = rel.get('tag_name'); rec['released'] = (rel.get('published_at') or '')[:10]
        rec['assets'] = [a.get('name') for a in (rel.get('assets') or [])][:10]
    except Exception as e:
        rec['release_error'] = str(e)[:60]
    out[full] = rec
    print(full, json.dumps(rec, ensure_ascii=False)[:700], flush=True)
    time.sleep(1.0)

json.dump(out, open('research/daily/2026-11-08-repo-meta2.json', 'w'), indent=1, ensure_ascii=False)
print('saved')
