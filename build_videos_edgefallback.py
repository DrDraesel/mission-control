
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
from gtts import gTTS
from datetime import datetime

OUT = Path(r"C:\Users\GAMEPOWER\Videos\generated")
OUT.mkdir(parents=True, exist_ok=True)
TTS_DIR = OUT / "tts_gtts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT_BOLD = "C:/Windows/Fonts/impact.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def gradient_bg(size, c1, c2):
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    top = np.array(c1, dtype=np.float32)
    bot = np.array(c2, dtype=np.float32)
    for y in range(size[1]):
        t = y / max(1, size[1]-1)
        a[y, :, :] = (top*(1-t) + bot*t).astype(np.uint8)
    return a

def noise(size, intensity=18, seed=0):
    rng = np.random.default_rng(seed)
    n = rng.integers(-intensity, intensity, (size[1], size[0], 3))
    return n.astype(np.int16)

def vignette_mask(size, strength=0.38):
    x = np.linspace(-1, 1, size[0])
    y = np.linspace(-1, 1, size[1])
    xx, yy = np.meshgrid(x, y)
    d = np.sqrt(xx**2 + yy**2)
    m = np.clip(1 - d*strength, 0, 1)
    return np.stack([m]*3, axis=-1).astype(np.float32)

def tts_save(text, path):
    if path.exists():
        return path
    try:
        gTTS(text=text, lang="en", slow=False).save(str(path))
        return path
    except Exception as e:
        print("tts fail:", e)
        return None

def build_video(name, scenes, out_name):
    clips = []
    audios = []
    t = 0.0
    for sc in scenes:
        bg = np.full((H, W, 3), fill_value=hex_to_rgb(sc['bg']), dtype=np.uint8) if sc.get('bg') else gradient_bg((W, H), hex_to_rgb(sc['c1']), hex_to_rgb(sc['c2']))
        base = bg.astype(np.float32)
        n = noise((W, H), 16, hash((name, sc['text'])) & 0xffffffff)
        base = np.clip(base + n.astype(np.float32)*0.07, 0, 255)
        v = vignette_mask((W, H), 0.4)
        base = np.clip(base * v, 0, 255).astype(np.uint8)

        img = Image.fromarray(base, 'RGB')
        draw = ImageDraw.Draw(img)
        txt = sc['text']
        font_size = sc.get('size', 72)
        try:
            font = ImageFont.truetype(FONT_BOLD, font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), txt, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (W-tw)//2
        y = sc.get('y', (H-th)//2)

        for dx in [-2,0,2]:
            for dy in [-2,0,2]:
                if dx == 0 and dy == 0:
                    continue
                draw.text((x+dx, y+dy), txt, font=font, fill=(0,0,0,200))
        draw.text((x, y), txt, font=font, fill=hex_to_rgb(sc.get('color','#ffffff')))

        frame = np.array(img)
        dur = float(sc.get('dur', 4))
        clip = ImageClip(frame).with_duration(dur)

        a_path = TTS_DIR / f"{name}_{abs(hash(txt))}.mp3"
        tts_save(txt, a_path)
        if a_path.exists():
            try:
                ac = AudioFileClip(str(a_path))
                ac = ac.with_start(t)
                audios.append(ac)
            except Exception as e:
                print('audio attach fail', a_path, e)

        clips.append(clip)
        t += dur

    final = concatenate_videoclips(clips, method="compose")
    if audios:
        try:
            final = final.with_audio(CompositeAudioClip(audios))
        except Exception as e:
            print('audio composite fail', e)
    out = OUT / out_name
    if out.exists():
        out.unlink()
    final.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
    print({'name': out_name, 'ok': out.exists(), 'size': out.stat().st_size if out.exists() else 0})
    return out

aidynamic_scenes = [
    {'c1':'#0f0a00','c2':'#1a0e00','text':'YOUR BUSINESS IS LOSING MONEY','size':68,'dur':5,'y':280,'color':'#FF6B00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'While you are doing paperwork','size':52,'dur':4,'y':420,'color':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'AI Dynamic automates everything','size':60,'dur':4,'y':360,'color':'#FF6B00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'Scheduling, follow-ups, billing — on autopilot','size':46,'dur':7,'y':440,'color':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'Small businesses using AI grow 3x faster','size':54,'dur':4,'y':400,'color':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'FREE CONSULTATION','size':72,'dur':4,'y':360,'color':'#FF6B00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'aidynamic.pro','size':72,'dur':5,'y':480,'color':'#FF6B00'},
]

miami_scenes = [
    {'c1':'#001410','c2':'#000a06','text':'MIAMI BUSINESS OWNERS','size':72,'dur':5,'y':300,'color':'#00D4AA'},
    {'c1':'#001410','c2':'#000a06','text':'Your competitors are already using AI','size':52,'dur':4,'y':420,'color':'#FF6B6B'},
    {'c1':'#001410','c2':'#000a06','text':'305 Business gives you the same tools','size':50,'dur':5,'y':380,'color':'#ffffff'},
    {'c1':'#001410','c2':'#000a06','text':'without the enterprise price','size':48,'dur':4,'y':460,'color':'#ffffff'},
    {'c1':'#001410','c2':'#000a06','text':'Old Way: paperwork, missed calls, manual','size':44,'dur':6,'y':380,'color':'#FF6B6B'},
    {'c1':'#001410','c2':'#000a06','text':'New Way: automated, responsive, growing','size':44,'dur':6,'y':440,'color':'#00D4AA'},
    {'c1':'#001410','c2':'#000a06','text':'305business.llc','size':72,'dur':5,'y':500,'color':'#00D4AA'},
]

cyber_scenes = [
    {'c1':'#000f00','c2':'#051400','text':'SYSTEM ONLINE','size':80,'dur':5,'y':340,'color':'#00FF41'},
    {'c1':'#000f00','c2':'#051400','text':'RTX 5070 Ti — 16GB VRAM','size':56,'dur':4,'y':420,'color':'#00FF41'},
    {'c1':'#000f00','c2':'#051400','text':'Local AI, no cloud costs','size':52,'dur':4,'y':400,'color':'#00FF41'},
    {'c1':'#000f00','c2':'#051400','text':'Effects: noise, scanline, vignette, glitch','size':44,'dur':6,'y':380,'color':'#00FF41'},
    {'c1':'#000f00','c2':'#051400','text':'Faceless videos in minutes','size':60,'dur':4,'y':420,'color':'#00FF41'},
    {'c1':'#000f00','c2':'#051400','text':'HERMES AGENT','size':84,'dur':5,'y':460,'color':'#00FF41'},
]

if __name__ == '__main__':
    build_video('aidynamic', aidynamic_scenes, 'aidynamic_promo.mp4')
    build_video('miami', miami_scenes, '305business_promo.mp4')
    build_video('cyber', cyber_scenes, 'cyberpunk_test.mp4')
