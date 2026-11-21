import json
from pathlib import Path

p = Path('research/daily/seen-repos.json')
d = json.loads(p.read_text(encoding='utf-8'))
r = d['repos']['KyaniteLabs/kinocut']
r['stars'] = 273
r['verified'] = '2026-11-21'
r['note'] = ('ON-MACHINE 11-21 (Apache-2.0, v2.0.1, formerly mcp-video): uvx install 35 pkgs/1.27 s, '
             'kino --version 2.0.1, doctor exit 0; 178 CLI commands + 206 MCP tools + Python Client; '
             'trim 6 s 1.15 s, resize 1.14 s, normalize -16.30 -> -14.51 LUFS TP -1.50 dBTP; '
             'release-checkpoint gate 47.1/36.9/66.6/69.4 at min-score 80 (real defects: letterbox, dark card, '
             'desaturation, quiet audio) and writes thumbnail.jpg + 6-frame storyboard; '
             'PITFALL resize -a 9:16 PADS -> crop -w 608 --height 1080 first; otio-export wants timeline_json not video; '
             'ships a first-party Hermes plugin (hermes plugins install kinocut)')
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
print('updated', d['total'], r['stars'], r['verified'])
