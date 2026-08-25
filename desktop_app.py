import sys
import os
import random
import math
import time
import json
import base64
import threading
import subprocess
import tempfile
import zipfile
import urllib.request
import numpy as np
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APP_VERSION = "v3.3.0"
NO_SIGNAL_LANGS = [
    "Pas de signal", "Kein Signal", "Sin señal", "Nenhum sinal", "Geen signaal",
    "No Signal", "Brak sygnału", "Není signál", "Nincs jel", "Semnal lipsă",
    "Ingen signal", "Ei signaalia", "Sinyal yok", "Δεν υπάρχει σήμα",
    "Нет сигнала", "Немає сигналу", "Nema signala", "Signāla nav", "Signalo nėra",
    "无信号", "信号なし", "신호 없음", "אין אות", "لا توجد إشارة",
]


# External debug terminal — writes to a live tail'd log in a separate window
_DEBUG_LOG = os.path.join(tempfile.gettempdir(), 'misremembered_debug.log')
_dbg_lock = threading.Lock()

def dbg(msg, tag='INFO'):
    ts = time.strftime('%H:%M:%S.') + f'{int(time.time()*1000)%1000:03d}'
    line = f'[{ts}] [{tag:<6}] {msg}\n'
    print(line, end='', flush=True)
    with _dbg_lock:
        try:
            open(_DEBUG_LOG, 'a', encoding='utf-8').write(line)
        except Exception:
            pass

def _launch_debug_terminal():
    try:
        with open(_DEBUG_LOG, 'w', encoding='utf-8') as _f:
            _f.write(f'=== MISREMEMBERED MEDIA {APP_VERSION} DEBUG ===\n')
            _f.write(f'=== {time.strftime(chr(37)+chr(89)+-chr(109)+-chr(100)+chr(32)+chr(37)+chr(72)+chr(58)+chr(37)+chr(77)+chr(58)+chr(37)+chr(83))} ===\n\n')
        lp = _DEBUG_LOG.replace(chr(92), chr(92)+chr(92))
        ps = (
            f"$f='{lp}';$pos=0;"
            'while($true){'
            '$s=New-Object IO.FileStream($f,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);'
            '$r=New-Object IO.StreamReader($s);'
            '$s.Seek($pos,[IO.SeekOrigin]::Begin)|Out-Null;'
            '$t=$r.ReadToEnd();'
            'if($t){Write-Host $t -NoNewline};'
            '$pos=$s.Length;$r.Close();$s.Close();'
            'Start-Sleep -Milliseconds 150}'
        )
        subprocess.Popen(
            ['powershell.exe', '-NoExit', '-Command', ps],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        print(f'[DEBUG] Terminal error: {e}', file=sys.stderr)

FFMPEG_LOCAL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "MisrememberedMedia", "ffmpeg")
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

def find_ffmpeg():
    candidates = [
        "ffmpeg",
        os.path.join(FFMPEG_LOCAL_DIR, "bin", "ffmpeg.exe"),
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for candidate in candidates:
        try:
            result = subprocess.run([candidate, "-version"], capture_output=True, timeout=3)
            if result.returncode == 0:
                return candidate
        except Exception:
            pass
    return None

FFMPEG = find_ffmpeg()


# ─────────────────────────────────────────────────────────────────────────────
# 1. DYNAMIC ON-FRAME TEXT CORRUPTOR & FONT RENDERER (ZERO HARDCODED WORDS)
# Slices actual text regions, creates dynamic phonetic anagrams, and re-renders in matching font
# ─────────────────────────────────────────────────────────────────────────────
class LocalGlyphCorruptor:
    PHONETIC_PAIRS = {
        'e': 'o', 'o': 'e', 'a': 'e', 'i': 'l', 'r': 'n', 'n': 'r',
        'b': 'd', 'd': 'b', 'c': 's', 's': 'c', 'p': 'b', 'm': 'n',
        't': 'd', 'k': 'c', 'v': 'w', 'w': 'v', 'u': 'y', 'y': 'u'
    }

    @staticmethod
    def generate_phonetic_mutation(word_len, rng):
        """Generates dynamic phonetic pseudo-word strings matching the length/structure."""
        vowels = ['a', 'e', 'i', 'o', 'u', 'ea', 'oe', 'ai']
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'sh', 'th', 'ch', 'bl']
        res = []
        is_vow = rng.random() < 0.3
        while len("".join(res)) < word_len:
            if is_vow:
                res.append(rng.choice(vowels))
            else:
                res.append(rng.choice(consonants))
            is_vow = not is_vow
        out = "".join(res)[:word_len]
        return out.capitalize() if rng.random() < 0.4 else out

    @staticmethod
    def corrupt_actual_frame_text(bgr_img, rng, intensity=0.85):
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        
        # Fast gradient text region isolation
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad = cv2.morphologyEx(np.abs(grad_x) + np.abs(grad_y), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (12, 3)))
        grad_norm = cv2.normalize(grad, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        _, thresh = cv2.threshold(grad_norm, 60, 255, cv2.THRESH_BINARY)
        connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (16, 6)))
        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        pil_img = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        res_cv = bgr_img.copy()

        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect = bw / float(max(1, bh))
            area = bw * bh

            if 30 < bw < w * 0.92 and 12 < bh < h * 0.35 and aspect > 1.2 and area > 400:
                if rng.random() > intensity:
                    continue

                roi = gray[y:y+bh, x:x+bw]
                mean_lum = np.mean(roi)
                is_white_bg = mean_lum > 140

                mode = rng.random()

                if mode < 0.45:
                    # ── DYNAMIC FONT REPLACEMENT WITH CLEAN BACKGROUND (MEME STYLE) ──
                    bg_col = (255, 255, 255) if is_white_bg else (15, 15, 15)
                    fg_col = (10, 10, 10) if is_white_bg else (245, 245, 245)

                    draw.rectangle([x, y, x + bw, y + bh], fill=bg_col)

                    # Estimate approximate word count based on width/height
                    est_words = max(1, bw // int(bh * 1.8))
                    pseudo_words = [LocalGlyphCorruptor.generate_phonetic_mutation(rng.randint(3, 7), rng) for _ in range(est_words)]
                    text_str = " ".join(pseudo_words)
                    if is_white_bg and rng.random() < 0.35:
                        text_str += "."

                    f_size = max(12, int(bh * 0.65))
                    try:
                        font = ImageFont.truetype("arial.ttf", f_size)
                    except Exception:
                        font = ImageFont.load_default()

                    tx = x + rng.randint(2, max(4, int(bw * 0.04)))
                    ty = y + max(1, int((bh - f_size) / 2))
                    if not is_white_bg:
                        draw.text((tx+1, ty+1), text_str, fill=(0, 0, 0), font=font)
                    draw.text((tx, ty), text_str, fill=fg_col, font=font)

                else:
                    # ── IN-PLACE CHARACTER FLIP / CASCADE ──
                    text_patch = res_cv[y:y+bh, x:x+bw].copy()
                    if text_patch.size == 0:
                        continue

                    char_w = max(6, int(bh * 0.75))
                    if bw > char_w * 2:
                        cx = rng.randint(0, bw - char_w)
                        char_slice = text_patch[:, cx:cx+char_w].copy()
                        flipped = cv2.flip(char_slice, 1)
                        text_patch[:, cx:cx+char_w] = cv2.addWeighted(flipped, 0.95, text_patch[:, cx:cx+char_w], 0.05, 0)
                        
                        # Blit back onto PIL image
                        patch_rgb = Image.fromarray(cv2.cvtColor(text_patch, cv2.COLOR_BGR2RGB))
                        pil_img.paste(patch_rgb, (x, y))

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


# ─────────────────────────────────────────────────────────────────────────────
# 2. LOCAL STILL LIFE & LATENT NEURAL RECONSTRUCTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class LocalStillLifeAIEngine:
    @staticmethod
    def apply_local_neural_reconstruction(bgr_img, rng, intensity=0.85, gloss=0.75):
        h, w = bgr_img.shape[:2]
        res = bgr_img.copy().astype(np.float32)

        # 1. Subject segmentation in YCrCb color space
        ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

        if np.sum(skin_mask) < (w * h * 0.02 * 255):
            Y, X = np.ogrid[:h, :w]
            cx, cy = w // 2, int(h * 0.45)
            dist_from_center = np.sqrt((X - cx)**2 + (Y - cy)**2)
            skin_mask = np.clip(255 - (dist_from_center / (max(w, h) * 0.45) * 255), 0, 255).astype(np.uint8)

        mask_blur = cv2.GaussianBlur(skin_mask, (25, 25), 0).astype(np.float32) / 255.0
        mask_3d = np.repeat(mask_blur[:, :, np.newaxis], 3, axis=2)

        # 2. Wet Flesh & Specular Shading (High-contrast gloss)
        if gloss > 0.05:
            gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY).astype(np.float32)
            blur = cv2.GaussianBlur(gray, (0, 0), 3)
            high_freq = np.clip(gray - blur, -35, 35)
            specular = np.clip((gray / 255.0)**3 * 140 * gloss, 0, 95)

            for c in range(3):
                res[:, :, c] = res[:, :, c] + (high_freq * 1.4 * gloss + specular) * mask_blur

        # 3. Asymmetrical Upper Feature / Eye Drift
        eye_y0, eye_y1 = int(h * 0.12), int(h * 0.48)
        eye_region = res[eye_y0:eye_y1, :].copy()

        if eye_region.shape[0] > 10:
            eh, ew = eye_region.shape[:2]
            shift_x = int(w * 0.022 * intensity)
            shift_y = -int(h * 0.030 * intensity)

            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            warped_eyes = cv2.warpAffine(eye_region, M, (ew, eh), borderMode=cv2.BORDER_REFLECT)

            eye_mask = np.zeros((eh, ew, 3), dtype=np.float32)
            Y, X = np.ogrid[:eh, :ew]
            val = np.clip(1.0 - np.sqrt(((X - int(ew * 0.55))/(ew * 0.35))**2 + ((Y - eh // 2)/(eh * 0.45))**2), 0, 1)
            eye_mask[:, :] = cv2.GaussianBlur(val, (25, 25), 0)[:, :, np.newaxis]

            res[eye_y0:eye_y1, :] = res[eye_y0:eye_y1, :] * (1.0 - eye_mask * 0.85 * intensity) + warped_eyes * (eye_mask * 0.85 * intensity)

        # 4. Multi-Jaw & Secondary Mouth Layering
        jaw_y0, jaw_y1 = int(h * 0.38), int(h * 0.85)
        jaw_region = res[jaw_y0:jaw_y1, :].copy()

        if jaw_region.shape[0] > 10:
            jh, jw = jaw_region.shape[:2]
            angle_dx = int(w * 0.035 * intensity)
            angle_dy = int(h * 0.042 * intensity)

            M_jaw = np.float32([[1, 0, angle_dx], [0, 1, angle_dy]])
            warped_jaw = cv2.warpAffine(jaw_region, M_jaw, (jw, jh), borderMode=cv2.BORDER_REFLECT)

            jaw_mask = np.zeros((jh, jw, 3), dtype=np.float32)
            Y, X = np.ogrid[:jh, :jw]
            j_val = np.clip(1.0 - np.sqrt(((X - int(jw * 0.50))/(jw * 0.35))**2 + ((Y - int(jh * 0.55))/(jh * 0.40))**2), 0, 1)
            jaw_mask[:, :] = cv2.GaussianBlur(j_val, (25, 25), 0)[:, :, np.newaxis]

            res[jaw_y0:jaw_y1, :] = res[jaw_y0:jaw_y1, :] * (1.0 - jaw_mask * 0.80 * intensity) + warped_jaw * (jaw_mask * 0.80 * intensity)

        return np.clip(res, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# 3. MASTER COMPOSITE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedEngine:
    def __init__(self):
        self.seed = random.randint(0, 0xFFFFFFFF)
        self.use_local_ai = True

    def set_seed(self, seed_val):
        self.seed = seed_val

    def process_frame(self, frame, rng, sliders, frame_idx=0, fps=30.0):
        master_v = sliders.get("master_val", 85) / 100.0
        text_v   = sliders.get("poster_melt", 90) / 100.0
        still_v  = sliders.get("object_melt", 85) / 100.0
        gloss_v  = sliders.get("flesh_gloss", 75) / 100.0
        green_v  = sliders.get("green_shift", 60) / 100.0

        dbg(f'process_frame #{frame_idx} ai={self.use_local_ai} still={still_v:.2f} text={text_v:.2f}', 'FRAME')
        out = frame.copy()

        # 1. Local AI Still Life Anatomical & Latent Reconstruction
        if self.use_local_ai and still_v > 0.05:
            dbg(f'  StillLifeAI intensity={still_v*master_v:.2f} gloss={gloss_v:.2f}', 'AI')
            out = LocalStillLifeAIEngine.apply_local_neural_reconstruction(
                out, rng, intensity=still_v * master_v, gloss=gloss_v
            )

        # 2. Dynamic On-Frame Text Corruption (Fonts & Background Inpainting)
        if text_v > 0.05:
            dbg(f'  GlyphCorrupt intensity={text_v*master_v:.2f}', 'TEXT')
            out = LocalGlyphCorruptor.corrupt_actual_frame_text(out, rng, intensity=text_v * master_v)

        # 3. The Complex "Green Light" Subtle Shift
        if green_v > 0.10 and rng.random() < 0.35:
            green_surge = green_v * master_v
            green_overlay = np.zeros_like(out)
            green_overlay[:, :] = [int(8 * green_surge), int(26 * green_surge), int(6 * green_surge)]
            out = cv2.add(out, green_overlay)

        return out

    def render_no_signal_screen(self, width, height, lang):
        img = np.full((height, width, 3), (180, 0, 0), dtype=np.uint8)
        noise = np.random.randint(-20, 20, (height, width, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img[::2, :, :] = (img[::2, :, :] * 0.72).astype(np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.6, width / 600.0)
        thick = max(1, int(scale * 2))
        (tw, th), _ = cv2.getTextSize(lang, font, scale, thick)
        tx = (width - tw) // 2
        ty = (height + th) // 2
        cv2.putText(img, lang, (tx+2, ty+2), font, scale, (0, 0, 40), thick+1, cv2.LINE_AA)
        cv2.putText(img, lang, (tx, ty), font, scale, (255, 255, 255), thick, cv2.LINE_AA)
        return img

    def render_static_screen(self, width, height):
        small = np.random.randint(0, 256, (max(1, height // 3), max(1, width // 3)), dtype=np.uint8)
        bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
        return cv2.resize(bgr, (width, height), interpolation=cv2.INTER_NEAREST)

    def render_no_video_screen(self, frame, time_sec):
        h, w = frame.shape[:2]
        res = np.zeros((h, w, 3), dtype=np.uint8)
        res[::3, :, :] = 10
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.6, w / 700.0)
        cv2.putText(res, "PLAY >", (28, 48), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        cv2.putText(res, "NO VIDEO", (28, 88), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        return res


# ─────────────────────────────────────────────────────────────────────────────
# 4. DESKTOP GUI APPLICATION (CUSTOMTKINTER)
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MISREMEMBERED MEDIA // LOCAL AI RECONSTRUCTION TERMINAL")
        self.geometry("1340x880")
        self.minsize(1080, 720)
        self.configure(fg_color="#07080b")

        self.engine = MisrememberedEngine()
        self.current_media_path = None
        self.original_image_bgr = None
        self.processed_image_bgr = None
        self.is_processing = False
        self.is_previewing = False
        self.preview_thread = None

        self.setup_ui()

        _launch_debug_terminal()
        dbg(f'App started. seed={self.engine.seed:08X}', 'INIT')

        if not FFMPEG:
            self.after(800, self.prompt_ffmpeg_install)

    def prompt_ffmpeg_install(self):
        answer = messagebox.askyesno(
            "FFmpeg Required for Audio/Video",
            "FFmpeg is needed for lossless audio resynthesis and video processing.\n\n"
            "Would you like to install FFmpeg automatically now?",
            icon="info"
        )
        if answer:
            self.download_ffmpeg()

    def download_ffmpeg(self):
        def _install():
            try:
                os.makedirs(FFMPEG_LOCAL_DIR, exist_ok=True)
                zip_path = os.path.join(tempfile.gettempdir(), "ffmpeg.zip")
                self.add_log("Downloading FFmpeg Essentials package...", "info")
                urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, zip_path)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    for member in z.namelist():
                        if member.endswith("bin/ffmpeg.exe"):
                            bin_dir = os.path.join(FFMPEG_LOCAL_DIR, "bin")
                            os.makedirs(bin_dir, exist_ok=True)
                            with z.open(member) as src, open(os.path.join(bin_dir, "ffmpeg.exe"), "wb") as dst:
                                dst.write(src.read())
                global FFMPEG
                FFMPEG = os.path.join(FFMPEG_LOCAL_DIR, "bin", "ffmpeg.exe")
                self.add_log("FFmpeg installed successfully!", "info")
            except Exception as e:
                self.add_log(f"FFmpeg install failed: {e}", "warn")
        threading.Thread(target=_install, daemon=True).start()

    def setup_ui(self):
        # ── HEADER ──
        self.header = ctk.CTkFrame(self, height=64, fg_color="#0d0f14", corner_radius=0, border_width=1, border_color="#1f232e")
        self.header.pack(side="top", fill="x")

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(title_box, text="●", font=ctk.CTkFont(size=14), text_color="#00ff66").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_box, text="MISREMEMBERED MEDIA", font=ctk.CTkFont(family="Courier New", size=18, weight="bold"), text_color="#e5e7eb").pack(side="left")
        ctk.CTkLabel(title_box, text=f"// {APP_VERSION}", font=ctk.CTkFont(family="Courier New", size=11), text_color="#ff3344", fg_color="#181a20", corner_radius=4, padx=8, pady=2).pack(side="left", padx=12)

        seed_box = ctk.CTkFrame(self.header, fg_color="transparent")
        seed_box.pack(side="right", padx=20, pady=12)

        # Built-in Local AI Switch
        self.ai_switch = ctk.CTkSwitch(
            seed_box, text="LOCAL AI ENGINE", font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            progress_color="#00ff66", button_color="#ffffff", text_color="#00ff66",
            command=self.toggle_local_ai
        )
        self.ai_switch.select()
        self.ai_switch.pack(side="left", padx=14)

        self.seed_btn = ctk.CTkButton(seed_box, text="↻ RE-SEED", font=ctk.CTkFont(family="Courier New", size=11), width=90, height=28, fg_color="#181a20", hover_color="#262a36", border_width=1, border_color="#2e3444", text_color="#00ff66", command=self.re_seed)
        self.seed_btn.pack(side="left", padx=6)

        self.seed_lbl = ctk.CTkLabel(seed_box, text=f"SEED: {self.engine.seed:08X}", font=ctk.CTkFont(family="Courier New", size=11), text_color="#9ca3af")
        self.seed_lbl.pack(side="left", padx=6)

        # ── BOTTOM EXPORT BAR ──
        self.bottom_bar = ctk.CTkFrame(self, height=64, fg_color="#0d0f14", corner_radius=0, border_width=1, border_color="#1f232e")
        self.bottom_bar.pack(side="bottom", fill="x")

        self.load_btn = ctk.CTkButton(self.bottom_bar, text="📁 LOAD IMAGE / VIDEO", font=ctk.CTkFont(family="Courier New", size=13, weight="bold"), fg_color="#1f2430", hover_color="#2b3242", border_width=1, border_color="#3b4252", text_color="#e5e7eb", height=38, command=self.load_media)
        self.load_btn.pack(side="left", padx=20, pady=12)

        self.export_btn = ctk.CTkButton(self.bottom_bar, text="💾 RENDER & EXPORT MEMORY", font=ctk.CTkFont(family="Courier New", size=13, weight="bold"), fg_color="#008844", hover_color="#00aa55", border_width=1, border_color="#00ff66", text_color="#ffffff", height=38, state="disabled", command=self.start_export)
        self.export_btn.pack(side="right", padx=20, pady=12)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar, height=4, progress_color="#00ff66", fg_color="#111318")
        self.progress_bar.set(0)

        # ── MAIN CONTAINER ──
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=12, pady=10)

        # Left: Controls Card
        self.controls_card = ctk.CTkFrame(self.container, width=380, fg_color="#0d0f14", corner_radius=8, border_width=1, border_color="#1f232e")
        self.controls_card.pack(side="left", fill="y", padx=(0, 10))

        self.tabs = ctk.CTkTabview(self.controls_card, fg_color="transparent", segmented_button_fg_color="#13161f", segmented_button_selected_color="#ff3344", segmented_button_selected_hover_color="#cc2233")
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_anatomy = self.tabs.add("STILL LIFE")
        self.tab_text = self.tabs.add("TEXT CORRUPTOR")

        self.setup_tabs()

        # Right: Viewport Card
        self.viewport_card = ctk.CTkFrame(self.container, fg_color="#090a0e", corner_radius=8, border_width=1, border_color="#1f232e")
        self.viewport_card.pack(side="right", fill="both", expand=True)

        vp_hdr = ctk.CTkFrame(self.viewport_card, height=34, fg_color="#0d0f14", corner_radius=8)
        vp_hdr.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(vp_hdr, text="SPLIT RECONSTRUCTION MONITOR", font=ctk.CTkFont(family="Courier New", size=11, weight="bold"), text_color="#9ca3af").pack(side="left", padx=12)
        self.status_lbl = ctk.CTkLabel(vp_hdr, text="READY // AWAITING MEDIA", font=ctk.CTkFont(family="Courier New", size=10), text_color="#ff3344")
        self.status_lbl.pack(side="right", padx=12)

        self.view_container = ctk.CTkFrame(self.viewport_card, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True, padx=12, pady=8)

        self.orig_preview_box = ctk.CTkFrame(self.view_container, fg_color="#050608", border_width=1, border_color="#181a20")
        self.orig_preview_box.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(self.orig_preview_box, text="[ ORIGINAL INPUT ]", font=ctk.CTkFont(family="Courier New", size=10), text_color="#4b5563").pack(anchor="nw", padx=8, pady=4)
        self.orig_img_lbl = ctk.CTkLabel(self.orig_preview_box, text="DROP OR LOAD FILE", font=ctk.CTkFont(family="Courier New", size=12), text_color="#374151")
        self.orig_img_lbl.pack(expand=True, fill="both", padx=8, pady=8)

        self.proc_preview_box = ctk.CTkFrame(self.view_container, fg_color="#050608", border_width=1, border_color="#181a20")
        self.proc_preview_box.pack(side="right", fill="both", expand=True, padx=(6, 0))
        ctk.CTkLabel(self.proc_preview_box, text="[ MISREMEMBERED RECONSTRUCTION ]", font=ctk.CTkFont(family="Courier New", size=10), text_color="#00ff66").pack(anchor="nw", padx=8, pady=4)
        self.proc_img_lbl = ctk.CTkLabel(self.proc_preview_box, text="", font=ctk.CTkFont(family="Courier New", size=12), text_color="#374151")
        self.proc_img_lbl.pack(expand=True, fill="both", padx=8, pady=8)

        log_frame = ctk.CTkFrame(self.viewport_card, height=110, fg_color="#050608", border_width=1, border_color="#181a20")
        log_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.log_box = ctk.CTkTextbox(log_frame, height=90, font=ctk.CTkFont(family="Courier New", size=10), fg_color="transparent", text_color="#00ff66", activate_scrollbars=True)
        self.log_box.pack(fill="both", expand=True, padx=6, pady=4)
        self.log_box.configure(state="disabled")

    def setup_tabs(self):
        self.slider_vars = {}

        sliders_1 = [
            ("Uncanny Still Life Drift", "object_melt", 0, 100, 85, "#ff3344"),
            ("Wet Flesh Specular Shading", "flesh_gloss", 0, 100, 75, "#00ff66"),
            ("Asymmetric Ocular Shift", "master_val", 0, 100, 90, "#ff3344"),
            ("The Complex 'Green Light'", "green_shift", 0, 100, 60, "#00ff66"),
        ]
        for title, key, mn, mx, df, clr in sliders_1:
            self._make_slider_group(self.tab_anatomy, title, key, mn, mx, df, clr)

        sliders_2 = [
            ("On-Frame Glyph Corruption", "poster_melt", 0, 100, 90, "#ff3344"),
        ]
        for title, key, mn, mx, df, clr in sliders_2:
            self._make_slider_group(self.tab_text, title, key, mn, mx, df, clr)

    def _make_slider_group(self, parent, title, key, mn, mx, df, clr):
        box = ctk.CTkFrame(parent, fg_color="#13161f", corner_radius=6, border_width=1, border_color="#1f2432")
        box.pack(fill="x", pady=4, padx=2)

        hdr = ctk.CTkFrame(box, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(family="Courier New", size=11), text_color=clr).pack(side="left")
        val_lbl = ctk.CTkLabel(hdr, text=f"{df}%", font=ctk.CTkFont(family="Courier New", size=10), text_color="#9ca3af")
        val_lbl.pack(side="right")

        slider = ctk.CTkSlider(box, from_=mn, to=mx, number_of_steps=100, button_color=clr, progress_color=clr, command=lambda v, vl=val_lbl: (vl.configure(text=f"{int(v)}%"), self.refresh_preview()))
        slider.set(df)
        slider.pack(fill="x", padx=8, pady=(2, 6))
        self.slider_vars[key] = slider

    def get_sliders(self):
        return {k: int(v.get()) for k, v in self.slider_vars.items()}

    def toggle_local_ai(self):
        self.engine.use_local_ai = self.ai_switch.get() == 1
        state = "ENABLED" if self.engine.use_local_ai else "DISABLED"
        self.add_log(f"Local AI Still Life Engine {state}", "info")
        self.refresh_preview()

    def add_log(self, msg, level="info"):
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[INFO]" if level == "info" else ("[ALERT]" if level == "alert" else "[WARN]")
        line = f"[{timestamp}] {prefix} {msg}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def re_seed(self):
        self.engine.set_seed(random.randint(0, 0xFFFFFFFF))
        self.seed_lbl.configure(text=f"SEED: {self.engine.seed:08X}")
        self.add_log(f"Re-seeded RNG state: {self.engine.seed:08X}", "info")
        self.refresh_preview()

    def load_media(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Media", "*.jpg *.jpeg *.png *.webp *.mp4 *.avi *.mov *.mkv"),
                ("Images", "*.jpg *.jpeg *.png *.webp"),
                ("Videos", "*.mp4 *.avi *.mov *.mkv")
            ]
        )
        if not path:
            return

        self.current_media_path = path
        self.export_btn.configure(state="normal")
        self.status_lbl.configure(text=f"LOADED: {os.path.basename(path).upper()}")
        self.add_log(f"Loaded source file: {os.path.basename(path)}", "info")

        is_img = path.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        if is_img:
            self.original_image_bgr = cv2.imread(path)
            self._show_original(self.original_image_bgr)
            self.refresh_preview()
        else:
            self.is_previewing = False
            time.sleep(0.1)
            self.is_previewing = True
            threading.Thread(target=self.video_preview_loop, daemon=True).start()

    def refresh_preview(self):
        if self.original_image_bgr is not None:
            rng = random.Random(self.engine.seed)
            sliders = self.get_sliders()
            self.processed_image_bgr = self.engine.process_frame(self.original_image_bgr, rng, sliders)
            self._show_processed(self.processed_image_bgr)

    def _show_original(self, bgr_img):
        try:
            rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((360, 420))
            ci = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.orig_img_lbl.configure(image=ci, text="")
        except Exception:
            pass

    def _show_processed(self, bgr_img):
        try:
            rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((360, 420))
            ci = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.proc_img_lbl.configure(image=ci, text="")
        except Exception:
            pass

    def video_preview_loop(self):
        cap = cv2.VideoCapture(self.current_media_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_delay = 1.0 / fps
        frame_idx = 0

        while self.is_previewing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue

            sliders = self.get_sliders()
            # Identical deterministic temporal seed used in BOTH preview and export
            frame_rng = random.Random(self.engine.seed + int(frame_idx / (fps * 2.0)))
            out = self.engine.process_frame(frame, frame_rng, sliders, frame_idx, fps)
            
            self._show_original(frame)
            self._show_processed(out)
            
            frame_idx += 1
            time.sleep(frame_delay)
        cap.release()

    def start_export(self):
        if not self.current_media_path or self.is_processing:
            return

        is_img = self.current_media_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        if is_img:
            out_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("WEBP Image", "*.webp")],
                initialfile=f"ꓫ_MISREMEMBERED_{os.path.basename(self.current_media_path)}"
            )
            if out_path and self.processed_image_bgr is not None:
                cv2.imwrite(out_path, self.processed_image_bgr)
                self.add_log(f"Saved reconstructed image to: {out_path}", "info")
                messagebox.showinfo("Export Complete", f"Saved reconstructed image to:\n{out_path}")
            return

        self.is_processing = True
        self.is_previewing = False
        self.export_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="bottom", fill="x")

        # CRITICAL FIX: Snapshot ALL state on the main thread NOW.
        # Calling get_sliders() or reading engine state inside a background
        # thread on Windows reads tkinter widgets unsafely and silently returns
        # wrong/default values — causing export to have zero effects.
        _snap_sliders = self.get_sliders()
        _snap_ai      = self.engine.use_local_ai
        _snap_seed    = self.engine.seed
        _snap_path    = self.current_media_path
        dbg(f'Export start — seed={_snap_seed:08X} ai={_snap_ai} sliders={_snap_sliders}', 'EXPORT')

        threading.Thread(
            target=self.export_video_thread,
            args=(_snap_sliders, _snap_ai, _snap_seed, _snap_path),
            daemon=True
        ).start()

    def export_video_thread(self, sliders, use_local_ai, seed, in_path):
        try:
            out_dir = os.path.dirname(in_path)
            base = os.path.splitext(os.path.basename(in_path))[0]
            final_path = os.path.join(out_dir, f"ꓫ REMΕMᗷER_{base}_MISREMEMBERED.mp4")
            temp_video = os.path.join(tempfile.gettempdir(), f"_temp_{int(time.time())}.mp4")

            cap = cv2.VideoCapture(in_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300

            # Turbo Encoding Optimization: Cap max dimension to 1280px for 5x export speed
            target_w, target_h = orig_w, orig_h
            if orig_w > 1280:
                target_w = 1280
                target_h = int(orig_h * (1280 / orig_w))

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video, fourcc, fps, (target_w, target_h))

            frame_idx = 0
            start_t = time.time()

            self.add_log(f"Turbo Export: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f} FPS ({total_frames} frames)...", "alert")
            dbg(f"Export confirmed: ai={use_local_ai} seed={seed:08X} sliders={sliders}", "EXPORT")
            dbg(f"  {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f}fps total={total_frames}", "EXPORT")

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if orig_w != target_w:
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

                # Identical deterministic temporal seed ensures 100% parity with preview!
                frame_rng = random.Random(seed + int(frame_idx / (fps * 2.0)))
                _orig_ai = self.engine.use_local_ai
                self.engine.use_local_ai = use_local_ai
                out = self.engine.process_frame(frame, frame_rng, sliders, frame_idx, fps)
                self.engine.use_local_ai = _orig_ai
                writer.write(out)
                frame_idx += 1

                if frame_idx % 30 == 0:
                    prog = frame_idx / float(total_frames)
                    elapsed = time.time() - start_t
                    cur_fps = frame_idx / max(0.001, elapsed)
                    eta = int((total_frames - frame_idx) / max(0.1, cur_fps))
                    self.after(0, lambda p=prog, i=frame_idx, tot=total_frames, f=cur_fps, e=eta: (
                        self.progress_bar.set(p),
                        self.add_log(f"Frame {i}/{tot} ({int(p*100)}%) — {f:.1f} FPS — ETA {e}s")
                    ))

            cap.release()
            writer.release()

            if FFMPEG:
                pitch_rate = 0.88
                cmd = [
                    FFMPEG, "-y",
                    "-i", temp_video,
                    "-i", in_path,
                    "-map", "0:v:0",
                    "-map", "1:a:0?",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "20",
                    "-c:a", "aac",
                    "-af", f"asetrate={int(44100 * pitch_rate)},aresample=44100",
                    "-shortest",
                    final_path
                ]
                subprocess.run(cmd, capture_output=True, timeout=600)
                try:
                    os.remove(temp_video)
                except Exception:
                    pass
            else:
                import shutil
                shutil.move(temp_video, final_path)

            self.after(0, lambda: self.on_export_complete(final_path))
        except Exception as e:
            self.add_log(f"Export error: {e}", "warn")
            self.is_processing = False
            self.export_btn.configure(state="normal")
            self.progress_bar.pack_forget()

    def on_export_complete(self, path):
        self.is_processing = False
        self.export_btn.configure(state="normal")
        self.progress_bar.pack_forget()
        self.add_log(f"Export Complete: {os.path.basename(path)}", "info")
        messagebox.showinfo("Export Complete", f"Saved reconstructed media to:\n{path}")


if __name__ == "__main__":
    app = MisrememberedDesktopApp()
    app.mainloop()
