import io, re

H = r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-history.md"
A = r"C:\Users\GAMEPOWER\AppData\Local\hermes\skills\research\mission-control-daily-research\references\query-yield-archive-2026-10a.md"

NEW = (
    "- → **11-23 DONE**: rotation applied (`content-repurposing-topic` kept one more run; `video-editing-topic` retired after a 2nd 0-new run → "
    "**`topic:motion-design`**; `ai-clip-generator-topic` parked (6 raw-new / 0 usable) → **`topic:explainer-video`**). Sweep 40 queries / 474 rows / "
    "**6 raw-new, 3 usable** (468 of 474 already ledgered = 15th confirmation). `motion-design` (1,202 repos) = 4 new / 2 usable: `nolangz/pixel2motion` "
    "2,706* MIT (raster logo → SVG → animated HTML/GIF/video + motion-QA evidence) and `oil-oil/oil-motion` 2,965* MIT (scroll/mouse web-animation skill); "
    "dead weight `ant-design/ant-motion` (archived 2022) + `andremion/Music-Player` (Android UI demo). `explainer-video` (332 repos) = 1 new "
    "(`HeyChengC/wallstreet-explainer` 1,054*, MIT + sample-asset carve-out → NOASSERTION). KEEP `motion-design` one more run; park `explainer-video`+`content-repurposing`. "
    "**The value was the ZanePoe index, not the sweep**: `docs/projects.md` produced 10 LEDGERED-BUT-NEVER-EVALUATED repos in one read — video-use 27.5k→31.5k, "
    "ffmpeg-skill 9.5k→10.1k (**MEASURED**), OpenKatana 22→85 (**MEASURED**), openfilm 9.1k (Win exe 366 MB), rea-video 12.5k, Jellyfish 7.3k, Clypra 3.4k (Win exe+msi), "
    "OpenChatCut 3.3k (Win exe 740 MB), openreel 6.4k (**NO Windows asset**), CozyClay 1.1k→2.1k (**renamed NomaDamas→HaD0Yun**). Ledger 2,237→**2,245 (+9: 7 sweep + 2 web)**. "
    "Next (11-24): `content-repurposing-topic` out → **`topic:video-translation`** or **`topic:b-roll`**; keep motion-design + explainer-video one more run."
)

hist = io.open(H, encoding="utf-8").read()
head, *entries = re.split(r"(?m)^(?=- → )", hist)
tail = ""
if entries and not entries[-1].strip().startswith("- →"):
    tail = entries.pop()

archived = []
budget = 97000 - len(NEW)
while len(head) + sum(len(e) for e in entries) > budget and len(entries) > 1:
    archived.append(entries.pop())  # oldest at the end

new_hist = head + NEW + "\n" + "".join(entries)
io.open(H, "w", encoding="utf-8", newline="\n").write(new_hist)

if archived:
    arch = io.open(A, encoding="utf-8").read()
    block = "\n\n<!-- archived 2026-11-23 to keep query-yield-history.md under 100k -->\n\n" + "".join(reversed(archived))
    io.open(A, "w", encoding="utf-8", newline="\n").write(arch.rstrip() + block)
    print("archived entries:", len(archived))

print("history chars:", len(new_hist), "archive chars:", len(io.open(A, encoding="utf-8").read()))
