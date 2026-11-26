import requests, json
reg = requests.get("https://remocn.dev/r/registry.json", timeout=60).json()["items"]
libs = [i["name"] for i in reg if i.get("type") == "registry:lib"]
print("lib items:", libs)
# show deps for counter-reveal and lib file targets
for name in ["counter-reveal"] + libs[:12]:
    d = requests.get(f"https://remocn.dev/r/{name}.json", timeout=30)
    if d.status_code != 200:
        print(name, "->", d.status_code); continue
    j = d.json()
    print(f"\n{name} type={j.get('type')} deps={j.get('dependencies')} regdeps={j.get('registryDependencies')}")
    for f in j.get("files", []):
        print("   ", f.get("path"), "->", f.get("target"), len(f.get("content","")), "chars")
