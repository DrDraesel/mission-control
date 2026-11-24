import re
txt = open('research/daily/_tmp-curated.md', encoding='utf-8').read()
# split on ## headings
blocks = re.split(r'\n## ', txt)
want = ['OpenMontageInc','win4r/video-director','video-to-shorts-skill','claude-code-video-toolkit',
        'hyperframes-motion-library','video-editing-skill','narrator-ai-cli-skill','OpenClip-App',
        'mcp-video-editing','lume/lume','drawcall/Proton','gifenc','cut-craft-bench','EditVerse',
        'VidBee','comecut','broll-mcp','hand-drawn-video-prompts','Wan2.2','LTX-Video','Open-Sora','mochi']
for b in blocks:
    head = b.split('\n',1)[0]
    for w in want:
        if w.lower() in head.lower():
            print('## ' + b.strip()[:900])
            print('-'*60)
            break
