
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, ColorClip, vfx
)
from gtts import gTTS
from datetime import datetime
import math

OUT = Path(r"C:\Users\GAMEPOWER\Videos\generated")
OUT.mkdir(parents=True, exist_ok=True)
TTS_DIR = OUT / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
FONT_BOLD = "C:/Windows/Fonts/impact.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"

# Palette
AIDYNAMIC_ACCENT = (255, 107, 0)      # #FF6B00
AIDYNAMIC_BG1 = (10, 10, 10)
AIDYNAMIC_BG2 = (30, 12, 0)

MIAMI_TEAL = (0, 212, 170)           # #00D4AA
MIAMI_CORAL = (255, 107, 107)        # #FF6B6B
MIAMI_BG1 = (8, 18, 16)
MIAMI_BG2 = (18, 8, 12)

CYBER_GREEN = (0, 255, 65)           # #00FF41
CYBER_BG1 = (6, 10, 6)
CYBER_BG2 = (0, 20, 8)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def gradient_bg(size, c1, c2, t_offset=0.0):
    """Animated vertical gradient that shifts over time."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.float32)
    c1 = np.array(c1, dtype=np.float32)
    c2 = np.array(c2, dtype=np.float32)
    # Create a wave that shifts up/down
    for y in range(size[1]):
        t = y / (size[1] - 1)
        shift = 0.15 * math.sin(t * math.pi * 2 + t_offset)
        t = max(0.0, min(1.0, t + shift))
        arr[y, :, :] = c1 * (1 - t) + c2 * t
    return np.clip(arr, 0, 255).astype(np.uint8)

def vignette(size, strength=0.5):
    x = np.linspace(-1, 1, size[0])
    y = np.linspace(-1, 1, size[1])
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    mask = np.clip(1 - dist * strength, 0, 1)
    return np.stack([mask]*3, axis=-1).astype(np.float32)

def noise_grain(size, intensity=18, frame_idx=0):
    rng = np.random.default_rng(seed=frame_idx)
    noise = rng.integers(-intensity, intensity, (size[1], size[0], 3), dtype=np.int16)
    return noise.astype(np.int16)

def apply_fx(base_frame, frame_idx, vig_strength=0.45, grain=14):
    """Apply vignette + film grain."""
    arr = base_frame.astype(np.float32)
    v = vignette(base_frame.shape[:2][::-1], vig_strength)
    arr = arr * v
    g = noise_grain(base_frame.shape[:2][::-1], grain, frame_idx)
    arr = arr + g.astype(np.float32)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr

def text_to_frame(size, text, font_path, font_size, color, align="center"):
    """Render text onto a transparent full-frame RGBA image."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if align == "center":
        x = (size[0] - tw) // 2
        y = (size[1] - th) // 2
    elif align == "left":
        x = 80
        y = (size[1] - th) // 2
    else:
        x, y = (size[0] - tw) // 2, 80
    draw.text((x, y), text, font=font, fill=color)
    arr = np.array(img)
    # Guarantee full-frame alpha mask
    if arr.shape[0] != size[1] or arr.shape[1] != size[0]:
        tmp = Image.new("RGBA", size, (0, 0, 0, 0))
        tmp.paste(Image.fromarray(arr), ((size[0] - arr.shape[1]) // 2, (size[1] - arr.shape[0]) // 2))
        arr = np.array(tmp)
    return arr

class Animator:
    def __init__(self, w=W, h=H):
        self.w = w
        self.h = h
    
    def fade_in(self, clip, start=0.0, duration=0.8):
        return clip.with_start(start).crossfadein(duration)
    
    def fade_out(self, clip, start=0.0, duration=0.8):
        # Simulate fade out by animating opacity via multiply
        def fl_filter(get_frame, t):
            frame = get_frame(t)
            if t < start:
                return frame
            alpha = max(0.0, 1.0 - (t - start) / duration)
            return (frame * alpha).astype(np.uint8)
        return clip.fl(fl_filter)
    
    def slide_from_left(self, text, font, size, color, bg_func, duration, start_t, y_pos="center"):
        def make_frame(t):
            progress = min(1.0, max(0.0, (t - start_t) / (duration * 0.8)))
            ease = 1 - (1 - progress) ** 3  # ease-out cubic
            x_offset = int(-self.w * (1 - ease))
            bg = bg_func(self.w, self.h, t)
            txt = text_to_frame((self.w, self.h), text, font, size, color, align="left")
            # shift text horizontally
            shifted = np.roll(txt, x_offset, axis=1)
            frame = apply_fx(bg, int(t * FPS))
            # alpha composite text
            mask = shifted[:, :, 3:4] / 255.0
            frame = (frame * (1 - mask) + shifted[:, :, :3] * mask).astype(np.uint8)
            return frame
        
        return ImageClip(make_frame(0), duration=duration).transform(lambda gf, t: make_frame(t))
    
    def pulse_scale(self, text, font, size, color, bg_func, duration, start_t, y_pos="center"):
        def make_frame(t):
            progress = min(1.0, max(0.0, (t - start_t) / duration))
            # sine pulse between 0.9 and 1.15
            scale = 1.0 + 0.12 * math.sin(progress * math.pi * 2)
            bg = bg_func(self.w, self.h, t)
            txt = text_to_frame((self.w, self.h), text, font, size, color)
            # simple scale by resize
            pil = Image.fromarray(txt)
            new_w = int(self.w * scale)
            new_h = int(self.h * scale)
            pil_scaled = pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            arr = np.array(pil_scaled)
            # crop center back to w,h
            x0 = (new_w - self.w) // 2
            y0 = (new_h - self.h) // 2
            arr = arr[y0:y0+self.h, x0:x0+self.w]
            frame = apply_fx(bg, int(t * FPS))
            mask = arr[:, :, 3:4] / 255.0
            frame = (frame * (1 - mask) + arr[:, :, :3] * mask).astype(np.uint8)
            return frame
        
        return ImageClip(make_frame(0), duration=duration).transform(lambda gf, t: make_frame(t))

def tts_line(text, path):
    if path.exists():
        return
    try:
        gTTS(text=text, lang="en", slow=False).save(str(path))
    except Exception as e:
        print("TTS failed:", e)

def build_segment(text, font, size, color, bg_func, duration, start_t, animator=None, anim="fade_in", audio_key=None, prefix="seg"):
    if animator is None:
        animator = Animator()
    """Build one animated segment."""
    if anim == "slide_left":
        clip = animator.slide_from_left(text, font, size, color, bg_func, duration, start_t)
    elif anim == "pulse":
        clip = animator.pulse_scale(text, font, size, color, bg_func, duration, start_t)
    elif anim == "fade_in":
        def make_frame(t):
            progress = min(1.0, max(0.0, t / 0.7))
            alpha = progress
            bg = bg_func(W, H, start_t + t)
            txt = text_to_frame((W, H), text, font, size, color)
            frame = apply_fx(bg, int((start_t + t) * FPS))
            mask = txt[:, :, 3:4] / 255.0
            frame = (frame * (1 - mask * alpha) + txt[:, :, :3] * mask * alpha).astype(np.uint8)
            return frame
        clip = ImageClip(make_frame(0), duration=duration).transform(lambda gf, t: make_frame(t))
    else:
        def make_frame(t):
            bg = bg_func(W, H, start_t + t)
            txt = text_to_frame((W, H), text, font, size, color)
            frame = apply_fx(bg, int((start_t + t) * FPS))
            mask = txt[:, :, 3:4] / 255.0
            frame = (frame * (1 - mask) + txt[:, :, :3] * mask).astype(np.uint8)
            return frame
        clip = ImageClip(make_frame(0), duration=duration).transform(lambda gf, t: make_frame(t))
    
    if audio_key:
        a_path = TTS_DIR / f"{prefix}_{audio_key}.mp3"
        tts_line(text, a_path)
        if a_path.exists():
            try:
                ac = AudioFileClip(str(a_path))
                clip = clip.with_audio(ac)
            except Exception as e:
                print("Audio fail", a_path, e)
    return clip

def build(name, segments, out_name, prefix="seg"):
    clips = []
    t = 0.0
    for seg in segments:
        dur = seg["dur"]
        clip = build_segment(
            text=seg["text"],
            font=seg.get("font", FONT_BOLD),
            size=seg.get("size", 64),
            color=seg.get("color", (255, 255, 255)),
            bg_func=seg["bg_func"],
            duration=dur,
            start_t=t,
            animator=seg.get("animator"),
            anim=seg.get("anim", "fade_in"),
            audio_key=seg.get("audio_key"),
            prefix=prefix,
        )
        clips.append(clip)
        t += dur
    
    final = concatenate_videoclips(clips, method="compose")
    out = OUT / out_name
    if out.exists():
        out.unlink()
    final.write_videofile(str(out), fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
    sz = out.stat().st_size if out.exists() else 0
    print({"name": out_name, "ok": out.exists(), "size": sz, "time": datetime.utcnow().isoformat()+"Z"})
    return out

# Define background functions
def aidynamic_bg(w, h, t):
    return gradient_bg((w, h), AIDYNAMIC_BG1, AIDYNAMIC_BG2, t * 0.3)

def miami_bg(w, h, t):
    return gradient_bg((w, h), MIAMI_BG1, MIAMI_BG2, t * 0.25)

def cyber_bg(w, h, t):
    return gradient_bg((w, h), CYBER_BG1, CYBER_BG2, t * 0.35)

animator = Animator()

# 1. aidynamic_promo.mp4 40s
aidynamic = [
    {"text":"YOUR BUSINESS", "dur":4, "size":80, "color":AIDYNAMIC_ACCENT, "bg_func":aidynamic_bg, "anim":"pulse", "audio_key":"l1"},
    {"text":"IS LOSING MONEY", "dur":4, "size":80, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"slide_left", "audio_key":"l2"},
    {"text":"While You're Doing Paperwork", "dur":4, "size":66, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"fade_in", "audio_key":"l3"},
    {"text":"AI Dynamic automates everything", "dur":4, "size":60, "color":AIDYNAMIC_ACCENT, "bg_func":aidynamic_bg, "anim":"pulse", "audio_key":"l4"},
    {"text":"scheduling, follow-ups, billing", "dur":7, "size":44, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"fade_in", "audio_key":"l5"},
    {"text":"Small businesses","dur":2, "size":64, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"slide_left", "audio_key":"l6"},
    {"text":"using AI grow 3x faster","dur":3, "size":64, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"pulse", "audio_key":"l7"},
    {"text":"FREE CONSULTATION","dur":4, "size":72, "color":AIDYNAMIC_ACCENT, "bg_func":aidynamic_bg, "anim":"fade_in", "audio_key":"l8"},
    {"text":"we audit your workflow for free","dur":3, "size":40, "color":(255,255,255), "bg_func":aidynamic_bg, "anim":"slide_left", "audio_key":"l9"},
    {"text":"aidynamic.pro","dur":4, "size":72, "color":AIDYNAMIC_ACCENT, "bg_func":aidynamic_bg, "anim":"pulse", "audio_key":"l10"},
    {"text":"FREE Consultation -- No obligation","dur":3, "size":34, "color":(187,187,187), "bg_func":aidynamic_bg, "anim":"fade_in", "audio_key":"l11"},
]

# 2. 305business_promo.mp4 40s
miami = [
    {"text":"MIAMI BUSINESS OWNERS","dur":4, "size":72, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"pulse", "audio_key":"m1"},
    {"text":"Your competitors are","dur":4, "size":52, "color":MIAMI_CORAL, "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m2"},
    {"text":"already using AI","dur":4, "size":52, "color":MIAMI_CORAL, "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m3"},
    {"text":"305 Business gives you","dur":5, "size":48, "color":(255,255,255), "bg_func":miami_bg, "anim":"pulse", "audio_key":"m4"},
    {"text":"the same tools","dur":4, "size":48, "color":(255,255,255), "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m5"},
    {"text":"without the enterprise price","dur":4, "size":48, "color":(255,255,255), "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m6"},
    {"text":"Old Way","dur":5, "size":56, "color":MIAMI_CORAL, "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m7"},
    {"text":"paperwork, missed calls, manual","dur":5, "size":40, "color":MIAMI_CORAL, "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m8"},
    {"text":"New Way","dur":5, "size":56, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m9"},
    {"text":"automated, responsive, growing","dur":5, "size":40, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"pulse", "audio_key":"m10"},
    {"text":"94% customer retention","dur":5, "size":40, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m11"},
    {"text":"60% less admin work","dur":5, "size":40, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m12"},
    {"text":"Same staff, 2x output","dur":5, "size":40, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"pulse", "audio_key":"m13"},
    {"text":"We build your AI system","dur":4, "size":56, "color":(255,255,255), "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m14"},
    {"text":"in 48 hours","dur":4, "size":56, "color":(255,255,255), "bg_func":miami_bg, "anim":"slide_left", "audio_key":"m15"},
    {"text":"305business.llc","dur":4, "size":72, "color":MIAMI_TEAL, "bg_func":miami_bg, "anim":"pulse", "audio_key":"m16"},
    {"text":"Miami's AI Partner","dur":3, "size":36, "color":MIAMI_CORAL, "bg_func":miami_bg, "anim":"fade_in", "audio_key":"m17"},
]

# 3. cyberpunk_test.mp4 45s
cyber = [
    {"text":"SYSTEM ONLINE","dur":4, "size":80, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c1"},
    {"text":"RTX 5070 Ti","dur":4, "size":56, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"slide_left", "audio_key":"c2"},
    {"text":"16GB VRAM","dur":4, "size":56, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c3"},
    {"text":"Local AI","dur":4, "size":48, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c4"},
    {"text":"No Cloud Costs","dur":4, "size":48, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"slide_left", "audio_key":"c5"},
    {"text":"NOISE","dur":5, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c6"},
    {"text":"SCANLINE","dur":5, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c7"},
    {"text":"VIGNETTE","dur":5, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"slide_left", "audio_key":"c8"},
    {"text":"GLITCH","dur":5, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c9"},
    {"text":"Faceless Videos","dur":4, "size":56, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c10"},
    {"text":"in Minutes","dur":4, "size":56, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"slide_left", "audio_key":"c11"},
    {"text":"For Your Business","dur":4, "size":64, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c12"},
    {"text":"HERMES + RTX 5070 Ti","dur":4, "size":40, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c13"},
    {"text":"SAY GOODBYE TO CLOUD COSTS","dur":4, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"slide_left", "audio_key":"c14"},
    {"text":"MAX EFFECTS","dur":4, "size":72, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c15"},
    {"text":"HERMES AGENT","dur":5, "size":84, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"pulse", "audio_key":"c16"},
    {"text":"Local. Fast. Unlimited.","dur":3, "size":36, "color":CYBER_GREEN, "bg_func":cyber_bg, "anim":"fade_in", "audio_key":"c17"},
]

if __name__ == "__main__":
    print("Building animated videos with motion + voice...")
    a = build("aidynamic", aidynamic, "aidynamic_promo.mp4", prefix="aidyn")
    m = build("miami", miami, "305business_promo.mp4", prefix="miami")
    c = build("cyber", cyber, "cyberpunk_test.mp4", prefix="cyber")
    print({"a": a, "m": m, "c": c})
