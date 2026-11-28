# Project notes and evidence

Each positioning statement comes from the official README at a pinned commit; not every project was installed and run. Metrics refreshes do not automatically re-audit features or licenses.


## [Concat](https://github.com/jub0t/Concat)

Local-first cross-platform multitrack editor with subtitles, TTS, background removal, keyframes, effects and 4K export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Offline models need a first-run download; in-product AI is not the same scope as full generative workflows.
- Maintenance: Commits within the last 90 days; 479 commits in 30 days, 1616 commits in 90 days.
- License: [AGPL-3.0](https://api.github.com/repos/jub0t/Concat/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/jub0t/Concat/blob/504a814ebe61d4f47bba4cd7949dc2580ecc405c/README.md#L6).

## [Jellyfish](https://github.com/Forget-C/Jellyfish)

AI short-drama production workbench covering script breakdown, storyboards, character and scene asset management, shot generation and export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Asset reuse aids consistency but does not guarantee generation quality; model services, costs and deployment requirements depend on configuration.
- Maintenance: Commits within the last 90 days; 1336 commits in 30 days, 1955 commits in 90 days.
- License: [Apache-2.0](https://github.com/Forget-C/Jellyfish/blob/a9678194ddf2d9be3ccbe78d4287d87d5089e123/LICENSE); Open license verified. Root LICENSE is Apache-2.0; model, media and third-party service terms are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/Forget-C/Jellyfish/blob/a9678194ddf2d9be3ccbe78d4287d87d5089e123/README.md#L30).

## [Clypra](https://github.com/AIEraDev/Clypra)

Rust/Tauri/React hardware-accelerated cross-platform video editor.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Primarily a general-purpose editor; AI feature scope and mobile maturity must be verified per release.
- Maintenance: Commits within the last 90 days; 333 commits in 30 days, 1643 commits in 90 days.
- License: [MIT](https://api.github.com/repos/AIEraDev/Clypra/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/AIEraDev/Clypra/blob/aa6b9c619cf98f7a1dfab6446345ec5f5660b93c/README.md#L9).

## [CozyClay](https://github.com/HaD0Yun/CozyClay)

In-browser scene blocking, character staging, shot cutting and AI video previs tool.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Output is mainly previs and shot references; final generation quality depends on external video models.
- Maintenance: Commits within the last 90 days; 186 commits in 30 days, 2104 commits in 90 days.
- License: [AGPL-3.0](https://api.github.com/repos/HaD0Yun/CozyClay/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/HaD0Yun/CozyClay/blob/297dd2a8a077613b329962d68e2a9bb4355be091/README.md#L6).

## [Editroom](https://github.com/robbietilton/Editroom)

Native Swift video editor for macOS: realtime 4K without proxies, built-in grading, speed ramps, transitions, audio mixing and loudness-target exports, plus natural-language cuts through Claude, ChatGPT or an on-device model.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Needs macOS 14 or later on Apple silicon; Magic's Local option additionally needs Apple Intelligence on macOS 26, and the Claude and ChatGPT options require those apps signed in to your plan. The 7.5 MB size and the no-proxy, no-buffering 4K claims are the README's own and were not installed or measured here; the post's 23 MB figure matches neither the README nor the v1.0.11 DMG, which is 12,238,527 bytes. Claude and ChatGPT edit the currently open project over MCP and Magic edits are undoable, but the upload scope of each mode still needs checking against your footage and privacy requirements.
- Maintenance: Commits within the last 90 days; 457 commits in 30 days, 457 commits in 90 days.
- License: [MIT (app) + bundled FFmpeg LGPL-2.1+, Sparkle MIT](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/LICENSE); Composite/conditional license. Repo root LICENSE is MIT; the app bundles FFmpeg 9.1 under LGPL-2.1+ (no GPL or non-free parts, built from ffmpeg.org sources by scripts/build-ffmpeg.sh and run as a separate program only to rewrap formats macOS cannot open), and Sparkle updates are MIT; redistributing must provide the FFmpeg sources and configure options, which Vendor/ffmpeg/README.md documents.
- Feature verified: 2026-11-27; [Source 1](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/README.md#L5) · [Source 2](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/README.md#L7) · [Source 3](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/README.md#L50) · [Source 4](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/README.md#L59) · [Source 5](https://github.com/robbietilton/Editroom/blob/6390ae7f3847d924126b2d4f7a964b9fee4e71a2/README.md#L87).

## [Huobao Drama](https://github.com/chatfire-AI/huobao-drama)

Web/desktop platform that turns a one-line idea or a pasted novel into rewritten script, images, storyboard videos, voiceover, subtitles and a finished short drama, orchestrated by a Mastra agent backend with UI-editable skills.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Licensed CC BY-NC-SA-4.0, which explicitly forbids commercial use (including paid services, commercial deployment and resale); text, image and video capabilities all need your own model-service API keys, and the README steers users to the author's FireMux keys; referencing local files for Seedance requires a PUBLIC_BASE_URL with a public address, and the desktop version errors out without one; SQLite plus a data directory storage, so migration means copying media files manually.
- Maintenance: Commits within the last 90 days; 18 commits in 30 days, 102 commits in 90 days.
- License: [CC BY-NC-SA-4.0 (no commercial use)](https://github.com/chatfire-AI/huobao-drama/blob/24d4c17612e71cf10c8eeb1a8b6439afa73e2c07/LICENSE); Source-available, not OSI open source. LICENSE is the full CC BY-NC-SA 4.0 text; the README's license section explicitly forbids commercial use, which requires written permission from the author; GitHub licenseInfo therefore reports NOASSERTION; the terms of invoked model services, media and voiceover copyrights are separate
- Feature verified: 2026-11-25; [Source 1](https://github.com/chatfire-AI/huobao-drama/blob/24d4c17612e71cf10c8eeb1a8b6439afa73e2c07/README.md#L33) · [Source 2](https://github.com/chatfire-AI/huobao-drama/blob/24d4c17612e71cf10c8eeb1a8b6439afa73e2c07/README.md#L55) · [Source 3](https://github.com/chatfire-AI/huobao-drama/blob/24d4c17612e71cf10c8eeb1a8b6439afa73e2c07/README.md#L131).

## [OpenChatCut](https://github.com/0xsline/OpenChatCut)

Local-first conversational AI video editor with a multitrack timeline, Agent Skills, MCP and Remotion rendering.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Capabilities of the built-in agent, the desktop app and external coding agents must be verified separately.
- Maintenance: Commits within the last 90 days; 22 commits in 30 days, 379 commits in 90 days.
- License: [AGPL-3.0](https://api.github.com/repos/0xsline/OpenChatCut/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/0xsline/OpenChatCut/blob/9242a95aea248ff3a8dab495514384e858320d47/README.md#L12).

## [OpenDirector](https://github.com/ThinkFlowLab/OpenDirector)

Agent video creation workflow from conversation, canvas and asset organization through timeline export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: First release; full production stability and model costs need hands-on testing.
- Maintenance: Commits within the last 90 days; 349 commits in 30 days, 373 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/ThinkFlowLab/OpenDirector/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/ThinkFlowLab/OpenDirector/blob/39288dfdf4f816798e5479c53363258fceeb6e11/README.md#L18).

## [AID Studio](https://github.com/shijue-aid/aid-studio)

Self-hostable AI workbench for comic dramas, short dramas and film/TV creation covering scripts, characters and scenes, storyboards, image and video generation, voiceover, infinite canvas and 3D previs.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Model calls, storage and compute may cost extra; official example image/audio/video asset packs ship separately per release; deployment needs MySQL, Redis, Docker and other dependencies, and rights for generated content, scripts, characters and assets must be verified by the user.
- Maintenance: Commits within the last 90 days; 46 commits in 30 days, 114 commits in 90 days.
- License: [MIT](https://github.com/shijue-aid/aid-studio/blob/9b78452d047b577d31d301c8998287139c93a312/LICENSE); Open license verified. Repo-root LICENSE is MIT, with NOTICE retaining attribution such as RuoYi-Vue; official example asset packs ship separately, and model-provider, storage and compute terms are separate
- Feature verified: 2026-11-23; [Source 1](https://github.com/shijue-aid/aid-studio/blob/9b78452d047b577d31d301c8998287139c93a312/README.md#L13) · [Source 2](https://github.com/shijue-aid/aid-studio/blob/9b78452d047b577d31d301c8998287139c93a312/README.md#L43) · [Source 3](https://github.com/shijue-aid/aid-studio/blob/9b78452d047b577d31d301c8998287139c93a312/README.md#L46).

## [CutVoke](https://github.com/frankShan001/CutVoke)

Local-first cross-platform open-source video editor with a built-in MCP server, letting agents such as Claude Code, Codex and Cursor edit alongside humans on one non-destructive multitrack timeline.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: The desktop bundle ships third-party components with their own licenses such as FFmpeg (GPLv3); subtitles use optional local faster-whisper, and models need a first-run download; connected agents are mostly cloud services, so accounts, fees and data policies are separate; v0.3.6 is a frozen preview not synced with main, and the README lists known issues such as export-window reuse, preview timeouts and cropping of long subtitles in vertical video; the macOS build is ad-hoc signed but not notarized; the project was created in 2026-09 and maturity is low.
- Maintenance: Commits within the last 90 days; 415 commits in 30 days, 557 commits in 90 days.
- License: [MIT](https://github.com/frankShan001/CutVoke/blob/a4920ad493c6317774141a9bccbd55eafe439b7c/LICENSE); Open license verified. Repo-root LICENSE is MIT; the desktop bundle ships third-party components with their own licenses such as FFmpeg (GPLv3), and community effect recipes, the faster-whisper model and the terms of connected AI services are counted separately
- Feature verified: 2026-11-25; [Source 1](https://github.com/frankShan001/CutVoke/blob/a4920ad493c6317774141a9bccbd55eafe439b7c/README.md#L28) · [Source 2](https://github.com/frankShan001/CutVoke/blob/a4920ad493c6317774141a9bccbd55eafe439b7c/README.md#L121) · [Source 3](https://github.com/frankShan001/CutVoke/blob/a4920ad493c6317774141a9bccbd55eafe439b7c/README.md#L159).

## [OpenReel Video](https://github.com/Augani/openreel-video)

Open-source timeline editor for browser and desktop with cutting, subtitles, mixing and watermark-free export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: General editing capabilities; not automatically a generative AI agent.
- Maintenance: Commits within the last 90 days; 10 commits in 30 days, 16 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Augani/openreel-video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Augani/openreel-video/blob/367d7e90b61b5181f9861b852bb8b9d7a7d2954a/README.md#L7).

## [AI Video Production Editor](https://github.com/LudwigKienle/ai-video-production-editor)

Local workbench covering script, directing, storyboarding and shot generation through editing, grading and export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: BYOK still sends requests to the configured model services; some hosted/billed features require external projects.
- Maintenance: Commits within the last 90 days; 7 commits in 30 days, 144 commits in 90 days.
- License: [GPL-3.0](https://api.github.com/repos/LudwigKienle/ai-video-production-editor/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/LudwigKienle/ai-video-production-editor/blob/a368af45b6cfd35e22bd3b5e101db198e1ac89a9/README.md#L4).

## [MakeMyClip Editor](https://github.com/MakeMyClip/editor)

Wraps FFmpeg editing in a local browser timeline, CLI, MCP and Skill.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Local editing does not require its cloud API; the browser UI, CLI and agent tools are different entry points of one project.
- Maintenance: Commits within the last 90 days; 145 commits in 30 days, 153 commits in 90 days.
- License: [MIT](https://api.github.com/repos/MakeMyClip/editor/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/MakeMyClip/editor/blob/f6f05206c1d2234d74134da27d322caebb260e6d/README.md#L7).

## [OpenKatana](https://github.com/rk0neki/OpenKatana)

Agent-driven studio, CLI, MCP and ComfyUI video editing engine.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: More of a code-driven editing engine; actual generation models and ComfyUI apps need separate setup.
- Maintenance: Commits within the last 90 days; 61 commits in 30 days, 126 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/rk0neki/OpenKatana/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/rk0neki/OpenKatana/blob/b9282bf0740a7df5b5a8862b5e289ef4cd642641/README.md#L7).

## [OpenScene](https://github.com/Theorvane/OpenScene)

Local desktop video editor that lets AI agents operate the timeline, generate media and export.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Default branch is a development branch; mobile and generation capabilities must be verified against the current implementation.
- Maintenance: Commits within the last 90 days; 47 commits in 30 days, 112 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Theorvane/OpenScene/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Theorvane/OpenScene/blob/4bd3d3c4c15fb27dd0b521065643b3a2d516be08/README.md#L8).

## [ScriptCut](https://github.com/FernandoAbishai/ScriptCut)

Edit the transcript to cut locally, package shorts and export for social media.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Focused on text-based rough cuts, not a full VFX and generative workbench.
- Maintenance: Commits within the last 90 days; 4 commits in 30 days, 66 commits in 90 days.
- License: [AGPL-3.0](https://api.github.com/repos/FernandoAbishai/ScriptCut/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/FernandoAbishai/ScriptCut/blob/12c6fe495939da344e6af3e942a45dfdfb2132fa/README.md#L7).

## [Waoowaoo](https://github.com/waooAI/waoowaoo)

AI image and video creation workbench that manages reference media, generates content and merges clips via a canvas and an Assistant.

- Category: Video editors and production workbenches; Restricted license.
- Scope boundary: Currently a beta; image and video capabilities depend on the models; calls to external models such as OpenRouter may cost money.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 6 commits in 90 days.
- License: [Elastic License 2.0](https://github.com/waooAI/waoowaoo/blob/dfec20e32298ed675050329e4a41477024148399/LICENSE); Source-available, not OSI open source. ELv2 since v0.5.0-beta.1, forbidding hosted provision of the main functionality to third parties without permission; not an OSI open-source license, and older versions may differ.
- Feature verified: 2026-11-20; [Source 1](https://github.com/waooAI/waoowaoo/blob/dfec20e32298ed675050329e4a41477024148399/README_zh.md#L24).

## [SeeCut](https://github.com/YeJe-cpu/SeeCut)

Skill workspace where a coding agent understands, cuts, renders and visually QA-checks talking-head shorts.

- Category: Video editors and production workbenches; Restricted license.
- Scope boundary: It is a Skill/workflow, not a standalone desktop NLE; CapCut drafts are only optional follow-up fine-tuning.
- Maintenance: Commits within the last 90 days; 1 commits in 30 days, 11 commits in 90 days.
- License: [PolyForm Noncommercial-1.0.0](https://github.com/YeJe-cpu/SeeCut/blob/b05d7ed27404a064060e0d370402f562b0c0c02e/LICENSE); Source-available, not OSI open source. Non-commercial use only; not an OSI open-source license
- Feature verified: 2026-11-12; [Source 1](https://github.com/YeJe-cpu/SeeCut/blob/b05d7ed27404a064060e0d370402f562b0c0c02e/README.md#L5).

## [Cutline](https://github.com/Aepzie/cutline)

Browser timeline editor with a first-class MCP interface for live agent operation.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Proxy files for large media and the browser encoding path still need evaluation per deployment setup.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 109 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Aepzie/cutline/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Aepzie/cutline/blob/ab71520285881d8dfa78f5ebca00f8a166e84962/README.md#L8).

## [Moyin Creator](https://github.com/MemeCalculate/moyin-creator)

Electron desktop tool for AI film/TV production that chains a five-stage pipeline — script → characters → scenes → directing → Seedance 2.0 — to batch-produce short dramas and anime series.

- Category: Video editors and production workbenches; Core candidate.
- Scope boundary: Requires your own AI provider API keys (multi-provider scheduling and key rotation supported); generation is billed by the provider; dual-licensed AGPL-3.0 + commercial, so closed-source modifications, commercial-product integration or SaaS require a commercial license; character consistency relies on a character bible and reference images, and cross-shot consistency and final quality depend on the model used; the default branch has seen README-only changes since 2026-08-27, the latest release tag is a sponsor-labeled custom build, and the README's netdisk package version differs from Releases.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [AGPL-3.0 + commercial dual license](https://github.com/MemeCalculate/moyin-creator/blob/7e5c5655de94d49885e13c369f0a71212893a0aa/COMMERCIAL_LICENSE.md); Composite/conditional license. LICENSE is the AGPL-3.0 text; README and COMMERCIAL_LICENSE.md declare dual licensing: closed-source modifications, integration into commercial products, or SaaS without open-sourcing require a commercial license; internal use of dependencies such as `@opencut/ai-core` and model-service terms are separate
- Feature verified: 2026-11-25; [Source 1](https://github.com/MemeCalculate/moyin-creator/blob/7e5c5655de94d49885e13c369f0a71212893a0aa/README.md#L70) · [Source 2](https://github.com/MemeCalculate/moyin-creator/blob/7e5c5655de94d49885e13c369f0a71212893a0aa/README.md#L105) · [Source 3](https://github.com/MemeCalculate/moyin-creator/blob/7e5c5655de94d49885e13c369f0a71212893a0aa/README.md#L122).

## [Hypit](https://github.com/hypit-ai/hypit)

Lets coding agents clone reference videos into editable, repeatable full workflows and batch-generate content variants.

- Category: Agent video production and automation; Restricted license.
- Scope boundary: Cloning popular videos involves the source video, people, music, assets and brand permissions; generation models and APIs are optional external services whose costs and data paths follow each provider.
- Maintenance: Commits within the last 90 days; 15 commits in 30 days, 662 commits in 90 days.
- License: [Hypit Open Source License (modified Apache-2.0)](https://github.com/hypit-ai/hypit/blob/6bacce093695ccc2bde5aa5d7de230e9682ffa79/LICENSE); Source-available, not OSI open source. Restricts multi-tenant hosting, commercial redistribution and removal of branding/copyright notices; those uses require a commercial license, so it is not standard Apache-2.0
- Feature verified: 2026-11-13; [Source 1](https://github.com/hypit-ai/hypit/blob/6bacce093695ccc2bde5aa5d7de230e9682ffa79/README.md#L51) · [Source 2](https://github.com/hypit-ai/hypit/blob/6bacce093695ccc2bde5aa5d7de230e9682ffa79/README.md#L164) · [Source 3](https://github.com/hypit-ai/hypit/blob/6bacce093695ccc2bde5aa5d7de230e9682ffa79/README.md#L338).

## [OpenMotion](https://github.com/nexu-io/openmotion)

Reference-video cloning and branded motion workbench for local coding agents, with Motion.md, a visual timeline and MP4 export.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Reference videos, people, music, brands and assets need separate clearance; media generation relies on your own APIs/subscriptions, and built-in templates and third-party components follow their own LICENSE/NOTICE.
- Maintenance: Commits within the last 90 days; 852 commits in 30 days, 857 commits in 90 days.
- License: [Apache-2.0](https://github.com/nexu-io/openmotion/blob/fcbaa2b0296167b0f14f47aa6c414f5bdd41316f/LICENSE); Open license verified. Repo-root LICENSE is standard Apache-2.0; built-in templates, model icons and vendored components carry their own LICENSE/NOTICE, which must be retained and verified when redistributing or reusing
- Feature verified: 2026-11-17; [Source 1](https://github.com/nexu-io/openmotion/blob/fcbaa2b0296167b0f14f47aa6c414f5bdd41316f/README.md#L40) · [Source 2](https://github.com/nexu-io/openmotion/blob/fcbaa2b0296167b0f14f47aa6c414f5bdd41316f/README.md#L308) · [Source 3](https://github.com/nexu-io/openmotion/blob/fcbaa2b0296167b0f14f47aa6c414f5bdd41316f/README.md#L386).

## [OpenMontage](https://github.com/OpenMontageInc/OpenMontage)

Multi-pipeline video production system for coding agents covering research, scripts, assets, voiceover, subtitles and rendering.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Some generation and speech providers are paid services; a large skill file count does not mean all pipelines were tested end to end.
- Maintenance: Commits within the last 90 days; 143 commits in 30 days, 267 commits in 90 days.
- License: [AGPL-3.0](https://api.github.com/repos/OpenMontageInc/OpenMontage/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/OpenMontageInc/OpenMontage/blob/fecb9a1e3cc23ef84de30b272059457a427f16f8/README.md#L14).

## [OpenFilm](https://github.com/openfilm/openfilm)

Lets coding agents create, inspect, edit and render videos in code, with an editable interface.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Code-driven shots differ from traditional footage timelines; asset and sound-library licenses must be verified per asset.
- Maintenance: Commits within the last 90 days; 115 commits in 30 days, 307 commits in 90 days.
- License: [MIT](https://api.github.com/repos/openfilm/openfilm/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/openfilm/openfilm/blob/f59cd4e0973feaf6917dcf3229b178b6baf9ad3f/README.md#L7).

## [Rea Video](https://github.com/JuneYaooo/rea-video)

Reverse-analyzes a video's live, AI and code components and outputs a shot-level replication plan and VIDEO.md.

- Category: Agent video production and automation; Adjacent infrastructure.
- Scope boundary: Mainly analysis and replication planning, not a final editor or generator.
- Maintenance: Commits within the last 90 days; 222 commits in 30 days, 222 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/JuneYaooo/rea-video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/JuneYaooo/rea-video/blob/4111ad9adb4936d92f6d57657000b414fee9f01f/README.md#L8).

## [Video Autopilot Kit](https://github.com/Hao0321/video-autopilot-kit)

Automation framework for video planning, auditing, review and learning from results.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Actual editing and rendering depend on Editkin; installing this repo alone cannot finish a video.
- Maintenance: Commits within the last 90 days; 9 commits in 30 days, 33 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Hao0321/video-autopilot-kit/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Hao0321/video-autopilot-kit/blob/b48c7d9a624ebceaa3a99f3f4aad6006e2be53fb/README.md#L1).

## [Video Director](https://github.com/win4r/video-director)

Guides Claude Code to plan, render and check short films with HTML/Canvas/SVG/Three.js/GSAP/Remotion.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Tuned mainly for specific Claude models; quality on other agents is not inherited automatically.
- Maintenance: Commits within the last 90 days; 14 commits in 30 days, 20 commits in 90 days.
- License: [MIT](https://api.github.com/repos/win4r/video-director/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/win4r/video-director/blob/02d1912ab251bf5235b45e8e7aad81b4bc786b15/README.md#L11).

## [Video Use](https://github.com/browser-use/video-use)

Editing, subtitles, grading, motion overlays and output checks on raw footage via a coding agent plus FFmpeg.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: Not a browser-automation video tool; exact dependencies and cloud paths follow project configuration.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 2 commits in 90 days.
- License: [MIT](https://github.com/browser-use/video-use/blob/43cfc566833548093455c9d4a46bd69913b7e552/LICENSE); Open license verified. Root LICENSE is MIT; model services, media and external dependency licenses are separate.
- Feature verified: 2026-11-21; [Source 1](https://github.com/browser-use/video-use/blob/43cfc566833548093455c9d4a46bd69913b7e552/README.md#L7).

## [WeVisCut](https://github.com/Tencent/WeVisCut)

Turns knowledge articles or narration scripts into multi-minute videos through planning, media retrieval, editing, checking and repair.

- Category: Agent video production and automation; Core candidate.
- Scope boundary: The 9B policy model, tool runtime and Studio must be deployed per the official environment; author results are not a cross-project ranking.
- Maintenance: Commits within the last 90 days; 2 commits in 30 days, 27 commits in 90 days.
- License: [Apache-2.0](https://github.com/Tencent/WeVisCut/blob/94dc8a7fe43a5e0da21e97d5aaf470a39329db3a/LICENSE); Open license verified. Root LICENSE states code, parameters and public weights are Apache-2.0; third-party components are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Tencent/WeVisCut/blob/94dc8a7fe43a5e0da21e97d5aaf470a39329db3a/README.md#L7).

## [NeonClipping](https://github.com/iamajmeena/neonclipping)

Paste a link to cut long YouTube/Twitch/Kick videos or your own MP4s locally into 9:16 clips with burned-in subtitles, titles and hooks.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Clipping depends on yt-dlp, Streamlink, faster-whisper, FFmpeg and an optional local Ollama model; media without YouTube captions needs local transcription or imported captions, with quality degradation; the README's speed claims and 187 checks are author self-tests, not an independent benchmark; downloading and redistribution are bound by platform terms and media rights.
- Maintenance: Commits within the last 90 days; 89 commits in 30 days, 89 commits in 90 days.
- License: [MIT](https://github.com/iamajmeena/neonclipping/blob/052500437bc8d44ed5c8311e8ce686373e098086/LICENSE); Open license verified. Repo-root LICENSE is MIT; requirements pull yt-dlp, faster-whisper, Streamlink, av, static-ffmpeg and other dependencies, and Ollama-pulled model weights and system fonts carry their own licenses
- Feature verified: 2026-11-23; [Source 1](https://github.com/iamajmeena/neonclipping/blob/052500437bc8d44ed5c8311e8ce686373e098086/README.md#L5) · [Source 2](https://github.com/iamajmeena/neonclipping/blob/052500437bc8d44ed5c8311e8ce686373e098086/README.md#L45) · [Source 3](https://github.com/iamajmeena/neonclipping/blob/052500437bc8d44ed5c8311e8ce686373e098086/README.md#L114).

## [Clipmint](https://github.com/kleZ799/clipmint)

Turns podcasts, interviews, tutorials and VODs into subtitled vertical Shorts/Reels/TikToks.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Highlight detection, cropping and upload depend on local models and platform configuration.
- Maintenance: Commits within the last 90 days; 185 commits in 30 days, 615 commits in 90 days.
- License: [MIT](https://api.github.com/repos/kleZ799/clipmint/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/kleZ799/clipmint/blob/f2f7ed16871a390d0fd5274fb28b157f22ac57e3/README.md#L7).

## [ChrisHKAI Video](https://github.com/ChrisHKAI/ChrisHKAI-Video)

Coding-agent Skill organizing a creator's public materials into 3D toy-style short films.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Full-film quality on Codex is unverified; use of public materials and portrait consent are the user's responsibility.
- Maintenance: Commits within the last 90 days; 159 commits in 30 days, 208 commits in 90 days.
- License: [MIT](https://api.github.com/repos/ChrisHKAI/ChrisHKAI-Video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/ChrisHKAI/ChrisHKAI-Video/blob/15b66ee613e621f82ba781d27547a67e76c55f50/README.md#L7).

## [Lanshu AI Presenter Video](https://github.com/cclank/lanshu-create-ai-presenter-video)

Agent Skill turning a topic or script into a verified digital-human/stylized explainer video.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Digital human, voice, lip sync and recognition are decided by external providers chosen at runtime.
- Maintenance: Commits within the last 90 days; 1 commits in 30 days, 17 commits in 90 days.
- License: [MIT](https://api.github.com/repos/cclank/lanshu-create-ai-presenter-video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/cclank/lanshu-create-ai-presenter-video/blob/762d3ee42623b75a4ec63ad6aa61ace69d78ce6e/README.md#L23).

## [Claude Animated Shorts](https://github.com/mromidev/claude-animated-shorts)

Skill for vertical animated story shorts made with Three.js, Remotion, score and sound effects.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: A method pack based on one finished sample; topical and visual generalization needs testing.
- Maintenance: Commits within the last 90 days; 2 commits in 30 days, 2 commits in 90 days.
- License: [MIT](https://api.github.com/repos/mromidev/claude-animated-shorts/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/mromidev/claude-animated-shorts/blob/e3b817b6afc6cd413466d43f11ba31209e034bbf/README.md#L5).

## [Vibe Knowledge](https://github.com/andyhuo520/vibe-knowledge)

Knowledge-short Skill from fact-checking and script writing, voiceover and code-to-video to QA and release packages.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Enhanced shots may call external generation platforms; baseline code illustrations and the enhanced tier should be compared separately.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 3 commits in 90 days.
- License: [MIT](https://api.github.com/repos/andyhuo520/vibe-knowledge/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/andyhuo520/vibe-knowledge/blob/c3a13a85f7cc560e5d396f063baecea4b2748e1e/README.md#L5).

## [Vox Director](https://github.com/alisa0808/vox-director)

End-to-end agent Skill from topic to Vox-style paper-collage explainer/ad videos.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Asset generation depends on Atlas Cloud and FFmpeg; style imitation needs brand and copyright care.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 1 commits in 90 days.
- License: [MIT](https://api.github.com/repos/alisa0808/vox-director/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/alisa0808/vox-director/blob/6a85a7c341610442a6a5b1885e6e0217ab82a11f/README.md#L5).

## [Video to Shorts Skill](https://github.com/social-media-skills/video-to-shorts-skill)

Lets an agent turn long videos or podcasts into vertical shorts with word-level captions and optional publishing.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Auto-publishing involves platform credentials; downloading source videos should respect platform terms and permissions.
- Maintenance: Commits within the last 90 days; 3 commits in 30 days, 3 commits in 90 days.
- License: [MIT](https://api.github.com/repos/social-media-skills/video-to-shorts-skill/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/social-media-skills/video-to-shorts-skill/blob/2e20fb008b584f3927798f36f580401d75318600/README.md#L3).

## [Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video)

Generates copy, images or video, voiceover and composited shorts from a topic, with ComfyUI workflows and media APIs.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: The original AIDC-AI address has moved; configuration, fees and asset licenses for local ComfyUI, RunningHub or model APIs must be verified separately.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://github.com/ATH-MaaS/Pixelle-Video/blob/848b054e4fae40dabc62ec58e960b573e83793ac/LICENSE); Open license verified. Root LICENSE is Apache-2.0; NOTICE lists third-party dependencies and their licenses.
- Feature verified: 2026-11-20; [Source 1](https://github.com/ATH-MaaS/Pixelle-Video/blob/848b054e4fae40dabc62ec58e960b573e83793ac/README.md#L52).

## [Atlas Explainer](https://github.com/AtlasCloudAI/atlas-explainer)

Skill/CLI generating a voiceover papercraft-style explainer video from one topic.

- Category: Knowledge shorts, clipping and explainers; Core candidate.
- Scope boundary: Image and speech generation depend on the Atlas Cloud API, not a fully local production chain.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://api.github.com/repos/AtlasCloudAI/atlas-explainer/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/AtlasCloudAI/atlas-explainer/blob/02f0d82392191a1c980a8a40348eb686b9e157dd/README.md#L3).

## [FFmpeg Skill](https://github.com/kajisho5/ffmpeg-skill)

CLI and MCP giving coding agents local FFmpeg cutting, subtitles, format export and output checks.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Needs local FFmpeg and Python; the skill, FFmpeg build and media follow their own licenses, and specific results were not tested.
- Maintenance: Commits within the last 90 days; 614 commits in 30 days, 1044 commits in 90 days.
- License: [MIT](https://github.com/kajisho5/ffmpeg-skill/blob/45df6b9ab0740cecc15d0169165e8cfbcefdfb0b/LICENSE); Open license verified. Skill repo root LICENSE is MIT; FFmpeg and encoder licenses must be verified per build.
- Feature verified: 2026-11-21; [Source 1](https://github.com/kajisho5/ffmpeg-skill/blob/45df6b9ab0740cecc15d0169165e8cfbcefdfb0b/README.md#L67).

## [Claude Code Video Toolkit](https://github.com/digitalsamba/claude-code-video-toolkit)

Skills, templates, commands and tools for Claude Code covering scripts, voiceover, music, image and video generation, QA, rendering and publishing, portable to Codex and Kiro CLI.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Needs Node 22+ and Claude Code; AI models deploy to your own Modal/RunPod cloud GPU account at cost; the README's $0.33 figure and sample films are author self-tests; community plugins, third-party design skills and hosted publishing services carry their own licenses and terms; generated content, voice cloning and media rights need self-verification.
- Maintenance: Commits within the last 90 days; 416 commits in 30 days, 550 commits in 90 days.
- License: [MIT](https://github.com/digitalsamba/claude-code-video-toolkit/blob/b3437fcd462c23b3c46cfd28f8cb61b71039269b/LICENSE); Open license verified. Repo-root LICENSE is MIT (copyright Digital Samba); licenses for invoked model weights such as Qwen3-TTS, FLUX.2, Ideogram 4, ACE-Step and LTX-Video, external services such as ElevenLabs, the Remotion renderer and community plugins (e.g. arkiv under PolyForm Perimeter) are each separate
- Feature verified: 2026-11-24; [Source 1](https://github.com/digitalsamba/claude-code-video-toolkit/blob/b3437fcd462c23b3c46cfd28f8cb61b71039269b/README.md#L9) · [Source 2](https://github.com/digitalsamba/claude-code-video-toolkit/blob/b3437fcd462c23b3c46cfd28f8cb61b71039269b/README.md#L12) · [Source 3](https://github.com/digitalsamba/claude-code-video-toolkit/blob/b3437fcd462c23b3c46cfd28f8cb61b71039269b/README.md#L66).

## [Video Shotcraft](https://github.com/Vincentwei1021/video-shotcraft)

Shot recipes, storyboards, Remotion animation, beat editing and frame-by-frame checks for agents.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: The shot library is a creative method and code asset, not a replacement for a general timeline editor.
- Maintenance: Commits within the last 90 days; 36 commits in 30 days, 56 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/Vincentwei1021/video-shotcraft/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Vincentwei1021/video-shotcraft/blob/6700db2ba80572ebc777b99d72049679fed9840c/README.md#L26).

## [Remocn](https://github.com/Remocn/remocn)

Claude Code plugin, agent skill and MCP server for making Remotion videos from 935 MIT-licensed components: the agent plans a storyboard first, then writes the video.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Requires Remotion and the shadcn CLI that installs the components; `scene-reviewer` only checks still frames for clipped text, empty frames and low contrast, so finish quality and render times were not measured; components, fonts and the hosted MCP carry their own terms, and Remotion itself is licensed separately.
- Maintenance: Commits within the last 90 days; 151 commits in 30 days, 189 commits in 90 days.
- License: [MIT](https://github.com/Remocn/remocn/blob/ac1e4081edcc70757db4dc4af32b079cb9ae5490/LICENSE); Open license verified. Repo root LICENSE is MIT; the README states the components are MIT-licensed, while the Remotion renderer, fonts and hosted MCP service must be verified under their own terms.
- Feature verified: 2026-11-26; [Source 1](https://github.com/Remocn/remocn/blob/ac1e4081edcc70757db4dc4af32b079cb9ae5490/README.md#L9) · [Source 2](https://github.com/Remocn/remocn/blob/ac1e4081edcc70757db4dc4af32b079cb9ae5490/README.md#L37) · [Source 3](https://github.com/Remocn/remocn/blob/ac1e4081edcc70757db4dc4af32b079cb9ae5490/README.md#L73).

## [Kinocut](https://github.com/KyaniteLabs/kinocut)

Local video editing MCP/Python/CLI with guardrails, preflight checks, receipts and quality gates.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Wraps FFmpeg plus optional Whisper/HyperFrames; typed tools do not guarantee editing taste.
- Maintenance: Commits within the last 90 days; 371 commits in 30 days, 698 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/KyaniteLabs/kinocut/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/KyaniteLabs/kinocut/blob/4ad02dba114cf12163663e7cd39da92d4f735212/README.md#L13).

## [Manju Laoli Skill](https://github.com/lixiaoxiao9888-create/manju-laoli-skill)

OpenClaw skill suite for AI comic dramas and short dramas covering scripts, asset locking, storyboards, fight scenes, Seedance prompting and machine checks.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Targets agent platforms such as OpenClaw, Coze and Dify; the only in-pack video-model line is Seedance 2.5/2.0; the author labels it beta assembled from open-source content, with external rule and asset sources not itemized; the package holds no images, so assets are generated on external platforms and licensed by the user.
- Maintenance: Commits within the last 90 days; 10 commits in 30 days, 53 commits in 90 days.
- License: [MIT](https://github.com/lixiaoxiao9888-create/manju-laoli-skill/blob/a01e647ac10134918a5de1b18bfe9317e5541a44/LICENSE); Open license verified. Repo root and short-drama-director are both MIT; the author labels it a beta assembled from open-source content without an itemized third-party NOTICE, so redistributing rule text and examples needs self-verification
- Feature verified: 2026-11-23; [Source 1](https://github.com/lixiaoxiao9888-create/manju-laoli-skill/blob/a01e647ac10134918a5de1b18bfe9317e5541a44/README.md#L60) · [Source 2](https://github.com/lixiaoxiao9888-create/manju-laoli-skill/blob/a01e647ac10134918a5de1b18bfe9317e5541a44/README.md#L72) · [Source 3](https://github.com/lixiaoxiao9888-create/manju-laoli-skill/blob/a01e647ac10134918a5de1b18bfe9317e5541a44/README.md#L137).

## [Remotion Agent Skills](https://github.com/remotion-dev/skills)

Official Skills for coding agents to create, preview and render Remotion videos.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Requires Remotion and an Agent-Skills-capable host; no license was found at this repo's root, and Remotion itself has separate license terms.
- Maintenance: Commits within the last 90 days; 9 commits in 30 days, 31 commits in 90 days.
- License: [License unverified](https://github.com/remotion-dev/skills/tree/6f55706d1069e512430582ad86e4e57dc07afe1b); License unverified. No LICENSE found in the repo root or file tree; Remotion's product and per-package licenses must be checked separately.
- Feature verified: 2026-11-20; [Source 1](https://github.com/remotion-dev/skills/blob/6f55706d1069e512430582ad86e4e57dc07afe1b/README.md#L5).

## [pixelfx](https://github.com/patch-gg/pixelfx)

Library of 244 code-drawn pixel effects and animations with a Claude Code effect-generation skill plus sprite-sheet and GIF/MP4 export tools.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: An effects and motion asset library without script, editing or publishing flows; the Patch Pixel font under `gallery/fonts` is Patch's own copyright, excluded from MIT; some code is adapted from Sprite Fusion and Hollow Crown (both MIT) and attribution must be kept per NOTICE; exporting into video still requires clearing third-party content visible on screen.
- Maintenance: Commits within the last 90 days; 10 commits in 30 days, 10 commits in 90 days.
- License: [MIT (code and effects) + Patch Pixel font excluded](https://github.com/patch-gg/pixelfx/blob/5294518ce7c72e48b6100a744596e0acf57f2826/NOTICE.md); Composite/conditional license. README states code and effects are MIT and commercially usable; NOTICE lists effects adapted from Hugo Duprez's Sprite Fusion and Hollow Crown (both MIT) requiring attribution, while `gallery/fonts/PatchPixel-Regular.woff2` is All Rights Reserved by Patch, outside MIT
- Feature verified: 2026-11-24; [Source 1](https://github.com/patch-gg/pixelfx/blob/5294518ce7c72e48b6100a744596e0acf57f2826/README.md#L7) · [Source 2](https://github.com/patch-gg/pixelfx/blob/5294518ce7c72e48b6100a744596e0acf57f2826/README.md#L89) · [Source 3](https://github.com/patch-gg/pixelfx/blob/5294518ce7c72e48b6100a744596e0acf57f2826/README.md#L156).

## [Wallstreet Explainer](https://github.com/HeyChengC/wallstreet-explainer)

Coding-agent Skill for Wall-Street-style finance/tech explainer shorts with style language, graphic component templates, and footage-finding, screenshot, voiceover, keying, rendering and mixing scripts.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Needs a host such as Claude Code plus ffmpeg, Python/Node dependencies, Playwright, and five fonts you download yourself; media comes from yt-dlp downloads and news-page screenshots quoted as commentary, so provenance and redistribution rights are yours to verify; third-party footage, screenshots, logos and people in the samples are not covered by MIT.
- Maintenance: Commits within the last 90 days; 10 commits in 30 days, 16 commits in 90 days.
- License: [MIT (code and docs) + third-party sample assets excluded](https://github.com/HeyChengC/wallstreet-explainer/blob/b79bc0573455cb5fe335e78f653012e658fa9758/LICENSE); Composite/conditional license. LICENSE is the MIT text plus additional terms explicitly excluding video frames, news screenshots, logos and photos under examples/; GitHub therefore reports NOASSERTION. Fonts are downloaded by the user under their own licenses
- Feature verified: 2026-11-23; [Source 1](https://github.com/HeyChengC/wallstreet-explainer/blob/b79bc0573455cb5fe335e78f653012e658fa9758/README.md#L3) · [Source 2](https://github.com/HeyChengC/wallstreet-explainer/blob/b79bc0573455cb5fe335e78f653012e658fa9758/README.md#L37) · [Source 3](https://github.com/HeyChengC/wallstreet-explainer/blob/b79bc0573455cb5fe335e78f653012e658fa9758/README.md#L92).

## [Awesome Motion Design Agent Skills](https://github.com/frankxai/awesome-motion-design-agent-skills)

Five installable SKILL.md motion workflows (including remotion-video-agent and web-motion-auditor) plus a curated index of GSAP, Motion, Remotion, Rive, Lottie and 3D tools.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Index entries point at third-party repositories whose licenses and availability need separate checks; the skills only supply method, checklists and routing, so motion and video quality depend on the host agent and the libraries chosen; the README advises scanning third-party packs with SkillSpector first.
- Maintenance: Commits within the last 90 days; 14 commits in 30 days, 24 commits in 90 days.
- License: [CC0-1.0](https://github.com/frankxai/awesome-motion-design-agent-skills/blob/e7dc6e2e728c918ffcea5edb2d7c94e2a6f7785d/LICENSE); Open license verified. Repo root LICENSE is CC0 1.0 Universal; the third-party projects, fonts and assets the index and skills point to stay under their own licenses.
- Feature verified: 2026-11-26; [Source 1](https://github.com/frankxai/awesome-motion-design-agent-skills/blob/e7dc6e2e728c918ffcea5edb2d7c94e2a6f7785d/README.md#L15) · [Source 2](https://github.com/frankxai/awesome-motion-design-agent-skills/blob/e7dc6e2e728c918ffcea5edb2d7c94e2a6f7785d/README.md#L51) · [Source 3](https://github.com/frankxai/awesome-motion-design-agent-skills/blob/e7dc6e2e728c918ffcea5edb2d7c94e2a6f7785d/README.md#L57).

## [ReelBench Skills](https://github.com/eternityspring/reelbench-skills)

Video analysis, cloning and production skill set for Claude Code/Codex.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Some related products and asset services are paid or external, verified per skill.
- Maintenance: Commits within the last 90 days; 1 commits in 30 days, 21 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/eternityspring/reelbench-skills/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/eternityspring/reelbench-skills/blob/8d8444894524c9beedbf8815dab517afb3ce3cbe/README.md#L5).

## [Video Agent Skills](https://github.com/Melvynx/video-agent-skills)

Organizes scripts, research, editing, translation and publishing for shorts/YouTube via Markdown skills.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: The skills do not bundle all models and renderers; you need a host and local tools.
- Maintenance: Commits within the last 90 days; 2 commits in 30 days, 27 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Melvynx/video-agent-skills/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Melvynx/video-agent-skills/blob/f4542923f7f796a1fa0e544cbfc1109d5eec87d8/README.md#L3).

## [AI Filmmaking Camera Control (Seedance 2.5)](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5)

137 cinematic camera-move templates with a previs pipeline: three.js plus Remotion render striped-pill reference clips, ready-made prompts hand them to Seedance 2.5, and Tein MCP or API setup plus a cinematic-previs skill drive the work.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Final footage must be generated through Tein-hosted (tein.ai) Seedance 2.5 with your own key - the repo stores none, but its homepage and description route there - and drafts are 480p and cheaper; rendering needs Node 22.12+, ffmpeg and one network access that downloads headless Chrome, the pill.mp4 files in git are mostly 960-wide gallery copies while full results sit in the v0.1.0 release zip; the author marks 4 of the 137 method questions UNPROVEN; NOTICE.md records 33 camera presets distilled from the E.T. dataset (estimated from copyrighted films, only the curves shipped), the author's own face and voice in the examples, and product shots with visible brand marks, none of which MIT covers; Remotion is free for individuals, for-profit organisations up to 3 employees and non-profits, and larger for-profit teams need a company licence; the repository was created and last pushed on 2026-11-07, and the moves and output quality were not reproduced here.
- Maintenance: Commits within the last 90 days; 5 commits in 30 days, 5 commits in 90 days.
- License: [MIT (code, prompts, notes, pill clips) + Remotion's own licence, Quaternius CC0, third-party material excluded](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/NOTICE.md); Composite/conditional license. Root LICENSE is MIT but covers only the code, prompts, notes and the pill clips made for this repo; NOTICE.md lists the Quaternius animation rig (CC0, with its licence text and checksums), Remotion 4.0.522 (free for individuals, organisations of up to 3 employees and non-profits, company licence above that), three.js, React and three-gpu-pathtracer (MIT) and Rapier (Apache-2.0); the faces and voices in the examples, the branded product photos and the 33 camera curves distilled from copyrighted films fall outside the MIT grant, so check the dataset and service terms before commercial use.
- Feature verified: 2026-11-27; [Source 1](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/README.md#L3) · [Source 2](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/README.md#L8) · [Source 3](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/README.md#L84) · [Source 4](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/NOTICE.md#L9) · [Source 5](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/NOTICE.md#L14).

## [HyperFrames Motion Library](https://github.com/nutllwhy/hyperframes-motion-library)

Local motion template and parameterized asset library built on HyperFrames.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: A motion asset library without full scripting, asset generation or publishing flows.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 2 commits in 90 days.
- License: [MIT](https://api.github.com/repos/nutllwhy/hyperframes-motion-library/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/nutllwhy/hyperframes-motion-library/blob/98c40ca18f23d7dc021a5d84308ab10599482cff/README.md#L3).

## [Video Editing Skill](https://github.com/social-media-skills/video-editing-skill)

Runs the first editing pass and caption handling for talking heads, courses, interviews and vlogs.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Targets the first rough cut, not replacing human final review, grading and complex packaging.
- Maintenance: Commits within the last 90 days; 3 commits in 30 days, 3 commits in 90 days.
- License: [MIT](https://api.github.com/repos/social-media-skills/video-editing-skill/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/social-media-skills/video-editing-skill/blob/f94d0517d717de281ee23569094aac616d32f4ef/README.md#L1).

## [GSAP Skills](https://github.com/greensock/gsap-skills)

Official Agent Skills teaching coding agents the GSAP timeline, motion and plugins.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Web animation skills needing a host agent; rendering to video requires video tooling, and GSAP product licensing is separate.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/greensock/gsap-skills/blob/aed9cfd3277740755f6bfc1155c7aa645403b760/LICENSE); Open license verified. Skills repo root LICENSE is MIT; the GSAP library and third-party assets follow their own terms.
- Feature verified: 2026-11-21; [Source 1](https://github.com/greensock/gsap-skills/blob/aed9cfd3277740755f6bfc1155c7aa645403b760/README.md#L23).

## [Narrator AI CLI Skill](https://github.com/NarratorAI-Studio/narrator-ai-cli-skill)

Guides an agent to drive narrator-ai-cli for automated film-commentary videos.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: A machine-readable skill for that CLI, not a standalone rendering engine; backend services and templates are separate.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://api.github.com/repos/NarratorAI-Studio/narrator-ai-cli-skill/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/NarratorAI-Studio/narrator-ai-cli-skill/blob/4b17c6f2175bd532c92db778a847f8fb6bdd3177/README.md#L9).

## [OpenClip Agent Skills](https://github.com/OpenClip-App/agent-skills)

Agent skills for long-video clipping, transcription, conversion, thumbnails, cutouts and UGC creative.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Skills drive the hosted OpenClip MCP; video and credentials pass through an external service.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://api.github.com/repos/OpenClip-App/agent-skills/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/OpenClip-App/agent-skills/blob/ea02c98db69c437616df1db4a4400cde1f4a0832/README.md#L1).

## [MCP Video Editing](https://github.com/mfortne/mcp-video-editing)

Wraps FFmpeg, HyperFrames and local reusable pipelines in an MCP, Python library and CLI.

- Category: Agent Skills, MCP and editing tools; Core candidate.
- Scope boundary: Results depend on external tool versions; same category as Kinocut but a different repository.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/mfortne/mcp-video-editing/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/mfortne/mcp-video-editing/blob/97ecab83d26c24bfe77be663784399b203b1fa55/README.md#L3).

## [HyperFrames](https://github.com/heygen-com/hyperframes)

HTML/CSS/JS-based code video and agent skill ecosystem, migratable from Remotion with frame-by-frame verification.

- Category: Code-to-video and motion graphics; Core candidate.
- Scope boundary: The project and HeyGen's hosted generation service are different tiers; specific templates and external assets carry separate licenses.
- Maintenance: Commits within the last 90 days; 1823 commits in 30 days, 4168 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/heygen-com/hyperframes/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/heygen-com/hyperframes/blob/234fb1aeef13f8d86b4f7f4cb1af624db3a81ec2/README.md#L5).

## [Remotion](https://github.com/remotion-dev/remotion)

Base framework for creating and rendering video in code with React/TypeScript.

- Category: Code-to-video and motion graphics; Restricted license.
- Scope boundary: General code-video infrastructure without built-in agent planning or generation models.
- Maintenance: Commits within the last 90 days; 2487 commits in 30 days, 6839 commits in 90 days.
- License: [Remotion License](https://github.com/remotion-dev/remotion/blob/51fd2b4a06a2b2ff0d4eb058dfe4db2b7275bac3/LICENSE.md); Source-available, not OSI open source. Free for individuals, non-profits and small organizations; for-profit organizations meeting the thresholds need a company license, so this is not regular OSI open source
- Feature verified: 2026-11-12; [Source 1](https://github.com/remotion-dev/remotion/blob/51fd2b4a06a2b2ff0d4eb058dfe4db2b7275bac3/README.md#L2).

## [raea](https://github.com/shinyobjectz/raea)

Engine and desktop agent workbench for writing video, motion, 3D and games in React/TypeScript, rendered on the local GPU.

- Category: Code-to-video and motion graphics; Core candidate.
- Scope boundary: Engine, CLI and desktop app are free to use; cloud storage, cross-machine search and publishing are Pro/Team; FSL-1.1-ALv2 forbids competing products, and each release converts to Apache-2.0 two years after publication; licenses for sample footage, models, binary runtimes, third-party components and assets in your account are separate.
- Maintenance: Commits within the last 90 days; 1612 commits in 30 days, 1615 commits in 90 days.
- License: [FSL-1.1-ALv2](https://github.com/shinyobjectz/raea/blob/0c9fc255f2287f0530fc773b895cb5d1877a6f54/LICENSE); Source-available, not OSI open source. Repo-root LICENSE is Functional Source License 1.1 (ALv2 Future License), forbidding use of the software in commercial products/services that replace raea or its existing products, with each version converting to Apache-2.0 two years after release; NOTICE and LICENSES separately list HyperFrames ports, Bevy, FFmpeg, QuickJS and other third-party licenses
- Feature verified: 2026-11-22; [Source 1](https://github.com/shinyobjectz/raea/blob/0c9fc255f2287f0530fc773b895cb5d1877a6f54/README.md#L13) · [Source 2](https://github.com/shinyobjectz/raea/blob/0c9fc255f2287f0530fc773b895cb5d1877a6f54/README.md#L42) · [Source 3](https://github.com/shinyobjectz/raea/blob/0c9fc255f2287f0530fc773b895cb5d1877a6f54/README.md#L111).

## [Lemo Opuscar](https://github.com/lemomo-ai/lemo-opuscar)

Cinematic style, examples and STYLE.md guidance for coding agents making video in code.

- Category: Code-to-video and motion graphics; Restricted license.
- Scope boundary: The project recommends Claude with higher reasoning effort; reusing footage, people, brands and voices from the demos must be verified individually.
- Maintenance: Commits within the last 90 days; 77 commits in 30 days, 151 commits in 90 days.
- License: [MIT code + CC BY-NC docs (additional license)](https://github.com/lemomo-ai/lemo-opuscar/blob/f9e204293930952b61ba921cd8944d05f121beee/LICENSE); Composite/conditional license. Code is MIT; Markdown docs are CC BY-NC 4.0, which additionally allows reading, modifying and delivering them with project files for your own or client films; commercial use beyond that needs a license. Sample media and some voiceovers have further restrictions.
- Feature verified: 2026-11-21; [Source 1](https://github.com/lemomo-ai/lemo-opuscar/blob/f9e204293930952b61ba921cd8944d05f121beee/README.md#L7).

## [Manim Community](https://github.com/ManimCommunity/manim)

Video engine for programmatic math and explainer animations in Python.

- Category: Code-to-video and motion graphics; Core candidate.
- Scope boundary: Suited to code-driven explainers; not an AI agent that generates content automatically; render dependencies and fonts are separate.
- Maintenance: Commits within the last 90 days; 29 commits in 30 days, 80 commits in 90 days.
- License: [MIT](https://github.com/ManimCommunity/manim/blob/ab7f9527fa2b37893aacc367e21b723845f44ef0/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/ManimCommunity/manim/blob/ab7f9527fa2b37893aacc367e21b723845f44ef0/README.md#L20).

## [GiveMotion](https://github.com/givemotion/givemotion)

Code video engine where agents write HTML/CSS, preview, check and render MP4s.

- Category: Code-to-video and motion graphics; Core candidate.
- Scope boundary: Code animation suits motion and explainers, not real-footage editing or diffusion video generation.
- Maintenance: Commits within the last 90 days; 76 commits in 30 days, 255 commits in 90 days.
- License: [MIT](https://api.github.com/repos/givemotion/givemotion/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/givemotion/givemotion/blob/8a7949e685bbfaec8bde20fad9aa8734cdfa6038/README.md#L6).

## [SenseNova Code2Video](https://github.com/OpenSenseNova/SenseNova-6.8-Code2Video)

Small open model that generates executable code rendered into short videos.

- Category: Code-to-video and motion graphics; Core candidate.
- Scope boundary: Currently focused on pure-code shorts; model weights, inference environment and generation-tool licenses need separate verification.
- Maintenance: Commits within the last 90 days; 1 commits in 30 days, 3 commits in 90 days.
- License: [Unverified](https://github.com/OpenSenseNova/SenseNova-6.8-Code2Video/blob/776ae79824e338ba5d63fef66167455edc94ad26/README.md); License unverified. No root license found; model weights and code-reuse conditions need separate confirmation
- Feature verified: 2026-11-12; [Source 1](https://github.com/OpenSenseNova/SenseNova-6.8-Code2Video/blob/776ae79824e338ba5d63fef66167455edc94ad26/README.md#L3).

## [Manim](https://github.com/3b1b/manim)

Python animation engine for math explainers.

- Category: Code-to-video and motion graphics; Adjacent infrastructure.
- Scope boundary: General animation tool and this is the 3Blue1Brown version, not a complete AI video agent.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 1 commits in 90 days.
- License: [MIT](https://api.github.com/repos/3b1b/manim/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/3b1b/manim/blob/fafa083a4fb274bba9cabde0b6e2f50ba6da0622/README.md#L2).

## [Motion Canvas](https://github.com/motion-canvas/motion-canvas)

Creates animations, explainers and motion graphics with TypeScript and generator functions.

- Category: Code-to-video and motion graphics; Adjacent infrastructure.
- Scope boundary: General animation framework; agent capability comes from upper-layer skills or the host.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://api.github.com/repos/motion-canvas/motion-canvas/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/motion-canvas/motion-canvas/blob/7b91435c301d530351dcf5ebb91dd139c002e405/README.md#L6).

## [three.js](https://github.com/mrdoob/three.js)

JavaScript 3D scene and rendering library that supplies 3D content for code motion.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: General rendering library that does not output video by itself; assets and the WebGL/WebGPU environment are yours to handle.
- Maintenance: Commits within the last 90 days; 316 commits in 30 days, 894 commits in 90 days.
- License: [MIT](https://github.com/mrdoob/three.js/blob/8b92052852735b67cfa8393f78e707b3f07a0eec/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/mrdoob/three.js/blob/8b92052852735b67cfa8393f78e707b3f07a0eec/README.md#L11).

## [Godot](https://github.com/godotengine/godot)

Open-source game engine for building 2D/3D scenes, interaction and animation.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: A game engine is not an automated video generator; capturing or exporting finished footage needs an extra designed pipeline.
- Maintenance: Commits within the last 90 days; 517 commits in 30 days, 1873 commits in 90 days.
- License: [MIT](https://github.com/godotengine/godot/blob/73ca6be2cebd5192d8b279979d04f29ea45c266e/LICENSE.txt); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/godotengine/godot/blob/73ca6be2cebd5192d8b279979d04f29ea45c266e/README.md#L11).

## [Motion](https://github.com/motiondivision/motion)

UI and layout animation library for JavaScript, React and Vue.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: General motion component; pairs with video renderers and does not itself provide a video agent.
- Maintenance: Commits within the last 90 days; 450 commits in 30 days, 1396 commits in 90 days.
- License: [MIT](https://github.com/motiondivision/motion/blob/cd009de7a4314e065d4d9df683057124792d5b34/LICENSE.md); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/motiondivision/motion/blob/cd009de7a4314e065d4d9df683057124792d5b34/README.md#L3).

## [Blender](https://github.com/blender/blender)

3D creation suite covering modeling, rigging, animation, rendering, compositing and video editing.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: The GitHub repo is the official mirror; third-party add-ons, models and assets follow their own licenses.
- Maintenance: Commits within the last 90 days; 1124 commits in 30 days, 3362 commits in 90 days.
- License: [GPL-2.0-or-later](https://github.com/blender/blender/blob/611d97903ad34434934f4cb1e586155c03eddd66/COPYING); Open license verified. COPYING points to the GPL license text; third-party assets and components are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/blender/blender/blob/611d97903ad34434934f4cb1e586155c03eddd66/.github/README.md#L14).

## [Babylon.js](https://github.com/BabylonJS/Babylon.js)

JavaScript 3D scene, game and rendering engine usable as code-motion infrastructure.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Primarily a real-time 3D renderer; video encoding needs extra tools, and the docs warn demo CDNs are not for production.
- Maintenance: Commits within the last 90 days; 146 commits in 30 days, 343 commits in 90 days.
- License: [Apache-2.0](https://github.com/BabylonJS/Babylon.js/blob/6226e393cef4295d8509b8a83e82572b2af4c9c9/license.md); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/BabylonJS/Babylon.js/blob/6226e393cef4295d8509b8a83e82572b2af4c9c9/readme.md#L1).

## [Konva](https://github.com/konvajs/konva)

2D Canvas scene graph with object interaction, transforms, animation and export.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: General canvas component; video or audio export needs other tools.
- Maintenance: Commits within the last 90 days; 32 commits in 30 days, 219 commits in 90 days.
- License: [MIT](https://github.com/konvajs/konva/blob/bf1927c1cfec7f47eb608a470aff6ca99dd09aa9/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/konvajs/konva/blob/bf1927c1cfec7f47eb608a470aff6ca99dd09aa9/README.md#L16).

## [Two.js](https://github.com/jonobr1/two.js)

2D shapes and animated scenes via WebGL, Canvas or SVG.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: 2D drawing base library; producing audio/video files needs separate rendering and encoding.
- Maintenance: Commits within the last 90 days; 15 commits in 30 days, 44 commits in 90 days.
- License: [MIT](https://github.com/jonobr1/two.js/blob/bd48e27ff8f3333ef442fb3d032cb6b5391f26dc/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/jonobr1/two.js/blob/bd48e27ff8f3333ef442fb3d032cb6b5391f26dc/README.md#L8).

## [Shifty](https://github.com/jeremyckahn/shifty)

TypeScript tweening engine with easings and playback control.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Low-level tween library without video generation or export workflows.
- Maintenance: Commits within the last 90 days; 8 commits in 30 days, 14 commits in 90 days.
- License: [MIT](https://github.com/jeremyckahn/shifty/blob/ee4c8ed53503d5a6bf658ccdbba5af58674e3245/LICENSE-MIT); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/jeremyckahn/shifty/blob/ee4c8ed53503d5a6bf658ccdbba5af58674e3245/README.md#L7).

## [Ola](https://github.com/franciscop/ola)

Lightweight animation library for real-time numeric smoothing.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Handles numeric interpolation only; you supply scenes, timelines and export.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 3 commits in 90 days.
- License: [MIT](https://github.com/franciscop/ola/blob/b269059c570405421acfcc55c84b3347cbeb0674/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/franciscop/ola/blob/b269059c570405421acfcc55c84b3347cbeb0674/readme.md#L3).

## [Anime.js](https://github.com/juliangarnier/anime)

Timeline animation of CSS, SVG, DOM and JavaScript properties.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: General web motion engine; video rendering and audio sync need extra tools.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/juliangarnier/anime/blob/01b81be1df6843ccfe0a71c0699a746bf740dd77/LICENSE.md); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/juliangarnier/anime/blob/01b81be1df6843ccfe0a71c0699a746bf740dd77/README.md#L13).

## [Proton](https://github.com/drawcall/Proton)

JavaScript particle animation library for fire, fireworks, explosions and similar effects.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Effects base library, not a standalone video renderer or editor.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/drawcall/Proton/blob/b4fdef5e5416d70a788978bec0fb4a1be26514b4/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/drawcall/Proton/blob/b4fdef5e5416d70a788978bec0fb4a1be26514b4/README.md#L26).

## [Lottie Web](https://github.com/airbnb/lottie-web)

Parses and renders exported Lottie vector animations in the web.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: A player is not a video editor; licenses for animation assets and their creation tools are separate.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/airbnb/lottie-web/blob/bede03d25d232826e0c9dca1733d542d8a7754fb/LICENSE.md); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/airbnb/lottie-web/blob/bede03d25d232826e0c9dca1733d542d8a7754fb/README.md#L3).

## [TweenJS](https://github.com/CreateJS/TweenJS)

Tweens and chained playback for JavaScript numbers and CSS properties.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Tween library that needs a renderer and export tooling alongside.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/CreateJS/TweenJS/blob/6df2b9ce7e68d3d824cc490b67cab2bc3204810a/LICENSE.txt); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/CreateJS/TweenJS/blob/6df2b9ce7e68d3d824cc490b67cab2bc3204810a/README.md#L3).

## [LUME](https://github.com/lume/lume)

Builds interactive 2D and 3D graphic scenes using HTML elements.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: General 3D/graphics component without a complete video production pipeline.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/lume/lume/blob/6336e365f1c02af6316017bcd6d7f79bd2efe13b/LICENSE); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/lume/lume/blob/6336e365f1c02af6316017bcd6d7f79bd2efe13b/README.md#L23).

## [gifenc](https://github.com/mattdesl/gifenc)

Encodes GIFs with animation and transparency in the browser or Node.js.

- Category: Animation, 3D and coding building blocks; Adjacent infrastructure.
- Scope boundary: Outputs GIF only; no MP4 export, video editing or AI generation.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/mattdesl/gifenc/blob/27db5b982dba701ca440b55ea36fad3999040973/LICENSE.md); Open license verified. Project license file verified; third-party components, assets and hosted services are separate.
- Feature verified: 2026-11-20; [Source 1](https://github.com/mattdesl/gifenc/blob/27db5b982dba701ca440b55ea36fad3999040973/README.md#L5).

## [VRGameDevGirl AI Video Builder](https://github.com/vrgamegirl19/comfyui-vrgamedevgirl)

ComfyUI workflow suite managing planning, prompts, generation, pacing, review and final assembly per scenario.

- Category: ComfyUI and open-source video generation; Restricted license.
- Scope boundary: Some custom nodes moved to separate packages; models, VRAM and install compatibility need verification per workflow.
- Maintenance: Commits within the last 90 days; 111 commits in 30 days, 661 commits in 90 days.
- License: [VRGameDevGirl Community and Commercial License](https://github.com/vrgamegirl19/comfyui-vrgamedevgirl/blob/b419bb5c2468432704e0339035844620f1b3ec18/LICENSE); Source-available, not OSI open source. Generated content may be commercialized; selling/hosting/commercially integrating the software itself requires a written commercial license
- Feature verified: 2026-11-12; [Source 1](https://github.com/vrgamegirl19/comfyui-vrgamedevgirl/blob/b419bb5c2468432704e0339035844620f1b3ec18/README.md#L1).

## [LTX-Video](https://github.com/Lightricks/LTX-Video)

Open video models and inference tools for text/image-to-video and audio-visual generation.

- Category: ComfyUI and open-source video generation; Core candidate.
- Scope boundary: Hardware, weights and audio capabilities differ markedly across LTX versions.
- Maintenance: Commits within the last 90 days; 2 commits in 30 days, 2 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/Lightricks/LTX-Video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Lightricks/LTX-Video/blob/50f0aef1297574a4b29acbdb874e3a363a6d5f2e/README.md#L4).

## [HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo)

Tencent's open large video-generation foundation model and inference framework.

- Category: ComfyUI and open-source video generation; Restricted license.
- Scope boundary: High hardware requirements; code license vs. model weights/output policy must be verified separately.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 3 commits in 90 days.
- License: [Tencent Hunyuan Community License](https://github.com/Tencent-Hunyuan/HunyuanVideo/blob/4eda9cb44c3be82a6b9c4261897cb6bd3cfb084e/LICENSE.txt); Source-available, not OSI open source. Includes territory exclusions, an acceptable-use policy and model derivative terms, so it is not a standard OSI open-source license
- Feature verified: 2026-11-12; [Source 1](https://github.com/Tencent-Hunyuan/HunyuanVideo/blob/4eda9cb44c3be82a6b9c4261897cb6bd3cfb084e/README.md#L1).

## [Wan2.2](https://github.com/Wan-Video/Wan2.2)

Alibaba's Wan family of open video generation models covering text/image-to-video and related tasks.

- Category: ComfyUI and open-source video generation; Core candidate.
- Scope boundary: Model sizes, active parameters and license conditions must be checked per checkpoint.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 2 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/Wan-Video/Wan2.2/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Wan-Video/Wan2.2/blob/1ea34ff48f87168174e12956e200b1d908b1c5ff/README.md#L1).

## [Mochi](https://github.com/genmoai/mochi)

Genmo's open video generation model and inference code.

- Category: ComfyUI and open-source video generation; Core candidate.
- Scope boundary: Model weights, VRAM, duration and resolution limits need verification per version.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 2 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/genmoai/mochi/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/genmoai/mochi/blob/15c9bad662df1fa3e7b53136423695b286484c08/README.md#L1).

## [Open-Sora](https://github.com/hpcaitech/Open-Sora)

Open-source efficient video generation training and inference framework.

- Category: ComfyUI and open-source video generation; Core candidate.
- Scope boundary: A research framework and model checkpoints are not a desktop finishing tool.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/hpcaitech/Open-Sora/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/hpcaitech/Open-Sora/blob/7ad6a96a135feb81f755c84fb391818718f6beb2/README.md#L2).

## [Bernini](https://github.com/bytedance/Bernini)

Video generation and editing research framework combining a semantic planner and a DiT renderer.

- Category: ComfyUI and open-source video generation; Research/benchmark.
- Scope boundary: Paper benchmarks are not capability conclusions when mixed with product-editor maintenance scores.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/bytedance/Bernini/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/bytedance/Bernini/blob/e6c2cf11843470b08491745947abcba9c3c6b079/README.md#L3).

## [HunyuanVideo-I2V](https://github.com/Tencent-Hunyuan/HunyuanVideo-I2V)

Customizable image-to-video framework built on HunyuanVideo.

- Category: ComfyUI and open-source video generation; Restricted license.
- Scope boundary: Separate from the base T2V project; input references and weight licenses need checking.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Tencent Hunyuan Community License](https://github.com/Tencent-Hunyuan/HunyuanVideo-I2V/blob/c8bba70b9517f08d770a9a2a3d1e93cc6d5b7949/LICENSE.txt); Source-available, not OSI open source. Includes territory exclusions, an acceptable-use policy and model derivative terms, so it is not a standard OSI open-source license
- Feature verified: 2026-11-12; [Source 1](https://github.com/Tencent-Hunyuan/HunyuanVideo-I2V/blob/c8bba70b9517f08d770a9a2a3d1e93cc6d5b7949/README.md#L9).

## [CogVideo / CogVideoX](https://github.com/zai-org/CogVideo)

Open text/image-to-video models and inference code.

- Category: ComfyUI and open-source video generation; Core candidate.
- Scope boundary: A model generator is not an editing workbench; weights, VRAM, resolution and model license must be checked per version.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/zai-org/CogVideo/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/zai-org/CogVideo/blob/7a1af7154511e0ce4e4be8d62faa8c5e5a3532d2/README.md#L1).

## [LiveTalking](https://github.com/lipku/LiveTalking)

Real-time interactive streaming system combining multiple digital-human backends.

- Category: Digital humans, portrait animation and lip sync; Core candidate.
- Scope boundary: License, hardware, latency and quality differ widely across backends.
- Maintenance: Commits within the last 90 days; 6 commits in 30 days, 12 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/lipku/LiveTalking/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/lipku/LiveTalking/blob/c7269433a2b6ecebcd9342445d2ecc882c98b0da/README.md#L250).

## [MuseTalk](https://github.com/TMElyralab/MuseTalk)

Audio-driven virtual human model for real-time high-quality lip sync.

- Category: Digital humans, portrait animation and lip sync; Core candidate.
- Scope boundary: Code, model weights, input portraits and commercial-use boundaries each need verification.
- Maintenance: Commits within the last 90 days; 1 commits in 30 days, 1 commits in 90 days.
- License: [MIT](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/LICENSE); Open license verified. Root LICENSE manually verified; model, data and performer-asset rights are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/README.md#L1).

## [LivePortrait](https://github.com/KlingAIResearch/LivePortrait)

Efficient portrait animation, retargeting and control framework.

- Category: Digital humans, portrait animation and lip sync; Core candidate.
- Scope boundary: The repo moved to KlingAIResearch; driving media and person consent are the user's responsibility.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/KlingAIResearch/LivePortrait/blob/9b294b3d0536135442ea73cb01e6cb3ca7029dd3/LICENSE); Open license verified. Root LICENSE manually verified; model, data and portrait rights are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/KlingAIResearch/LivePortrait/blob/9b294b3d0536135442ea73cb01e6cb3ca7029dd3/readme.md#L1).

## [SadTalker](https://github.com/OpenTalker/SadTalker)

Generates talking-head video from a single portrait and audio.

- Category: Digital humans, portrait animation and lip sync; Core candidate.
- Scope boundary: Generated portraits involve person consent; model and dependency licenses follow the current repo's terms.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/LICENSE); Open license verified. Root LICENSE manually verified; third-party components are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/OpenTalker/SadTalker/blob/cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8/README.md#L6).

## [Wav2Lip](https://github.com/Rudrabha/Wav2Lip)

Classic audio-video lip-sync research implementation.

- Category: Digital humans, portrait animation and lip sync; Restricted license.
- Scope boundary: Open code/weights are mostly limited to personal, research and non-commercial use; not recommended as ordinary commercial open source.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Personal/research/non-commercial license](https://github.com/Rudrabha/Wav2Lip/blob/bac9a81e63ecc153202353372e5724b83d9e6322/README.md#L207); Source-available, not OSI open source. README explicitly forbids commercial use of the released model
- Feature verified: 2026-11-12; [Source 1](https://github.com/Rudrabha/Wav2Lip/blob/bac9a81e63ecc153202353372e5724b83d9e6322/README.md#L1).

## [FFmpeg](https://github.com/FFmpeg/FFmpeg)

Low-level toolchain for transcoding, filtering, muxing, compositing and stream processing.

- Category: Download, capture, transcoding and media CLIs; Adjacent infrastructure.
- Scope boundary: License may become LGPL/GPL depending on build options; many higher-level projects merely wrap it.
- Maintenance: Commits within the last 90 days; 432 commits in 30 days, 3014 commits in 90 days.
- License: [LGPL-2.1+; GPL-2.0+ once GPL components are enabled](https://github.com/FFmpeg/FFmpeg/blob/23c454005319dee4a5bcae5c370f75fdeb325230/LICENSE.md); Composite/conditional license. Final license depends on compile options and linked components
- Feature verified: 2026-11-12; [Source 1](https://github.com/FFmpeg/FFmpeg/blob/23c454005319dee4a5bcae5c370f75fdeb325230/README.md#L1).

## [yt-dlp](https://github.com/yt-dlp/yt-dlp)

Feature-rich command-line audio/video downloader supporting a large number of sites.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: The underlying extraction CLI for products such as Downvid/VidBee; not a full editing workbench.
- Maintenance: Commits within the last 90 days; 38 commits in 30 days, 75 commits in 90 days.
- License: [Unlicense](https://api.github.com/repos/yt-dlp/yt-dlp/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/yt-dlp/yt-dlp/blob/412e7f0a4b0588fe884a02b344ac66a06538475b/README.md#L16).

## [Streamlink](https://github.com/streamlink/streamlink)

CLI that resolves online livestreams and pipes them to a local player.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: Aimed at stream playback/recording, not general on-demand downloading or editing.
- Maintenance: Commits within the last 90 days; 27 commits in 30 days, 156 commits in 90 days.
- License: [BSD-2-Clause](https://api.github.com/repos/streamlink/streamlink/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/streamlink/streamlink/blob/993f9f1b63bd7a87292e05eda98d461ddc1f62c9/README.md#L13).

## [Downvid](https://github.com/Downvid/downvid)

Cross-platform video download GUI/WebUI built on yt-dlp and FFmpeg.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: Mainly a product-layer wrapper; site extraction comes from yt-dlp, and use must respect platform terms and content rights.
- Maintenance: Commits within the last 90 days; 40 commits in 30 days, 361 commits in 90 days.
- License: [MIT](https://api.github.com/repos/Downvid/downvid/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Downvid/downvid/blob/770bd3e3bf6157f1a2dd0ccb67ea6ce2a4b31807/README.md#L7).

## [VidBee](https://github.com/nexmoe/VidBee)

Downloads media, then runs local transcription, speaker labeling, summarization, translation and media chat.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: Downloading comes from the yt-dlp ecosystem; AI summaries may call a remote model you choose.
- Maintenance: Commits within the last 90 days; 11 commits in 30 days, 51 commits in 90 days.
- License: [MIT](https://api.github.com/repos/nexmoe/VidBee/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/nexmoe/VidBee/blob/6082e2604f0c37d942cdb896040aa0c88b5c527f/README.md#L2).

## [cobalt](https://github.com/imputnet/cobalt)

Ad- and tracker-free media download web app and self-hostable API covering YouTube, TikTok, Instagram and more.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: The monorepo holds api, web and docs, with no public pre-hosted API, so you deploy your own instance; it handles only publicly accessible content, and download/redistribution rights are the user's responsibility; brand and mascot are copyrighted and not covered by the code license.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [AGPL-3.0 (api and the rest) + CC-BY-NC-SA-4.0 (web)](https://github.com/imputnet/cobalt/blob/a636575b09de1fc55d9b8cd98cac88f5f2f16b42/README.md#L59); Composite/conditional license. api and the rest of the repo are AGPL-3.0, web code is non-commercial CC-BY-NC-SA-4.0; brand and mascot are separately copyrighted, allowing only non-commercial hosting of unmodified instances; licenses for components such as ffmpeg/libav.js are separate
- Feature verified: 2026-11-23; [Source 1](https://github.com/imputnet/cobalt/blob/a636575b09de1fc55d9b8cd98cac88f5f2f16b42/README.md#L28) · [Source 2](https://github.com/imputnet/cobalt/blob/a636575b09de1fc55d9b8cd98cac88f5f2f16b42/README.md#L33) · [Source 3](https://github.com/imputnet/cobalt/blob/a636575b09de1fc55d9b8cd98cac88f5f2f16b42/README.md#L45).

## [Lux](https://github.com/iawia002/lux)

Multi-site video download CLI written in Go.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: Extraction coverage and site-update cadence are the main maintenance risks.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://api.github.com/repos/iawia002/lux/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/iawia002/lux/blob/dd00f6d258d80b6684a0b9402d7124e5c18ef42f/README.md#L1).

## [you-get](https://github.com/soimort/you-get)

Python command-line tool downloading media from web pages.

- Category: Download, capture, transcoding and media CLIs; Core candidate.
- Scope boundary: Site coverage and maintenance activity should be compared with yt-dlp separately.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [MIT](https://github.com/soimort/you-get/blob/049548f3f3f35e67ba8d3181c71fdc71d11cf260/LICENSE.txt); Open license verified. Root LICENSE.txt manually verified
- Feature verified: 2026-11-12; [Source 1](https://github.com/soimort/you-get/blob/049548f3f3f35e67ba8d3181c71fdc71d11cf260/README.md#L1).

## [Aurora / AgentEdit-Bench](https://github.com/yeates/Aurora)

Unifies video editing through a tool-using agent and ships AgentEdit-Bench.

- Category: Benchmarks, research and external indexes; Research/benchmark.
- Scope boundary: AgentEdit-Bench scores are not directly comparable with VEFX/EditVerse metrics.
- Maintenance: Commits within the last 90 days; 4 commits in 30 days, 4 commits in 90 days.
- License: [MIT](https://api.github.com/repos/yeates/Aurora/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/yeates/Aurora/blob/2599b748c56b29b67b9be352dc091b8ddf72ae8f/README.md#L3).

## [Awesome AI Video for Creators](https://github.com/sasateguh/awesome-ai-video-for-creators)

Organizes open-source editing, captioning, clipping, voiceover and code-video tools by creator workflow.

- Category: Benchmarks, research and external indexes; Adjacent infrastructure.
- Scope boundary: External star snapshots drift; final data comes from official repos.
- Maintenance: Commits within the last 90 days; 9 commits in 30 days, 15 commits in 90 days.
- License: [CC0-1.0](https://api.github.com/repos/sasateguh/awesome-ai-video-for-creators/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/sasateguh/awesome-ai-video-for-creators/blob/3b88db72b425a89b751b6ea279532e3ae0a3d6f9/README.md#L1).

## [CutCraft Bench](https://github.com/AlibabaResearch/cut-craft-bench)

Benchmarks professional editing-technique execution in multi-shot audio-video generation, with agent baselines.

- Category: Benchmarks, research and external indexes; Research/benchmark.
- Scope boundary: Generation coherence and editability are different metrics and should not be collapsed into one composite score.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 5 commits in 90 days.
- License: [Unverified](https://github.com/AlibabaResearch/cut-craft-bench/blob/df2b35d63822d0832679fe675a274c33c51f7f75/README.md); License unverified. No root license found
- Feature verified: 2026-11-12; [Source 1](https://github.com/AlibabaResearch/cut-craft-bench/blob/df2b35d63822d0832679fe675a274c33c51f7f75/README.md#L6).

## [Awesome Video Editing](https://github.com/devanasolver/awesome-video-editing)

Curates open-source video editing tools, agent skills and usable media.

- Category: Benchmarks, research and external indexes; Adjacent infrastructure.
- Scope boundary: Used as a discovery and coverage baseline, not for capability judgments.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 2 commits in 90 days.
- License: [CC0-1.0](https://github.com/devanasolver/awesome-video-editing/blob/637c0b63835cccaca2c5362baa7e564fee89a6dc/LICENSE); Open license verified. Directory content is CC0
- Feature verified: 2026-11-12; [Source 1](https://github.com/devanasolver/awesome-video-editing/blob/637c0b63835cccaca2c5362baa7e564fee89a6dc/README.md#L1).

## [Awesome AI Video](https://github.com/thoxakihiko/awesome-ai-video)

Curates text/image-to-video models, tools and resources.

- Category: Benchmarks, research and external indexes; Adjacent infrastructure.
- Scope boundary: Includes commercial products and models, so it is not directly an open-source tool list.
- Maintenance: Commits within the last 90 days; 0 commits in 30 days, 3 commits in 90 days.
- License: [CC0-1.0](https://api.github.com/repos/thoxakihiko/awesome-ai-video/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/thoxakihiko/awesome-ai-video/blob/45e9e2bfb3e1e1193e4725ce94bba45d0f342c5a/README.md#L1).

## [VEFX-Bench](https://github.com/Visko-Platform/VEFX-Bench)

Benchmarks instruction following and quality for general video editing and visual effects.

- Category: Benchmarks, research and external indexes; Research/benchmark.
- Scope boundary: Model, data, reward and commercial-API versions must be pinned before comparison.
- Maintenance: No commits for 91–365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/Visko-Platform/VEFX-Bench/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Visko-Platform/VEFX-Bench/blob/a82437764d1e2a2068e5e183075f437d5bd0568b/README.md#L9).

## [EditVerse](https://github.com/adobe-research/EditVerse)

Image/video generation and editing research code plus EditVerseBench.

- Category: Benchmarks, research and external indexes; Restricted license.
- Scope boundary: Research code and data downloads depend on external sources; results need reproduction under the paper's settings.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Adobe Research License (some files)](https://github.com/adobe-research/EditVerse/blob/eeca9ce9f99db2d5c90e775853735025523c9334/LICENSE.md); Source-available, not OSI open source. LICENSE covers only the explicitly listed files; the remaining files are outside that license
- Feature verified: 2026-11-12; [Source 1](https://github.com/adobe-research/EditVerse/blob/eeca9ce9f99db2d5c90e775853735025523c9334/README.md#L1).

## [Video-Bench](https://github.com/Video-Bench/Video-Bench)

Organizes and runs multi-dimensional evaluations of video generation models.

- Category: Benchmarks, research and external indexes; Research/benchmark.
- Scope boundary: A generation benchmark is not timeline-editor or production-system quality.
- Maintenance: No commits for over 365 days; 0 commits in 30 days, 0 commits in 90 days.
- License: [Apache-2.0](https://api.github.com/repos/Video-Bench/Video-Bench/license); Open license verified. Identified via GitHub licenseInfo; model weights, media assets, fonts, third-party dependencies and hosted-service licenses are separate
- Feature verified: 2026-11-12; [Source 1](https://github.com/Video-Bench/Video-Bench/blob/d40b917c4238011aea27d24f85b1e3bf996715bd/README.md#L1).

## [Palmier Pro](https://github.com/palmier-io/palmier-pro)

AI-oriented video editor whose older sources were released under GPLv3.

- Category: Historical and restricted versions; Historical reference.
- Scope boundary: Binaries after v0.7.6 are proprietary with no corresponding public source; treat last-gpl-source as the historical open-source version only.
- Maintenance: Archived / historical; 5 commits in 30 days, 9 commits in 90 days.
- License: [GPL-3.0 (source up to v0.7.6) / later binaries proprietary](https://github.com/palmier-io/palmier-pro/blob/dfc810b561f1692947eb81bbb689e078923ebb59/README.md#L112); Composite/conditional license. last-gpl-source and sources before v0.7.6 are GPLv3; later binaries have no corresponding public source
- Feature verified: 2026-11-12; [Source 1](https://github.com/palmier-io/palmier-pro/blob/dfc810b561f1692947eb81bbb689e078923ebb59/README.md#L2).
