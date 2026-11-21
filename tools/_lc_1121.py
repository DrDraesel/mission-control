import json
d = json.load(open('research/daily/seen-repos.json', encoding='utf-8'))
repos = d['repos']
names = ['kajisho5/motion-graphics-skill', 'kyanitelabs/kinocut', 'radityama/motion-studio',
         'sant-0/facelesspro', 'delexw/motion-graphics-agent',
         'jema-software-ltd/faceless-video-pipeline', 'mmagdyelsafty/faceless-video-pipeline',
         'kajisho5/ffmpeg-skill']
for n in names:
    hit = repos.get(n.lower())
    print(('LEDGER ' if hit else 'ABSENT ') + n, (json.dumps(hit)[:260] if hit else ''))
print('keys', list(d.keys()), 'total', d['total'])
extra = d.get('extra') or {}
print('extra count', len(extra))
for n in names:
    if n.lower() in {k.lower() for k in extra}:
        print('EXTRA', n)
