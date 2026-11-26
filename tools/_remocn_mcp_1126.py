import json, time, requests

url = "https://remocn.dev/mcp"
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

def parse_sse(text):
    out = []
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                out.append(json.loads(line[5:].strip()))
            except Exception:
                pass
    return out

def call(method, params=None, id=1, sid=None):
    h = dict(H)
    if sid:
        h["Mcp-Session-Id"] = sid
    body = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        body["params"] = params
    t0 = time.time()
    r = requests.post(url, headers=h, json=body, timeout=60)
    dt = time.time() - t0
    return r, dt, parse_sse(r.text)

r, dt, msgs = call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "hermes", "version": "0.1"}})
sid = r.headers.get("Mcp-Session-Id")
requests.post(url, headers=H, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=20).close()

r, dt, msgs = call("tools/list", {}, 2, sid)
tools = msgs[0]["result"]["tools"] if msgs else []
print("TOOLS:", [(t["name"], t.get("title")) for t in tools])

# real semantic search: a brief from this user's actual workload
q = {"query": "lab test explainer with big numbers and a clean chart reveal", "vibe": "clean", "maxLength": 150}
r, dt, msgs = call("tools/call", {"name": "search_components", "arguments": q}, 3, sid)
print(f"\nsearch_components HTTP {r.status_code} in {dt:.2f}s")
if msgs and "result" in msgs[0]:
    res = msgs[0]["result"]
    content = res.get("content", [])
    txt = "\n".join(c.get("text", "") for c in content)
    print("isError:", res.get("isError"), "| chars:", len(txt))
    print(txt[:2500])
else:
    print(r.text[:800])

# get_component on the first name we see
