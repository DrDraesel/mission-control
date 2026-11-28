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
# ROTATION 2026-10-23 (applied per 10-22 plan): canva-alt RETIRED — 'canva
# alternative stars:>100' returned only 5 results (too narrow to be a lane);
# replaced by brand-kit ('brand kit generator') to probe the brand-asset lane
# (logos/palettes/brand systems → social templates). Kept ai-video-editor-movers
# (proved a pattern: >200* tier is macOS-native/stale/SDK, not a lane, but the
# movers filter keeps it cheap).
# ROTATION 2026-10-22 (applied per 10-21 plan): topic lane saturated (26 of 27
# queries returned 0 new on 10-21), so both additions are category-name /
# movers-only probes rather than more vocabulary: ADDED canva-alt
# ('canva alternative stars:>100' — design category name, the figma-alt query
# was the only yielder on 10-21) and ai-video-editor-movers ('ai video editor
# stars:>200' — restrict a noisy lane to actual movers). Keep everything else.
# ROTATION 2026-10-18 (applied per 10-17 plan): moviepy REPHRASED -> 'moviepy
# automation' (query flat since 10-05, but the moviepy lane is in the cron
# mandate — try automation vocab before retiring); ADDED code-rendered-film
# ('agent film skill') to chase the lemo-opuscar/anidoodle lane that was
# invisible to all 25 queries on 10-17 (probe 10-18: total=147, 8 fresh
# agent-film skills incl. motionmaxxing 857*, procedural-film 512*).
# Kept capcut-alt. kandinsky-s2v = 3rd recheck due (done manually in report).
# ROTATION 2026-10-17 (applied per 10-16 plan): fresh-faceless-yt retired
# ('faceless youtube automation' = total=0 dead phrasing x2) -> ADDED
# capcut-alt ('capcut alternative'); compositing revisited (last 10-03) on the
# Concat/OpenCut CapCut-replacement wave; background-removal already in the pool.
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
    ("ai-video-marketing", "ai video marketing"),
    ("motion-graphics", "motion graphics"),
    ("video-automation", "video automation"),
    ("typography-animation", "typography animation"),
    ("video-editor-oss", "open source video editor"),
    ("short-drama", "ai short drama"),
    ("programmatic-video", "programmatic video"),
    ("code-rendered-film", "agent film skill"),
    # figma-alt retired 11-19 (see rotation note at the tts-voice/webgl-3d block)

    ("ugc-video", "ai ugc video"),
    ("reels-automation", "instagram reels automation"),
    ("3d-web-design", "3d web design"),
    ("local-video-gen", "local video generation"),
    ("clip-factory", "video clip generator"),
    ("digital-human", "digital human avatar"),
    ("social-publishing", "social media publishing"),
    ("capcut-alt", "capcut alternative"),
    # 10-30 rotation: 7 mapped/mined probes out -> star-floored category NAMES + tail bands in
    ("lottie-motion", "lottie stars:>500"),
    ("blender-addons", "blender addon stars:>300"),
    ("mocap", "motion capture stars:>500"),
    ("music-generation", "music generation stars:>500"),
    ("screen-capture", "screen capture stars:>1000"),
    ("social-scheduler", "social media scheduler stars:>1000"),
    ("photo-editor", "photo editor stars:>2000"),
    # 10-31 rotation: retire voice-cloning (0/30) + image-editor-tail (tail = pure noise)
    ("vector-graphics", "vector graphics stars:>1000 pushed:>2026-06-01"),
    # 11-02 rotation: retire storyboard/color-grading/font-editor (all mined 11-01);
    # the alpha/matte lane is the live edge and `video compositor` is the unambiguous
    # spelling of the 10-31 Wayland collision
    ("matting", "matting stars:>200"),
    # 11-04 rotation: retire rotoscoping (3 results, both stale/unclear);
    # add two adjacent craft names for the VO-cleanup + scripting halves of the pipeline
    # 11-07: audio-editor retired here (mined 11-03/11-04/11-06, 9 new on debut then flat)
    # 11-05 rotation: retire speech-enhance + screenwriting (both mined in one run 11-04);
    # audio-editor kept one more run. Two fresh craft names with star floors.
    # 11-06: keyframe-animation = iOS Obj-C name collision -> retired after one run.
    #       speech-to-text kept (only 10 of 50 mined). New craft name: image upscaling
    #       (Real-ESRGAN/upscayl/chaiNNer cluster = the 4K delivery step, never probed).
    # 11-07 rotation: audio-editor retired (mined 11-03/11-04/11-06); the 11-06 pitfall
    # says famous tools hide from phrase probes -> probe the CATEGORY at a star floor:
    # Kdenlive/Shotcut/Pitivi/Flowblade-class NLEs were never verified as a category.
    ("speech-to-text", "speech to text stars:>2000"),
    # 11-08 rotation: `video-editor-giants` (14 total, top-12 all ledgered) parked — the
    # GitHub-visible NLE tier is fully mapped. Two unprobed craft names, both unambiguous
    # to a Linux dev (unlike `compositor`/`keyframe animation`) and both pipeline steps
    # the ledger has never covered as a category: the subtitle editor (SRT/ASS/karaoke
    # work happens nowhere in the ledger) and video stabilization (the camera-footage
    # cleanup step for the RunTrack/Bertec vision lane).
    # 11-09 rotation: `subtitle-editor` retired (5 results total, fully mined 11-08);
    # replaced with the VFX/compositing craft name — the ledger's compositing tier is
    # thin (Natron/EffectCraft only) and no query has ever named the craft. `vfx` is
    # unambiguous to a Linux dev (Nuke/Fusion/Natron vocabulary, unlike `compositor`).
    # 11-10 rotation: `vfx` = 54 total / 9 new, but ALL infrastructure (ASWF libs +
    # renderers) -> mined; `video-stabilization` = 0 new on 2nd run -> mined.
    # Two fresh craft names with star floors: caption INTERCHANGE (the sibling of the
    # subtitle-editor lane — parsers/renderers, not GUI editors) and the render-engine
    # tier (Filament/bgfx/OSPRay/Embree class, never probed).
    # 11-11 rotation: BOTH retired after one run. `render-engine` = game-engine collision
    # (opentk/PainterEngine/SpartanEngine/gzdoom/UZDoom/anki-3d + a React *view* engine) —
    # only takumi + raea were real, and both came from elsewhere too. `closed-captioning`
    # = 2 marginal hits (OBS live captions, a subtitle format converter).
    # New: music visualization (audio-reactive visuals, the faceless-music half) and the
    # design-system category (shadcn/Radix/Mantine class = the web/social asset layer).
    # 11-12 rotation: BOTH retired after one run, plus `image-upscaling` (0 new twice).
    #   `music visualization stars:>300` = 27 total / 11 new but the output is desktop
    #   PLAYERS (SPlayer, BetterLyrics WinUI, MusicDNA, Rainmeter) - only projectM,
    #   musializer and wave.js are render-side. `design system stars:>1000` = name
    #   collision with "system design" (9 of 12 were interview-prep/infra repos); the two
    #   real hits (google-labs-code/design.md 28.8k*, awesome-design-md 126k*) were still
    #   worth the slot because the real vocabulary is invisible under the collision.
    # New three are CERTAIN gaps (checked against the ledger first, all absent):
    # TripoSR/TRELLIS/Hunyuan3D-2 (image->3D), Depth-Anything V1/V2 + MoGe class
    # (depth estimation = the 3D-insert/relight step), abi/screenshot-to-code
    # (design->code, the inverse of our render path).
    ("image-to-3d", "image to 3d stars:>300"),
    ("depth-estimation", "depth estimation stars:>500"),
    # 11-13 rotation: `screenshot-to-code` = 7 total / 7 new, fully mined in one
    # run (abi 81k*, emilwallner 16.5k*, ScreenCoder, codeimage, agent-vision-toolkit...).
    # Two craft names checked against the ledger first: SAM 2 / segment-anything /
    # rembg / BiRefNet / U2-Net are ALL absent (the matting probe covered matting
    # models, never segmentation), and nerfstudio / gsplat / Brush are absent too
    # (only LichtFeld-Studio and supersplat are ledgered).
    # 11-16 rotation: BOTH new probes paid — `image-segmentation` 49 total / 11 new
    # (ultralytics 63.5k*, BiRefNet 4.4k* MIT, Mask2Former, UNet family, albumentations)
    # and `gaussian-splatting` 141 total / 10 new (graphdeco 24.5k*, awesome-3DGS 9k*,
    # nerfstudio/gsplat 5.9k* Apache, sparkjsdev/spark 3.9k* MIT = three.js splat renderer).
    # 11-17: tighten segmentation with a pushed floor to drop the 2017-19 research tier,
    # and add the SAM-family phrase probe — `image segmentation` sorted by stars hides
    # SAM 2 / SAM 3 / FastSAM / MobileSAM behind bigger general-purpose repos.
    ("image-segmentation", "image segmentation stars:>1000 pushed:>2026-01-01"),
    ("gaussian-splatting", "gaussian splatting stars:>300"),
    # 11-17 rotation: `segment-anything` = 12 of 12 new on debut (the whole SAM family:
    # 55.1k* SAM, 20.2k* SAM2, 12.3k* SAM3, 17.8k* Grounded-SAM, FastSAM, samurai, Track-Anything,
    # MedSAM, sam-hq, sam-audio) -> fully mined in one run, retire.
    # REPLACED BY `screen-studio`: the demo-video lane is 27 repos under that TOPIC and
    # ~46k* across Recordly/OpenScreen/capptivo/agent-screenplay - the 10-27 probe
    # ('screen recorder demo video') failed on vocabulary, not on the lane. Topic names
    # are the correct query form for a software CATEGORY.
    # 11-19 rotation: `screen-studio` retired after one run — its head (Recordly/OpenScreen/
    # capptivo/agent-screenplay) was already ledgered and its NEW tail was exporters for the
    # paid macOS Screen Studio. `figma-alt` retired too (phrase probe, flat since 10-21; the
    # design lane is covered by design.md/astryx/takumi/penpot/graphite).
    # New probes, both ledger-checked first: TTS is the VOICE half of the faceless pipeline
    # (whisper/faster-whisper/piper/kokoro absent or thin; F5-TTS/GPT-SoVITS/ChatTTS/IndexTTS
    # never probed) and topic:webgl is the correct category form for the 3D-WEB lane
    # (react-three-fiber, model-viewer, fabric.js, deck.gl, d3 all absent from the ledger).
    # 11-20 rotation: `tts-voice` and `webgl-3d` PARKED — both returned 0 new on
    # debut because their top-12 was already 100% ledgered (coverage confirmed, not a
    # dead lane). Per the 11-19 lesson, the sweep adds TOPIC forms with a known head,
    # never more star-floored phrase vocabulary:
    #   topic:design-tools = PAID on debut (12 real gaps, 41,968* -> 1,940*: plasmic,
    #   VisBug, style-dictionary, @shadcn/lint, pattern-craft, animockup, typeui...)
    #   topic:faceless = 7 new / 0 usable (1 licence-crack spam, 1 dormant API wrapper,
    #   1 unlicensed influencer pipeline, 4 off-topic) -> STAGED OUT 11-21 for
    #   `topic:video-editing`, the sibling category form with a head the ledger knows.
    # 11-22 rotation: `design-tools` out (mined 11-20: 12 real gaps in one run);
    # `topic:content-repurposing` in — the sibling category form for the
    # long-form → clips lane (OpusClip/autoclip vocabulary), where the ledger's
    # known heads are autoclip 12.6k* and shortsflow-class tools.
    # 11-23 rotation (per 11-22 plan): keep `content-repurposing-topic` one more run
    # (head real: autoclip 13.2k, article2media 533*); `video-editing-topic` retired
    # after 2nd run = 0 new (mined) -> replaced by topic:motion-design, the
    # motion-graphics CATEGORY form where the ledger's head is thin;
    # `ai-clip-generator-topic` parked (6 raw-new / 0 usable, installer impersonation)
    # -> replaced by topic:explainer-video (video-automation sibling).
    # 11-24 rotation (per 11-23 plan): `content-repurposing-topic` out (0 new on 2nd
    # run) -> `topic:b-roll` (DEBUT: 59 repos, 11 raw-new, 3 usable — broll-mcp,
    # motion-director, b-roll-finder; mined in one pass).
    # 11-25 rotation (per 11-24 plan): b-roll + motion-design (0 new 2nd run) +
    # explainer-video (0 new 2nd run) all OUT. Two direct-mandate TOPIC forms in:
    #   topic:product-video  = AI video marketing (head video-shotcraft 22,394*)
    #   topic:kinetic-typography = typography animation (203 repos, video-talkcraft 2,516*)
    # 11-26 rotation (per 11-25 plan): product-video + kinetic-typography parked
    # after their 11-25 debut (each 0 new usable on 2nd look; heads fully ledgered).
    # Two direct-mandate TOPIC forms in:
    #   topic:after-effects = the AE-replacement lane (Lumit-class tools that run
    #     .jsx scripts are invisible to phrase probes)
    #   topic:screen-recording = demo-video category form (OpenScreen/Recordly
    #     ledgered; the tail is not)
    # 11-27 rotation (per 11-26 plan): both parked — after-effects = 892 repos but its
    #   head is Lottie PLAYERS + Duik/after-effects-mcp bridges (mined); screen-recording
    #   = 1,189 repos, 0 Windows-usable (all macOS/Swift). Two ecosystem TOPIC forms in
    #   per the Remocn finding (the Remotion component registry is a category with a head):
    #   topic:remotion = the code-video ecosystem (remotion-dev, players, templates,
    #     component registries — the lane Remocn sits in)
    #   topic:lottie = the runtime side of AE-authored motion (players/exporters; the
    #     gap after libpag: what plays PAG/Lottie inside video pipelines)
    # 11-28 rotation (per 11-27 plan): both parked after mining — remotion head is fully
    # ledgered, lottie tail is players and the conversion gap was filled by
    # lottie-converter. NOTE: the 11-27 report proposed topic:design-tools, but that was
    # already PAID out on 11-20 (12 gaps), so it is not re-run. Two unprobed category
    # forms in, both direct mandate lanes ("social media assets"):
    #   topic:captions  = the caption/subtitle RENDERER category (only SubtitleEdit +
    #     captions.js in the ledger; karaoke/word-level tools are invisible to phrase probes)
    #   topic:thumbnail = the social-thumbnail generator category (Canva-replacement lane)
    ("captions-topic", "topic:captions"),
    ("thumbnail-topic", "topic:thumbnail"),
    # NEW `medical-imaging`: the segmentation sweep surfaced a whole clinical tier
    # (TotalSegmentator 3.2k*, MedSAM 4.4k*, 3D Slicer 2.7k*, ITK 1.7k*) that no query
    # names - and the user builds clinical/biomechanics apps, so this is a standing lane.
    ("medical-imaging", "medical imaging stars:>500 pushed:>2026-01-01"),
]

# freshness: brand-new projects getting traction (rotated windows)
FRESH_QUERIES = [
    # 11-01: H3/Pika wave is a licence dead end for the US -> re-target LTX vocabulary
    ("fresh-ltx", 'ltx created:>2026-08-01 stars:>5'),
    # 11-22: `fresh-agents` parked (0 new x3 — the phrase matches harnesses, not tools).
    # Replaced with the TOPIC form of the clip-generator category (20-repo head:
    # openshorts/hotclip/reelsaw/shortsflow class, per the 11-19 topic survey).
    # 11-23: ai-clip-generator-topic parked (0 usable) -> topic:explainer-video
    # 11-25: explainer-video parked (0 new on 2nd run) -> a plain "new + already
    # moving" window: repos created in the last month that already cleared 30 stars.
    # Catches the agent-video wave early without needing the right vocabulary.
    ("fresh-month-movers", 'video created:>2026-10-25 stars:>30'),
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
