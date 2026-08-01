import sys
import os
import random
import math
import time
import threading
import subprocess
import tempfile
import zipfile
import urllib.request
import numpy as np
import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

NO_SIGNAL_LANGS = [
    "Pas de signal", "Kein Signal", "Sin señal", "Nenhum sinal", "Geen signaal",
    "No Signal", "Brak sygnału", "Není signál", "Nincs jel", "Semnal lipsă",
    "Ingen signal", "Ei signaalia", "Sinyal yok", "Δεν υπάρχει σήμα",
    "Нет сигнала", "Немає сигналу", "Nema signala", "Signāla nav", "Signalo nėra",
    "无信号", "信号なし", "신호 없음", "אין אות", "لا توجد إشارة",
]

# App-local ffmpeg install location (no admin rights needed)
FFMPEG_LOCAL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "MisrememberedMedia", "ffmpeg")
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

def find_ffmpeg():
    """Locate ffmpeg binary — checks PATH, common locations, and the app-local install."""
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

def _add_to_user_path(new_dir):
    """Permanently add new_dir to the current user's PATH via the Windows registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS
        )
        try:
            current, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            current = ""
        if new_dir.lower() not in current.lower():
            updated = current.rstrip(";") + ";" + new_dir if current else new_dir
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, updated)
        winreg.CloseKey(key)
        # Broadcast the change so Explorer picks it up without a reboot
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
        # Also update the current process environment
        os.environ["PATH"] = os.environ.get("PATH", "").rstrip(";") + ";" + new_dir
    except Exception as e:
        print(f"[PATH] Could not update registry PATH: {e}")

FFMPEG = find_ffmpeg()


class MisrememberedEngine:
    def __init__(self):
        self.seed = random.randint(0, 0xFFFFFFFF)

    def set_seed(self, seed_val):
        self.seed = seed_val

    # ── EDGE / TEXT CANDIDATE DETECTION (4x DOWNSCALED FAST SCAN) ────────────
    def scan_high_contrast_bands(self, frame, block_h=28, threshold=20):
        """Fast downscaled edge detection for text/face band finding."""
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (w // 4, h // 4), interpolation=cv2.INTER_NEAREST)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        diff = np.abs(gray[1:, :] - gray[:-1, :])
        
        sh, sw = diff.shape
        sb_h = max(2, block_h // 4)
        bands = []
        for sy in range(0, sh - sb_h, sb_h):
            score = float(np.mean(diff[sy:sy+sb_h, :]))
            if score > threshold:
                bands.append((sy * 4, 0, w, block_h, score))
        bands.sort(key=lambda b: b[4], reverse=True)
        return bands[:12]

    # ── POSTER BAND MELT (the "MISSING poster" effect) ────────────────────────
    def apply_poster_band_melt(self, frame, rng, master_val=0.8):
        """
        Finds high-contrast horizontal text-line bands and applies one of:
        - Vertical flip overlay  (the "MISSING" inverted header look)
        - Horizontal mirror ghost (backwards letters)
        - Wax column drip         (letter bottoms stretched downward)
        """
        h, w = frame.shape[:2]
        bands = self.scan_high_contrast_bands(frame, block_h=28, threshold=25)
        if not bands:
            return frame

        res = frame.copy()
        num_bands = max(1, int(1 + master_val * 2))
        chosen = rng.sample(bands, min(num_bands, len(bands)))

        for (by, bx, bw, bh, _) in chosen:
            mode = rng.random()
            pad = 4
            y0 = max(0, by - pad)
            y1 = min(h, by + bh + pad)
            bh_eff = y1 - y0

            region = res[y0:y1, bx:bx+bw].copy()
            if region.size == 0:
                continue

            if mode < 0.35:
                # Vertical flip overlay — whole band flipped upside-down
                flipped = cv2.flip(region, 0)
                alpha = 0.60 + rng.random() * 0.25
                try:
                    res[y0:y1, bx:bx+bw] = cv2.addWeighted(flipped, alpha, res[y0:y1, bx:bx+bw], 1.0 - alpha, 0)
                    # Faint ghost 6px lower
                    ghost_y0 = min(h - bh_eff, y1)
                    ghost_y1 = min(h, ghost_y0 + bh_eff)
                    ghost_src = cv2.flip(frame[y0:y0+(ghost_y1-ghost_y0), bx:bx+bw], 0)
                    if ghost_src.shape[0] == (ghost_y1 - ghost_y0):
                        res[ghost_y0:ghost_y1, bx:bx+bw] = cv2.addWeighted(
                            ghost_src, 0.20, res[ghost_y0:ghost_y1, bx:bx+bw], 0.80, 0)
                except Exception:
                    pass

            elif mode < 0.68:
                # Horizontal mirror ghost — text reads backwards + faint original offset
                mirrored = cv2.flip(region, 1)
                alpha = 0.62 + rng.random() * 0.25
                try:
                    res[y0:y1, bx:bx+bw] = cv2.addWeighted(mirrored, alpha, res[y0:y1, bx:bx+bw], 1.0 - alpha, 0)
                    # Ghost shifted 4px right
                    gx0 = min(w - bw, bx + 4)
                    res[y0:y1, gx0:gx0+bw] = cv2.addWeighted(
                        region, 0.25, res[y0:y1, gx0:gx0+bw], 0.75, 0)
                except Exception:
                    pass

            else:
                # Wax column drip — bottom slice of band stretched downward
                slice_h = max(2, bh_eff // 5)
                src_slice = region[-slice_h:, :]
                drip_h = int(10 + rng.random() * 25)
                dest_y0 = y1
                dest_y1 = min(h, dest_y0 + drip_h + slice_h)
                if dest_y1 > dest_y0 and src_slice.size > 0:
                    try:
                        stretched = cv2.resize(src_slice, (bw, dest_y1 - dest_y0), interpolation=cv2.INTER_LINEAR)
                        for step in range(4):
                            step_y0 = dest_y0 + step * ((dest_y1 - dest_y0) // 4)
                            step_y1 = min(h, step_y0 + max(1, (dest_y1 - dest_y0) // 4 + slice_h))
                            alpha = max(0.0, 0.55 - step * 0.12)
                            patch = stretched[step * ((dest_y1 - dest_y0) // 4):step * ((dest_y1 - dest_y0) // 4) + (step_y1 - step_y0), :]
                            if patch.shape[0] == (step_y1 - step_y0) and alpha > 0.05:
                                res[step_y0:step_y1, bx:bx+bw] = cv2.addWeighted(
                                    patch, alpha, res[step_y0:step_y1, bx:bx+bw], 1.0 - alpha, 0)
                    except Exception:
                        pass

        return res

    # ── OBJECT MELTING (downward feature smear) ───────────────────────────────
    def apply_object_melting(self, frame, rng, master_val=0.8):
        h, w = frame.shape[:2]
        # Fast downscaled 4x sampling for edge candidates
        small = cv2.resize(frame, (w // 4, h // 4), interpolation=cv2.INTER_NEAREST)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        diff = np.abs(gray[1:, :] - gray[:-1, :])

        bs = 28
        s_bs = max(2, bs // 4)
        sh, sw = diff.shape
        candidates = []
        for sy in range(0, sh - s_bs, s_bs):
            for sx in range(0, sw - s_bs, s_bs):
                score = float(np.mean(diff[sy:sy+s_bs, sx:sx+s_bs]))
                if score > 15:
                    candidates.append((score, sx * 4, sy * 4))

        candidates.sort(key=lambda item: item[0], reverse=True)
        top = candidates[:15]
        if not top:
            return frame

        res = frame.copy()
        count = min(len(top), int(2 + master_val * 5))
        chosen = rng.sample(top, count)

        for _, bx, by in chosen:
            patch = frame[by:by+bs, bx:bx+bs].copy()
            num_steps = rng.randint(3, 7)
            step_dx = rng.randint(-6, 6)
            step_dy = rng.randint(6, 14)
            angle = (rng.random() - 0.5) * 0.18

            for s in range(1, num_steps):
                nx = bx + s * step_dx
                ny = by + s * step_dy
                if 0 <= nx < w - bs and 0 <= ny < h - bs:
                    alpha = max(0.15, 1.0 - s * 0.18)
                    # Apply slight rotation to the patch for each step
                    M = cv2.getRotationMatrix2D((bs // 2, bs // 2), math.degrees(angle * s), 1.0)
                    rotated = cv2.warpAffine(patch, M, (bs, bs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                    res[ny:ny+bs, nx:nx+bs] = cv2.addWeighted(
                        rotated, alpha, res[ny:ny+bs, nx:nx+bs], 1.0 - alpha, 0)
        return res

    # ── OBJECT STRETCH ────────────────────────────────────────────────────────
    def apply_object_stretch(self, frame, rng, master_val=0.8):
        h, w = frame.shape[:2]
        res = frame.copy()
        rw = int(w * (0.15 + rng.random() * 0.35))
        rh = int(h * (0.15 + rng.random() * 0.35))
        rx = rng.randint(0, max(1, w - rw))
        ry = rng.randint(0, max(1, h - rh))

        patch = frame[ry:ry+rh, rx:rx+rw]
        stretch_mult = 2.0 + rng.random() * 3.0

        # 70% vertical (Backrooms tall-chair geometry)
        if rng.random() < 0.70:
            dst_h = min(h - ry, int(rh * stretch_mult))
            dst_w = rw
            draw_y = max(0, ry - (dst_h - rh))
        else:
            dst_w = min(w - rx, int(rw * stretch_mult))
            dst_h = rh
            draw_y = ry

        if dst_w > 0 and dst_h > 0 and patch.size > 0:
            try:
                resized = cv2.resize(patch, (dst_w, dst_h), interpolation=cv2.INTER_LINEAR)
                blend_region = res[draw_y:draw_y+dst_h, rx:rx+dst_w]
                if resized.shape == blend_region.shape:
                    res[draw_y:draw_y+dst_h, rx:rx+dst_w] = cv2.addWeighted(resized, 0.88, blend_region, 0.12, 0)
            except Exception:
                pass
        return res

    # ── ARCHITECTURAL MIRROR ──────────────────────────────────────────────────
    def apply_architectural_mirror(self, frame, rng):
        h, w = frame.shape[:2]
        res = frame.copy()
        mode = rng.random()
        alpha = 0.55 + rng.random() * 0.35
        if mode < 0.45:
            half = cv2.flip(frame[:, :w//2], 1)
            res[:, w//2:w//2+half.shape[1]] = cv2.addWeighted(half, alpha, res[:, w//2:w//2+half.shape[1]], 1-alpha, 0)
        elif mode < 0.80:
            half = cv2.flip(frame[:h//2, :], 0)
            res[h//2:h//2+half.shape[0], :] = cv2.addWeighted(half, alpha, res[h//2:h//2+half.shape[0], :], 1-alpha, 0)
        else:
            quad = cv2.flip(frame[:h//2, :w//2], -1)
            res[h//2:, w//2:] = cv2.addWeighted(quad, alpha, res[h//2:, w//2:], 1-alpha, 0)
        return res

    # ── CHROMATIC ABERRATION ──────────────────────────────────────────────────
    def apply_chromatic_aberration(self, frame, shift=6):
        res = frame.copy()
        if shift < 1:
            return res
        res[:, :-shift, 2] = frame[:, shift:, 2]   # B channel right-shift
        res[:, shift:,  0] = frame[:, :-shift, 0]  # R channel left-shift
        return res

    # ── REALITY TEAR ──────────────────────────────────────────────────────────
    def apply_reality_tear(self, frame, rng, master_val=0.8):
        h, w = frame.shape[:2]
        res = frame.copy()
        num_tears = rng.randint(1, max(1, int(master_val * 3)))
        for _ in range(num_tears):
            tear_y = rng.randint(0, max(0, h - 20))
            tear_h = rng.randint(3, int(10 + master_val * 15))
            src_y  = rng.randint(0, max(0, h - tear_h))
            shift_x = int((rng.random() - 0.5) * w * 0.35)
            if tear_h < 1:
                continue
            src_band = frame[src_y:src_y+tear_h, :].copy()
            # Shift horizontally with wraparound
            src_shifted = np.roll(src_band, shift_x, axis=1)
            blend = 0.50 + master_val * 0.35
            try:
                res[tear_y:tear_y+tear_h, :] = cv2.addWeighted(
                    src_shifted, blend, res[tear_y:tear_y+tear_h, :], 1.0 - blend, 0)
            except Exception:
                pass
        return res

    # ── PIXEL SLICING (VHS head skip) ─────────────────────────────────────────
    def apply_pixel_slicing(self, frame, rng, freq=0.75):
        h, w = frame.shape[:2]
        res = frame.copy()
        num_slices = rng.randint(1, max(1, int(freq * 5)))
        for _ in range(num_slices):
            sy = rng.randint(0, max(0, h - 20))
            sh = rng.randint(3, 22)
            shift = int((rng.random() - 0.5) * 55 * freq)
            if sh < 1:
                continue
            try:
                strip = frame[sy:sy+sh, :].copy()
                res[sy:sy+sh, :] = np.roll(strip, shift, axis=1)
            except Exception:
                pass
        return res

    # ── PIXEL SORT ────────────────────────────────────────────────────────────
    def apply_pixel_sort(self, frame, rng):
        h, w = frame.shape[:2]
        res = frame.copy()
        num_strips = rng.randint(2, 5)
        for _ in range(num_strips):
            y = rng.randint(0, max(0, h - 30))
            sh = rng.randint(10, 30)
            if sh < 1:
                continue
            strip = res[y:y+sh, :].copy()
            gray_strip = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)
            indices = np.argsort(gray_strip, axis=1)
            for r in range(strip.shape[0]):
                strip[r] = strip[r, indices[r]]
            res[y:y+sh, :] = strip
        return res

    # ── BLOCK ECHO ────────────────────────────────────────────────────────────
    def apply_block_echo(self, frame, rng, master_val=0.8):
        h, w = frame.shape[:2]
        res = frame.copy()
        num_echoes = rng.randint(1, max(1, int(master_val * 3)))
        for _ in range(num_echoes):
            bw = rng.randint(30, w // 3)
            bh = rng.randint(15, h // 4)
            bx = rng.randint(0, max(0, w - bw))
            by = rng.randint(0, max(0, h - bh))
            offset_x = int((rng.random() - 0.5) * w * 0.35)
            offset_y = int((rng.random() - 0.5) * h * 0.35)
            src_x = max(0, min(w - bw, bx + offset_x))
            src_y = max(0, min(h - bh, by + offset_y))
            src_patch = frame[src_y:src_y+bh, src_x:src_x+bw].copy()
            blend = 0.40 + master_val * 0.30
            try:
                res[by:by+bh, bx:bx+bw] = cv2.addWeighted(
                    src_patch, blend, res[by:by+bh, bx:bx+bw], 1.0 - blend, 0)
            except Exception:
                pass
        return res

    # ── COLOR BURST (brief hue flash) ─────────────────────────────────────────
    def apply_color_burst(self, frame, rng):
        burst_type = rng.randint(0, 3)
        res = frame.copy().astype(np.float32)
        if burst_type == 0:
            res[:, :, [0, 1]] = res[:, :, [1, 0]]  # swap B/G
        elif burst_type == 1:
            bright = res[:, :, 0] > 120
            res[bright, 0] = 255 - res[bright, 0]  # invert bright blues
        elif burst_type == 2:
            gray = 0.299 * res[:, :, 2] + 0.587 * res[:, :, 1] + 0.114 * res[:, :, 0]
            res[:, :, 0] = np.clip(gray * 0.45, 0, 255)
            res[:, :, 1] = np.clip(gray * 0.35 + res[:, :, 1] * 0.75, 0, 255)
        else:
            res = 255 - res  # full invert
        return np.clip(res, 0, 255).astype(np.uint8)

    # ── SCREEN RENDERS ────────────────────────────────────────────────────────
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
        cv2.putText(img, "CH 03", (width - 100, 40), font, scale * 0.6, (200, 200, 200), 1, cv2.LINE_AA)
        return img

    def render_no_video_screen(self, frame, time_sec):
        h, w = frame.shape[:2]
        res = np.zeros((h, w, 3), dtype=np.uint8)
        res[::3, :, :] = 10
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.6, w / 700.0)
        hrs = int(time_sec // 3600)
        mins = int((time_sec % 3600) // 60)
        secs = int(time_sec % 60)
        tc = f"SP -{hrs:02d}:{mins:02d}:{secs:02d}"
        cv2.putText(res, "PLAY >", (30, 50), font, scale, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(res, "PLAY >", (28, 48), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        cv2.putText(res, "NO VIDEO", (30, 90), font, scale, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(res, "NO VIDEO", (28, 88), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        cv2.putText(res, tc, (30, h - 30), font, scale, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(res, tc, (28, h - 32), font, scale, (34, 238, 232), 2, cv2.LINE_AA)
        return res

    def render_static_screen(self, width, height):
        # Reuse same base static frame — adding small per-frame flicker via roll
        # Avoids generating a full random array 30x per second during interrupts.
        if not hasattr(self, '_static_cache') or self._static_cache.shape[:2] != (height, width):
            sw, sh = max(1, width // 3), max(1, height // 3)
            small = np.random.randint(0, 256, (sh, sw), dtype=np.uint8)
            bgr = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
            self._static_cache = cv2.resize(bgr, (width, height), interpolation=cv2.INTER_NEAREST)
        # Cheap per-frame flicker: roll a few rows and darken alternates
        out = np.roll(self._static_cache, random.randint(-4, 4), axis=0)
        out[::2, :, :] = (out[::2, :, :] * 0.72).astype(np.uint8)
        if len(out.shape) == 2 or out.shape[2] == 1:
            out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
        return out

    # ── FULL FRAME COMPOSITE ───────────────────────────────────────────────────
    def process_frame(self, frame, rng, sliders, frame_idx, fps):
        """Apply all active effects to a single frame."""
        master_v     = sliders["master_val"]     / 100.0
        obj_melt_v   = sliders["object_melt"]    / 100.0
        obj_stretch_v= sliders["object_stretch"] / 100.0
        spatial_v    = sliders["spatial_mirror"] / 100.0
        chromatic_v  = sliders["chromatic_val"]  / 100.0
        pixel_sort_v = sliders["pixel_sort_val"] / 100.0
        poster_v     = sliders["poster_melt"]    / 100.0
        tear_v       = sliders["reality_tear"]   / 100.0

        out = frame.copy()

        if rng.random() < 0.40 * master_v:
            out = self.apply_object_melting(out, rng, obj_melt_v)
        if rng.random() < 0.20 * master_v:
            out = self.apply_object_stretch(out, rng, obj_stretch_v)
        # Mirror: 5% only (was 25% — way too frequent)
        if rng.random() < 0.05 * spatial_v:
            out = self.apply_architectural_mirror(out, rng)
        if chromatic_v > 0 and rng.random() < 0.50 * chromatic_v:
            out = self.apply_chromatic_aberration(out, int(4 + chromatic_v * 12))
        if pixel_sort_v > 0 and rng.random() < 0.25 * pixel_sort_v:
            out = self.apply_pixel_sort(out, rng)
        # Poster band melt: 80% of frames when enabled
        if poster_v > 0 and rng.random() < 0.80 * poster_v:
            out = self.apply_poster_band_melt(out, rng, master_v)
        # Reality tear: 15% of frames
        if tear_v > 0 and rng.random() < 0.15 * tear_v:
            out = self.apply_reality_tear(out, rng, master_v)
        # Pixel slicing: always some chance
        if rng.random() < 0.08 * master_v:
            out = self.apply_pixel_slicing(out, rng, 0.75)
        # Block echo: occasional ghost
        if rng.random() < 0.10 * master_v:
            out = self.apply_block_echo(out, rng, master_v)
        # Color burst: rare (1.2% per frame max)
        if rng.random() < 0.012 * master_v:
            out = self.apply_color_burst(out, rng)
        # Ensure output is strictly 3 channels (BGR uint8) to avoid OpenCV VideoWriter skips
        if len(out.shape) == 2 or out.shape[2] == 1:
            out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
        return out

class FFmpegInstallDialog(ctk.CTkToplevel):
    """Modal dialog that downloads, extracts ffmpeg and updates system PATH."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("DOWNLOADING FFMPEG")
        self.geometry("450x180")
        self.resizable(False, False)
        self.configure(fg_color="#0e0d08")
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(
            self, text="DOWNLOADING FFMPEG ESSENTIALS",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            text_color="#d8c880"
        ).pack(pady=(16, 4))

        self.status_lbl = ctk.CTkLabel(
            self, text="Connecting to build server...",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#7a6628"
        )
        self.status_lbl.pack(pady=(0, 10))

        self.progress = ctk.CTkProgressBar(self, width=380, height=8, progress_color="#c8a84a", fg_color="#0a0908")
        self.progress.pack(pady=5)
        self.progress.set(0)

        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        try:
            os.makedirs(FFMPEG_LOCAL_DIR, exist_ok=True)
            zip_path = os.path.join(tempfile.gettempdir(), "ffmpeg_essentials.zip")

            self.after(0, lambda: self.status_lbl.configure(text="Downloading package (~90MB)..."))

            def progress_hook(blocks, block_size, total_size):
                if total_size > 0:
                    pct = min(1.0, (blocks * block_size) / total_size)
                    self.after(0, lambda p=pct: self.progress.set(p))

            urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, zip_path, reporthook=progress_hook)

            self.after(0, lambda: self.status_lbl.configure(text="Extracting binaries..."))

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find root directory in zip
                for member in zip_ref.namelist():
                    if member.endswith("bin/ffmpeg.exe") or member.endswith("bin/ffprobe.exe"):
                        filename = os.path.basename(member)
                        bin_dir = os.path.join(FFMPEG_LOCAL_DIR, "bin")
                        os.makedirs(bin_dir, exist_ok=True)
                        with zip_ref.open(member) as source, open(os.path.join(bin_dir, filename), "wb") as target:
                            target.write(source.read())

            try:
                os.remove(zip_path)
            except Exception:
                pass

            self.after(0, lambda: self.status_lbl.configure(text="Configuring environment PATH..."))
            bin_path = os.path.join(FFMPEG_LOCAL_DIR, "bin")
            _add_to_user_path(bin_path)

            global FFMPEG
            FFMPEG = os.path.join(bin_path, "ffmpeg.exe")

            self.after(0, self._on_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_error(err))

    def _on_success(self):
        self.grab_release()
        self.destroy()
        messagebox.showinfo(
            "FFmpeg Installation Complete",
            "FFmpeg has been installed successfully!\n\n"
            "Full audio processing and video export are now enabled."
        )

    def _on_error(self, err_msg):
        self.grab_release()
        self.destroy()
        messagebox.showerror(
            "Installation Failed",
            f"Failed to download/install FFmpeg:\n{err_msg}\n\n"
            "Please install FFmpeg manually and add it to your PATH."
        )


class MisrememberedApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MISREMEMBERED MEDIA • RECONSTRUCTION TERMINAL")
        self.geometry("1280x820")
        self.minsize(980, 680)
        self.configure(fg_color="#040507")

        self.engine = MisrememberedEngine()
        self.current_video_path = None
        self.is_processing = False
        self.is_previewing = False
        self.preview_thread = None
        self._color_burst_cooldown = 0

        self.setup_ui()

        if not FFMPEG:
            self.after(800, self.prompt_ffmpeg_install)

    def prompt_ffmpeg_install(self):
        """Offer to auto-download and install ffmpeg with a nice progress dialog."""
        answer = messagebox.askyesno(
            "ffmpeg not found — Audio Required",
            "ffmpeg was not found on your system.\n\n"
            "Without it, exported videos will have NO AUDIO.\n\n"
            "Install ffmpeg automatically? (~90 MB download)\n"
            "It will be placed in %LOCALAPPDATA%\\MisrememberedMedia\\ffmpeg\\ "
            "and added to your user PATH.",
            icon="warning"
        )
        if answer:
            FFmpegInstallDialog(self)

    def setup_ui(self):
        # ── TOP HEADER ──────────────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(
            self, height=70, corner_radius=0,
            fg_color="#0e0d08",
            border_width=2, border_color="#2e2a1e"
        )
        self.header_frame.pack(side="top", fill="x", padx=0, pady=0)

        brand_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_frame.pack(side="left", padx=18, pady=14)

        self.pulse_dot = ctk.CTkLabel(brand_frame, text="●", font=ctk.CTkFont(size=14), text_color="#7a2020")
        self.pulse_dot.pack(side="left", padx=(0, 8))

        self.title_lbl = ctk.CTkLabel(
            brand_frame,
            text="MISREMEMBERED MEDIA",
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
            text_color="#d8c880"
        )
        self.title_lbl.pack(side="left")

        self.ver_lbl = ctk.CTkLabel(
            brand_frame, text="ASYNC UNIT 04 // RECONSTRUCTION DECAY",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#7a3030",
            fg_color="#120e0e", corner_radius=0, padx=6, pady=2
        )
        self.ver_lbl.pack(side="left", padx=10)

        # Seed input + button on right
        seed_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        seed_frame.pack(side="right", padx=18, pady=14)

        self.seed_input = ctk.CTkEntry(
            seed_frame, width=90, height=30,
            placeholder_text="HEX SEED",
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#0a0908", border_color="#3a3525", text_color="#c8a84a"
        )
        self.seed_input.pack(side="left", padx=(0, 6))

        self.seed_btn = ctk.CTkButton(
            seed_frame, text="↻ SET SEED",
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#1a1912", hover_color="#252318",
            border_width=1, border_color="#3a3525", text_color="#c8a84a",
            width=100, height=30,
            command=self.regen_seed
        )
        self.seed_btn.pack(side="left")

        self.seed_display = ctk.CTkLabel(
            seed_frame, text=f"SEED: {self.engine.seed:08X}",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#7a6628"
        )
        self.seed_display.pack(side="left", padx=(8, 0))

        # ── BOTTOM BAR ────────────────────────────────────────────────────
        self.bottom_bar = ctk.CTkFrame(
            self, height=68,
            fg_color="#0e0d08",
            border_width=1, border_color="#2e2a1e", corner_radius=0
        )
        self.bottom_bar.pack(side="bottom", fill="x")

        self.load_btn = ctk.CTkButton(
            self.bottom_bar, text="📁  feed it a file",
            font=ctk.CTkFont(family="Courier New", size=13),
            fg_color="#1e1c12", hover_color="#252318",
            border_width=1, border_color="#3a3525", text_color="#c8a84a",
            height=40, command=self.load_media
        )
        self.load_btn.pack(side="left", padx=18, pady=14)

        self.export_btn = ctk.CTkButton(
            self.bottom_bar, text="💾  RENDER THE MEMORY",
            font=ctk.CTkFont(family="Courier New", size=13),
            fg_color="#1e2818", hover_color="#252e1e",
            border_width=1, border_color="#4a7840", text_color="#4a7840",
            height=40, state="disabled",
            command=self.start_export
        )
        self.export_btn.pack(side="right", padx=18, pady=14)

        self.progress_bar = ctk.CTkProgressBar(
            self.bottom_bar, height=4,
            progress_color="#4a7840", fg_color="#0a0908"
        )
        self.progress_bar.set(0)

        # ── MAIN WORKSPACE ────────────────────────────────────────────────
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="top", fill="both", expand=True, padx=10, pady=6)

        # Left: Controls panel
        self.controls_card = ctk.CTkFrame(
            self.main_container, width=320,
            fg_color="#0e0d08",
            border_width=1, border_color="#2e2a1e", corner_radius=0
        )
        self.controls_card.pack(side="left", fill="y", padx=(0, 8))

        self.controls_scroll = ctk.CTkScrollableFrame(self.controls_card, fg_color="transparent")
        self.controls_scroll.pack(fill="both", expand=True, padx=4, pady=8)

        self.setup_control_sliders()

        # Right: Viewport
        self.viewport_card = ctk.CTkFrame(
            self.main_container,
            fg_color="#050503",
            border_width=1, border_color="#2e2a1e", corner_radius=0
        )
        self.viewport_card.pack(side="right", fill="both", expand=True)

        vp_hdr = ctk.CTkFrame(self.viewport_card, height=32, fg_color="#0a0908")
        vp_hdr.pack(fill="x")

        ctk.CTkLabel(
            vp_hdr, text="RECONSTRUCTION MONITOR",
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color="#7a6628"
        ).pack(side="left", padx=12, pady=6)

        self.status_lbl = ctk.CTkLabel(
            vp_hdr, text="NO MEDIA LOADED",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#3a3525"
        )
        self.status_lbl.pack(side="right", padx=12, pady=6)

        self.preview_label = ctk.CTkLabel(
            self.viewport_card,
            text="give it something to remember\n\n[ CLICK TO CHOOSE FILE ]\n.MP4  .AVI  .MKV  .MOV  .JPG  .PNG",
            font=ctk.CTkFont(family="Courier New", size=13),
            text_color="#4a3e20",
            cursor="hand2"
        )
        self.preview_label.pack(expand=True, fill="both", padx=15, pady=(15, 5))
        self.preview_label.bind("<Button-1>", lambda e: self.load_media())
        self.viewport_card.bind("<Button-1>", lambda e: self.load_media())

        # ── CRT LOGGING TERMINAL CONSOLE ──────────────────────────────────
        log_frame = ctk.CTkFrame(self.viewport_card, height=140, fg_color="#080705", border_width=1, border_color="#1e1c12")
        log_frame.pack(fill="x", padx=10, pady=(0, 10))

        log_hdr = ctk.CTkFrame(log_frame, height=22, fg_color="#0d0b08")
        log_hdr.pack(fill="x")
        ctk.CTkLabel(log_hdr, text="TERMINAL LOG // RECONSTRUCTION TELEMETRY", font=ctk.CTkFont(family="Courier New", size=9), text_color="#7a6628").pack(side="left", padx=8)

        self.log_textbox = ctk.CTkTextbox(
            log_frame, height=100, font=ctk.CTkFont(family="Courier New", size=10),
            fg_color="#080705", text_color="#4a7840", border_width=0, activate_scrollbars=True
        )
        self.log_textbox.pack(fill="both", expand=True, padx=4, pady=2)
        self.log_textbox.configure(state="disabled")

    def add_log(self, msg, level="info"):
        """Append log message to terminal console."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[INFO]" if level == "info" else ("[ALERT]" if level == "alert" else "[WARN]")
        line = f"[{timestamp}] {prefix} {msg}\n"
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", line)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

        # ── BOTTOM BAR ────────────────────────────────────────────────────
        self.bottom_bar = ctk.CTkFrame(
            self, height=68,
            fg_color="#0e0d08",
            border_width=1, border_color="#2e2a1e", corner_radius=0
        )
        self.bottom_bar.pack(side="bottom", fill="x")

        self.load_btn = ctk.CTkButton(
            self.bottom_bar, text="📁  feed it a file",
            font=ctk.CTkFont(family="Courier New", size=13),
            fg_color="#1e1c12", hover_color="#252318",
            border_width=1, border_color="#3a3525", text_color="#c8a84a",
            height=40, command=self.load_media
        )
        self.load_btn.pack(side="left", padx=18, pady=14)

        self.export_btn = ctk.CTkButton(
            self.bottom_bar, text="💾  RENDER THE MEMORY",
            font=ctk.CTkFont(family="Courier New", size=13),
            fg_color="#1e2818", hover_color="#252e1e",
            border_width=1, border_color="#4a7840", text_color="#4a7840",
            height=40, state="disabled",
            command=self.start_export
        )
        self.export_btn.pack(side="right", padx=18, pady=14)

        self.progress_bar = ctk.CTkProgressBar(
            self.bottom_bar, height=4,
            progress_color="#4a7840", fg_color="#0a0908"
        )
        self.progress_bar.set(0)

    def setup_control_sliders(self):
        sliders_data = [
            ("how wrong it looks",        "master_val",     0, 100, 85,  "#8a3030"),
            ("text it got wrong",         "poster_melt",    0, 100, 90,  "#7a6628"),
            ("faces that aren't right",   "object_melt",    0, 100, 80,  "#7a6628"),
            ("objects stretched wrong",   "object_stretch", 0, 100, 70,  "#7a6628"),
            ("reality tearing",           "reality_tear",   0, 100, 75,  "#4a6040"),
            ("geometry that folds wrong", "spatial_mirror", 0, 100, 40,  "#4a6040"),
            ("colour bleeding at edges",  "chromatic_val",  0, 100, 60,  "#4a6040"),
            ("tape head skipping",        "pixel_sort_val", 0, 100, 55,  "#4a6040"),
        ]

        self.slider_vars = {}
        for title, key, mn, mx, default, color in sliders_data:
            grp = ctk.CTkFrame(
                self.controls_scroll,
                fg_color="#0e0d08", border_width=1,
                border_color="#1e1c12", corner_radius=0
            )
            grp.pack(fill="x", pady=3, padx=2)

            row = ctk.CTkFrame(grp, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=(6, 2))

            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=color).pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=f"{default}%",
                                   font=ctk.CTkFont(family="Courier New", size=10),
                                   text_color="#3a3525")
            val_lbl.pack(side="right")

            slider = ctk.CTkSlider(
                grp, from_=mn, to=mx, number_of_steps=100,
                button_color=color, button_hover_color="#c8a84a",
                progress_color=color,
                command=lambda v, vl=val_lbl: vl.configure(text=f"{int(v)}%")
            )
            slider.set(default)
            slider.pack(fill="x", padx=8, pady=(0, 8))
            self.slider_vars[key] = slider

    def get_sliders(self):
        return {k: int(v.get()) for k, v in self.slider_vars.items()}

    def regen_seed(self):
        raw = self.seed_input.get().strip()
        if raw:
            try:
                val = int(raw, 16)
            except ValueError:
                try:
                    val = int(raw)
                except ValueError:
                    val = None
            if val is not None and val > 0:
                self.engine.set_seed(val & 0xFFFFFFFF)
            else:
                self.engine.set_seed(random.randint(0, 0xFFFFFFFF))
        else:
            self.engine.set_seed(random.randint(0, 0xFFFFFFFF))

        self.seed_display.configure(text=f"SEED: {self.engine.seed:08X}")
        self.seed_input.delete(0, "end")
        self.seed_input.insert(0, f"{self.engine.seed:08X}")

    def load_media(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Media", "*.mp4 *.avi *.mov *.mkv *.webm *.jpg *.jpeg *.png *.webp"),
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("Image Files", "*.jpg *.jpeg *.png *.webp"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return
        
        self.current_video_path = path
        self.export_btn.configure(state="normal")
        self.status_lbl.configure(text=f"MONITORING: {os.path.basename(path).upper()}")
        self.add_log(f"Loaded media file: {os.path.basename(path)}", "info")

        # New seed on every upload
        self.engine.set_seed(random.randint(0, 0xFFFFFFFF))
        self.seed_display.configure(text=f"SEED: {self.engine.seed:08X}")
        self.seed_input.delete(0, "end")
        self.seed_input.insert(0, f"{self.engine.seed:08X}")

        self.is_previewing = False
        time.sleep(0.15)
        self.is_previewing = True
        self.preview_thread = threading.Thread(target=self.live_preview_loop, daemon=True)
        self.preview_thread.start()

    def live_preview_loop(self):
        path = self.current_video_path
        if not path or not os.path.exists(path):
            self.after(0, lambda: self.add_log("Media file path invalid or missing.", "warn"))
            return

        is_image = path.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))

        if is_image:
            frame = cv2.imread(path)
            if frame is None:
                self.after(0, lambda: self.add_log("Failed to decode image file.", "warn"))
                return
            
            while self.is_previewing:
                rng = random.Random(self.engine.seed)
                sliders = self.get_sliders()
                out = self.engine.process_frame(frame, rng, sliders, 0, 30.0)
                self._show_frame(out)
                time.sleep(0.5)
            return

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.after(0, lambda: self.add_log("OpenCV failed to open video file stream.", "warn"))
            return
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_delay = 1.0 / fps
        rng = random.Random(self.engine.seed)
        active_interrupt = None
        frame_idx = 0

        while self.is_previewing and cap.isOpened():
            start_t = time.time()
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                rng = random.Random(self.engine.seed)
                active_interrupt = None
                continue

            h, w = frame.shape[:2]
            time_sec = frame_idx / fps
            sliders = self.get_sliders()
            master_v = sliders["master_val"] / 100.0
            interrupt_density = 0.65

            # Visual interrupt check
            if active_interrupt and frame_idx >= active_interrupt[1]:
                active_interrupt = None
            if not active_interrupt and frame_idx % max(1, int(fps * 7)) == 0:
                if rng.random() < interrupt_density * master_v:
                    v_type = rng.choice(["no_video", "static", "no_signal"])
                    dur = 3.0 if v_type == "no_signal" else 1.2
                    lang = rng.choice(NO_SIGNAL_LANGS)
                    active_interrupt = (v_type, frame_idx + int(dur * fps), lang)

            if active_interrupt:
                v_type, _, lang = active_interrupt
                if v_type == "no_signal":
                    out = self.engine.render_no_signal_screen(w, h, lang)
                elif v_type == "static":
                    out = self.engine.render_static_screen(w, h)
                else:
                    out = self.engine.render_no_video_screen(frame, time_sec)
            else:
                out = self.engine.process_frame(frame, rng, sliders, frame_idx, fps)

            self._show_frame(out)
            frame_idx += 1
            elapsed = time.time() - start_t
            time.sleep(max(0.001, frame_delay - elapsed))

        cap.release()

    def _show_frame(self, bgr_frame):
        try:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((760, 500))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.after(0, lambda ci=ctk_img: self.preview_label.configure(image=ci, text=""))
        except Exception:
            pass

    def start_export(self):
        if not self.current_video_path or self.is_processing:
            return
        self.is_processing = True
        self.is_previewing = False
        self.export_btn.configure(state="disabled")
        self.load_btn.configure(state="disabled")
        self.progress_bar.pack(side="bottom", fill="x", padx=0, pady=0)
        self.progress_bar.set(0)
        threading.Thread(target=self.process_video_thread, daemon=True).start()

    def process_video_thread(self):
        try:
            in_path = self.current_video_path
            out_dir = os.path.dirname(in_path)
            base = os.path.splitext(os.path.basename(in_path))[0]
            temp_video = os.path.join(tempfile.gettempdir(), f"_misrem_temp_{int(time.time())}.mp4")
            final_path = os.path.join(out_dir, f"ꓫ REMΕMᗷER_{base}_MISREMEMBERED.mp4")

            cap = cv2.VideoCapture(in_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300

            # Optimize resolution for fast desktop processing (max 1280x720)
            target_w, target_h = orig_w, orig_h
            if orig_w > 1280:
                target_w = 1280
                target_h = int(orig_h * (1280 / orig_w))
            
            self.after(0, lambda: self.add_log(f"Starting export: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f} FPS", "alert"))

            # Use mp4v for temp file
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video, fourcc, fps, (target_w, target_h))

            sliders = self.get_sliders()
            master_v = sliders["master_val"] / 100.0
            rng = random.Random(self.engine.seed)
            active_interrupt = None
            frame_idx = 0
            start_export_time = time.time()

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if orig_w != target_w:
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

                time_sec = frame_idx / fps

                if active_interrupt and frame_idx >= active_interrupt[1]:
                    active_interrupt = None
                if not active_interrupt and frame_idx % max(1, int(fps * 7)) == 0:
                    if rng.random() < 0.65 * master_v:
                        v_type = rng.choice(["no_video", "static", "no_signal"])
                        dur = 3.0 if v_type == "no_signal" else 1.2
                        lang = rng.choice(NO_SIGNAL_LANGS)
                        active_interrupt = (v_type, frame_idx + int(dur * fps), lang)
                        self.after(0, lambda vt=v_type: self.add_log(f"Visual Interrupt Triggered: {vt}", "warn"))

                if active_interrupt:
                    v_type, _, lang = active_interrupt
                    if v_type == "no_signal":
                        out = self.engine.render_no_signal_screen(target_w, target_h, lang)
                    elif v_type == "static":
                        out = self.engine.render_static_screen(target_w, target_h)
                    else:
                        out = self.engine.render_no_video_screen(frame, time_sec)
                else:
                    out = self.engine.process_frame(frame, rng, sliders, frame_idx, fps)

                writer.write(out)
                frame_idx += 1

                # Update progress bar every 60 frames — calling self.after()
                # more frequently causes tkinter event queue back-pressure
                # which drags the worker thread down from 38 FPS to 20 FPS.
                if frame_idx % 60 == 0:
                    prog = frame_idx / float(total_frames)
                    elapsed = time.time() - start_export_time
                    fps_real = frame_idx / max(0.001, elapsed)
                    eta = int((total_frames - frame_idx) / max(0.1, fps_real))
                    self.after(0, lambda p=prog, f=fps_real, idx=frame_idx, tot=total_frames, e=eta: (
                        self.progress_bar.set(min(0.95, p)),
                        self.add_log(f"Frame {idx}/{tot} — {f:.0f} FPS — ETA {e}s")
                    ))

            cap.release()
            writer.release()

            # ── AUDIO MUXING ─────────────────────────────────────────────────
            # If ffmpeg is available: re-encode video to H.264 and mux in original audio (or emg.mp3 if silent)
            if FFMPEG:
                pitch_rate = 0.82 + rng.random() * 0.36  # slight pitch warp
                emg_path = os.path.join(os.path.dirname(__file__), "emg.mp3")

                # Check if input has audio track
                probe_cmd = [
                    FFMPEG, "-i", in_path
                ]
                probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
                has_audio = "Audio:" in probe_res.stderr

                audio_input = in_path if has_audio else (emg_path if os.path.exists(emg_path) else None)

                if audio_input:
                    cmd = [
                        FFMPEG, "-y",
                        "-i", temp_video,       # processed video
                        "-i", audio_input,      # audio source (original or emg.mp3)
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "18",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-af", f"asetrate={int(44100 * pitch_rate)},aresample=44100,atempo={1.0/pitch_rate:.4f}",
                        "-shortest",
                        final_path
                    ]
                else:
                    cmd = [
                        FFMPEG, "-y",
                        "-i", temp_video,
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "18",
                        final_path
                    ]

                result = subprocess.run(cmd, capture_output=True, timeout=600)
                try:
                    os.remove(temp_video)
                except Exception:
                    pass
                if result.returncode != 0:
                    # ffmpeg failed — fall back to temp video renamed
                    import shutil
                    shutil.move(temp_video, final_path)
            else:
                # No ffmpeg: just move the temp video (no audio)
                import shutil
                shutil.move(temp_video, final_path)

            self.after(0, lambda: self.on_export_complete(final_path))

        except Exception as e:
            print("Export Error:", e)
            self.after(0, self.on_export_error)

    def on_export_complete(self, out_path):
        self.is_processing = False
        self.export_btn.configure(state="normal")
        self.load_btn.configure(state="normal")
        self.progress_bar.pack_forget()
        self.progress_bar.set(0)
        self.status_lbl.configure(text=f"COMPLETE: {os.path.basename(out_path)}")
        messagebox.showinfo("Export Complete", f"Saved to:\n{out_path}")

    def on_export_error(self):
        self.is_processing = False
        self.export_btn.configure(state="normal")
        self.load_btn.configure(state="normal")
        self.progress_bar.pack_forget()
        messagebox.showerror("Export Failed", "Check console for error details.")


if __name__ == "__main__":
    app = MisrememberedApp()
    app.mainloop()
