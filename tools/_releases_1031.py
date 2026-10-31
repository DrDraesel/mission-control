"""Check /releases/latest for key pipeline repos: tag, published, asset names+sizes.
Core API (60/hr). Prints one block per repo.
"""
import sys
import time

import requests

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "mission-control-research"}
REPOS = [
    "heygen-com/hyperframes",
    "jub0t/concat",
    "storytold/effectcraft",
    "storytold/filmcraft",
    "tangency-labs/solidcraft",
    "Lightricks/LTX-Desktop",
    "D3voz/openjutsu",
    "Comfy-Org/ComfyUI",
    "open-pencil/open-pencil",
    "0xShug0/audio.cpp",
]


def main() -> None:
    for r in REPOS:
        try:
            resp = requests.get(f"https://api.github.com/repos/{r}/releases/latest",
                                headers=HEADERS, timeout=25, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            print(f"{r}: net {e}")
            continue
        if resp.status_code != 200:
            print(f"{r}: HTTP {resp.status_code}")
            time.sleep(1)
            continue
        d = resp.json()
        assets = [(a["name"], round(a["size"] / 1e6, 1)) for a in d.get("assets", [])]
        win = [a for a in assets if "win" in a[0].lower() or a[0].endswith(".exe") or a[0].endswith(".msi")]
        print(f"{r}: {d['tag_name']} published {d['published_at'][:10]} assets={len(assets)}")
        for n, s in (win or assets)[:6]:
            print(f"    {n}  {s} MB")
        time.sleep(1)


if __name__ == "__main__":
    main()
