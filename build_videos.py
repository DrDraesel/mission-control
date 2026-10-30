
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
from datetime import datetime

OUT = Path(r"C:\Users\GAMEPOWER\Videos\generated")
OUT.mkdir(parents=True, exist_ok=True)
TTS_DIR = OUT / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT_BOLD = "C:/Windows/Fonts/impact.ttf"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def text_frame(size, txt, y, font_size=64, color=(255,255,255), bg=(10,10,10)):
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_BOLD, font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), txt, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size[0] - tw) // 2
    draw.text((x, int(y)), txt, font=font, fill=color)
    return np.array(img)

def solid_frame(size, color):
    return np.full((size[1], size[0], 3), fill_value=color, dtype=np.uint8)

def bar_frame(size, width=1400, height=24, color=(255,107,0)):
    img = np.full((size[1], size[0], 3), fill_value=(10,10,10), dtype=np.uint8)
    x1 = (size[0]-width)//2
    y1 = (size[1]-height)//2
    img[y1:y1+height, x1:x1+width] = color
    return img

def tts_line(text, path):
    if path.exists():
        return
    try:
        gTTS(text=text, lang="en", slow=False).save(str(path))
    except Exception as e:
        print("TTS failed:", e)

def build(name, segments, out_name, tts=False):
    clips = []
    for seg in segments:
        if seg["type"] == "text":
            frame = text_frame(
                (W, H), seg["text"], seg["y"],
                seg.get("size", 64),
                hex_to_rgb(seg.get("color", "#ffffff")),
                hex_to_rgb(seg.get("bg", "#0a0a0a")),
            )
        elif seg["type"] == "solid":
            frame = solid_frame((W, H), hex_to_rgb(seg["bg"]))
        elif seg["type"] == "bar":
            frame = bar_frame(
                (W, H),
                seg.get("width", 1400),
                seg.get("height", 24),
                hex_to_rgb(seg.get("color", "#ff6b00")),
            )
        else:
            raise ValueError(seg)
        clip = ImageClip(frame).with_duration(seg["dur"])
        if tts and "audio_key" in seg:
            a_path = TTS_DIR / f"{name}_{seg['audio_key']}.mp3"
            tts_line(seg["text"], a_path)
            if a_path.exists():
                try:
                    ac = AudioFileClip(str(a_path))
                    clip = clip.with_audio(ac)
                except Exception as e:
                    print("Audio fail", a_path, e)
        clips.append(clip)
    final = concatenate_videoclips(clips, method="compose")
    out = OUT / out_name
    if out.exists():
        out.unlink()
    final.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
    sz = out.stat().st_size if out.exists() else 0
    print({"name": out_name, "ok": out.exists(), "size": sz, "time": datetime.utcnow().isoformat()+"Z"})
    return out

# 1. aidynamic_promo.mp4 40s
aidynamic = [
    {"type":"solid","bg":"#0a0a0a","dur":1.0},
    {"type":"text","text":"YOUR BUSINESS","y":340,"size":80,"color":"#ffffff","dur":4,"audio_key":"line1"},
    {"type":"text","text":"IS LOSING MONEY","y":460,"size":80,"color":"#ffffff","dur":4,"audio_key":"line2"},
    {"type":"text","text":"While You're Doing Paperwork","y":420,"size":66,"color":"#ffffff","dur":4,"audio_key":"line3"},
    {"type":"text","text":"AI Dynamic automates everything","y":340,"size":60,"color":"#FF6B00","dur":4,"audio_key":"line4"},
    {"type":"text","text":"scheduling, follow-ups, billing","y":460,"size":44,"color":"#ffffff","dur":7,"audio_key":"line5"},
    {"type":"bar","width":1400,"height":24,"color":"#FF6B00","dur":5},
    {"type":"text","text":"Small businesses","y":340,"size":64,"color":"#ffffff","dur":2,"audio_key":"line6"},
    {"type":"text","text":"using AI grow 3x faster","y":440,"size":64,"color":"#ffffff","dur":3,"audio_key":"line7"},
    {"type":"text","text":"FREE CONSULTATION","y":380,"size":72,"color":"#FF6B00","dur":4,"audio_key":"line8"},
    {"type":"text","text":"we audit your workflow for free","y":500,"size":40,"color":"#ffffff","dur":3,"audio_key":"line9"},
    {"type":"text","text":"aidynamic.pro","y":440,"size":72,"color":"#FF6B00","dur":4,"audio_key":"line10"},
    {"type":"text","text":"FREE Consultation -- No obligation","y":580,"size":34,"color":"#bbbbbb","dur":3,"audio_key":"line11"},
]

# 2. 305business_promo.mp4 40s
miami = [
    {"type":"solid","bg":"#0a0a0a","dur":1.0},
    {"type":"text","text":"MIAMI BUSINESS OWNERS","y":300,"size":72,"color":"#00D4AA","dur":4,"audio_key":"m1"},
    {"type":"text","text":"Your competitors are already using AI","y":420,"size":52,"color":"#FF6B6B","dur":4,"audio_key":"m2"},
    {"type":"text","text":"305 Business gives you the same tools","y":380,"size":48,"color":"#ffffff","dur":5,"audio_key":"m3"},
    {"type":"text","text":"without the enterprise price","y":460,"size":48,"color":"#ffffff","dur":4,"audio_key":"m4"},
    {"type":"text","text":"Old Way","y":280,"size":56,"color":"#FF6B6B","dur":5,"audio_key":"m5"},
    {"type":"text","text":"paperwork, missed calls, manual","y":380,"size":40,"color":"#FF6B6B","dur":5,"audio_key":"m6"},
    {"type":"text","text":"New Way","y":280,"size":56,"color":"#00D4AA","dur":5,"audio_key":"m7"},
    {"type":"text","text":"automated, responsive, growing","y":380,"size":40,"color":"#00D4AA","dur":5,"audio_key":"m8"},
    {"type":"text","text":"94% customer retention with AI follow-up","y":320,"size":40,"color":"#00D4AA","dur":5,"audio_key":"m9"},
    {"type":"text","text":"60% less admin work","y":440,"size":40,"color":"#00D4AA","dur":5,"audio_key":"m10"},
    {"type":"text","text":"Same staff, 2x output","y":560,"size":40,"color":"#00D4AA","dur":5,"audio_key":"m11"},
    {"type":"bar","width":1400,"height":24,"color":"#00D4AA","dur":5},
    {"type":"text","text":"We build your AI system in 48 hours","y":380,"size":56,"color":"#ffffff","dur":4,"audio_key":"m12"},
    {"type":"text","text":"305business.llc","y":480,"size":72,"color":"#00D4AA","dur":4,"audio_key":"m13"},
    {"type":"text","text":"Miami's AI Partner","y":320,"size":36,"color":"#FF6B6B","dur":4,"audio_key":"m14"},
]

# 3. cyberpunk_test.mp4 45s
cyber = [
    {"type":"solid","bg":"#0a0a0a","dur":1.0},
    {"type":"text","text":"SYSTEM ONLINE","y":340,"size":80,"color":"#00FF41","dur":4,"audio_key":"c1"},
    {"type":"text","text":"RTX 5070 Ti -- 16GB VRAM","y":420,"size":52,"color":"#00FF41","dur":4,"audio_key":"c2"},
    {"type":"text","text":"Local AI -- No Cloud Costs","y":400,"size":48,"color":"#00FF41","dur":4,"audio_key":"c3"},
    {"type":"text","text":"NOISE","y":180,"size":36,"color":"#00FF41","dur":5,"audio_key":"c4"},
    {"type":"text","text":"SCANLINE","y":300,"size":36,"color":"#00FF41","dur":5,"audio_key":"c5"},
    {"type":"text","text":"VIGNETTE","y":420,"size":36,"color":"#00FF41","dur":5,"audio_key":"c6"},
    {"type":"text","text":"GLITCH","y":540,"size":36,"color":"#00FF41","dur":5,"audio_key":"c7"},
    {"type":"text","text":"Faceless Videos in Minutes","y":380,"size":56,"color":"#00FF41","dur":4,"audio_key":"c8"},
    {"type":"bar","width":1200,"height":8,"color":"#00FF41","dur":2},
    {"type":"text","text":"For Your Business","y":340,"size":64,"color":"#00FF41","dur":4,"audio_key":"c9"},
    {"type":"text","text":"HERMES + RTX 5070 Ti","y":460,"size":40,"color":"#00FF41","dur":4,"audio_key":"c10"},
    {"type":"text","text":"SAY GOODBYE TO CLOUD COSTS","y":580,"size":36,"color":"#00FF41","dur":4,"audio_key":"c11"},
    {"type":"text","text":"MAX EFFECTS","y":340,"size":72,"color":"#00FF41","dur":4,"audio_key":"c12"},
    {"type":"text","text":"HERMES AGENT","y":440,"size":84,"color":"#00FF41","dur":5,"audio_key":"c13"},
]

if __name__ == "__main__":
    print("Starting reliable video build...")
    a = build("aidynamic", aidynamic, "aidynamic_promo.mp4", tts=False)
    m = build("miami", miami, "305business_promo.mp4", tts=False)
    c = build("cyber", cyber, "cyberpunk_test.mp4", tts=False)
    print({"a": a, "m": m, "c": c})
