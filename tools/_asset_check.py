"""HEAD-check that today's key Windows release assets are actually downloadable."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0"}
URLS = {
    "dub-studio portable win zip": "https://github.com/timoncool/dub-studio/releases/download/v4.0.0/Dub-Studio-4.0.0-portable-windows-x64.zip",
    "dub-studio win setup exe": "https://github.com/timoncool/dub-studio/releases/download/v4.0.0/Dub.Studio_4.0.0_x64-setup.exe",
    "nextgenUp win setup exe": "https://github.com/riponcm/nextgenUp/releases/download/v1.2.0/NextGenUp_1.2.0_x64-setup.exe",
    "SmartSub win exe": "https://github.com/buxuku/SmartSub/releases/download/v3.9.0/SmartSub_Windows_3.9.0_x64.exe",
}
for name, url in URLS.items():
    try:
        r = requests.head(url, headers=HEADERS, timeout=20, allow_redirects=True)
        size = r.headers.get("Content-Length")
        print(f"{name}: HTTP {r.status_code} size={round(int(size)/1e6,1) if size else '?'}MB")
    except Exception as e:
        print(f"{name}: ERR {e}")
