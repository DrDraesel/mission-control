import requests
for u in ["https://remocn.dev/llms.txt", "https://remocn.dev/registry.json",
          "https://remocn.dev/r/registry.json", "https://remocn.dev/api/registry",
          "https://remocn.dev/docs/getting-started/agent-skill.md"]:
    try:
        r = requests.get(u, timeout=25)
        print(f"{u} -> {r.status_code} {len(r.content)}B")
        if r.status_code == 200 and u.endswith("llms.txt"):
            print(r.text[:1200])
    except Exception as e:
        print(u, "ERR", e)
