"""Real archive.org run through broll-mcp (11-25): initialise -> tools/list -> search_footage.
Kills the process tree at the end (plain terminate hangs on Windows)."""
import json
import subprocess
import sys
import time

CMD = [
    "uvx", "--from", "git+https://github.com/edigeh/broll-mcp", "broll-mcp",
]


def send(p, obj):
    p.stdin.write((json.dumps(obj) + "\n").encode())
    p.stdin.flush()


def read_until_id(p, want_id, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        line = p.stdout.readline()
        if not line:
            return None
        try:
            msg = json.loads(line.decode("utf-8", "replace"))
        except Exception:
            continue
        if msg.get("id") == want_id:
            return msg
    return None


p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, bufsize=0)
try:
    t0 = time.time()
    send(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "hermes-probe", "version": "1"}}})
    r = read_until_id(p, 1, timeout=120)
    print("initialize_ms", int((time.time() - t0) * 1000))
    print("server:", json.dumps((r or {}).get("result", {}).get("serverInfo", {}))[:300])
    send(p, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    send(p, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    r = read_until_id(p, 2, timeout=60)
    tools = (r or {}).get("result", {}).get("tools", [])
    print("tools:", [t["name"] for t in tools])
    schema = next((t for t in tools if t["name"] == "search_footage"), None)
    if schema:
        print("search_footage schema:", json.dumps(schema.get("inputSchema", {}))[:800])

    # REAL archive.org call
    t0 = time.time()
    send(p, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "search_footage",
                        "arguments": {"brief": "empty gym treadmill running workout b-roll",
                                      "limit": 4}}})
    r = read_until_id(p, 3, timeout=240)
    dt = time.time() - t0
    print("search_ms", int(dt * 1000))
    if r is None:
        print("TIMEOUT waiting for search")
    else:
        if "error" in r:
            print("ERROR", json.dumps(r["error"])[:600])
        else:
            res = r["result"]
            for item in res.get("content", []):
                if item.get("type") == "text":
                    print("TEXT:", item["text"][:2500])
                else:
                    print("CONTENT_TYPE:", item.get("type"))
            if res.get("structuredContent"):
                print("STRUCTURED:", json.dumps(res["structuredContent"])[:2500])
finally:
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                       capture_output=True, timeout=30)
    except Exception as e:
        print("kill note:", e)
