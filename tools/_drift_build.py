import json, re, urllib.request, time

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
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read().decode()
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    return json.loads(raw)["result"]["content"][0].get("text", "")

ops = [
    {"tool": "set_project_setup", "args": {"width": 1080, "height": 1920, "fps": 30}},
    {"tool": "set_background", "args": {"kind": "color", "color": "#0B1220"}},
    {"tool": "add_text", "args": {"text": "MISSION CONTROL", "at": 0}},
]
print("APPLY:", call("apply", {"ops": ops})[:900])
print()
print("INSPECT:", call("inspect", {"clips": True, "detail": True})[:1400])
