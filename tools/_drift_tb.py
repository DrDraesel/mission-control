import json, re, urllib.request

LOG = r"C:/Users/GAMEPOWER/AppData/Local/Temp/drift/drift-headless.log"
tok = re.search(r"token\s+([0-9a-f]{16,})", open(LOG, encoding="utf-8", errors="replace").read()).group(1)
URL = "http://127.0.0.1:4731/mcp"

def call(name, args=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": args or {}}}).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream",
                                          "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read().decode()
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    return json.loads(raw)["result"]["content"][0].get("text", "")

for tb in ["text", "project"]:
    out = call("toolbox", {"name": tb})
    try:
        d = json.loads(out)
        names = [t.get("name") for t in d.get("ops", d.get("tools", []))]
        print(tb, "->", names)
        print(json.dumps(d)[:400])
    except Exception:
        print(tb, "RAW:", out[:800])
    print()
