import json, re, urllib.request, time, os

LOG = r"C:/Users/GAMEPOWER/AppData/Local/Temp/drift/drift-headless.log"
tok = re.search(r"token\s+([0-9a-f]{16,})", open(LOG, encoding="utf-8", errors="replace").read()).group(1)
URL = "http://127.0.0.1:4731/mcp"
OUT = r"C:/Users/GAMEPOWER/projects/mission-control/research/daily/2026-11-16-drift-mcp-test.mp4"

def call(name, args=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": args or {}}}).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream",
                                          "Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read().decode()
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    return json.loads(raw)["result"]["content"][0].get("text", "")

t0 = time.time()
print("EXPORT:", call("export_video", {"path": OUT, "height": 1920, "fps": 30})[:500])
for i in range(120):
    time.sleep(2)
    st = call("export_status", {})
    try:
        d = json.loads(st)
    except Exception:
        print("status raw", st[:200]); continue
    if i % 3 == 0:
        print(f"  t={time.time()-t0:5.1f}s", json.dumps(d)[:220])
    if not d.get("active") and (d.get("done") or d.get("path") or d.get("progress") == 1 or d.get("ok") and not d.get("active")):
        if not d.get("active"):
            print("FINAL:", json.dumps(d)[:400])
            break
print("exit loop after", round(time.time() - t0, 1), "s")
print("exists:", os.path.exists(OUT), os.path.getsize(OUT) if os.path.exists(OUT) else 0, "bytes")
