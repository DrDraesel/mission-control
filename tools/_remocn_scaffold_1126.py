import json, pathlib, requests

root = pathlib.Path(r"C:\Users\GAMEPOWER\AppData\Local\hermes\cache\scratch\remocn-test")
items = ["counter-reveal", "glide", "frame-rate", "timeline"]
written = []
for name in items:
    d = requests.get(f"https://remocn.dev/r/{name}.json", timeout=40).json()
    for f in d.get("files", []):
        target = f.get("target") or f["path"]
        p = root / "src" / target
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"], encoding="utf-8")
        written.append(f"{name}: src/{target} ({len(f['content'])} chars)")
print("\n".join(written))

(root / "tsconfig.json").write_text(json.dumps({
    "compilerOptions": {
        "target": "ES2020", "module": "ESNext", "jsx": "react-jsx",
        "moduleResolution": "bundler", "strict": False, "skipLibCheck": True,
        "esModuleInterop": True, "allowJs": True, "noEmit": True,
        "baseUrl": ".", "paths": {"@/*": ["src/*"]}
    },
    "include": ["src"]
}, indent=2), encoding="utf-8")

(root / "src" / "index.ts").write_text(
    'import { registerRoot } from "remotion";\nimport { RemotionRoot } from "./Root";\nregisterRoot(RemotionRoot);\n',
    encoding="utf-8")

(root / "src" / "Root.tsx").write_text('''import { Composition } from "remotion";
import { CounterReveal } from "@/components/remocn/counter-reveal";

const Scene = () => (
  <CounterReveal word="Beta" line="Out now." accent="#3B5BFD" />
);

export const RemotionRoot = () => (
  <Composition
    id="CounterReveal"
    component={Scene}
    durationInFrames={128}
    fps={30}
    width={1280}
    height={720}
  />
);
''', encoding="utf-8")
print("wrote tsconfig, index.ts, Root.tsx")
