import json, requests

def hf(model):
    r = requests.get(f"https://huggingface.co/api/models/{model}", timeout=30)
    if r.status_code != 200:
        print(model, "HTTP", r.status_code)
        return None
    d = r.json()
    files = [(f["rfilename"], f.get("size")) for f in d.get("siblings", [])]
    ggufs = [f for f in files if f[0].lower().endswith(".gguf")]
    print(f"{model}: id={d.get('id')} gated={d.get('gated')} downloads={d.get('downloads')} likes={d.get('likes')} lastModified={d.get('lastModified','')[:10]}")
    for n, s in ggufs[:14]:
        print("   ", n, f"{round(s/1e9,2)} GB" if s else "")
    return d

for m in ["agosh/LTX-2.5-Comfy-GGUF", "Lightricks/LTX-2.5", "KandinskyLab/Kandinsky-6"]:
    hf(m)
