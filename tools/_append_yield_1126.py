from pathlib import Path

p = Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-history.md")
arc = p.with_name("query-yield-archive-2026-10a.md")
txt = p.read_text(encoding="utf-8")

entry = (
    "\n- \u2192 **11-26 DONE**: rotation applied per the 11-25 plan \u2014 `product-video-topic` + `kinetic-typography-topic` out \u2192 "
    "**`topic:after-effects`** + **`topic:screen-recording`** in. Sweep 40 queries / 474 rows / **17 raw-new / 6 usable**; "
    "**457 of 474 already ledgered (19th proof)**. `topic:after-effects` = 892 repos, 8 raw-new: usable = **`Tencent/libpag` 5,825* "
    "Apache-2.0** (the AE \u2192 PAG runtime: PAGExporter AE plugin + PAGViewer, Windows/macOS, plays on Android/iOS/Win/Linux/Web \u2014 "
    "**adjacent infra, NO render-to-MP4 CLI**) and `Dakkshin/after-effects-mcp` 933* MIT (MCP driving a real AE install); the rest are "
    "Lottie players (lottie-react 969*, Lottie-Windows 724*, compottie 700*) + Duik 411* GPL (AE rigging) \u2192 **park (mined)**. "
    "`topic:screen-recording` = 1,189 repos, 9 raw-new, **0 Windows-usable** (Dayflow 7,498* Swift, Capso 1,555*, capcap 1,127*, "
    "scrawl 965* all macOS; **`screenpipe` 22,553* = Screenpipe Commercial License, source-available, NOT open source**) \u2192 **park after one run**. "
    "**THE FIND came from the curated index, not the sweep**: `ZanePoe` index grew 109 \u2192 165 entries and surfaced **`Remocn/remocn` 1,924* MIT** = "
    "\u201cshadcn for video\u201d \u2014 a **940-item shadcn registry of Remotion components** + Claude Code/Codex plugin + agent skill + **keyless hosted MCP**. "
    "ON MACHINE: `initialize` 0.49 s / `tools/list` 0.44 s (4 tools), `search_components` **0.61 s**, `get_component` 0.46 s, "
    "`plan_video` **0.58 s / 15,562 chars** (6-beat storyboard + ranked picks); real render **128 f 1280\u00d7720@30 H.264 765,482 B in 6.6 s** "
    "with frames inspected. **Pitfalls: Remotion does not honour tsconfig paths (`@/` alias needs a webpack override); `ComSpec` unset in cron bash "
    "\u2192 `npm install` dies `spawn C:\\WINDOWS\\system32\\cmd.exe ENOENT`; npm 11 blocks esbuild postinstall.** "
    "Web lane: **`fastvideo-project/dreamverse-harness` 115* MIT** (agent filmmaking on a FastVideo/FastH3 backend \u2014 4 GPUs or 2\u00d7>80 GB, H3 US ban \u2192 watchlist), "
    "`imputnet/cobalt` 47,296* AGPL backfill (**yt-dlp was already ledgered 11-24, 210,380*** \u2014 check before calling a gap), `omnimux-ai/omnimux-client` 110* AGPL (13 days old, Win+mac). "
    "Video-gen: **MAGI-2 flagship announced 11-24 (480B) but weights NOT released** (`SandAI-org/MAGI-2` 404s; Preview 114B needs 8\u00d7Hopper/307 GB); "
    "**HyperFlow H3 Flash GGUF Q4 9.1 GB fits data-wise but inherits the H3 US-excluded licence**; ComfyUI upstream **v0.46.0 vs local 0.25.0 = 21 behind (40th run)**; "
    "aifilmhq static at 11-16 (10 days); HyperFrames **v0.9.99 today**. Ledger 2,297\u2192**2,317 (+20: 17 sweep + Remocn + DreamVerse + cobalt)**. "
    "Next (11-27): park both topics; keep `fresh-month-movers` (2nd run found `omnimux`) + `fresh-ltx`; add **`topic:remotion`** and **`topic:lottie`**. "
    "**Wire Remocn's MCP into the agent + keep its craft rules as the review checklist.**\n"
)

if "11-26 DONE" in txt:
    print("entry already present")
else:
    txt = txt + entry

lines = txt.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("- \u2192 ")]
while len("\n".join(lines)) > 99000 and len(idx) > 1:
    i = idx[0]
    moved = lines.pop(i)
    idx = [j - 1 for j in idx[1:]]
    with arc.open("a", encoding="utf-8") as f:
        f.write(moved + "\n")
    if i < len(lines) and lines[i].strip() == "":
        lines.pop(i)
        idx = [j - 1 if j > i else j for j in idx]

txt = "\n".join(lines)
p.write_text(txt, encoding="utf-8")
print("final chars", len(txt), "| archived entries:", len(arc.read_text(encoding="utf-8").split("\n- \u2192 ")))
