
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
import asyncio
from edge_tts import Communicate
from datetime import datetime
import math

OUT = Path(r"C:\Users\GAMEPOWER\Videos\generated")
OUT.mkdir(parents=True, exist_ok=True)
TTS_DIR = OUT / "tts_edge"
TTS_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT_BOLD = "C:/Windows/Fonts/impact.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"

HERMES_EDGE_TTS_CONFIRMED = True

def hex_to_rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp(a, b, t):
    return a * (1 - t) + b * t

def gradient_bg(c1, c2, t):
    a = np.array(c1, dtype=np.float32)
    b = np.array(c2, dtype=np.float32)
    col = (lerp(a, b, t)).astype(np.uint8)
    arr = np.full((H, W, 3), fill_value=col, dtype=np.uint8)
    return arr

def noise_layer(size, intensity=14):
    return np.random.randint(-intensity, intensity, (size[1], size[0], 3), dtype=np.int16)

def vignette_mask(size, strength=0.4):
    x = np.linspace(-1, 1, size[0])
    y = np.linspace(-1, 1, size[1])
    xx, yy = np.meshgrid(x, y)
    d = np.sqrt(xx**2 + yy**2)
    m = np.clip(1 - d * strength, 0, 1)
    return np.stack([m]*3, axis=-1).astype(np.float32)

def glow_circle(size, center, radius, color, intensity=1.0):
    x = np.linspace(-1, 1, size[0])
    y = np.linspace(-1, 1, size[1])
    xx, yy = np.meshgrid(x, y)
    cx, cy = center
    d = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    m = np.clip(1 - d / max(radius, 1e-6), 0, 1)
    m = np.power(m, 2) * intensity
    m = np.stack([m]*3, axis=-1)
    col = np.array(color, dtype=np.float32) / 255.0
    return m * col

def draw_centered_text(img, text, y, font, color):
    draw = ImageDraw.Draw(img)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
    except TypeError:
        bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    x = (img.width - tw) // 2
    for dx in [-2, 0, 2]:
        for dy in [-2, 0, 2]:
            if dx == 0 and dy == 0:
                continue
            draw.text((x+dx, y+dy), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=color)
    return img

async def tts_save_edge(text, path, voice="en-US-GuyNeural", rate="+5%"):
    if path.exists():
        return path
    try:
        await Communicate(text=text, voice=voice, rate=rate).save(str(path))
        return path
    except Exception as e:
        print("Edge TTS fail:", e)
        return None

def make_frame_factory(scene):
    c1 = hex_to_rgb(scene['c1'])
    c2 = hex_to_rgb(scene['c2'])
    glow_color = hex_to_rgb(scene.get('glow', '#ffffff'))
    font_size = scene.get('size', 72)
    text = scene['text']
    base_y = scene.get('y', 400)
    color = hex_to_rgb(scene.get('color', '#ffffff'))
    try:
        font = ImageFont.truetype(FONT_BOLD, font_size)
    except Exception:
        font = ImageFont.load_default()

    def make_frame(t):
        frame_idx = int(t * FPS)
        phase = (math.sin(frame_idx * 0.02) + 1) * 0.5
        bg = gradient_bg(c1, c2, phase)
        base = bg.astype(np.float32)
        n = noise_layer((W, H), 14)
        base = base + n.astype(np.float32) * 0.06
        base = np.clip(base, 0, 255)

        center = (math.sin(frame_idx * 0.012), math.cos(frame_idx * 0.01))
        glow = glow_circle((W, H), center, 0.55, glow_color, 0.35) * 255
        base = base + glow
        base = np.clip(base, 0, 255)

        v = vignette_mask((W, H), 0.4)
        base = base * v
        base = np.clip(base, 0, 255).astype(np.uint8)

        y_offset = int(math.sin(frame_idx * 0.04 + hash(text) % 100) * 10)
        y = base_y + y_offset

        img = Image.fromarray(base, 'RGB')
        img = draw_centered_text(img, text, y, font, color)
        return np.array(img)
    return make_frame

async def async_tts(text, path):
    loop = asyncio.get_event_loop()
    await loop.create_task(tts_save_edge(text, path))

def build(name, scenes, out_name, voice="en-US-GuyNeural", rate="+5%"):
    clips = []
    audios = []
    t = 0.0
    for sc in scenes:
        dur = float(sc.get('dur', 4))
        txt = sc['text']
        mk = make_frame_factory(sc)
        clip = VideoClip(mk, duration=dur)
        clips.append(clip)

        a_path = TTS_DIR / f"{name}_{abs(hash(txt + voice))}.mp3"
        asyncio.run(tts_save_edge(txt, a_path, voice=voice, rate=rate))
        if a_path.exists():
            try:
                ac = AudioFileClip(str(a_path))
                ac = ac.with_start(t)
                audios.append(ac)
            except Exception as e:
                print("Audio attach fail", a_path, e)
        t += dur

    final = concatenate_videoclips(clips, method="compose")
    if audios:
        try:
            final = final.with_audio(CompositeAudioClip(audios))
        except Exception as e:
            print("Audio composite fail", e)

    out = OUT / out_name
    if out.exists():
        out.unlink()
    final.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
    print({'name': out_name, 'ok': out.exists(), 'size': out.stat().st_size if out.exists() else 0})
    return out

aidynamic_scenes = [
    {'c1':'#0f0a00','c2':'#1a0e00','text':'YOUR BUSINESS IS LOSING MONEY','size':68,'dur':5,'y':280,'color':'#FF6B00','glow':'#ff6b00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'While you are doing paperwork','size':52,'dur':4,'y':420,'color':'#ffffff','glow':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'AI Dynamic automates everything','size':60,'dur':4,'y':360,'color':'#FF6B00','glow':'#ff6b00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'Scheduling, follow-ups, billing — on autopilot','size':46,'dur':7,'y':440,'color':'#ffffff','glow':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'Small businesses using AI grow 3x faster','size':54,'dur':4,'y':400,'color':'#ffffff','glow':'#ffffff'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'FREE CONSULTATION','size':72,'dur':4,'y':360,'color':'#FF6B00','glow':'#ff6b00'},
    {'c1':'#0f0a00','c2':'#1a0e00','text':'aidynamic.pro','size':72,'dur':5,'y':480,'color':'#FF6B00','glow':'#ff6b00'},
]

miami_scenes = [
    {'c1':'#001410','c2':'#000a06','text':'MIAMI BUSINESS OWNERS','size':72,'dur':5,'y':300,'color':'#00D4AA','glow':'#00d4aa'},
    {'c1':'#001410','c2':'#000a06','text':'Your competitors are already using AI','size':52,'dur':4,'y':420,'color':'#FF6B6B','glow':'#ff6b6b'},
    {'c1':'#001410','c2':'#000a06','text':'305 Business gives you the same tools','size':50,'dur':5,'y':380,'color':'#ffffff','glow':'#ffffff'},
    {'c1':'#001410','c2':'#000a06','text':'without the enterprise price','size':48,'dur':4,'y':460,'color':'#ffffff','glow':'#ffffff'},
    {'c1':'#001410','c2':'#000a06','text':'Old Way: paperwork, missed calls, manual','size':44,'dur':6,'y':380,'color':'#FF6B6B','glow':'#ff6b6b'},
    {'c1':'#001410','c2':'#000a06','text':'New Way: automated, responsive, growing','size':44,'dur':6,'y':440,'color':'#00D4AA','glow':'#00d4aa'},
    {'c1':'#001410','c2':'#000a06','text':'305business.llc','size':72,'dur':5,'y':500,'color':'#00D4AA','glow':'#00d4aa'},
]

cyber_scenes = [
    {'c1':'#000f00','c2':'#051400','text':'SYSTEM ONLINE','size':80,'dur':5,'y':340,'color':'#00FF41','glow':'#00ff41'},
    {'c1':'#000f00','c2':'#051400','text':'RTX 5070 Ti — 16GB VRAM','size':56,'dur':4,'y':420,'color':'#00FF41','glow':'#00ff41'},
    {'c1':'#000f00','c2':'#051400','text':'Local AI, no cloud costs','size':52,'dur':4,'y':400,'color':'#00FF41','glow':'#00ff41'},
    {'c1':'#000f00','c2':'#051400','text':'Effects: noise, scanline, vignette, glitch','size':44,'dur':6,'y':380,'color':'#00FF41','glow':'#00ff41'},
    {'c1':'#000f00','c2':'#051400','text':'Faceless videos in minutes','size':60,'dur':4,'y':420,'color':'#00FF41','glow':'#00ff41'},
    {'c1':'#000f00','c2':'#051400','text':'HERMES AGENT','size':84,'dur':5,'y':460,'color':'#00FF41','glow':'#00ff41'},
]

if __name__ == '__main__':
    build('aidynamic', aidynamic_scenes, 'aidynamic_promo.mp4')
    build('miami', miami_scenes, '305business_promo.mp4')
    build('cyber', cyber_scenes, 'cyberpunk_test.mp4')
