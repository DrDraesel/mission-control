import json, time
import requests
HEADERS = {"User-Agent": "mission-control-research/1.0", "Accept": "application/vnd.github+json"}
REPOS = ["k2-fsa/sherpa-onnx", "modelscope/ClearerVoice-Studio", "resemble-ai/resemble-enhance",
         "jtydhr88/screenwriting-skills", "Shanyin-ai/shanyin-screenwriting-master",
         "lixiaoxiao9888-create/short-drama-factory", "mrpaidsocial/mrpaidsocial-video-editor-agent",
         "afj176/open-cinema-studio", "bkingfilm/lapian-notes", "zenstory-ai/oh-story-dsh",
         "yusharma3501/LavaSR", "facebookresearch/denoiser", "Audio-WestlakeU/FullSubNet", "fgnt/nara_wpe",
         "WenzheLiu-Speech/awesome-speech-enhancement", "santi-pdp/segan", "sp-uhh/sgmse", "vbelz/Speech-enhancement"]
meta = {}
for repo in REPOS:
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            d = r.json()
            rec = {"stars": d.get("stargazers_count"), "license": (d.get("license") or {}).get("spdx_id"),
                   "language": d.get("language"), "created_at": (d.get("created_at") or "")[:10],
                   "pushed_at": (d.get("pushed_at") or "")[:10], "archived": d.get("archived"),
                   "description": (d.get("description") or "")[:200], "topics": d.get("topics", []),
                   "homepage": d.get("homepage")}
            meta[repo] = rec
            print(f"OK {repo}: {rec['stars']}* lic={rec['license']} lang={rec['language']} created={rec['created_at']} pushed={rec['pushed_at']} archived={rec['archived']}")
            print(f"    {rec['description'][:150]}")
        else:
            print(f"HTTP {r.status_code} {repo}")
    except Exception as e:
        print("err", repo, e)
    time.sleep(1)

print("\n--- releases ---")
for repo in ["k2-fsa/sherpa-onnx", "resemble-ai/resemble-enhance", "modelscope/ClearerVoice-Studio"]:
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=HEADERS, timeout=25)
    if r.status_code == 200:
        d = r.json()
        assets = [(a["name"], round(a["size"] / 1048576, 1)) for a in d.get("assets", [])]
        meta.setdefault(repo, {})["latest_release"] = {"tag": d.get("tag_name"), "published": (d.get("published_at") or "")[:10], "assets": [a[0] for a in assets][:12]}
        print(f"{repo}: {d.get('tag_name')} {(d.get('published_at') or '')[:10]} n={len(assets)} {assets[:8]}")
    else:
        print(f"{repo}: HTTP {r.status_code}")
    time.sleep(1)

Path = r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-11-04-repo-meta2.json"
open(Path, "w", encoding="utf-8").write(json.dumps(meta, indent=1, ensure_ascii=False))
print("wrote", Path, len(meta))
