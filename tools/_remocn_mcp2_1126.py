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
    return r, time.time() - t0, parse_sse(r.text)

r, dt, msgs = call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "hermes", "version": "0.1"}})
sid = r.headers.get("Mcp-Session-Id")
requests.post(url, headers=H, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=20).close()

r, dt, msgs = call("tools/call", {"name": "get_component", "arguments": {"name": "counter-reveal"}}, 4, sid)
print(f"get_component HTTP {r.status_code} in {dt:.2f}s")
if msgs and "result" in msgs[0]:
    txt = "\n".join(c.get("text", "") for c in msgs[0]["result"].get("content", []))
    print("chars:", len(txt)); print(txt[:1200])
else:
    print(r.text[:600])

# plan_video tool probe
r, dt, msgs = call("tools/call", {"name": "plan_video",
    "arguments": {"brief": "20-second teaser for a lab force-plate dashboard, clean tech vibe"}}, 5, sid)
print(f"\nplan_video HTTP {r.status_code} in {dt:.2f}s")
if msgs and "result" in msgs[0]:
    txt = "\n".join(c.get("text", "") for c in msgs[0]["result"].get("content", []))
    print("chars:", len(txt)); print(txt[:1500])
else:
    print(r.text[:600])

# registry endpoints
for u in ["https://remocn.dev/r/registry.json", "https://remocn.dev/registry.json",
          "https://remocn.dev/r/counter-reveal.json",
          "https://remocn.dev/docs/typography/counter-reveal.md"]:
    try:
        rr = requests.get(u, timeout=25)
        print(f"\nGET {u} -> {rr.status_code} {len(rr.content)}B {rr.headers.get('content-type')}")
        if rr.status_code == 200 and len(rr.content) < 3000:
            print(rr.text[:400].replace("\n", " "))
    except Exception as e:
        print(u, "ERR", type(e).__name__, e)
