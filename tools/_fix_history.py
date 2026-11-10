import re, pathlib

ref = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references")
main = ref / "query-yield-history.md"
t = main.read_text(encoding="utf-8")
parts = re.split(r"(?m)^(?=- )", t)
header, old_summary = parts[0], parts[1]

archive = ref / "query-yield-archive-2026-10a.md"
archive.write_text(
    "# Query Yield Archive — 2026-10-01 launching summary\n\n"
    "Moved out of query-yield-history.md on 2026-11-10 to keep the live file under the\n"
    "100 KB skill-file limit. Historical only; the live rotation rules are in\n"
    "`query-yield-history.md`.\n\n" + old_summary,
    encoding="utf-8",
)

entry = """
- → **11-10 DONE**: rotation applied — `vfx` + `video-stabilization` retired (mined 11-09) → **`closed-captioning`** and **`render-engine`**, both retired after one run. `render-engine` = **game-engine collision** (opentk 3,547★, PainterEngine 3,330★, SpartanEngine 3,224★, gzdoom 3,124★, UZDoom 2,335★, anki-3d-engine 1,629★, Generals-Mac 1,731★, `reactjs/express-react-views` = a *view* engine) — only **`kane50613/takumi` 3,189★ MIT/Apache** (JSX/HTML/CSS → PNG/PDF/SVG/paint tree, **no browser**, Windows native bindings) and **raea** were real. `closed-captioning` = OBS-captions-plugin 1,349★ GPL-2.0 + netflix-to-srt 868★ MIT, both marginal. Sweep: 37 queries / 427 entries / **13 new from 3 queries; 34 of 37 = 0 new** (8th consecutive proof). **THE FIND: `shinyobjectz/raea` 1,851★ FSL-1.1-ALv2, created 10-18** — React/TS compositions rendered by Rust+Bevy **on the GPU, no browser**; **ON-MACHINE: install.ps1 → 0.1.1-rc1, 90 f 1920×1080@30 in 4.65 s (6.2 ms/frame), `check` = nothing to fix, `--alpha` = RGBA PNG sequence** (17× OpenEdit's 105 ms/frame, ~70× kinetograph); CLI has cut/track/song/splat/gen(+comfy import)/blender/media/check/brand/guide. **Web lane carried again via NEW SOURCE `aifilmhq.com/new`** (dated feed + RSS; also GitHub Trending #2 = astryx 21,717★ +3,278/day): **`voyager-so/vork` 1,344★ (created 11-05) Preview Licence** headless 3D/VFX engine for agents (RTX ray tracing, no resale); **`ismael-joffroy-chandoutis/spritz` 0★ MIT** film-set data model + camera-guide.mp4 from Blender + **FCP7 XML export**; **`hodgemann/mondo-music-video` 15★ Apache** song→beat-cut music video; **`Ltamann/ComfyUI-TBG-RevealLayer` 9★** occlusion-aware image→RGBA layers (SAM3 grounding, needs FLUX.1-dev); **`NickPittas/Keyloom` 2★** Windows/Linux keyer on CorridorKey (engine CC BY-NC-SA + no resale, outputs commercial-OK); `EtienneLescot/shouldercut` 0★ MIT (voice-driven editor, WGSL effects written on the spot); `tencent-hunyuan/Hy-Nomas` 561★ (RTX 4090 low-memory interactive world gen); `Moh4696/cinematic-skill` 84★ MIT created 11-09 (Skia code-drawn documentary/explainer, 90 s worked example). **ComfyUI: v0.44.0 still latest (11-04) vs local 0.25.0 = 19 behind (27th run)**; **WeVisOne-VL (Apache-2.0 2B/4B) entered ComfyUI CORE 11-09** = prompt→boxes/masks/**alpha mattes**/OCR, no SAM; **LTX-Desktop 1.3.1 AlphaGen IC-LoRA** = no-green-screen subject cutout as transparent WebM + matte MP4, and its notes put Windows at **9 GB VRAM + fp8** for smaller settings; every H3 derivative (HyperFlow H3 Flash 14B, Open-H3-Regenerate-2K-IC, Viggle Remake, IV Studio) stays US-banned. **No Higgsfield winner published as of 09:15 ET on the announced day** — hub still the same 3 apps. Releases today: HyperFrames **v0.9.30** (agent-plugin + lambda only), EffectCraft **v0.23.1** (win msi), open-design **v0.27.1** (win setup), FilmCraft v0.19.0 (11-09), Concat v0.2.9. wabcut **0.7.0** (11-06) now ships gyro Warp Stabilizer + local AI effects = the Premiere-rules Windows editor. Momentum: ComfyUI 146,107★, hyperframes 82,066, Concat 16,434, FilmCraft 17,972, EffectCraft 8,622, open-design 106,978, MoneyPrinterTurbo 141,859, astryx 21,717. Ledger 2,003→**2,023 (+20: 13 sweep + 7 web)**. Next rotation (11-11): `music-visualizer` ('music visualization stars:>300') + `design-system` ('design system stars:>1000'); test `raea cut` on a real VO and `raea gen comfy import`; adopt takumi for static social assets; keep ComfyUI update #1.
"""

new_main = header + "".join(parts[2:]).rstrip("\n") + "\n" + entry
main.write_text(new_main, encoding="utf-8")
print("archive:", len(archive.read_text(encoding='utf-8')), "chars")
print("main:", len(new_main), "chars")
