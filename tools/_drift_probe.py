import json, re, urllib.request, sys

LOG = r"C:/Users/GAMEPOWER/AppData/Local/Temp/drift/drift-headless.log"
txt = open(LOG, encoding="utf-8", errors="replace").read()
tok = re.search(r"token\s+([0-9a-f]{16,})", txt).group(1)
URL = "http://127.0.0.1:4731/mcp"
print("token", tok[:12], "...")

def call(name, args=None, id=1):
    body = json.dumps({"jsonrpc": "2.0", "id": id, "method": "tools/call",
                       "params": {"name": name, "arguments": args or {}}}).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream",
                                          "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    # streamable-http may return SSE framing
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    d = json.loads(raw)
    c = d["result"]["content"][0]
    return c.get("text", "")

cat = call("catalog", {"brief": True})
print("catalog len", len(cat))
print(cat[:600])
print()

for q in ["canvas", "title", "text clip", "background", "export"]:
    out = call("search", {"q": q})
    print("== search", q, "==")
    print(out[:700])
    print()
