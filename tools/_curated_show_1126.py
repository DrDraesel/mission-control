import pathlib

cur = pathlib.Path(r"C:\Users\GAMEPOWER\projects\mission-control\research\daily\2026-11-26-curated-projects.md").read_text(encoding="utf-8", errors="replace")
blocks = cur.split("\n## ")
want = ["atlas-explainer", "OpenClip", "Remocn", "mcp-video-editing", "manju-laoli",
        "video-editing-skill", "video-to-shorts", "cut-craft-bench", "EditVerse",
        "lume", "Aurora", "openfilm", "OpenDirector"]
for b in blocks:
    head = b.split("\n")[0]
    if any(w.lower() in head.lower() for w in want):
        print("##", b[:1100].strip())
        print("\n" + "=" * 90 + "\n")
