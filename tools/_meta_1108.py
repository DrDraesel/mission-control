import json, time, urllib.request

HEAD = {'User-Agent': 'mission-control-research', 'Accept': 'application/vnd.github+json'}

def get(url):
    req = urllib.request.Request(url, headers=HEAD)
    return json.load(urllib.request.urlopen(req, timeout=25))

REPOS = [
    'SubtitleEdit/SubtitleEdit',
    'gyroflow/gyroflow',
    'heyheyalpha/hyperframes',
    'jub0t/Concat',
    'storytold/filmcraft',
    'storytold/effectcraft',
    'Comfy-Org/ComfyUI',
    '0xS4N4TG/kinetograph',
    'veedstudio/open-edit',
    'maskin25/captions.js',
    'CloudAI-X/threejs-skills',
]

out = {}
for full in REPOS:
    rec = {}
    try:
        j = get('https://api.github.com/repos/' + full)
        rec['stars'] = j.get('stargazers_count')
        rec['pushed_at'] = (j.get('pushed_at') or '')[:10]
        rec['license'] = (j.get('license') or {}).get('spdx_id')
    except Exception as e:
        rec['repo_error'] = str(e)[:100]
    try:
        rel = get('https://api.github.com/repos/%s/releases/latest' % full)
        rec['release'] = rel.get('tag_name')
        rec['released'] = (rel.get('published_at') or '')[:10]
        assets = rel.get('assets') or []
        rec['assets'] = [(a.get('name'), round((a.get('size') or 0) / 1048576, 1)) for a in assets][:14]
    except Exception as e:
        rec['release_error'] = str(e)[:80]
    out[full] = rec
    print(full, json.dumps(rec, ensure_ascii=False)[:900], flush=True)
    time.sleep(1.0)

json.dump(out, open('research/daily/2026-11-08-repo-meta.json', 'w'), indent=1, ensure_ascii=False)
print('saved')
