import inspect, json, subprocess, sys

try:
    import text_fx
except Exception as e:
    print("IMPORT_FAIL", e)
    sys.exit(0)

print("version:", getattr(text_fx, "__version__", "?"))
print("dir:", [n for n in dir(text_fx) if not n.startswith("_")][:40])

# find render entry points and their signatures
for name in ("render_overlay", "render", "TextEffectConfig"):
    obj = getattr(text_fx, name, None)
    if obj is None:
        continue
    try:
        print(f"--- {name}{inspect.signature(obj)}")
    except Exception:
        print(f"--- {name} (no signature)")
    if name == "TextEffectConfig":
        import dataclasses
        try:
            print("fields:", [f.name for f in dataclasses.fields(obj)])
        except Exception:
            print("annotations:", getattr(obj, "__annotations__", {}).keys())

# look for alpha / codec / pix_fmt knobs
src = ""
try:
    import text_fx.render as r
    src = inspect.getsource(r)
except Exception as e:
    print("no render module:", e)

for kw in ("yuva420p", "alpha", "codec", "libvpx", "pix_fmt", "transparent"):
    hits = [ln.strip() for ln in src.splitlines() if kw in ln][:6]
    if hits:
        print(f"== {kw} ==")
        for h in hits:
            print("   ", h[:160])
