"""Daily GitHub research for mission-control.
Queries GitHub search API for open-source tools in graphics/video/faceless-content/3D/web categories.
Saves raw JSON + filtered candidates to research/daily/<date>-github.json
Rate-limit safe: unauthenticated search API allows 10 req/min -> sleep 7s between calls.

Robustness (2026-10-12): retries transient network errors (10054 connection resets) and
5xx, saves incrementally after every query, and RESUMES from a partial file instead of
restarting the whole sweep (a mid-run crash previously lost all fetched queries).
"""
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

ROOT = Path(r"C:\Users\GAMEPOWER\projects\mission-control")
OUT_DIR = ROOT / "research" / "daily"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()

HEADERS = {
    "User-Agent": "mission-control-research/1.0",
    "Accept": "application/vnd.github+json",
}

# (slug, github search query)
# ROTATION 2026-10-16 (applied per 10-15 plan): retired viral-clone (0 new on
# 2nd of 2 runs); replaced fresh-motion (stale x2) with a fresh window on
# 'faceless youtube automation' (new vocabulary for the faceless lane).
# compositing/bg-removal revisit due ~10-17.
# ROTATION 2026-10-14 (applied per 10-13 plan): rephrased adobe-alt
# ("premiere alternative" -> "after effects alternative") to test the AE-side
# copycat vocabulary from the ArtCraft wave; ADDED viral-clone lane
# ('viral video clone') to catch hypit-class tools the fresh-agents window
# missed on 10-13. (adobe-alt retired 10-15; viral-clone retired 10-16.)
# ROTATION 2026-10-12 (applied per 10-11 plan): retired fresh-editors (two runs,
# junk wave only) -> replaced with manim-ecology ('manim stars:>50
# pushed:>2026-07-01') to ride the manimgx/showtime explainer-engine momentum.
# Kept fresh-agents (HIGH first run 10-11).
# ROTATION 2026-10-11 (applied per 10-10 plan): tightened video-diffusion-model
# with stars:>500 pushed:>2026-06-01 (it was pulling 2023-era research repos);
# retired fresh-clips (sparse 2 runs) -> replaced with fresh-agents window
# ('video agent' created) to catch the hot agent-harness lane early.
# ROTATION 2026-10-10: added background-removal (weekly revisit, last 10-03) and
# fresh-editors window ('video editor' fresh — new OSS editors are rare + valuable).
# ROTATION 2026-10-09 (applied per 10-08 plan): retired
# fresh-sd-video + fresh-3d-web (both dead windows, total=1); revived
# social-publishing topic ("social media publishing" — GitHub queries missed
# Postiz/Mixpost/OpenPost/trypost that web found); rephrased sd-video ->
# video-diffusion-model ("video diffusion model") since sd-video top-12 were
# all <=2025; kept video-editing-model. Earlier retirements: fresh-faceless,
# fresh-agent-video (10-07), caption-subtitle, streaming-avatar,
# lip-sync-avatar, fresh-avatar + fresh-digital-human (10-04/10-05),
# lottie/svg + ai-dubbing (10-04), compositing, background-removal,
# explainer-video, video-effects (10-03), blender-addons, photo-enhancement,
# design-tokens, video-compression, screen-recording, 2d-animation,
# webgl, video-hosting (10-01/10-02 runs).
TOPIC_QUERIES = [
    ("hyperframes-eco", "hyperframes"),
    ("agent-video-editing", "claude code video editing"),
    ("ai-video-editing-agent", "ai video editing agent"),
    ("video-editing-model", "video editing model"),
    ("faceless-video-gen", "faceless video generator"),
    ("video-diffusion-model", "video diffusion model stars:>500 pushed:>2026-06-01"),
    ("ai-video-marketing", "ai video marketing"),
    ("motion-graphics", "motion graphics"),
    ("video-automation", "video automation"),
    ("typography-animation", "typography animation"),
    ("video-editor-oss", "open source video editor"),
    ("short-drama", "ai short drama"),
    ("moviepy", "moviepy"),
    ("reels-automation", "instagram reels automation"),
    ("3d-web-design", "3d web design"),
    ("local-video-gen", "local video generation"),
    ("clip-factory", "video clip generator"),
    ("digital-human", "digital human avatar"),
    ("social-publishing", "social media publishing"),
    ("background-removal", "background removal"),
]

# freshness: brand-new projects getting traction (rotated windows)
FRESH_QUERIES = [
    ("fresh-video-gen", 'video generation created:>2026-09-01 stars:>15'),
    ("fresh-faceless-yt", 'faceless youtube automation created:>2026-08-25 stars:>10'),
    ("fresh-agents", 'video agent created:>2026-08-25 stars:>10'),
    ("manim-ecology", 'manim stars:>50 pushed:>2026-09-01'),
]


def gh_search(q: str, per_page: int = 12) -> dict:
    url = "https://api.github.com/search/repositories"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": per_page}
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            wait = 15 * (attempt + 1)
            print(f"  network error on '{q}': {e}; waiting {wait}s...", flush=True)
            time.sleep(wait)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (403, 429, 500, 502, 503, 504):
            wait = 30 * (attempt + 1)
            print(f"  HTTP {r.status_code} on '{q}', waiting {wait}s...", flush=True)
            time.sleep(wait)
            continue
        print(f"  HTTP {r.status_code} for '{q}': {r.text[:200]}", flush=True)
        return {}
    print(f"  giving up on '{q}' after retries", flush=True)
    return {}


def slim(item: dict) -> dict:
    return {
        "full_name": item.get("full_name"),
        "url": item.get("html_url"),
        "description": (item.get("description") or "")[:300],
        "stars": item.get("stargazers_count"),
        "language": item.get("language"),
        "created_at": (item.get("created_at") or "")[:10],
        "pushed_at": (item.get("pushed_at") or "")[:10],
        "license": (item.get("license") or {}).get("spdx_id"),
        "topics": item.get("topics", []),
        "archived": item.get("archived", False),
        "forks": item.get("forks_count"),
    }


def main() -> None:
    out = OUT_DIR / f"{TODAY}-github.json"
    results = {"date": TODAY, "fetched_at": datetime.now(timezone.utc).isoformat(), "queries": {}}
    if out.exists():
        try:
            prev = json.loads(out.read_text(encoding="utf-8"))
            if prev.get("date") == TODAY:
                results["queries"] = prev.get("queries", {})
                print(f"resuming: {len(results['queries'])} queries already fetched", flush=True)
        except Exception as e:
            print(f"could not resume from partial file: {e}", flush=True)
    all_queries = TOPIC_QUERIES + FRESH_QUERIES
    fetched_any = False
    for i, (slug, q) in enumerate(all_queries):
        if results["queries"].get(slug, {}).get("count") is not None:
            print(f"[{i+1}/{len(all_queries)}] {slug}: already fetched, skipping", flush=True)
            continue
        if fetched_any:
            time.sleep(7)
        print(f"[{i+1}/{len(all_queries)}] {slug}: {q}", flush=True)
        data = gh_search(q)
        items = [slim(it) for it in data.get("items", [])]
        results["queries"][slug] = {"query": q, "count": data.get("total_count"), "items": items}
        fetched_any = True
        for it in items[:5]:
            print(f"   * {it['full_name']} ({it['stars']}*) - {(it['description'] or '')[:80]}", flush=True)
        out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"   -> saved ({len(items)} items)", flush=True)
    total = sum(len(v["items"]) for v in results["queries"].values())
    missing = [s for s, _ in all_queries if results["queries"].get(s, {}).get("count") is None]
    if missing:
        print(f"\nNOTE: {len(missing)} queries incomplete: {missing} — rerun to fill", flush=True)
    print(f"\nSaved {total} repo entries to {out}")


if __name__ == "__main__":
    main()
