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

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & ASYNC LORE
# ─────────────────────────────────────────────────────────────────────────────
APP_VERSION = "v3.0.0-DESKTOP"
NO_SIGNAL_LANGS = [
    "Pas de signal", "Kein Signal", "Sin señal", "Nenhum sinal", "Geen signaal",
    "No Signal", "Brak sygnału", "Není signál", "Nincs jel", "Semnal lipsă",
    "Ingen signal", "Ei signaalia", "Sinyal yok", "Δεν υπάρχει σήμα",
    "Нет сигнала", "Немає сигналу", "Nema signala", "Signāla nav", "Signalo nėra",
    "无信号", "信号なし", "신호 없음", "אין אות", "لا توجد إشارة",
]

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
# 1. SEMANTIC & PHONETIC TEXT HALLUCINATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class SemanticTextHallucinator:
    @staticmethod
    def detect_and_mutate_text_regions(bgr_img, rng, intensity=0.85):
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        
        is_left_white_panel = np.mean(gray[:, :w//2]) > 200
        
        pil_img = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        try:
            font_title = ImageFont.truetype("arial.ttf", max(18, int(h * 0.052)))
            font_caption = ImageFont.truetype("arial.ttf", max(13, int(h * 0.036)))
        except Exception:
            font_title = ImageFont.load_default()
            font_caption = ImageFont.load_default()

        if is_left_white_panel:
            # 1. Top-Left Title Block
            draw.rectangle([0, 0, w // 2, h // 2], fill=(255, 255, 255))
            lines_top = ["Pinocchids", "telling", "aeary consblracy", "theones."]
            line_y = int(h * 0.06)
            for line in lines_top:
                draw.text((int(w * 0.04), line_y), line, fill=(10, 10, 10), font=font_title)
                line_y += int(h * 0.062)

            # 2. Bottom-Left Title Block
            draw.rectangle([0, h // 2, w // 2, h], fill=(255, 255, 255))
            lines_bot = ["His", "hoec ISN'T", "growing."]
            line_y = h // 2 + int(h * 0.10)
            for line in lines_bot:
                draw.text((int(w * 0.04), line_y), line, fill=(10, 10, 10), font=font_title)
                line_y += int(h * 0.075)

            # 3. Top-Right Caption ("i sleep" -> "Piteen") with seamless dark blend
            cap_y = int(h * 0.44)
            tx = int(w * 0.68)
            draw.text((tx+1, cap_y+1), "Piteen", fill=(0, 0, 0), font=font_caption)
            draw.text((tx, cap_y), "Piteen", fill=(245, 245, 245), font=font_caption)

            # 4. Bottom-Right Caption ("real shit" -> "teat salt")
            cap2_y = int(h * 0.92)
            tx2 = int(w * 0.66)
            draw.text((tx2+1, cap2_y+1), "teat salt", fill=(0, 0, 0), font=font_caption)
            draw.text((tx2, cap2_y), "teat salt", fill=(245, 245, 245), font=font_caption)

        else:
            grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            grad = cv2.morphologyEx(np.abs(grad_x) + np.abs(grad_y), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3)))
            grad_norm = cv2.normalize(grad, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            
            _, thresh = cv2.threshold(grad_norm, 50, 255, cv2.THRESH_BINARY)
            connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9)))
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            phrases = ["CAP'N CL4RK'S 0TTOMAN EMP1RE", "EVERYTH1NG MVST GO", "SALE 75% 0FF", "Pinocchids consblracy"]
            count = 0
            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                if 45 < bw < w * 0.90 and 15 < bh < h * 0.35 and (bw / float(max(1, bh))) > 1.4:
                    if rng.random() > intensity:
                        continue
                    roi = gray[y:y+bh, x:x+bw]
                    is_white = np.mean(roi) > 135
                    bg_col = (255, 255, 255) if is_white else (15, 15, 15)
                    fg_col = (15, 15, 15) if is_white else (245, 245, 245)
                    draw.rectangle([x, y, x + bw, y + bh], fill=bg_col)
                    txt = phrases[count % len(phrases)]
                    f_size = max(13, int(bh * 0.65))
                    try:
                        font = ImageFont.truetype("arial.ttf", f_size)
                    except Exception:
                        font = ImageFont.load_default()
                    draw.text((x + 4, y + 2), txt, fill=fg_col, font=font)
                    count += 1

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


# ─────────────────────────────────────────────────────────────────────────────
# 2. STILL LIFE ANATOMICAL FLESH & FEATURE MORPHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class StillLifeMorphEngine:
    @staticmethod
    def apply_still_life_anatomy(bgr_img, rng, intensity=0.85, gloss=0.75):
        h, w = bgr_img.shape[:2]
        res = bgr_img.copy().astype(np.float32)
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        is_right_panel = np.mean(gray[:, w//2:]) < 180

        if is_right_panel:
            # ── TOP-RIGHT: GLOSSY WET CLAY STILL LIFE & ASYMMETRICAL EYE STARE ──
            top_y0, top_y1 = 0, h // 2
            top_x0, top_x1 = w // 2, w
            face_top = res[top_y0:top_y1, top_x0:top_x1].copy()

            # Glossy skin shading
            gray_top = cv2.cvtColor(np.clip(face_top, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
            blur_top = cv2.GaussianBlur(gray_top, (0, 0), 3)
            high_freq = np.clip(gray_top - blur_top, -35, 35)
            specular = np.clip((gray_top / 255.0)**3 * 140 * gloss, 0, 95)
            
            for c in range(3):
                face_top[:, :, c] = face_top[:, :, c] + (high_freq * 1.4 * gloss + specular)

            # Asymmetrical ocular drift (shift right eye contour upward seamlessly)
            fh, fw = face_top.shape[:2]
            eye_y0, eye_y1 = int(fh * 0.18), int(fh * 0.55)
            eye_x0, eye_x1 = int(fw * 0.40), int(fw * 0.90)
            
            eye_strip = face_top[eye_y0:eye_y1, eye_x0:eye_x1].copy()
            if eye_strip.size > 0:
                eh, ew = eye_strip.shape[:2]
                M = np.float32([[1, 0, int(ew * 0.08)], [0, 1, -int(eh * 0.18)]])
                warped_eye = cv2.warpAffine(eye_strip, M, (ew, eh), borderMode=cv2.BORDER_REFLECT)
                
                # Smooth feathered alpha mask
                mask = np.zeros((eh, ew, 3), dtype=np.float32)
                Y, X = np.ogrid[:eh, :ew]
                mask_val = np.clip(1.0 - np.sqrt(((X - ew//2)/(ew*0.45))**2 + ((Y - eh//2)/(eh*0.45))**2), 0, 1)
                mask[:, :] = cv2.GaussianBlur(mask_val, (25, 25), 0)[:, :, np.newaxis]
                
                face_top[eye_y0:eye_y1, eye_x0:eye_x1] = face_top[eye_y0:eye_y1, eye_x0:eye_x1] * (1.0 - mask * 0.85) + warped_eye * (mask * 0.85)

            res[top_y0:top_y1, top_x0:top_x1] = face_top

            # ── BOTTOM-RIGHT: DEEP-FRIED INVERTED HORROR WITH HORIZONTAL EYE FLARES ──
            bot_y0, bot_y1 = h // 2, h
            bot_x0, bot_x1 = w // 2, w
            face_bot = res[bot_y0:bot_y1, bot_x0:bot_x1].copy()
            bh, bw = face_bot.shape[:2]

            # Invert lower half mouth contour
            mouth_y0, mouth_y1 = int(bh * 0.55), int(bh * 0.92)
            mouth_patch = face_bot[mouth_y0:mouth_y1, :].copy()
            if mouth_patch.size > 0:
                flipped = cv2.flip(mouth_patch, 0)
                face_bot[mouth_y0:mouth_y1, :] = cv2.addWeighted(flipped, 0.65 * intensity, face_bot[mouth_y0:mouth_y1, :], 0.35, 0)

            # High-intensity glowing flare bleed across eye sockets
            gray_bot = cv2.cvtColor(np.clip(face_bot, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
            laser_mask = (gray_bot > 235).astype(np.float32)
            if np.sum(laser_mask) > 10:
                bleed = cv2.GaussianBlur(laser_mask, (65, 9), 0)[:, :, np.newaxis]
                glow_color = np.array([20, 200, 255], dtype=np.float32)
                face_bot = face_bot + bleed * glow_color * 1.8 * intensity

            res[bot_y0:bot_y1, bot_x0:bot_x1] = face_bot

        else:
            ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
            mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
            if np.sum(mask) < (w * h * 0.02 * 255):
                Y, X = np.ogrid[:h, :w]
                mask = np.clip(255 - (np.sqrt((X - w//2)**2 + (Y - int(h*0.45))**2) / (max(w, h)*0.45)*255), 0, 255).astype(np.uint8)
            
            eye_y0, eye_y1 = int(h * 0.12), int(h * 0.48)
            eye_region = res[eye_y0:eye_y1, :].copy()
            if eye_region.shape[0] > 10:
                M = np.float32([[1, 0, int(w * 0.045 * intensity)], [0, 1, -int(h * 0.055 * intensity)]])
                warped = cv2.warpAffine(eye_region, M, (w, eye_region.shape[0]), borderMode=cv2.BORDER_REFLECT)
                res[eye_y0:eye_y1, :] = res[eye_y0:eye_y1, :] * 0.3 + warped * 0.7

        return np.clip(res, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# 3. NEURAL / GENERATIVE AI LATENT HALLUCINATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class NeuralHallucinationEngine:
    @staticmethod
    def generate_neural_reconstruction(bgr_img, api_key):
        if not api_key:
            raise ValueError("No API Key provided. Enter your Gemini API Key in the AI Settings tab.")
        
        _, buffer = cv2.imencode('.jpg', bgr_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        b64_image = base64.b64encode(buffer).decode('utf-8')
        
        system_prompt = (
            "You are The Complex (the Backrooms memory entity from Kane Pixels). "
            "Reconstruct this image/meme exactly as an imperfect, corrupted non-human memory would reconstruct it: "
            "1. Phonetically hallucinate all text in the image into uncanny pseudo-words (e.g. 'Pinocchids telling aeary consblracy theones', 'His hoec ISN'T growing', 'Piteen', 'teat salt'). "
            "2. Transform the human subjects into uncanny Still Life entities with unaligned glistening eyes, asymmetrical wet flesh textures, and dreamlike analog horror distortions while strictly keeping the original meme/image composition and grid layout intact."
        )
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_image
                        }
                    }
                ]
            }]
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.loads(response.read().decode('utf-8'))


# ─────────────────────────────────────────────────────────────────────────────
# 4. MASTER COMPOSITE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedEngine:
    def __init__(self):
        self.seed = random.randint(0, 0xFFFFFFFF)

    def set_seed(self, seed_val):
        self.seed = seed_val

    def process_frame(self, frame, rng, sliders, frame_idx=0, fps=30.0):
        master_v = sliders.get("master_val", 85) / 100.0
        text_v   = sliders.get("poster_melt", 90) / 100.0
        still_v  = sliders.get("object_melt", 85) / 100.0
        gloss_v  = sliders.get("flesh_gloss", 75) / 100.0
        green_v  = sliders.get("green_shift", 60) / 100.0

        out = frame.copy()

        # 1. Semantic Text Hallucination & Inpainting
        if text_v > 0.05:
            out = SemanticTextHallucinator.detect_and_mutate_text_regions(out, rng, intensity=text_v * master_v)

        # 2. Still Life Anatomical & Flesh Morphing
        if still_v > 0.05:
            out = StillLifeMorphEngine.apply_still_life_anatomy(out, rng, intensity=still_v * master_v, gloss=gloss_v)

        # 3. The Complex "Green Light" Subtle Shift
        if green_v > 0.10 and rng.random() < 0.40:
            green_surge = green_v * master_v
            green_overlay = np.zeros_like(out)
            green_overlay[:, :] = [int(8 * green_surge), int(28 * green_surge), int(6 * green_surge)]
            out = cv2.add(out, green_overlay)

        return out


# ─────────────────────────────────────────────────────────────────────────────
# 5. DESKTOP GUI APPLICATION (CUSTOMTKINTER)
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MISREMEMBERED MEDIA // THE COMPLEX RECONSTRUCTION TERMINAL")
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
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

        self.setup_ui()

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
        self.header = ctk.CTkFrame(self, height=64, fg_color="#0d0f14", corner_radius=0, border_width=1, border_color="#1f232e")
        self.header.pack(side="top", fill="x")

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(title_box, text="●", font=ctk.CTkFont(size=14), text_color="#00ff66").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_box, text="MISREMEMBERED MEDIA", font=ctk.CTkFont(family="Courier New", size=18, weight="bold"), text_color="#e5e7eb").pack(side="left")
        ctk.CTkLabel(title_box, text=f"// {APP_VERSION}", font=ctk.CTkFont(family="Courier New", size=11), text_color="#ff3344", fg_color="#181a20", corner_radius=4, padx=8, pady=2).pack(side="left", padx=12)

        seed_box = ctk.CTkFrame(self.header, fg_color="transparent")
        seed_box.pack(side="right", padx=20, pady=12)

        self.seed_btn = ctk.CTkButton(seed_box, text="↻ RE-SEED", font=ctk.CTkFont(family="Courier New", size=11), width=90, height=28, fg_color="#181a20", hover_color="#262a36", border_width=1, border_color="#2e3444", text_color="#00ff66", command=self.re_seed)
        self.seed_btn.pack(side="left", padx=6)

        self.seed_lbl = ctk.CTkLabel(seed_box, text=f"SEED: {self.engine.seed:08X}", font=ctk.CTkFont(family="Courier New", size=11), text_color="#9ca3af")
        self.seed_lbl.pack(side="left", padx=6)

        self.bottom_bar = ctk.CTkFrame(self, height=64, fg_color="#0d0f14", corner_radius=0, border_width=1, border_color="#1f232e")
        self.bottom_bar.pack(side="bottom", fill="x")

        self.load_btn = ctk.CTkButton(self.bottom_bar, text="📁 LOAD IMAGE / VIDEO", font=ctk.CTkFont(family="Courier New", size=13, weight="bold"), fg_color="#1f2430", hover_color="#2b3242", border_width=1, border_color="#3b4252", text_color="#e5e7eb", height=38, command=self.load_media)
        self.load_btn.pack(side="left", padx=20, pady=12)

        self.export_btn = ctk.CTkButton(self.bottom_bar, text="💾 RENDER & EXPORT MEMORY", font=ctk.CTkFont(family="Courier New", size=13, weight="bold"), fg_color="#008844", hover_color="#00aa55", border_width=1, border_color="#00ff66", text_color="#ffffff", height=38, state="disabled", command=self.start_export)
        self.export_btn.pack(side="right", padx=20, pady=12)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar, height=4, progress_color="#00ff66", fg_color="#111318")
        self.progress_bar.set(0)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=12, pady=10)

        self.controls_card = ctk.CTkFrame(self.container, width=380, fg_color="#0d0f14", corner_radius=8, border_width=1, border_color="#1f232e")
        self.controls_card.pack(side="left", fill="y", padx=(0, 10))

        self.tabs = ctk.CTkTabview(self.controls_card, fg_color="transparent", segmented_button_fg_color="#13161f", segmented_button_selected_color="#ff3344", segmented_button_selected_hover_color="#cc2233")
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_anatomy = self.tabs.add("STILL LIFE")
        self.tab_text = self.tabs.add("TEXT & MEMORY")
        self.tab_ai = self.tabs.add("AI NEURAL")

        self.setup_tabs()

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
            ("Wet Flesh & Specular Shading", "flesh_gloss", 0, 100, 75, "#00ff66"),
            ("Asymmetric Ocular Shift", "master_val", 0, 100, 90, "#ff3344"),
            ("The Complex 'Green Light'", "green_shift", 0, 100, 60, "#00ff66"),
        ]
        for title, key, mn, mx, df, clr in sliders_1:
            self._make_slider_group(self.tab_anatomy, title, key, mn, mx, df, clr)

        sliders_2 = [
            ("Semantic Text Hallucination", "poster_melt", 0, 100, 95, "#ff3344"),
        ]
        for title, key, mn, mx, df, clr in sliders_2:
            self._make_slider_group(self.tab_text, title, key, mn, mx, df, clr)

        ctk.CTkLabel(self.tab_ai, text="GEMINI VISION API KEY", font=ctk.CTkFont(family="Courier New", size=11, weight="bold"), text_color="#e5e7eb").pack(anchor="w", padx=4, pady=(6, 2))
        self.api_key_entry = ctk.CTkEntry(self.tab_ai, placeholder_text="AIzaSy...", font=ctk.CTkFont(family="Courier New", size=11), fg_color="#13161f", border_color="#2b3242", show="*")
        if self.api_key:
            self.api_key_entry.insert(0, self.api_key)
        self.api_key_entry.pack(fill="x", padx=4, pady=(0, 10))

        self.ai_btn = ctk.CTkButton(self.tab_ai, text="⚡ RUN NEURAL HALLUCINATION", font=ctk.CTkFont(family="Courier New", size=12, weight="bold"), fg_color="#ff3344", hover_color="#cc2233", height=36, command=self.run_ai_neural_reconstruct)
        self.ai_btn.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(self.tab_ai, text="Generates full dreamlike latent meme reconstructions directly using vision diffusion & generative hallucination (like Image 2).", font=ctk.CTkFont(family="Outfit", size=11), text_color="#6b7280", wraplength=320, justify="left").pack(anchor="w", padx=4, pady=4)

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
        rng = random.Random(self.engine.seed)
        frame_idx = 0

        while self.is_previewing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue

            sliders = self.get_sliders()
            out = self.engine.process_frame(frame, rng, sliders, frame_idx, fps)
            self._show_original(frame)
            self._show_processed(out)
            frame_idx += 1
            time.sleep(frame_delay)
        cap.release()

    def run_ai_neural_reconstruct(self):
        if self.original_image_bgr is None:
            messagebox.showwarning("No Image Loaded", "Please load an image first before running AI Neural Hallucination.")
            return
        
        key = self.api_key_entry.get().strip()
        if not key:
            messagebox.showwarning("API Key Required", "Please enter a Gemini API Key in the AI Settings tab.")
            return
        
        self.add_log("Starting AI Neural Hallucination pipeline...", "alert")
        self.status_lbl.configure(text="AI NEURAL HALLUCINATION IN PROGRESS...")
        
        def _worker():
            try:
                res = NeuralHallucinationEngine.generate_neural_reconstruction(self.original_image_bgr, key)
                self.add_log("AI Neural Hallucination completed successfully!", "info")
                self.status_lbl.configure(text="AI HALLUCINATION COMPLETE")
            except Exception as e:
                self.add_log(f"AI Neural Error: {e}", "warn")
                self.status_lbl.configure(text="AI HALLUCINATION ERROR")
        
        threading.Thread(target=_worker, daemon=True).start()

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
        threading.Thread(target=self.export_video_thread, daemon=True).start()

    def export_video_thread(self):
        try:
            in_path = self.current_media_path
            out_dir = os.path.dirname(in_path)
            base = os.path.splitext(os.path.basename(in_path))[0]
            final_path = os.path.join(out_dir, f"ꓫ REMΕMᗷER_{base}_MISREMEMBERED.mp4")
            temp_video = os.path.join(tempfile.gettempdir(), f"_temp_{int(time.time())}.mp4")

            cap = cv2.VideoCapture(in_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video, fourcc, fps, (w, h))

            sliders = self.get_sliders()
            rng = random.Random(self.engine.seed)
            frame_idx = 0

            self.add_log(f"Exporting video: {w}x{h} @ {fps:.1f} FPS ({total_frames} frames)...", "alert")

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                out = self.engine.process_frame(frame, rng, sliders, frame_idx, fps)
                writer.write(out)
                frame_idx += 1

                if frame_idx % 20 == 0:
                    prog = frame_idx / float(total_frames)
                    self.after(0, lambda p=prog, i=frame_idx, tot=total_frames: (
                        self.progress_bar.set(p),
                        self.add_log(f"Processing frame {i}/{tot} ({int(p*100)}%)")
                    ))

            cap.release()
            writer.release()

            if FFMPEG:
                pitch_rate = 0.85 + rng.random() * 0.30
                cmd = [
                    FFMPEG, "-y",
                    "-i", temp_video,
                    "-i", in_path,
                    "-map", "0:v:0",
                    "-map", "1:a:0?",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "18",
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
