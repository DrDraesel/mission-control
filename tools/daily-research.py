
import os
import requests
from urllib.parse import quote_plus
from pathlib import Path

ROOT = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research")
ROOT.mkdir(parents=True, exist_ok=True)

TOPICS = [
    "faceless video generation",
    "motion graphics templates",
    "ai video automation",
    "youtube shorts generator",
    "typography animation",
    "local video generation",
    "open source video editor",
    "instagram reels generator",
    "moviepy video automation",
    "stable diffusion video"
]

def fetch(url, path):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            path.write_text(r.text, encoding="utf-8")
            print("saved", path.name, len(r.text))
        else:
            print("skip", url, r.status_code)
    except Exception as e:
        print("err", url, e)

for t in TOPICS:
    url = f"https://github.com/search?q={quote_plus(t)}&type=repositories"
    path = ROOT / f"{hash(t)%10000}.html"
    fetch(url, path)
