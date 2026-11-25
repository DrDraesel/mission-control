"""Append the 11-25 yield entry; archive the 10-19..10-23 blocks to stay under 100k chars."""
import re
from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-history.md")
arc = p.with_name("query-yield-archive-2026-10a.md")
txt = p.read_text(encoding="utf-8")

ENTRY = (
    "\n- \u2192 **11-25 DONE**: rotation applied per the 11-24 plan \u2014 b-roll-topic + motion-design-topic + "
    "explainer-video-topic **out** \u2192 **`topic:product-video`** + **`topic:kinetic-typography`** in, and the FRESH slot "
    "replaced by a plain movers window **`video created:>2026-10-25 stars:>30`**. "
    "Sweep **40 queries / 474 rows / 17 raw-new (6 usable)**; **457 of 474 already ledgered (18th proof)**; 37 of 40 queries = 0 new. "
    "Per-query: `product-video-topic` **8 new** (head 100% ledgered \u2014 video-shotcraft 22,550*, openmotion 16,221*, herk-edit-kit 3,153*, guizang 975*, ai-promo-video-maker 500*; "
    "tail = skill packs: promo-creator-skills 124* MIT, product-film 37* MIT, SallyRS/video-director 31* MIT, atlas-marketing-studio 55* **no licence**) \u2192 **PARK**; "
    "`kinetic-typography-topic` **4 new** (real one = **`arla6ka/design.how` 634* MIT** = 9 agent skills incl. make-motion/make-font/make-logo/design-system-boss, `npx skills@latest add https://design.how`; "
    "silkreel 52* Apache = .kicad_pcb \u2192 12 s launch film; jit-motion 39* MIT = one-file HTML promo animation; vocaloid-style-mv-pipeline 300* MIT; persian-motion-director 153* NOASSERTION) \u2192 **PARK**; "
    "**`fresh-month-movers` 5 new and it found the day's biggest new repo** \u2014 **`haziqahmedqasmi/PeakCut` 1,932* MIT** (created 11-14: long video **or live stream** \u2192 captioned 9:16; rolling-buffer live clipping on loudness+chat+transcript; per-creator workspaces; YT/IG/TT posting; "
    "AI = any OpenAI-compatible/Gemini/Claude/Ollama **and a keyless loudness mode**; Win = py3.10+ + ffmpeg + `python -m studio.server` :8765, 480 MB Whisper on first run, **install to C:\\peakcut** (260-char path limit)), "
    "plus 3,070* lastbook (off-mandate), a Bilibili-UI extension, and **two junk-wave twins created 11-23** (offline-file-converter-windows 1,061*, ffmpeg-video-audio-converter 1,024* \u2014 do not download) \u2192 **KEEP the instrument**. "
    "**THE FIND came from the curated index + web lane, not the sweep: `Hao0321/Editkin` 339* + `Hao0321/video-autopilot-kit` 2,361* MIT** = a free Windows NLE with a **local MCP server** (editable timeline + shared EditGraph + structured commands; v0.31.0 today, "
    "`Editkin_0.31.0_windows_x64-setup.exe` 1,430.3 MB) paired with an MIT agent controller (evidence receipts \u2192 edit-plan/v4 \u2192 audit \u2192 atomic apply \u2192 render \u2192 delivery QA). "
    "**Licence split matters: repo source frozen at 0.15.0-preview under GPL-3.0-or-later, 0.16.0+ is free CLOSED-source freeware (commercial use allowed forever per EULA) \u2014 free to use, not forkable.** "
    "Also web-verified: **`frankShan001/CutVoke` 51* MIT** (MCP-native editor, v0.3.6 preview `CutVoke-0.3.6-windows-x64-portable.zip` 431.7 MB + SHA256SUMS, bundled engine, 408 commits/30 d), "
    "**`kleZ799/clipmint` 71* MIT = ledgered 10-04 never evaluated** (`ClipMint.exe` 229.6 MB HEAD 200 / 527 dl, zero-setup local OpusClip), `MemeCalculate/moyin-creator` 4,879* AGPL (Seedance 2.0 = **paid cloud**), "
    "narrator-ai-cli-skill 3,324* MIT (dormant 07-05), comfyui-vrgamedevgirl 905* NOASSERTION, Linnea 118* MIT, GTA-Auto-Clipper 193* MIT. "
    "**ON MACHINE (2)**: (a) **`broll-mcp` REAL archive.org run** \u2014 initialize 2.93 s, `search_footage{brief:'empty gym treadmill running workout b-roll', filters:{max_tier:2, license:'commercial_ok'}}` \u2192 **6.19 s, 312 upstream matches \u2192 100 ranked \u2192 5 returned** with tier/licenceurl/commercial_use/shotlist-`why`/cursor; "
    "**strict schema**: an extra `limit` field was rejected in 1 ms with `INVALID_INPUT` naming the field (no silent no-op); **caveat: tier-1 PD is archival** (1951 'Survival Under Atomic Attack', 1958 'American Look') \u2014 use tier 3 or own footage for modern b-roll; "
    "(b) **`video-autopilot-kit` bootstrap**: `install_or_upgrade.py --check` \u2192 exit 0 JSON `{\"status\":\"BOOTSTRAP_AVAILABLE\",\"latest\":\"0.28.1\",\"asset\":...}`. "
    "**ComfyUI upstream v0.46.0 (11-18) vs local 0.25.0 = 21 behind (39th run)**; aifilmhq feed static at 11-16 (**9 days**); no new open-weights model. "
    "Releases: **HyperFrames v0.9.94 today** (89,929*, agent-plugin + lambda + arm64 OCI only), **autoclip v1.6.1 today** (15,944*, cli-mcp zip 20.6 MB + Win setup 198.8 MB). "
    "Momentum: Concat 20,125*, OpenMontage 83,250*, video-shotcraft 22,550*, openmotion 16,221*, kinocut 281*. Ledger 2,273\u2192**2,297 (+24: 15 sweep + 9 web)**. "
    "Next (11-26): park product-video + kinetic-typography; keep fresh-month-movers + fresh-ltx + manim-ecology; add **`topic:after-effects`** (AE-replacement lane \u2014 Lumit-class `.jsx` runners are invisible to phrase probes) and **`topic:screen-recording`**; "
    "run ClipMint and PeakCut on the same 20-min recording before choosing a clipper; install Editkin only if the closed-source EULA is acceptable."
)

# split into blocks on entry starts
parts = re.split(r"(?m)^(?=- \u2192 )", txt)
header = parts[0]
blocks = parts[1:]
print("header", len(header), "blocks", len(blocks))

arch_dates = ("10-19", "10-20", "10-21", "10-22", "10-23")
moved = [b for b in blocks if re.match(r"- \u2192 \*\*(10-19|10-20|10-21|10-22|10-23)", b)]
kept = [b for b in blocks if b not in moved]
print("moving", len(moved), "chars", sum(len(b) for b in moved), "kept chars", sum(len(b) for b in kept))

arc_txt = arc.read_text(encoding="utf-8") if arc.exists() else "# Query Yield Archive \u2014 2026-10a\n\nOldest entries moved out of query-yield-history.md when it approached the 100,000-char limit.\n\n"
if not arc_txt.endswith("\n\n"):
    arc_txt = arc_txt.rstrip("\n") + "\n\n"
arc.write_text(arc_txt + "".join(moved), encoding="utf-8")

new = header + ENTRY + "\n" + "".join(kept)
p.write_text(new, encoding="utf-8")
print("history chars:", len(new), "archive chars:", len(arc.read_text(encoding='utf-8')))
