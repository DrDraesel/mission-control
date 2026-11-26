import json, time, requests

# 1) hosted MCP: initialize + tools/list over Streamable HTTP (JSON-RPC)
url = "https://remocn.dev/mcp"
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

def rpc(payload, sid=None):
    h = dict(H)
    if sid:
        h["Mcp-Session-Id"] = sid
    t0 = time.time()
    r = requests.post(url, headers=h, json=payload, timeout=45)
    dt = time.time() - t0
    return r, dt

init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "hermes-probe", "version": "0.1"}}}
t0 = time.time()
try:
    r, dt = rpc(init)
    print("initialize HTTP", r.status_code, f"{dt:.2f}s")
    print("session:", r.headers.get("Mcp-Session-Id"))
    print("body:", r.text[:600].replace("\n", " "))
    sid = r.headers.get("Mcp-Session-Id")
    if r.status_code == 200:
        # notifications/initialized then tools/list
        requests.post(url, headers={**H, "Mcp-Session-Id": sid}, timeout=20,
                      json={"jsonrpc": "2.0", "method": "notifications/initialized"}).close()
        r2, dt2 = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
        print("tools/list HTTP", r2.status_code, f"{dt2:.2f}s")
        txt = r2.text
        print("tools raw:", txt[:900].replace("\n", " "))
except Exception as e:
    print("MCP ERR", type(e).__name__, e)

# 2) shadcn registry item for one component
for name in ["blur-reveal", "typography"]:
    for u in [f"https://remocn.dev/r/{name}.json"]:
        try:
            rr = requests.get(u, timeout=30)
            print(f"\nGET {u} -> {rr.status_code}, {len(rr.content)} bytes, ctype {rr.headers.get('content-type')}")
            if rr.status_code == 200:
                d = rr.json()
                print("  name:", d.get("name"), "| type:", d.get("type"), "| deps:", d.get("dependencies"))
                files = d.get("files") or []
                print("  files:", [f.get("path") for f in files])
                if files:
                    src = files[0].get("content", "")
                    print("  source head:", src[:300].replace("\n", " "))
        except Exception as e:
            print(u, "ERR", e)
