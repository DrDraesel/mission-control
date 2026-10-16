"""HEAD-check that today's key Windows release assets are actually downloadable."""
import requests

HEADERS = {"User-Agent": "mission-control-research/1.0"}
URLS = {
    "LTX-Desktop win setup exe": "https://github.com/Lightricks/LTX-Desktop/releases/download/v1.2.7/LTX-Desktop-Setup.exe",
    "TiXL win exe (4.2.1)": "https://github.com/tixl3d/tixl/releases/download/v4.2.1/Tixl-v4.2.1.exe",
    "Astrofox win setup exe (2.0.0)": "https://github.com/astrofox-io/astrofox/releases/download/v2.0.0/Astrofox-windows-x64-setup.exe",
    "Rhubarb win zip (1.14.0)": "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip",
}
for name, url in URLS.items():
    try:
        r = requests.head(url, headers=HEADERS, timeout=30, allow_redirects=True)
        size = r.headers.get("Content-Length")
        print(f"{name}: HTTP {r.status_code} size={round(int(size)/1e6,1) if size else '?'}MB")
    except Exception as e:
        print(f"{name}: ERR {e}")
