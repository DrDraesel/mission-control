
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from gtts import gTTS
from datetime import datetime
import random

OUT = Path(r"C:\Users\GAMEPOWER\Videos\generated")
OUT.mkdir(parents=True, exist_ok=True)
TTS_DIR = OUT / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT_BOLD = "C:/Windows/Fonts/impact.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def gradient_background(size, color1, color2):
    """Vertical gradient background."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    c1 = np.array(color1, dtype=np.float32)
    c2 = np.array(color2, dtype=np.float32)
    for y in range(size[1]):
        t = y / (size[1] - 1)
        arr[y, :, :] = (c1 * (1 - t) + c2 * t).astype(np.uint8)
    return arr

def noise_overlay(size, intensity=30):
    """Add subtle noise grain."""
    noise = np.random.randint(-intensity, intensity, (size[1], size[0], 3), dtype=np.int16)
    base = np.zeros((size[1], size[0], 3), dtype=np.int16)
    return np.clip(base + noise, 0, 255).astype(np.uint8)

def vignette(size, strength=0.4):
    """Darken edges."""
    x = np.linspace(-1, 1, size[0])
    y = np.linspace(-1, 1, size[1])
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    mask = np.clip(1 - dist * strength, 0, 1)
    mask = np.stack([mask]*3, axis=-1)
    return mask

class RichFrame:
    def __init__(self):
        self.fonts = {}
        self.fonts["bold"] = ImageFont.truetype(FONT_BOLD, 64)
        self.fonts["reg"] = ImageFont.truetype(FONT_REG, 36)
        self.grain_cache = None

    def get_grain(self, size):
        if self.grain_cache is None or self.grain_cache.shape[:2] != (size[1], size[0]):
            self.grain_cache = noise_overlay(size, 18)
        return self.grain_cache

    def composite(self, bg, text_layer, grain=True, vig=True):
        arr = bg.astype(np.float32)
        if grain:
            g = self.get_grain(bg.shape[:2][::-1])
            arr = arr * 0.92 + g.astype(np.float32) * 0.08
        if vig:
            v = vignette(bg.shape[:2][::-1], 0.35)
            arr = arr * v
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        if text_layer is not None:
            mask = text_layer[:, :, 3] / 255.0
            for c in range(3):
                arr[:, :, c] = (arr[:, :, c] * (1 - mask) + text_layer[:, :, c] * mask).astype(np.uint8)
        return arr

    def text_layer(self, size, lines, font_key="bold", color=(255,255,255,255)):
        img = Image.new("RGBA", size, (0,0,0,0))
        draw = ImageDraw.Draw(img)
        font = self.fonts[font_key]
        y = size[1] // 2 - (len(lines) * 80) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (size[0] - tw) // 2
            draw.text((x, y), line, font=font, fill=color)
            y += th + 20
        return np.array(img)

rf = RichFrame()

def tts_line(text, path):
    if path.exists():
        return
    try:
        gTTS(text=text, lang="en", slow=False).save(str(path))
    except Exception as e:
        print("TTS failed:", e)

def build(name, segments, out_name, tts=True):
    clips = []
    audio_clips = []
    for seg in segments:
        if seg["type"] == "gradient":
            bg = gradient_background((W, H), hex_to_rgb(seg["c1"]), hex_to_rgb(seg["c2"]))
        elif seg["type"] == "solid":
            bg = np.full((H, W, 3), fill_value=hex_to_rgb(seg["bg"]), dtype=np.uint8)
        else:
            raise ValueError(seg)

        lines = seg.get("lines", [seg.get("text", "")])
        color = seg.get("color", "#ffffff")
        alpha = seg.get("alpha", 255)
        c = hex_to_rgb(color) + (alpha,)
        txt = rf.text_layer((W, H), lines, seg.get("font", "bold"), c)
        frame = rf.composite(bg, txt)

        clip = ImageClip(frame).with_duration(seg["dur"])
        clips.append(clip)

        if tts and "audio_key" in seg and lines:
            a_key = seg["audio_key"]
            a_path = TTS_DIR / f"{name}_{a_key}.mp3"
            tts_line(" ".join(lines), a_path)
            if a_path.exists():
                try:
                    ac = AudioFileClip(str(a_path))
                    audio_clips.append(ac.with_start(sum(s["dur"] for s in segments[:segments.index(seg)])))
                except Exception as e:
                    print("Audio fail", a_path, e)

    if not clips:
        print("no clips", name)
        return None

    final = concatenate_videoclips(clips, method="compose")
    if audio_clips:
        try:
            final = final.with_audio(CompositeAudioClip(audio_clips))
        except Exception as e:
            print("Audio composite fail", e)

    out = OUT / out_name
    if out.exists():
        out.unlink()
    final.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
    sz = out.stat().st_size if out.exists() else 0
    print({"name": out_name, "ok": out.exists(), "size": sz, "time": datetime.utcnow().isoformat()+"Z"})
    return out

# 1. aidynamic_promo.mp4 40s
aidynamic = [
    {"type":"gradient","c1":"#1a0a00","c2":"#0a0a0a","dur":1.0},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":4,"lines":["YOUR BUSINESS","IS LOSING MONEY"],"color":"#FF6B00","audio_key":"l1"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":4,"lines":["While You're Doing Paperwork"],"color":"#ffffff","audio_key":"l2"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":4,"lines":["AI Dynamic automates everything"],"color":"#FF6B00","audio_key":"l3"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":7,"lines":["scheduling, follow-ups, billing"],"color":"#ffffff","audio_key":"l4"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":5,"lines":["Small businesses using AI","grow 3x faster"],"color":"#ffffff","audio_key":"l5"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":4,"lines":["FREE CONSULTATION"],"color":"#FF6B00","audio_key":"l6"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":3,"lines":["we audit your workflow for free"],"color":"#ffffff","audio_key":"l7"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":4,"lines":["aidynamic.pro"],"color":"#FF6B00","audio_key":"l8"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":3,"lines":["FREE Consultation -- No obligation"],"color":"#bbbbbb","audio_key":"l9"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#1a0a00","dur":2,"lines":["aidynamic.pro"],"color":"#FF6B00","audio_key":"l10"},
]

# 2. 305business_promo.mp4 40s
miami = [
    {"type":"gradient","c1":"#001a10","c2":"#0a0a0a","dur":1.0},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":4,"lines":["MIAMI BUSINESS OWNERS"],"color":"#00D4AA","audio_key":"m1"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":4,"lines":["Your competitors are","already using AI"],"color":"#FF6B6B","audio_key":"m2"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["305 Business gives you","the same tools"],"color":"#ffffff","audio_key":"m3"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":4,"lines":["without the enterprise price"],"color":"#ffffff","audio_key":"m4"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["Old Way","paperwork, missed calls, manual"],"color":"#FF6B6B","audio_key":"m5"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["New Way","automated, responsive, growing"],"color":"#00D4AA","audio_key":"m6"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["94% customer retention","with AI follow-up"],"color":"#00D4AA","audio_key":"m7"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["60% less admin work"],"color":"#00D4AA","audio_key":"m8"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":5,"lines":["Same staff, 2x output"],"color":"#00D4AA","audio_key":"m9"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":4,"lines":["We build your AI system","in 48 hours"],"color":"#ffffff","audio_key":"m10"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":4,"lines":["305business.llc"],"color":"#00D4AA","audio_key":"m11"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a10","dur":3,"lines":["Miami's AI Partner"],"color":"#FF6B6B","audio_key":"m12"},
]

# 3. cyberpunk_test.mp4 45s
cyber = [
    {"type":"gradient","c1":"#001a00","c2":"#0a0a0a","dur":1.0},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["SYSTEM ONLINE"],"color":"#00FF41","audio_key":"c1"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["RTX 5070 Ti","16GB VRAM"],"color":"#00FF41","audio_key":"c2"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["Local AI","No Cloud Costs"],"color":"#00FF41","audio_key":"c3"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":5,"lines":["NOISE","SCANLINE","VIGNETTE","GLITCH"],"color":"#00FF41","audio_key":"c4"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["Faceless Videos","in Minutes"],"color":"#00FF41","audio_key":"c5"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["For Your Business"],"color":"#00FF41","audio_key":"c6"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["HERMES + RTX 5070 Ti","SAY GOODBYE TO CLOUD COSTS"],"color":"#00FF41","audio_key":"c7"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":4,"lines":["MAX EFFECTS"],"color":"#00FF41","audio_key":"c8"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":5,"lines":["HERMES AGENT"],"color":"#00FF41","audio_key":"c9"},
    {"type":"gradient","c1":"#0a0a0a","c2":"#001a00","dur":3,"lines":["Local. Fast. Unlimited."],"color":"#00FF41","audio_key":"c10"},
]

if __name__ == "__main__":
    print("Starting improved build with backgrounds, noise, vignette, voice...")
    a = build("aidynamic", aidynamic, "aidynamic_promo.mp4", tts=True)
    m = build("miami", miami, "305business_promo.mp4", tts=True)
    c = build("cyber", cyber, "cyberpunk_test.mp4", tts=True)
    print({"a": a, "m": m, "c": c})
