"""Preview (not final): list raw repos not in the ledger, sorted by stars, with spam filter.
Run anytime, even mid-sweep, to see what's coming. Does not write anything.
"""
import json
from pathlib import Path

RAW = Path("research/daily/2026-10-31-github.json")
SEEN = Path("research/daily/seen-repos.json")

SPAM = (
    "setup-guide", "-win-guide", "workflow-guide", "download-free", "crack",
    "jailbreak", "tutorial-download", "installer-guide", "free-download",
    "sonyvegas", "movavi", "filmora", "avid-media", "slideshow-video-maker",
    "shotcut-download", "render-in", "womble", "solveigmm", "gom-player",
    "hitfilm", "whiteboard", "hiring-without", "ziwei", "jailbreaks",
)

def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    repos = json.loads(SEEN.read_text(encoding="utf-8"))["repos"]
    seen = set(repos)
    hits = {}
    for slug, q in raw.get("queries", {}).items():
        for it in q.get("items", []):
            fn = it.get("full_name")
            if not fn or fn in seen:
                continue
            low = fn.lower()
            if any(s in low for s in SPAM):
                continue
            if it.get("language") is None:
                continue
            prev = hits.get(fn)
            if prev is None or (it.get("stars") or 0) > (prev.get("stars") or 0):
                it = dict(it)
                it["query"] = slug
                hits[fn] = it
    order = sorted(hits.values(), key=lambda x: -(x.get("stars") or 0))
    print(f"{len(order)} tentative NEW (ledger {len(repos)}); {len(raw.get('queries', {}))} queries fetched")
    for it in order:
        print(f"{it['stars']:>7}* {it.get('license')} {it['created_at']} {it['full_name']} [{it['query']}]")
        print(f"          {(it.get('description') or '')[:110]}")

if __name__ == "__main__":
    main()
