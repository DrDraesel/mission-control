import re
from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-history.md")
arc = p.with_name("query-yield-archive-2026-10a.md")
txt = p.read_text(encoding="utf-8")

entry = (
    "\n- \u2192 **11-24 DONE**: rotation applied per the 11-23 plan \u2014 `content-repurposing-topic` out \u2192 "
    "**`topic:b-roll`** in; `motion-design-topic` + `explainer-video-topic` kept for run 2. "
    "Sweep 40 queries / 474 rows / **11 raw-new / 3 usable**; **463 of 474 already ledgered (16th proof)**. "
    "`topic:b-roll` = 59 repos, head 373*: usable = **`edigeh/broll-mcp` 55* MIT** (ON MACHINE: uvx 39 pkgs/1.06 s, "
    "ffmpeg 9.0.2 https=True, MCP `initialize` OK + **4 tools** search_footage/inspect_item/extract_clip/get_provenance, "
    "provenance JSON written before the clip), **`sharbelxyz/motion-director` 72* MIT** (10\u201330 s branded films + **266 cutaway/overlay moves**, "
    "NO keys, **names HERMES as a target** via `install.sh --hermes`), `louisedesadeleer/b-roll-finder` 156* MIT (methodology only, code frozen 06-11); "
    "the rest micro-skills. `motion-design-topic` run 2 = **0 new**; `explainer-video-topic` run 2 = **0 new** \u2192 both park. "
    "**THE FIND was a curated-index rename of a ledgered-never-evaluated entry**: `ZanePoe` listed **`OpenMontageInc/OpenMontage`** \u2014 "
    "the 09-25 `calesthio/OpenMontage` entry (61,243*, never read) 301s to it and it is now **82,968* AGPL-3.0** with **13 pipelines** "
    "(clip-factory, localization-dub, podcast-repurpose, talking-head, cinematic \u2026), 7-dimension provider scoring, multi-point pre-delivery self-review, "
    "Remotion composer, documented Windows PowerShell setup. Second curated index recorded: **`zhuyansen/awesome-claude-video-skills` 2,656*** "
    "(532 repos, security-graded, 8 h refresh). Web/curated finds API-verified: **`digitalsamba/claude-code-video-toolkit` 2,742* MIT** "
    "(ON MACHINE: minimal Remotion 4.0.544 composition renders 30 f 640\u00d7360 \u2192 6,038 B in ~4 s, but `examples/hello-world` dies at frame 0 "
    "with **React #130** even from a full checkout; npm 11 blocks postinstall \u2192 `npm approve-scripts`; 269 MB node_modules + Chrome Headless Shell), "
    "**`memoryoffish/film-director-skill-plugin` 127* Apache** (created 11-22: film grammar + Blender white-model previz + Freesound CC0/CC-BY layers + "
    "ComfyUI per shot), **`win4r/video-director` 525* MIT** (check_timeline.py + qa_video.py = plan/render gates), `kaomei/hand-drawn-video-prompts` 329* MIT, "
    "`liyupi/awesome-vibe-coding-websites` 216*, `juntaosun/ComeCut` 626* AGPL (active), `FireRed-OpenStoryline` 3,737* Apache (dormant since 07-31), "
    "`heygen-com/skills` 566* MIT (paid API), `hetpatel-11/Adobe_Premiere_Pro_MCP` 931* MIT (needs Premiere). "
    "**Famous base-model ledger gaps closed (9)**: LTX-Video 11,476* Apache, Wan2.2 18,882* Apache, HunyuanVideo 12,828*, mochi 3,767*, Open-Sora 29,949* (dormant), "
    "CogVideo 13,227*, SadTalker 14,218*, FFmpeg 68,040*, yt-dlp 210,380* Unlicense. "
    "**ComfyUI upstream v0.46.0 (11-18) vs local 0.25.0 = 21 behind (38th run)**; aifilmhq feed static at 11-16 (8 days); no new open-weights model. "
    "Releases today: **autoclip v1.6.0 (15,099*)**, **HyperFrames v0.9.90 (89,318*)**. Ledger 2,245\u2192**2,273 (+29 net: 11 sweep + 18 web/backfill \u2212 1 rename dup)**. "
    "Next (11-25): b-roll/motion-design/explainer topics **out** \u2192 **`topic:product-video`** (head video-shotcraft 22,394*, guizang 971, ai-promo-video-maker 500, "
    "promo-creator-skills 123, motionboard 66) + **`topic:kinetic-typography`** (203 repos: video-talkcraft 2,516*, motion-skills 2,117*, design.how 631*, opus-video-skills 563*); "
    "run `broll-mcp` against archive.org for real; install motion-director into the PROFILE skills dir and verify alpha on one overlay; OpenMontage `make setup` + clip-factory next.\n"
)

if entry.strip() in txt:
    print("entry already present")
else:
    txt = txt + entry

# keep under 100k by moving the oldest '- → ' entries into the archive (top of file first)
lines = txt.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("- \u2192 ")]
while len("\n".join(lines)) > 99000 and len(idx) > 1:
    i = idx[0]
    moved = lines.pop(i)
    idx = [j - 1 for j in idx[1:]]
    with arc.open("a", encoding="utf-8") as f:
        f.write(moved + "\n")
    # drop a following blank line if present
    if i < len(lines) and lines[i].strip() == "":
        lines.pop(i)
        idx = [j - 1 if j > i else j for j in idx]

txt = "\n".join(lines)
p.write_text(txt, encoding="utf-8")
print("final chars", len(txt), "archived entries now", len((arc.read_text(encoding='utf-8')).split('\n- \u2192 ')))
