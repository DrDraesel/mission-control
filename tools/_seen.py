"""Merge today's repos into the seen-repos ledger (dedupe key: full_name). Keeps history across runs."""
import json
import sys
from datetime import date
from pathlib import Path

D = Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily")
today = date.today().isoformat()

ledger_path = D / "seen-repos.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"repos": {}}
repos = ledger.get("repos", {})

SPAM = ("dictat", "dictatorship", "cirosantilli", "scaling-octo-guide", "this-analysis-terminated",
        "setup-guide", "win-guide", "workflow-guide", "shotcut-download")
new_names = []
raw_files = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [D / f"{today}-github.json"]
for raw_file in raw_files:
    raw = json.loads(raw_file.read_text(encoding="utf-8"))
    for slug, q in raw["queries"].items():
        for it in q["items"]:
            name = it["full_name"]
            if any(s in name.lower() for s in SPAM):
                continue
            if name not in repos:
                repos[name] = {"stars": it["stars"], "first_seen": today, "queries": [slug]}
                new_names.append(name)
            else:
                repos[name]["stars"] = it["stars"]  # refresh star count
                if slug not in repos[name]["queries"]:
                    repos[name]["queries"].append(slug)

# web-verified repos found outside the API sweep (add manually when needed)
EXTRA = {
    # 2026-10-16 web finds (API-verified; stars @ verify time)
    "playcanvas/supersplat": 10390,       # browser-based 3D Gaussian Splat editor; Editor 3.0 rebuilt on WebGPU (Stochastic Alpha = sort-free rendering at 20M+ Gaussians); free/OSS MIT; WebGL+WebGPU, engine-agnostic; 3D-web lane
    "playcanvas/engine": 17066,           # PlayCanvas web graphics runtime (WebGL/WebGPU/WebXR/glTF); MIT; the engine behind SuperSplat; 3D-web lane
    "FlashML-org/FreeVideo": 1993,        # local MiniMax H3 inference engine (VDN-H3 8-step + hybrid Video DeltaNet attention); claims 8GB VRAM/16GB RAM min; int8 (GeForce/30-series) / FP8 paths; weight streaming + disk offload; ComfyUI plugin + Win/mac/Linux one-click launchers (FreeVideo.exe 98.2MB v0.4.8 10-16 HEAD-verified, SHA256SUMS); agent-drivable since v0.4.0; repo Apache-2.0, VDN weights = custom OpenVDN agreement (flag before commercial use)
    "jub0t/concat": 7278,                 # free cross-platform CapCut replacement: local Whisper captions, TTS + voice cloning, bg-removal, keyframes+curve editor, 100 GPU effects, multi-track, 4K60 10-bit H.264/HEVC/AV1; native Rust + GPU compositor; JSON-RPC API for agents; AGPL-3.0; beta; Win x86_64 setup.exe 84.8MB + msi 102MB v0.2.7 HEAD-verified; mac/Linux/Android/iOS too
    "hao-ai-lab/fastvideo": 4612,         # unified post-training + realtime inference for accelerated video gen; FastH3 V2 on single consumer GPU (5090/4090/Pro6000, DGX Spark, Apple Silicon); FastH3 Trim NVFP4 ~8GB GPU mem (experimental); Win/Linux/Mac; Apache-2.0; pushed 10-16
    "kandinskylab/kandinsky-s2v": 0,      # Kandinsky S2V 1.0 speech-to-video avatars (Lite 2B / Pro 21B; Qwen2.5-Omni conditioning + 3-scale visual memory; pi-Flow distilled 16-step, 5.4x faster; MIT); announced 10-15 (arXiv 2610.19290); HF collection kandinskylab/kandinsky-s2v-10 live; GitHub repo linked by paper 404 as of 10-16 09:xx — RECHECK next run
    "TaoLiveAIGC/TaoMate-H3": 798,        # streaming audio-video runtime on MiniMax H3 (3-step LoRA; T2AV/FL2VA chunked long-form 480p/768p/1080p); validated on 8xH20-96GB — NOT consumer; H3 Community License (territory terms); created 09-05
    "kandinskylab/kvae-audio": 123,       # continuous full-band audio waveform autoencoder (Kandinsky audio codec); MIT
    # 2026-10-15 web finds (API-verified; stars @ verify time)
    "WeftCut/WeftCut": 224,               # MCP-driven desktop NLE (Electron 44 + PixiJS v8 WebGPU + WebCodecs + native ffmpeg sink); localhost MCP server exposes ALL editing tools; checkpoints/dry-run; whisper.cpp/FunASR opt-in local engines; MIT; WeftCut-win-x64.exe 237MB v0.4.0 verified; Win/mac/Linux; pushed daily
    "deepbeepmeep/Wan2GP": 10517,         # 'GPU Poor' one-stop runner: Wan 2.1/2.2, LTX-2/2.3/2.5, MiniMax H3, Hunyuan 1/1.5, Kandinsky, LTXV, KugelAudio (voice-clone TTS claiming >ElevenLabs), Qwen3 TTS, Chatterbox; 6GB min, LTX-2 @ 10GB; LTX-2.5 VFX tools (SDR→HDR LoRA, alpha gen → ProRes 4444, layout-to-render), DLSS 5 neural rendering; Windows one-click .bat + Triton/Sage/GGUF kernels; WanGP Community License 2.0 (free local + outputs sellable w/ credit; no resale/SaaS)
    "kyogreultima/tramme": 0,             # motion design "written as data": JSON document = source of truth, editor+AI share one ops API; deterministic frame=f(t) render; Tauri 2 desktop Win/mac/Linux (unsigned) + hosted app.tramme.dev; CLI offline renders (headless Chrome + ffmpeg); Node≥22.18; Apache-2.0; v0.6.0 tramme-windows-x64-setup.exe 21.3MB verified; created 10-02 (very early)
    "nexu-io/motion-anything": 867,       # nexu.io agentic motion layer: local-first chat-native motion engine (animated pages/launch videos from one sentence; live GPU shader recipes); Apache-2.0; pushed 07-07 (dormant ~3mo)
    "johnnyang0612/bearcarousel": 3,      # IG carousel generator + quality audit gate (WCAG AA contrast, centering, copy density, logo placement) → 1080x1350 PNGs from JSON; pip install bearcarousel; Claude Code plugin; Apache-2.0; BearCarousel.exe 29.9MB verified; stale since 07-23
    "TonyciencIA/claude-carruseles": 5,   # chat→carousel editor: Claude CLI generates HTML/CSS slides → Puppeteer/Sharp PNG at IG dims; Next.js 16; MIT; Win/mac/Linux; stale since 04
    "ucouerbe/instagram-carousel-automation": 1,  # Python batch carousel pipeline + Claude Code skill (@reveur_ai setup); Gemini images; MIT; stale since 04
    "Anil-matcha/open-larryloop": 14,     # open-source larryloop alt: generate + publish viral TikTok/IG carousel slides; MIT; pushed 09-02
    "mbasaglia/glaxnimate": 85,           # original Glaxnimate personal repo (stale 2023) — successor/mirror = KDE/glaxnimate; kept to avoid re-flag
    "beziointeractive/morphable-desktop": 4,  # Morphable Community: GPLv3 motion-design editor (vector animation, text, audio mix, 4K120 export, JSON projects); Win x64/arm64 setup.exe 30.6MB + mac dmg + linux verified; morphable.video; solo dev, v26.1.0 (09-02)
    # 2026-10-14 web finds (API-verified; stars @ verify time)
    "MengTo/threeui": 6612,               # ThreeUI Community: three.js component catalog freemium community edition (50 parent comps, 164 browse results); MIT (app + community comps); React/npm @designcodeio/threeui; 3D-web lane; Pro tier paid
    "AkariLabs/akari-video": 209,         # AI-edits-your-footage editor: Theia desktop shell + 26 agent skills (opencode/Claude Code/Cursor); edit.json file contract; review-and-fix workflow; MIT; Win .exe+portable zip (.akari runtime); "under construction"
    "Comfy-Org/ComfyUI_Nvidia_VFX_Nodes": 675,  # Renamed from Nvidia_RTX_Nodes_ComfyUI: RTX VSR (upscale/denoise/deblur) + TrueHDR + FrameGen (40-series+) ComfyUI nodes; Apache-2.0 wrapper; underlying nvidia-vfx PyPI bindings PROPRIETARY (free); RTX GPU + cu130 pytorch
    "bazodev/open-vids": 34,              # Agent-first desktop editor (chat → real non-destructive timeline; 4 agents: Main/Motion/Audio/Research w/ license tracking); Apache-2.0; Win x64 NSIS unsigned + mac dmg; indie, created 09-28 (very early)
    "naman-sharma12345/kimo": 6,          # MCP-first no-GUI video editor, Rust/C++, "every operation an AI-callable tool" (255-tool claim); MIT; Win setup.exe 12.1MB + portable zip v3.0.0 HEAD-verified; created 10-10 (very early; watchlist)
    "KDE/glaxnimate": 41,                 # vector animation / motion design (Lottie-compatible); KDE project, GitHub mirror of invent.kde.org; v0.6.0 = first KDE stable (2026-03); GPL; Win/mac/Linux (NOT the stale mbasaglia/glaxnimate personal fork)
    # 2026-10-13 web finds (API-verified; stars @ verify time)
    "hypit-ai/hypit": 22161,              # viral-video cloning agent skill (Claude Code/Codex); SVGML word-anchored; modified Apache-2.0 (free self/client use; no multi-tenant SaaS/resale); Node 22+; renders via headless Chromium; models optional
    "storytold/wordcraft": 10243,         # ArtCraft #8: Word clone (docx); MIT/Apache-2.0; Win x64/x86/arm; created 10-07
    "storytold/gridcraft": 4187,          # ArtCraft #9: Excel clone; Apache-2.0; Win; created 10-07
    "storytold/cadcraft": 3877,           # ArtCraft #10: AutoCAD clone (DXF); Apache-2.0; Win; created 10-07
    "storytold/deckcraft": 2792,          # ArtCraft #11: PowerPoint clone; Apache-2.0; Win; created 10-07
    "storytold/soundcraft": 2413,         # ArtCraft #12: Avid Pro Tools clone (DAW); Apache-2.0; Win signed x64/x86/arm; created 10-07
    "storytold/figcraft": 122,            # ArtCraft #13: Figma clone; MIT/Apache-2.0; Win x64/x86/arm; created 10-09
    # 2026-10-12 web finds (kept for history; already merged)
    "storytold/photocraft": 50950,    # ArtCraft: Photoshop clean-room reimplementation in pure Rust; Apache-2.0; Win/mac/Linux + WASM; released 09-30, v0.7.0 (10-11)
    "storytold/lightcraft": 10718,    # ArtCraft: Lightroom-alt (photo library + raw development); Apache-2.0
    "storytold/pdfcraft": 10441,      # ArtCraft: Acrobat-alt (PDF read/organize/protect); Apache-2.0
    "storytold/vectorcraft": 7511,    # ArtCraft: Illustrator-alt (vector illustration); Apache-2.0
    "storytold/designcraft": 3203,    # ArtCraft: InDesign-alt (page layout/publishing); Apache-2.0
    "runesleo/claude-video-kit": 119, # Agent Skill + Remotion pipeline: brief/script -> review receipt -> narrated 9:16 explainer; MIT; v0.3.0-rc.1
    "thearnavrustagi/marketmenow": 137,  # agentic outbound marketing automation across 7 platforms (OpenClaw-compatible); MIT; semi-stale (04-13)
    "oratis/influencex": 15,          # self-hosted KOL marketing automation (creator discovery/outreach/ROI); MIT
    "LuisSotelo/vod-to-viral": 12,    # python VOD->shorts pipeline (ffmpeg, highlight detection); NO license; stale (pushed 06-15)
    # 2026-10-11 web finds (kept for history; already merged)
    "Friedrich-M/UniMate": 1695,          # SIGGRAPH Asia 2026 text-to-animation for ANY rigged skeleton (GLB/glTF/FBX); MIT; brought its own rig_preprocess 10-05
    "PurpleDoubleD/locally-uncensored": 2178,  # all-in-one local AI studio (chat/image/video/code) Win+Linux installer; AGPL-3.0
    "mnm967/qamba-studio-oss": 10,        # local-only AI video studio: plan (40+ agent tools) -> ComfyUI render -> multi-track NLE; AGPL-3.0; Win10+ tested
    "iPythoning/ai-video-studio": 10,     # OpenClaw skill: Seedance 2.0 gen + CapCut Mate/FFmpeg edit; MIT; small
    "OpenX-Inc/flow": 21,                 # autonomous topic->film pipeline on self-hosted Wan 2.2; MIT; needs cloud GPU box; semi-stale (pushed 07-23)
    "abhinavshrivastava950/Montara": 22,  # local-first video engine, editable Timeline IR -> any renderer; AGPL-3.0; zero-key
    "Creatorberry/faceless": 49,          # script -> faceless reel w/ character dialogue (Fish Audio VOX); MIT; small
    "marciogranzotto/lottie-tools": 50,   # Lottie Open Studio: browser Lottie editor (SVG import -> keyframes -> Lottie JSON); MIT; semi-stale
    "ronin1770/reel-quick": 14,           # self-hosted FastAPI+Next.js+FFmpeg reel creator (trim/merge/text/transitions); MIT
    "Jakeschincariol/instagram-agent-skill": 900,  # 13 Claude skills running an IG account (26 hook formulas, viral research, caption linter); MIT
    "baldiga/headless-studio": 11,        # "make me a video" from Claude Desktop; MIT; small
    # 2026-10-10 web finds (kept for history; already merged)
    "opencut-app/opencut-classic": 267,
    "F-R-L/forge-film": 539,
    "pablostanley/yoinks": 5672,
    "opencut-desktop-app/opencut": 0,
    # 2026-10-07 web finds (kept for history; already merged)
    "remotion-dev/skills": 4873,
    "trypostit/trypost": 677,
    "getopenpost/openpost": 653,
    "AstaBlackClove/posthive": 16,
    "pendpost/pendpost": 11,
}
for name, stars in EXTRA.items():
    if name not in repos:
        repos[name] = {"stars": stars, "first_seen": today, "queries": ["web-verified"]}
        new_names.append(name)

out = {"updated": today, "total": len(repos), "repos": repos}
ledger_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"ledger: {len(repos)} total, {len(new_names)} new today")
for n in sorted(new_names, key=lambda x: -(repos[x]['stars'] or 0)):
    print(f"NEW {n} ({repos[n]['stars']}*) {repos[n]['queries'][:3]}")
