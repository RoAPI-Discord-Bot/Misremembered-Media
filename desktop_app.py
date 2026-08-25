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
import scipy.signal as signal
from scipy.io import wavfile
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APP_VERSION = "v3.5.0-FORGETS-PRO"

# ─────────────────────────────────────────────────────────────────────────────
# EXTERNAL DEBUG TERMINAL
# Opens a separate PowerShell window showing live debug output in real-time.
# ─────────────────────────────────────────────────────────────────────────────
_DEBUG_LOG = os.path.join(tempfile.gettempdir(), "misremembered_debug.log")
_dbg_lock = threading.Lock()

def dbg(msg, tag="INFO"):
    """Write a timestamped debug line to external terminal and stdout."""
    ts = time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"
    line = f"[{ts}] [{tag:<6}] {msg}\n"
    print(line, end="", flush=True)
    with _dbg_lock:
        try:
            with open(_DEBUG_LOG, "a", encoding="utf-8") as _f:
                _f.write(line)
        except Exception:
            pass

def _launch_debug_terminal():
    """Open a separate PowerShell window only if not already running in an interactive terminal."""
    # If already running inside an interactive PowerShell / CMD prompt, don't spawn a second console!
    if sys.stdout and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        dbg("Running in interactive terminal — live logs stream directly to current console.", "INIT")
        return

    try:
        with open(_DEBUG_LOG, "w", encoding="utf-8") as _f:
            _f.write(f"=== MISREMEMBERED MEDIA {APP_VERSION} LIVE DEBUG ===\n")
            _f.write(f"=== Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        lp = _DEBUG_LOG.replace("\\", "\\\\")
        ps = (
            f"$f='{lp}';$pos=0;"
            "while($true){"
            "$s=New-Object IO.FileStream($f,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);"
            "$r=New-Object IO.StreamReader($s);"
            "$s.Seek($pos,[IO.SeekOrigin]::Begin)|Out-Null;"
            "$t=$r.ReadToEnd();"
            "if($t){Write-Host $t -NoNewline};"
            "$pos=$s.Length;$r.Close();$s.Close();"
            "Start-Sleep -Milliseconds 150}"
        )
        subprocess.Popen(
            ["powershell.exe", "-NoExit", "-Command", ps],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        dbg("External live debug terminal launched successfully", "INIT")
    except Exception as e:
        print(f"[DEBUG] Terminal error: {e}", file=sys.stderr)

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

NO_SIGNAL_LANGS = [
    "Pas de signal", "Kein Signal", "Sin señal", "Nenhum sinal", "Geen signaal",
    "No Signal", "Brak sygnału", "Není signál", "Nincs jel", "Semnal lipsă",
    "Ingen signal", "Ei signaalia", "Sinyal yok", "Δεν υπάρχει σήμα",
    "Нет сигнала", "Немає сигналу", "Nema signala", "Signāla nav", "Signalo nėra",
    "无信号", "信号なし", "신호 없음", "אין אות", "لا توجد إشارة",
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. KANE PIXELS BACKROOMS AUDIO DSP ENGINE
# Analog tape wow/flutter/stalls, weighted intervals (20/45/35),
# liminal drywall/concrete Schroeder reverb, 60Hz buzz, and Green Light transformer hum
# ─────────────────────────────────────────────────────────────────────────────
class KanePixelsAudioDSP:
    @staticmethod
    def synthesize_fluorescent_hum(n_samples, sr=44100, gain=0.032):
        """Generates authentic Backrooms 60Hz + harmonic fluorescent light buzz."""
        t = np.linspace(0, n_samples / sr, n_samples, endpoint=False)
        hum = (
            0.48 * np.sin(2 * np.pi * 60 * t) +
            0.36 * np.sin(2 * np.pi * 120 * t) +
            0.22 * np.sin(2 * np.pi * 180 * t) +
            0.14 * np.sin(2 * np.pi * 240 * t) +
            0.08 * np.sin(2 * np.pi * 360 * t) +
            0.05 * np.sin(2 * np.pi * 480 * t)
        )
        mod = 0.85 + 0.15 * np.sin(2 * np.pi * 0.4 * t) + 0.08 * np.sin(2 * np.pi * 2.3 * t)
        noise = np.random.normal(0, 0.035, n_samples)
        out = (hum * mod + noise) * gain
        return np.column_stack((out, out)).astype(np.float32)

    @staticmethod
    def apply_tape_warp(audio, sr=44100, seed=12345, intensity=0.85):
        """
        Applies continuous analog tape speed drift, weighted Kane Pixels intervals
        (20% normal / 45% warped / 35% low drag), and sporadic tape stalls.
        """
        rng = random.Random(seed)
        n_samples = len(audio)
        duration = n_samples / sr
        t = np.linspace(0, duration, n_samples, endpoint=False)

        # 1. Base speed intervals (3.0s to 5.5s chunks)
        speed_curve = np.ones(n_samples, dtype=np.float32)
        chunk_t = 0.0
        while chunk_t < duration:
            chunk_len = rng.uniform(3.0, 5.5)
            i0 = int(chunk_t * sr)
            i1 = min(n_samples, int((chunk_t + chunk_len) * sr))
            
            # Kane Pixels weighted distribution: 20% normal / 45% warped / 35% low drag
            roll = rng.random()
            if roll < 0.20:
                base_speed = rng.uniform(0.97, 1.03)
            elif roll < 0.65:
                base_speed = rng.uniform(0.82, 0.91) if rng.random() < 0.55 else rng.uniform(1.08, 1.18)
            else:
                base_speed = rng.uniform(0.66, 0.78)

            eff_speed = 1.0 + (base_speed - 1.0) * intensity
            speed_curve[i0:i1] = eff_speed
            chunk_t += chunk_len

        # Smooth interval transitions (250ms Hann window)
        smooth_len = max(5, int(sr * 0.25))
        window = np.hanning(smooth_len)
        window /= window.sum()
        speed_curve = signal.convolve(speed_curve, window, mode='same')

        # 2. Add continuous tape flutter and micro-wobble
        flutter = (
            0.020 * np.sin(2 * np.pi * 0.35 * t + rng.uniform(0, 6.28)) +
            0.012 * np.sin(2 * np.pi * 1.80 * t + rng.uniform(0, 6.28)) +
            0.006 * np.sin(2 * np.pi * 5.20 * t + rng.uniform(0, 6.28))
        ) * intensity
        speed_curve = np.clip(speed_curve + flutter, 0.50, 1.45)

        # 3. Sporadic tape catch / drag dropouts
        n_stalls = max(1, int(duration / 7.0))
        for _ in range(n_stalls):
            stall_center = rng.uniform(1.0, max(1.5, duration - 1.0))
            stall_w = rng.uniform(0.4, 0.9)
            stall_idx0 = max(0, int((stall_center - stall_w / 2) * sr))
            stall_idx1 = min(n_samples, int((stall_center + stall_w / 2) * sr))
            if stall_idx1 > stall_idx0:
                s_len = stall_idx1 - stall_idx0
                dip = 1.0 - (0.38 * intensity * np.sin(np.linspace(0, np.pi, s_len)))
                speed_curve[stall_idx0:stall_idx1] *= dip

        speed_curve = np.clip(speed_curve, 0.45, 1.50)

        # 4. Integrate speed curve to compute resampled phase positions
        dt = 1.0 / sr
        phase = np.cumsum(speed_curve) * dt * sr
        phase = phase - phase[0]

        # Resample each channel
        out = np.zeros_like(audio)
        orig_indices = np.arange(n_samples)
        for ch in range(audio.shape[1]):
            out[:, ch] = np.interp(phase, orig_indices, audio[:, ch], left=0, right=0)

        return out

    @staticmethod
    def apply_liminal_reverb(audio, sr=44100, wet=0.35, decay=0.68):
        """Multi-comb and all-pass Schroeder reverberation modeling vast empty Backrooms halls."""
        out = np.zeros_like(audio)
        delays_ms = [29.7, 37.1, 41.1, 44.3]
        
        for ch in range(audio.shape[1]):
            channel_in = audio[:, ch]
            comb_sum = np.zeros_like(channel_in)
            for d_ms in delays_ms:
                d_samples = int(sr * d_ms / 1000.0)
                if d_samples >= len(channel_in):
                    continue
                b = np.zeros(d_samples + 1)
                b[0] = 1.0
                a = np.zeros(d_samples + 1)
                a[0] = 1.0
                a[-1] = -decay * 0.82
                comb_out = signal.lfilter(b, a, channel_in)
                comb_sum += comb_out
            
            comb_sum /= len(delays_ms)

            # All-pass diffusion stages
            for ap_ms in [5.1, 1.8]:
                ap_samples = int(sr * ap_ms / 1000.0)
                if ap_samples >= len(comb_sum):
                    continue
                g = 0.55
                b_ap = np.zeros(ap_samples + 1)
                b_ap[0] = -g
                b_ap[-1] = 1.0
                a_ap = np.zeros(ap_samples + 1)
                a_ap[0] = 1.0
                a_ap[-1] = -g
                comb_sum = signal.lfilter(b_ap, a_ap, comb_sum)

            out[:, ch] = channel_in * (1.0 - wet * 0.5) + comb_sum * wet

        return out

    @staticmethod
    def apply_memory_whisper_echo(audio, sr=44100, delay_sec=2.6, gain=0.18):
        """Delayed copy passed through corridor bandpass formant filter (ghost voice echo)."""
        d_samples = int(sr * delay_sec)
        if d_samples >= len(audio):
            return audio
        
        # Bandpass 750Hz - 2600Hz
        sos = signal.butter(4, [750, 2600], btype='bandpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, audio, axis=0)

        delayed = np.zeros_like(audio)
        delayed[d_samples:] = filtered[:-d_samples] * gain
        return audio + delayed

    @staticmethod
    def apply_green_light_audio_surge(audio, sr=44100, duration_s=10.0, intensity=0.85):
        """
        Injects loud 60Hz transformer electrical buzz and sub-bass surge during Green Light events.
        """
        n_samples = len(audio)
        green_event_time = duration_s * 0.45 # Trigger at 45% of video
        event_dur = 2.4 # 2.4s duration
        
        idx0 = int(green_event_time * sr)
        idx1 = min(n_samples, int((green_event_time + event_dur) * sr))
        
        if idx1 > idx0:
            seg_len = idx1 - idx0
            t = np.linspace(0, seg_len / sr, seg_len, endpoint=False)
            # Envelope: fast rise, plateau, smooth fade out
            env = np.sin(np.linspace(0, np.pi, seg_len)) ** 1.5
            
            # Sub-bass rumble + heavy 60Hz/120Hz transformer hum
            buzz = (
                0.60 * np.sin(2 * np.pi * 58.0 * t) +
                0.40 * np.sin(2 * np.pi * 116.0 * t) +
                0.25 * np.sin(2 * np.pi * 232.0 * t) +
                0.15 * np.random.normal(0, 0.1, seg_len)
            ) * env * (0.28 * intensity)
            
            audio[idx0:idx1, 0] += buzz
            audio[idx0:idx1, 1] += buzz

        return audio

    @staticmethod
    def process_full_audio(audio, sr=44100, seed=12345, sliders=None):
        if sliders is None:
            sliders = {}
        master_v = sliders.get("master_val", 85) / 100.0
        green_v  = sliders.get("green_shift", 60) / 100.0
        
        # Ensure float32 stereo (-1.0 to 1.0)
        if audio.dtype == np.int16:
            audio_f = (audio.astype(np.float32) / 32768.0)
        elif audio.dtype == np.int32:
            audio_f = (audio.astype(np.float32) / 2147483648.0)
        else:
            audio_f = audio.astype(np.float32).copy()

        if audio_f.ndim == 1:
            audio_f = np.column_stack((audio_f, audio_f))

        duration_s = len(audio_f) / float(sr)
        dbg(f"Audio DSP: Processing {duration_s:.1f}s audio track with Kane Pixels parameters...", "AUDIO")

        # 1. Analog tape warping with weighted pitch intervals & stalls
        warped = KanePixelsAudioDSP.apply_tape_warp(audio_f, sr=sr, seed=seed, intensity=master_v)

        # 2. Backrooms vast liminal reverb
        reverbed = KanePixelsAudioDSP.apply_liminal_reverb(warped, sr=sr, wet=0.38 * master_v, decay=0.70)

        # 3. Ghost memory whisper echo
        with_echo = KanePixelsAudioDSP.apply_memory_whisper_echo(reverbed, sr=sr, delay_sec=2.6, gain=0.20 * master_v)

        # 4. Fluorescent light 60Hz electromagnetic hum
        hum = KanePixelsAudioDSP.synthesize_fluorescent_hum(len(with_echo), sr=sr, gain=0.030 * master_v)
        mixed = with_echo + hum

        # 5. Green Light Complex loud electrical hum surge
        if green_v > 0.10:
            mixed = KanePixelsAudioDSP.apply_green_light_audio_surge(mixed, sr=sr, duration_s=duration_s, intensity=green_v * master_v)

        # 6. Camcorder AGC & soft saturation limiter (prevent clipping)
        saturated = np.tanh(mixed * 1.15) / 1.15
        
        # Convert back to int16
        out_int16 = np.clip(saturated * 32767.0, -32767.0, 32767.0).astype(np.int16)
        dbg(f"Audio DSP: Processing complete.", "AUDIO")
        return out_int16


# ─────────────────────────────────────────────────────────────────────────────
# 2. KANE PIXELS "FORGETS / STILL LIFE" TEXT CORRUPTOR
# Full implementation of the 5 authentic Kane Pixels text corruption modes:
# - Inpainted box & multi-language / phonetic duplicate overlay (Ref 1)
# - Vertical barcode smear / dripping lines (Ref 5)
# - In-place razor glyph serration (Ref 3)
# - Horizontal bisect & inverted mirror fold (Ref 4)
# - Angled ghost trailing & offset layers (Ref 2)
# ─────────────────────────────────────────────────────────────────────────────
INTERNATIONAL_PHRASES = [
    # Japanese
    "記憶の喪失", "立ち入り禁止", "存在しない部屋", "忘れた名前", "警告",
    # Russian
    "ПАМЯТЬ СТЕРТА", "НЕ СМОТРИ НАЗАД", "ВЫХОДА НЕТ", "ОШИБКА СВЯЗИ", "ОСТАНОВИСЬ",
    # French
    "SOUVENIR PERDU", "NE REGARDE PAS", "AUCUN SIGNAL", "OUBLIE-MOI", "ZONE INTERDITE",
    # German
    "VERLORENE ERINNERUNG", "KEIN ZURÜCK", "SYSTEM FEHLER", "NICHT ANFASSEN",
    # Spanish
    "MEMORIA PERDIDA", "NO MIRES", "SIN SALIDA", "REGISTRO BORRADO",
    # Romanian / Latin / Greek
    "FĂRĂ SEMNAL", "ΔΕＮ ΥΠΑΡΧΕΙ", "MEMORIA DAMNATA", "NON RESPIRARE"
]

class LocalGlyphCorruptor:
    @staticmethod
    def generate_phonetic_mutation(word_len, rng):
        # 35% chance to output an authentic international anomaly phrase
        if rng.random() < 0.35:
            return rng.choice(INTERNATIONAL_PHRASES)

        vowels = ['a', 'e', 'i', 'o', 'u', 'ea', 'oe', 'ai']
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'sh', 'th', 'ch', 'bl', 'st', 'cl']
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
    def corrupt_actual_frame_text(bgr_img, rng, intensity=0.85, frame_idx=0, fps=30.0):
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        
        # Fast 4x Accelerated Sobel Gradient on Half-Resolution
        scale_factor = 2
        gray_small = cv2.resize(gray, (w // scale_factor, h // scale_factor), interpolation=cv2.INTER_LINEAR)
        grad_x = cv2.Sobel(gray_small, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray_small, cv2.CV_32F, 0, 1, ksize=3)
        grad = cv2.morphologyEx(np.abs(grad_x) + np.abs(grad_y), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (8, 2)))
        grad_norm = cv2.normalize(grad, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        _, thresh = cv2.threshold(grad_norm, 55, 255, cv2.THRESH_BINARY)
        connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (10, 4)))
        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        out = bgr_img.copy()
        pil_img = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        corrupted_count = 0
        max_corrupt = 6

        for cnt in contours:
            if corrupted_count >= max_corrupt:
                break

            sx, sy, sbw, sbh = cv2.boundingRect(cnt)
            # Scale coordinates back up to full resolution
            x, y, bw, bh = sx * scale_factor, sy * scale_factor, sbw * scale_factor, sbh * scale_factor
            aspect = bw / float(max(1, bh))
            area = bw * bh

            if 25 < bw < w * 0.95 and 10 < bh < h * 0.40 and aspect > 1.1 and area > 350:
                if rng.random() > intensity:
                    continue

                roi = gray[y:y+bh, x:x+bw]
                is_white_bg = np.mean(roi) > 135

                # ── COMPOUNDING KANE PIXELS "FORGETS / STILL LIFE" TEXT DISTORTION ──
                patch = out[y:y+bh, x:x+bw].copy()
                if patch.size == 0:
                    continue

                # 1. In-Place Razor Glyph Serration & Vertical Slicing (Ref 3)
                if intensity > 0.20:
                    strip_w = max(2, int(bh * 0.16))
                    for sx_pos in range(0, bw, strip_w * 2):
                        ex_pos = min(bw, sx_pos + strip_w)
                        shift = rng.choice([-1, 1]) * rng.randint(2, max(3, int(bh * 0.22)))
                        M = np.float32([[1, 0, 0], [0, 1, shift]])
                        patch[:, sx_pos:ex_pos] = cv2.warpAffine(patch[:, sx_pos:ex_pos], M, (ex_pos - sx_pos, bh), borderMode=cv2.BORDER_REFLECT)
                    out[y:y+bh, x:x+bw] = patch

                # 2. Horizontal Bisect & Inversion Seam (Ref 4)
                if intensity > 0.35 and rng.random() < 0.65:
                    half_h = bh // 2
                    if half_h > 2:
                        flipped_lower = cv2.flip(patch[half_h:, :], -1)
                        patch[half_h:, :] = cv2.addWeighted(flipped_lower, 0.85, patch[half_h:, :], 0.15, 0)
                        bar_h = max(2, int(bh * 0.10))
                        patch[half_h-bar_h//2:half_h+bar_h//2, :] = 0
                        out[y:y+bh, x:x+bw] = patch

                # 3. Angled Ghost Trailing & Offset Duplicate Layers (Ref 2)
                if intensity > 0.25 and rng.random() < 0.80:
                    shift_x = rng.choice([-1, 1]) * rng.randint(3, max(5, int(bw * 0.07)))
                    shift_y = rng.choice([-1, 1]) * rng.randint(2, max(4, int(bh * 0.20)))
                    M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
                    ghost = cv2.warpAffine(patch, M, (bw, bh), borderMode=cv2.BORDER_REFLECT)
                    out[y:y+bh, x:x+bw] = cv2.addWeighted(out[y:y+bh, x:x+bw], 0.60, ghost, 0.40, 0)

                # 4. Vertical Barcode Smear / Dripping Lines (Ref 5)
                if intensity > 0.40 and rng.random() < 0.70:
                    drip_len = rng.randint(int(bh * 1.5), int(bh * 3.5))
                    bottom_row = patch[-2:, :, :]
                    drip_block = np.repeat(bottom_row[-1:, :, :], drip_len, axis=0)
                    y_end = min(h, y + bh + drip_len)
                    act_len = y_end - (y + bh)
                    if act_len > 0:
                        out[y+bh:y_end, x:x+bw] = cv2.addWeighted(out[y+bh:y_end, x:x+bw], 0.35, drip_block[:act_len, :], 0.65, 0)

                # 5. Inpainted Box & Phonetic / Multi-Language Overlays (Ref 1)
                if intensity > 0.30 and rng.random() < 0.75:
                    bg_col = (255, 255, 255) if is_white_bg else (10, 10, 10)
                    fg_col = (10, 10, 10) if is_white_bg else (245, 245, 245)
                    
                    ox = x + rng.randint(-int(bw*0.06), int(bw*0.06))
                    oy = y + rng.randint(-int(bh*0.12), int(bh*0.12))
                    draw.rectangle([ox, oy, ox + bw, oy + bh], fill=bg_col)

                    mutation_text = LocalGlyphCorruptor.generate_phonetic_mutation(rng.randint(3, 7), rng)
                    f_size = max(11, int(bh * 0.68))
                    try:
                        font = ImageFont.truetype("arial.ttf", f_size)
                    except Exception:
                        font = ImageFont.load_default()
                    draw.text((ox + 4, oy + max(1, int((bh - f_size)/2))), mutation_text, fill=fg_col, font=font)

                corrupted_count += 1

        pil_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return cv2.addWeighted(out, 0.5, pil_bgr, 0.5, 0)


# ─────────────────────────────────────────────────────────────────────────────
# 3. 2023 EARLY AI STILL LIFE & ANATOMICAL ENGINE
# Clean subject-targeted 2023 AI flesh/texture distortion (ZERO global background waves):
# - Precise subject/skin segmentation
# - Wet clay & charred flesh shading with deep pore/wrinkle specular sheen
# - Target-masked asymmetric ocular & jaw distortion
# ─────────────────────────────────────────────────────────────────────────────
class LocalStillLifeEngine:
    @staticmethod
    def apply_still_life_reconstruction(bgr_img, rng, intensity=0.85, gloss=0.75):
        h, w = bgr_img.shape[:2]
        out = bgr_img.copy().astype(np.float32)

        # 1. Precise Subject / Skin Segmentation (Strictly targeted, NO global radial circle fallback)
        ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
        
        # If no human skin found, isolate high-contrast central subject contour
        if np.sum(skin_mask) < (w * h * 0.01 * 255):
            gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (15, 15), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            subject_mask = np.zeros((h, w), dtype=np.uint8)
            for cnt in contours:
                if cv2.contourArea(cnt) > (w * h * 0.03):
                    cv2.drawContours(subject_mask, [cnt], -1, 255, -1)
            if np.sum(subject_mask) > 0:
                skin_mask = subject_mask
            else:
                # Nothing to distort — return original image untouched! (ZERO global waves)
                return bgr_img

        mask_f = cv2.GaussianBlur(skin_mask, (21, 21), 0).astype(np.float32) / 255.0

        # 2. 2023 Wet Clay & Charred Flesh Shading (Targeted ONLY inside mask)
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        blur_g = cv2.GaussianBlur(gray, (0, 0), 3)
        high_pass_texture = np.clip(gray - blur_g, -40, 40)
        specular_sheen = np.clip(((gray / 255.0) ** 3.2) * 200.0 * gloss, 0, 130)

        dark_clay_tint = np.zeros_like(out)
        dark_clay_tint[:, :, 0] = -30 * intensity # Blue drop
        dark_clay_tint[:, :, 1] = -12 * intensity # Green drop
        dark_clay_tint[:, :, 2] = 22 * intensity  # Warm Clay / Ember boost

        for c in range(3):
            flesh_val = out[:, :, c] + (high_pass_texture * 1.6 * gloss + specular_sheen + dark_clay_tint[:, :, c])
            out[:, :, c] = out[:, :, c] * (1.0 - mask_f) + np.clip(flesh_val, 0, 255) * mask_f

        # 3. Asymmetrical Anatomical Ocular & Jaw Shift (Masked strictly to subject)
        eye_y0, eye_y1 = int(h * 0.15), int(h * 0.50)
        if (eye_y1 - eye_y0) > 10:
            shift_x = int(w * 0.022 * intensity)
            shift_y = -int(h * 0.028 * intensity)
            M_eye = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            warped_eyes = cv2.warpAffine(out[eye_y0:eye_y1, :], M_eye, (w, eye_y1 - eye_y0), borderMode=cv2.BORDER_REFLECT)
            eye_mask = mask_f[eye_y0:eye_y1, :, np.newaxis] * 0.80 * intensity
            out[eye_y0:eye_y1, :] = out[eye_y0:eye_y1, :] * (1.0 - eye_mask) + warped_eyes * eye_mask

        jaw_y0, jaw_y1 = int(h * 0.45), int(h * 0.85)
        if (jaw_y1 - jaw_y0) > 10:
            shift_dx = int(w * 0.032 * intensity)
            shift_dy = int(h * 0.038 * intensity)
            M_jaw = np.float32([[1, 0, shift_dx], [0, 1, shift_dy]])
            warped_jaw = cv2.warpAffine(out[jaw_y0:jaw_y1, :], M_jaw, (w, jaw_y1 - jaw_y0), borderMode=cv2.BORDER_REFLECT)
            jaw_mask = mask_f[jaw_y0:jaw_y1, :, np.newaxis] * 0.75 * intensity
            out[jaw_y0:jaw_y1, :] = out[jaw_y0:jaw_y1, :] * (1.0 - jaw_mask) + warped_jaw * jaw_mask

        return np.clip(out, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# 4. MASTER COMPOSITE ENGINE
# Green Light time pause + electric cracks, visual interrupts, and Forgets corruption
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedEngine:
    def __init__(self):
        self.seed = random.randint(0, 0xFFFFFFFF)
        self.use_still_life = True
        self.frozen_green_frame = None

    def set_seed(self, seed_val):
        self.seed = seed_val

    def generate_green_light_cracks(self, w, h, progress, rng, origin=None):
        """
        Authentic Kane Pixels Green Light: Inward perimeter caustic lightning & screen-edge surge.
        Cracks crawl from outside borders/corners inward toward the center.
        """
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Perimeter Origin Points along border perimeter (Outside In!)
        perimeter_origins = [
            (0, int(h * 0.15)),             # Left edge high
            (0, int(h * 0.75)),             # Left edge low
            (w - 1, int(h * 0.20)),         # Right edge high
            (w - 1, int(h * 0.80)),         # Right edge low
            (int(w * 0.25), 0),             # Top edge left
            (int(w * 0.75), 0),             # Top edge right
            (int(w * 0.30), h - 1),         # Bottom edge left
            (int(w * 0.70), h - 1),         # Bottom edge right
        ]
        
        center_x, center_y = w * 0.50, h * 0.50
        branch_rng = random.Random(rng.randint(0, 0xFFFF))
        
        for ox, oy in perimeter_origins:
            target_angle = math.atan2(center_y - oy, center_x - ox)
            max_dist = np.sqrt(w**2 + h**2) * 0.65 * progress
            
            cur_x, cur_y = float(ox), float(oy)
            step_len = max(5, int(w * 0.016))
            points = [(int(cur_x), int(cur_y))]
            dist_traveled = 0.0
            
            while dist_traveled < max_dist:
                cur_angle = target_angle + branch_rng.uniform(-0.55, 0.55)
                cur_x += np.cos(cur_angle) * step_len
                cur_y += np.sin(cur_angle) * step_len
                dist_traveled += step_len
                
                if 0 <= int(cur_x) < w and 0 <= int(cur_y) < h:
                    points.append((int(cur_x), int(cur_y)))
                else:
                    break
                    
                # Electric fork branches
                if branch_rng.random() < 0.28 and len(points) > 2:
                    fork_angle = cur_angle + branch_rng.choice([-0.70, 0.70])
                    fx, fy = cur_x, cur_y
                    fork_pts = [(int(fx), int(fy))]
                    for _ in range(branch_rng.randint(4, 9)):
                        fx += np.cos(fork_angle + branch_rng.uniform(-0.30, 0.30)) * (step_len * 0.7)
                        fy += np.sin(fork_angle + branch_rng.uniform(-0.30, 0.30)) * (step_len * 0.7)
                        if 0 <= int(fx) < w and 0 <= int(fy) < h:
                            fork_pts.append((int(fx), int(fy)))
                    if len(fork_pts) > 1:
                        cv2.polylines(overlay, [np.array(fork_pts)], False, (15, 180, 40), 2, cv2.LINE_AA)
                        cv2.polylines(overlay, [np.array(fork_pts)], False, (180, 255, 200), 1, cv2.LINE_AA)

            if len(points) > 1:
                # 3-layer electric discharge glow
                cv2.polylines(overlay, [np.array(points)], False, (10, 160, 30), 5, cv2.LINE_AA)
                cv2.polylines(overlay, [np.array(points)], False, (40, 240, 80), 2, cv2.LINE_AA)
                cv2.polylines(overlay, [np.array(points)], False, (230, 255, 235), 1, cv2.LINE_AA)

        # Luminous Caustic Edge & Corner Illumination Surge
        glow_map = np.zeros((h, w, 3), dtype=np.float32)
        Y, X = np.ogrid[:h, :w]
        dist_top = Y
        dist_bottom = h - Y
        dist_left = X
        dist_right = w - X
        min_edge_dist = np.minimum(np.minimum(dist_top, dist_bottom), np.minimum(dist_left, dist_right))
        edge_glow = np.clip(1.0 - (min_edge_dist / (max(w, h) * 0.35)), 0, 1) ** 1.8 * 0.85 * progress
        
        glow_map[:, :, 0] = edge_glow * 35   # Blue
        glow_map[:, :, 1] = edge_glow * 240  # Intense Emerald Green
        glow_map[:, :, 2] = edge_glow * 75   # Lime Green tint

        return cv2.add(overlay, np.clip(glow_map, 0, 255).astype(np.uint8))

    def render_no_signal_screen(self, width, height, lang):
        img = np.full((height, width, 3), (170, 10, 10), dtype=np.uint8) # Dark blue background
        noise = np.random.randint(-25, 25, (height, width, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img[::2, :, :] = (img[::2, :, :] * 0.70).astype(np.uint8)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.65, width / 550.0)
        thick = max(1, int(scale * 2))
        (tw, th), _ = cv2.getTextSize(lang, font, scale, thick)
        tx = (width - tw) // 2
        ty = (height + th) // 2
        
        # Text shadow and bright white foreground
        cv2.putText(img, lang, (tx+2, ty+2), font, scale, (0, 0, 30), thick+2, cv2.LINE_AA)
        cv2.putText(img, lang, (tx, ty), font, scale, (255, 255, 255), thick, cv2.LINE_AA)
        return img

    def render_static_screen(self, width, height):
        small = np.random.randint(0, 256, (max(1, height // 3), max(1, width // 3)), dtype=np.uint8)
        bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
        return cv2.resize(bgr, (width, height), interpolation=cv2.INTER_NEAREST)

    def render_no_video_screen(self, width, height):
        res = np.zeros((height, width, 3), dtype=np.uint8)
        res[::3, :, :] = 12
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.65, width / 650.0)
        cv2.putText(res, "PLAY >", (32, 54), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        cv2.putText(res, "NO VIDEO", (32, 98), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        return res

    def process_frame(self, frame, rng, sliders, frame_idx=0, fps=30.0):
        h, w = frame.shape[:2]
        master_v = sliders.get("master_val", 85) / 100.0
        text_v   = sliders.get("poster_melt", 90) / 100.0
        still_v  = sliders.get("object_melt", 85) / 100.0
        gloss_v  = sliders.get("flesh_gloss", 75) / 100.0
        green_v  = sliders.get("green_shift", 60) / 100.0

        is_video = (fps > 0 and frame_idx >= 0)
        t_sec = frame_idx / max(1.0, fps) if is_video else 0.0

        # ── 1. VISUAL INTERRUPT EVENTS (no_signal / no_video / static) ──
        if is_video and master_v > 0.30:
            cycle_time = t_sec % 18.0
            # Sporadic 0.4s static snow burst
            if 6.8 <= cycle_time < 7.2:
                return self.render_static_screen(w, h)
            # Sporadic 0.8s No Signal event
            elif 13.5 <= cycle_time < 14.3:
                lang = NO_SIGNAL_LANGS[(self.seed + int(t_sec / 18.0)) % len(NO_SIGNAL_LANGS)]
                return self.render_no_signal_screen(w, h, lang)
            # Sporadic 0.5s No Video OSD
            elif 17.5 <= cycle_time < 18.0:
                return self.render_no_video_screen(w, h)

        # ── 2. THE GREEN LIGHT EVENT (Spatial Pause + Branching Electric Cracks) ──
        if green_v > 0.10 and is_video:
            green_cycle = t_sec % 22.0
            green_start = 9.0
            green_dur = 2.4
            
            if green_start <= green_cycle < (green_start + green_dur):
                dt = green_cycle - green_start
                # Phase 1 & 2: Pause video on frozen frame & expand electric cracks
                if self.frozen_green_frame is None or dt < 0.1:
                    self.frozen_green_frame = frame.copy()

                out_base = self.frozen_green_frame.copy() if dt < 1.3 else frame.copy()
                
                # Crack progress: expand from 0.0 to 1.0, then fade out
                if dt < 1.3:
                    prog = dt / 1.3
                    cracks = self.generate_green_light_cracks(w, h, prog, rng)
                    return cv2.add(out_base, cracks)
                else:
                    fade = 1.0 - ((dt - 1.3) / 1.1)
                    cracks = self.generate_green_light_cracks(w, h, fade, rng)
                    return cv2.add(out_base, cracks)
            else:
                self.frozen_green_frame = None

        out = frame.copy()

        # ── 3. STILL LIFE ANATOMICAL RECONSTRUCTION ──
        if self.use_still_life and still_v > 0.05:
            out = LocalStillLifeEngine.apply_still_life_reconstruction(
                out, rng, intensity=still_v * master_v, gloss=gloss_v
            )

        # ── 4. KANE PIXELS "FORGETS" TEXT CORRUPTOR SUITE ──
        if text_v > 0.05:
            out = LocalGlyphCorruptor.corrupt_actual_frame_text(
                out, rng, intensity=text_v * master_v, frame_idx=frame_idx, fps=fps
            )

        return out


# ─────────────────────────────────────────────────────────────────────────────
# 5. DESKTOP GUI APPLICATION (CUSTOMTKINTER)
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MISREMEMBERED MEDIA // FORGETS & STILL LIFE TERMINAL")
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
        dbg(f'App initialized. seed={self.engine.seed:08X}', 'INIT')

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
                dbg("FFmpeg installed locally", "INIT")
            except Exception as e:
                self.add_log(f"FFmpeg install failed: {e}", "warn")
                dbg(f"FFmpeg install failed: {e}", "ERROR")
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

        self.tab_anatomy = self.tabs.add("2023 STILL LIFE")
        self.tab_text = self.tabs.add("FORGETS TEXT")
        self.tab_audio = self.tabs.add("KANE AUDIO")

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

        # ── 2023 STILL LIFE TAB ──
        switch_frame = ctk.CTkFrame(self.tab_anatomy, fg_color="#181c26", corner_radius=6, border_width=1, border_color="#2b3242")
        switch_frame.pack(fill="x", pady=(2, 8), padx=2)

        self.still_life_switch = ctk.CTkSwitch(
            switch_frame, text="2023 AI LATENT ENGINE", font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            progress_color="#00ff66", button_color="#ffffff", text_color="#00ff66",
            command=self.toggle_still_life
        )
        self.still_life_switch.select()
        self.still_life_switch.pack(side="top", anchor="w", padx=10, pady=(8, 4))
        ctk.CTkLabel(switch_frame, text="Latent space flow, molten flesh & incandescent glow", font=ctk.CTkFont(family="Courier New", size=9), text_color="#9ca3af").pack(side="top", anchor="w", padx=10, pady=(0, 8))

        sliders_1 = [
            ("2023 Latent Space Flow & Melt", "object_melt", 0, 100, 85, "#ff3344"),
            ("Wet Clay & Molten Specular Gloss", "flesh_gloss", 0, 100, 80, "#00ff66"),
            ("Incandescent Cavity Glow & Shift", "master_val", 0, 100, 90, "#ff3344"),
            ("The Green Light Pause & Cracks", "green_shift", 0, 100, 70, "#00ff66"),
        ]
        for title, key, mn, mx, df, clr in sliders_1:
            self._make_slider_group(self.tab_anatomy, title, key, mn, mx, df, clr)

        sliders_2 = [
            ("Forgets Glyph Corruption Intensity", "poster_melt", 0, 100, 90, "#ff3344"),
        ]
        for title, key, mn, mx, df, clr in sliders_2:
            self._make_slider_group(self.tab_text, title, key, mn, mx, df, clr)

        sliders_3 = [
            ("Tape Wow / Flutter & Stalls", "audio_warp", 0, 100, 85, "#00ff66"),
            ("Vast Drywall Liminal Reverb", "audio_reverb", 0, 100, 75, "#ff3344"),
            ("60Hz Fluorescent Buzz Gain", "audio_hum", 0, 100, 65, "#00ff66"),
            ("Memory Ghost Voice Echo", "audio_echo", 0, 100, 70, "#ff3344"),
        ]
        for title, key, mn, mx, df, clr in sliders_3:
            self._make_slider_group(self.tab_audio, title, key, mn, mx, df, clr)

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

    def toggle_still_life(self):
        self.engine.use_still_life = self.still_life_switch.get() == 1
        state = "ENABLED" if self.engine.use_still_life else "DISABLED"
        self.add_log(f"Still Life Reconstruction Engine {state}", "info")
        dbg(f"Still Life Engine toggled: {state}", "STILL_LIFE")
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
        dbg(f"Re-seeded RNG state: {self.engine.seed:08X}", "SEED")
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
        dbg(f"Loaded media: {path}", "IO")

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
        frame_delay = 1.0 / max(10.0, fps)
        frame_idx = 0

        while self.is_previewing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue

            sliders = self.get_sliders()
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

        # Snapshot all state on main thread before spawning
        _snap_sliders   = self.get_sliders()
        _snap_still_life = self.engine.use_still_life
        _snap_seed      = self.engine.seed
        _snap_path      = self.current_media_path
        dbg(f'Export initiated — seed={_snap_seed:08X} still_life={_snap_still_life} sliders={_snap_sliders}', 'EXPORT')

        threading.Thread(
            target=self.export_video_thread,
            args=(_snap_sliders, _snap_still_life, _snap_seed, _snap_path),
            daemon=True
        ).start()

    def export_video_thread(self, sliders, use_still_life, seed, in_path):
        temp_video = None
        temp_in_wav = None
        temp_out_wav = None
        try:
            out_dir = os.path.dirname(in_path)
            base = os.path.splitext(os.path.basename(in_path))[0]
            final_path = os.path.join(out_dir, f"ꓫ REMΕMᗷER_{base}_MISREMEMBERED.mp4")
            temp_video = os.path.join(tempfile.gettempdir(), f"_temp_vid_{int(time.time())}.mp4")
            temp_in_wav = os.path.join(tempfile.gettempdir(), f"_temp_in_{int(time.time())}.wav")
            temp_out_wav = os.path.join(tempfile.gettempdir(), f"_temp_out_{int(time.time())}.wav")

            cap = cv2.VideoCapture(in_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300

            target_w, target_h = orig_w, orig_h
            if orig_w > 1280:
                target_w = 1280
                target_h = int(orig_h * (1280 / orig_w))

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video, fourcc, fps, (target_w, target_h))

            frame_idx = 0
            start_t = time.time()

            self.add_log(f"Reconstruction Export: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f} FPS ({total_frames} frames)...", "alert")
            dbg(f"Video Export started: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f}fps, total={total_frames}", "EXPORT")

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if orig_w != target_w:
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

                # Identical deterministic temporal seed ensures 100% parity with preview!
                frame_rng = random.Random(seed + int(frame_idx / (fps * 2.0)))
                _orig_sl = self.engine.use_still_life
                self.engine.use_still_life = use_still_life
                out = self.engine.process_frame(frame, frame_rng, sliders, frame_idx, fps)
                self.engine.use_still_life = _orig_sl
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
            dbg(f"Video frame rendering complete ({total_frames} frames).", "EXPORT")

            # ── AUDIO PROCESSING WITH KANE PIXELS DSP ──
            if FFMPEG:
                self.add_log("Processing Backrooms audio DSP (tape wow, liminal reverb, fluorescent hum)...", "info")
                ext_cmd = [FFMPEG, "-y", "-i", in_path, "-vn", "-ac", "2", "-ar", "44100", temp_in_wav]
                subprocess.run(ext_cmd, capture_output=True, timeout=60)

                has_audio = os.path.exists(temp_in_wav) and os.path.getsize(temp_in_wav) > 1000

                if has_audio:
                    try:
                        sr, raw_audio = wavfile.read(temp_in_wav)
                        proc_audio = KanePixelsAudioDSP.process_full_audio(raw_audio, sr=sr, seed=seed, sliders=sliders)
                        wavfile.write(temp_out_wav, sr, proc_audio)
                    except Exception as e:
                        dbg(f"Audio DSP error on input audio: {e}", "ERROR")
                        has_audio = False

                if not has_audio:
                    sr = 44100
                    duration_s = max(1.0, total_frames / float(fps))
                    n_samples = int(sr * duration_s)
                    dbg(f"Synthesizing {duration_s:.1f}s Backrooms atmospheric drone...", "AUDIO")
                    hum = KanePixelsAudioDSP.synthesize_fluorescent_hum(n_samples, sr=sr, gain=0.045)
                    wavfile.write(temp_out_wav, sr, (hum * 32767.0).astype(np.int16))

                # Remux with FFmpeg
                self.add_log("Remuxing final high-fidelity video & audio payload...", "info")
                cmd = [
                    FFMPEG, "-y",
                    "-i", temp_video,
                    "-i", temp_out_wav,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "19",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    final_path
                ]
                subprocess.run(cmd, capture_output=True, timeout=600)
            else:
                import shutil
                shutil.move(temp_video, final_path)

            self.after(0, lambda: self.on_export_complete(final_path))
        except Exception as e:
            self.add_log(f"Export error: {e}", "warn")
            dbg(f"Export error: {e}", "ERROR")
            self.is_processing = False
            self.export_btn.configure(state="normal")
            self.progress_bar.pack_forget()
        finally:
            for p in [temp_video, temp_in_wav, temp_out_wav]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

    def on_export_complete(self, path):
        self.is_processing = False
        self.export_btn.configure(state="normal")
        self.progress_bar.pack_forget()
        self.add_log(f"Export Complete: {os.path.basename(path)}", "info")
        dbg(f"Export completed: {path}", "DONE")
        messagebox.showinfo("Export Complete", f"Saved reconstructed media to:\n{path}")


if __name__ == "__main__":
    app = MisrememberedDesktopApp()
    app.mainloop()
