"""Final 10-15 checks: morphable full assets + Wan2GP license file."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}

r = requests.get("https://api.github.com/repos/beziointeractive/morphable-desktop/releases/latest", headers=HEADERS, timeout=20)
if r.status_code == 200:
    d = r.json()
    names = [a["name"] for a in d.get("assets", [])]
    print("MORPHABLE assets:")
    for n in names:
        print("  ", n)

for branch in ("main", "master"):
    for fn in ("LICENSE", "LICENSE.md", "LICENSE.txt", "license"):
        u = f"https://raw.githubusercontent.com/deepbeepmeep/Wan2GP/{branch}/{fn}"
        rr = requests.get(u, timeout=20)
        if rr.status_code == 200:
            print(f"\nWan2GP license file found: {branch}/{fn}")
            print(rr.text[:800])
            raise SystemExit
print("\nWan2GP: no standalone license file found on main/master")
