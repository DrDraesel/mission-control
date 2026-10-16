"""Probe PyPI/npm for today's candidate packages (installability check)."""
import json
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0"}

pypi_names = ["manimgx", "kinocut", "showtime", "moviepy"]
for n in pypi_names:
    try:
        r = requests.get(f"https://pypi.org/pypi/{n}/json", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()["info"]
            print(f"PyPI {n}: v{d['version']} | {d.get('license') or d.get('license_expression') or '?'} | {d.get('summary','')[:80]}")
        else:
            print(f"PyPI {n}: HTTP {r.status_code}")
    except Exception as e:
        print("PyPI err", n, e)

npm_names = ["manimgx", "rivemcp", "openfilm", "@hyperframes/runtime"]
for n in npm_names:
    try:
        r = requests.get(f"https://registry.npmjs.org/{n.replace('/', '%2F')}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            latest = d.get("dist-tags", {}).get("latest")
            print(f"npm {n}: v{latest} | license={d.get('license')} | repo={((d.get('repository') or {}).get('url'))}")
        else:
            print(f"npm {n}: HTTP {r.status_code}")
    except Exception as e:
        print("npm err", n, e)

# motion-script repo retry (case variant + direct page check)
for repo in ["Motion-Script/motion-script", "motion-script/motion-script"]:
    r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
    print(f"GH {repo}: HTTP {r.status_code}")
