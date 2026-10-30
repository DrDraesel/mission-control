
import os, sys, webbrowser, textwrap, subprocess
from urllib.parse import quote_plus

ORG_1 = "aidynamic.pro"
ORG_2 = "305business.llc"
ROOT = os.getcwd()
os.makedirs("content", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("research", exist_ok=True)
os.makedirs("dashboard", exist_ok=True)

TOPICS = {
    "cto": [
        "autonomous agents",
        "agent observability",
        "local first video",
        "faceless generation",
        "open source AI automation stack",
        "self hosted video generation",
        "image generation local GPU",
        "RAG for video production",
        "AI coding agents",
        "AI CTO stack 2026",
    ],
    "marketer": [
        "faceless video advertising",
        "social media faceless shorts",
        "ai video marketing automation",
        "promotional video ai generators",
        "video for small business advertising",
        "ai youtube shorts automation",
        "instagram reels automation",
        "tiktok ai faceless content",
        "video marketing python automation",
        "ad content generation open source",
    ],
    "designer": [
        "motion design ai assets",
        "open source video graphics templates",
        "gradient motion backgrounds",
        "hero video background generator",
        "cinematic video generator",
        "typography animation generator",
        "ai driven video transitions",
        "open source c4d alternatives",
        "blender ai video generation",
        "social media motion design system",
    ],
}

CATEGORIES = list(TOPICS.keys())


def open_tabs(urls):
    first = True
    for u in urls:
        if first:
            webbrowser.open(u, new=0)
            first = False
        else:
            webbrowser.open_new_tab(u)


def gather(role, company):
    print(f"\n=== {role.upper()} | {company} ===\n")
    queries = TOPICS[role]
    urls = [f"https://github.com/search?q={quote_plus(q)}&type=repositories" for q in queries[:5]]
    subprocess.run("start " + " ".join(urls), shell=True)

    # Write per comapny folders
    odir = os.path.join("research", company, role)
    os.makedirs(odir, exist_ok=True)

    # Build a short 10 line mission file per role
    path = os.path.join(odir, "mission.md")
    mission = textwrap.dedent(
        f"""
    # {role.title()} Mission — {company}
    
    ## Objective
    Find and validate open-source tools that directly reduce timeline for creating high-performance advertising video content.
    Filter for usable, maintained, Windows-friendly stacks where possible.
    
    ## Daily Watch List (Auto-Generated Links)
    1. {TOPICS[role][0]}: https://github.com/search?q={quote_plus(TOPICS[role][0])}&type=repositories
    2. {TOPICS[role][1]}: https://github.com/search?q={quote_plus(TOPICS[role][1])}&type=repositories
    3. {TOPICS[role][2]}: https://github.com/search?q={quote_plus(TOPICS[role][2])}&type=repositories
    4. {TOPICS[role][3]}: https://github.com/search?q={quote_plus(TOPICS[role][3])}&type=repositories
    5. {TOPICS[role][4]}: https://github.com/search?q={quote_plus(TOPICS[role][4])}&type=repositories
    """
    ).strip()
    open(path, "w", encoding="utf-8").write(mission + "\n")
    print("Created research file:", path)


if __name__ == "__main__":
    print("Choose target company: 1=aidynamic.pro  2=305business.llc  B=both")
    ch = input("Input: ").strip().lower()
    company = (
        ORG_1
        if ch == "1"
        else ORG_2
        if ch == "2"
        else f"{ORG_1} + {ORG_2}"
    )

    roles = CATEGORIES if ch.lower() in ("b", "both", "2", "1", "") else CATEGORIES
    for r in roles:
        gather(r, company)

    print("\nOpening browser tabs for each agent. Keep them open during a quick pass and save approved suggestions into data/stacks.json")
