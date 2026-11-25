"""Real archive.org run through broll-mcp (11-25), attempt 2: strict schema (no 'limit'),
then search -> inspect_item. Kills the process tree at the end."""
import json
import subprocess
import time

CMD = ["uvx", "--from", "git+https://github.com/edigeh/broll-mcp", "broll-mcp"]


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


def call(p, mid, name, args, timeout=240):
    t0 = time.time()
    send(p, {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
             "params": {"name": name, "arguments": args}})
    r = read_until_id(p, mid, timeout=timeout)
    return r, time.time() - t0


p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, bufsize=0)
try:
    send(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "hermes-probe", "version": "1"}}})
    read_until_id(p, 1, timeout=120)
    send(p, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    r, dt = call(p, 3, "search_footage",
                 {"brief": "empty gym treadmill running workout b-roll",
                  "filters": {"max_tier": 2, "license": "commercial_ok"}})
    print("search_s", round(dt, 2))
    sc = (r or {}).get("result", {}).get("structuredContent")
    print("STRUCTURED:", json.dumps(sc)[:3000] if sc else "none")
    for c in (r or {}).get("result", {}).get("content", [])[:3]:
        print("CONTENT_TYPE:", c.get("type"))
        if c.get("type") == "text":
            print("TEXT:", c["text"][:1200])

    ident = None
    if isinstance(sc, dict):
        for k in ("results", "items", "footage"):
            if isinstance(sc.get(k), list) and sc[k]:
                first = sc[k][0]
                if isinstance(first, dict):
                    ident = first.get("identifier") or first.get("id")
                    print("TOP:", json.dumps(first)[:600])
                    break
    if ident:
        r2, dt2 = call(p, 4, "inspect_item", {"identifier": ident})
        print("inspect_s", round(dt2, 2))
        sc2 = (r2 or {}).get("result", {}).get("structuredContent")
        print("INSPECT:", json.dumps(sc2)[:1500] if sc2 else "none")
        for c in (r2 or {}).get("result", {}).get("content", [])[:3]:
            print("INSPECT_TYPE:", c.get("type"))
finally:
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                       capture_output=True, timeout=30)
    except Exception as e:
        print("kill note:", e)
