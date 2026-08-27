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

APP_VERSION = "v4.6.2-ON-DEMAND-DIFFUSION"

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM TELEMETRY & HARDWARE MONITORING
# ─────────────────────────────────────────────────────────────────────────────
def get_system_memory_status():
    """Returns (ram_total_gb, ram_avail_gb, ram_load_pct, vram_info_str)."""
    ram_total, ram_avail, ram_load = 16.0, 8.0, 50
    try:
        import ctypes
        class _MS(ctypes.Structure):
            _fields_ = [
                ('l', ctypes.c_ulong), ('load', ctypes.c_ulong),
                ('t_phys', ctypes.c_ulonglong), ('a_phys', ctypes.c_ulonglong),
                ('t_page', ctypes.c_ulonglong), ('a_page', ctypes.c_ulonglong),
                ('t_virt', ctypes.c_ulonglong), ('a_virt', ctypes.c_ulonglong),
                ('a_ext', ctypes.c_ulonglong)
            ]
        m = _MS()
        m.l = ctypes.sizeof(_MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            ram_total = round(m.t_phys / (1024 ** 3), 1)
            ram_avail = round(m.a_phys / (1024 ** 3), 1)
            ram_load = int(m.load)
    except Exception:
        pass

    vram_str = "VRAM: N/A"
    try:
        import torch
        if torch.cuda.is_available():
            dev = torch.cuda.current_device()
            dev_name = torch.cuda.get_device_name(dev)
            v_total = round(torch.cuda.get_device_properties(dev).total_memory / (1024 ** 3), 1)
            v_alloc = round(torch.cuda.memory_allocated(dev) / (1024 ** 3), 1)
            vram_str = f"GPU: {dev_name} [{v_alloc}/{v_total}GB]"
        else:
            vram_str = "GPU: CPU MODE"
    except Exception:
        pass

    return ram_total, ram_avail, ram_load, vram_str

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
    def synthesize_fluorescent_hum(n_samples, sr=44100, gain=0.038):
        """Generates authentic Backrooms 60Hz + harmonic fluorescent light buzz with high-pitched ballast/CRT whine."""
        t = np.linspace(0, n_samples / sr, n_samples, endpoint=False)
        # Deep 60Hz ballast transformer hum
        low_hum = (
            0.48 * np.sin(2 * np.pi * 60 * t) +
            0.36 * np.sin(2 * np.pi * 120 * t) +
            0.22 * np.sin(2 * np.pi * 180 * t) +
            0.14 * np.sin(2 * np.pi * 240 * t) +
            0.08 * np.sin(2 * np.pi * 360 * t) +
            0.05 * np.sin(2 * np.pi * 480 * t)
        )
        # High-pitched piercing fluorescent light capacitor buzz & CRT 15.7kHz flyback whine
        high_whine = (
            0.18 * np.sin(2 * np.pi * 1200 * t) +
            0.14 * np.sin(2 * np.pi * 3180 * t) +
            0.10 * np.sin(2 * np.pi * 4800 * t) +
            0.08 * np.sin(2 * np.pi * 8400 * t) +
            0.06 * np.sin(2 * np.pi * 15734 * t) # CRT television / monitor flyback whine
        )
        mod = 0.85 + 0.15 * np.sin(2 * np.pi * 0.4 * t) + 0.08 * np.sin(2 * np.pi * 2.3 * t)
        noise = np.random.normal(0, 0.035, n_samples)
        out = ((low_hum + high_whine) * mod + noise) * gain
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
    def synthesize_liminal_ambient(n_samples, sr=44100, gain=0.042):
        """
        Procedural Kane Pixels / Still Life liminal ambient drone.
        Slow sine pads (55Hz drone, 110Hz octave, 165Hz fifth) with slight detuning,
        a noise carpet band-passed to 400-1200Hz, and a slow LFO undulation.
        Sounds like: vast empty building, far-off HVAC, endless corridor.
        """
        t = np.linspace(0, n_samples / sr, n_samples, endpoint=False)

        # Detuned slow drone pads — slightly out of phase for unsettling shimmer
        pad = (
            0.55 * np.sin(2 * np.pi * 55.00 * t) +
            0.35 * np.sin(2 * np.pi * 55.13 * t) +
            0.28 * np.sin(2 * np.pi * 110.0 * t) +
            0.16 * np.sin(2 * np.pi * 110.19 * t) +
            0.18 * np.sin(2 * np.pi * 165.0 * t) +
            0.10 * np.sin(2 * np.pi * 220.5 * t) +
            0.06 * np.sin(2 * np.pi * 440.0 * t)
        )

        # Very slow LFO undulation (0.07Hz & 0.13Hz)
        lfo = (
            0.60 + 0.22 * np.sin(2 * np.pi * 0.07 * t) +
            0.12 * np.sin(2 * np.pi * 0.13 * t + 1.1) +
            0.08 * np.sin(2 * np.pi * 0.31 * t + 2.4)
        )

        # Band-passed noise carpet — "room that isn't quite silent" feel
        raw_noise = np.random.normal(0, 1, n_samples).astype(np.float32)
        sos_bp = signal.butter(4, [400, 1200], btype='bandpass', fs=sr, output='sos')
        noise_bp = signal.sosfilt(sos_bp, raw_noise) * 0.15

        # Sub-bass breath: very slow 0.04Hz throb at 28Hz
        sub_breath = 0.30 * np.sin(2 * np.pi * 28.0 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t))

        mono = np.clip((pad * lfo + noise_bp + sub_breath) * gain, -1.0, 1.0)

        # Slight stereo width via tiny time offset
        shift = max(1, int(sr * 0.011))
        left = mono
        right = np.concatenate((np.zeros(shift), mono[:-shift]))
        return np.column_stack((left, right)).astype(np.float32)

    @staticmethod
    def synthesize_no_signal_jingle(n_samples, sr=44100, gain=0.35):
        """
        Procedural 'Everything Must Go' style No Signal audio event.
        Short broken-chord ascending pattern with retro telephone band EQ (300Hz-3400Hz).
        """
        note_freqs = [311.13, 392.00, 466.16, 523.25, 622.25, 783.99]
        note_dur = max(1, int(sr * 0.10))
        jingle = np.zeros(n_samples, dtype=np.float32)

        for i in range(0, n_samples, note_dur):
            note_idx = (i // note_dur) % len(note_freqs)
            freq = note_freqs[note_idx]
            end = min(n_samples, i + note_dur)
            seg_len = end - i
            seg_t = np.arange(seg_len) / sr
            fade_in = min(int(seg_len * 0.06), seg_len)
            fade_out = max(0, seg_len - int(seg_len * 0.76))
            sustain = max(0, int(seg_len * 0.70))
            env = np.concatenate([
                np.linspace(0, 1, fade_in),
                np.ones(sustain),
                np.linspace(1, 0, fade_out)
            ])[:seg_len]
            jingle[i:end] += np.sin(2 * np.pi * freq * seg_t) * env * 0.7
            jingle[i:end] += np.sin(2 * np.pi * freq * 2.0 * seg_t) * env * 0.20

        # Telephone band EQ — retro broadcast deadness
        sos_tel = signal.butter(4, [300, 3400], btype='bandpass', fs=sr, output='sos')
        jingle = signal.sosfilt(sos_tel, jingle)
        jingle = np.tanh(jingle * 2.2) * 0.45

        mono = np.clip(jingle * gain, -1.0, 1.0)
        return np.column_stack((mono, mono)).astype(np.float32)

    @staticmethod
    def process_full_audio(audio, sr=44100, seed=12345, sliders=None, fps=30.0, total_frames=0, emg_audio_f=None):
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

        n_samples = len(audio_f)
        duration_s = n_samples / float(sr)
        dbg(f"Audio DSP: Processing {duration_s:.1f}s audio track with Kane Pixels parameters...", "AUDIO")

        # 1. Analog tape warping with weighted pitch intervals & stalls
        warped = KanePixelsAudioDSP.apply_tape_warp(audio_f, sr=sr, seed=seed, intensity=master_v)

        # 2. Backrooms vast liminal reverb
        reverbed = KanePixelsAudioDSP.apply_liminal_reverb(warped, sr=sr, wet=0.38 * master_v, decay=0.70)

        # 3. Ghost memory whisper echo
        with_echo = KanePixelsAudioDSP.apply_memory_whisper_echo(reverbed, sr=sr, delay_sec=2.6, gain=0.20 * master_v)

        # 4. Fluorescent light 60Hz electromagnetic hum
        hum = KanePixelsAudioDSP.synthesize_fluorescent_hum(n_samples, sr=sr, gain=0.030 * master_v)
        mixed = with_echo + hum

        # 5. Kane Pixels / Still Life liminal ambient drone layer under entire track
        dbg("Synthesizing liminal ambient drone layer...", "AUDIO")
        ambient = KanePixelsAudioDSP.synthesize_liminal_ambient(n_samples, sr=sr, gain=0.040 * master_v)
        mixed = mixed + ambient

        # 6. Green Light electrical hum surge
        if green_v > 0.10:
            mixed = KanePixelsAudioDSP.apply_green_light_audio_surge(mixed, sr=sr, duration_s=duration_s, intensity=green_v * master_v)

        # 7. Inject No Signal audio at each no_signal window (every 18s cycle at 12.8s mark)
        # Uses real emg_audio_f (the emg.mp3 loaded by export thread) if available,
        # otherwise falls back to the procedural synthesized jingle.
        if master_v > 0.30:
            no_signal_dur = 1.80   # matches longer 12.8s–14.6s visual window
            ns_n = int(sr * no_signal_dur)

            if emg_audio_f is not None:
                dbg("Injecting EMG audio at No Signal timestamps...", "AUDIO")
                # Loop or trim the EMG audio to exactly ns_n samples
                emg_src = emg_audio_f
                if len(emg_src) < ns_n:
                    reps = int(np.ceil(ns_n / len(emg_src)))
                    emg_src = np.tile(emg_src, (reps, 1))[:ns_n]
                else:
                    emg_src = emg_src[:ns_n]
                ns_audio = emg_src * (0.80 * master_v)
            else:
                dbg("Injecting synthesized No Signal jingle at interrupt timestamps...", "AUDIO")
                ns_audio = KanePixelsAudioDSP.synthesize_no_signal_jingle(ns_n, sr=sr, gain=0.38 * master_v)

            cycle_time = 18.0
            t_sec = 0.0
            while t_sec < duration_s:
                event_t = t_sec + 12.8
                if event_t < duration_s:
                    idx0 = int(event_t * sr)
                    idx1 = min(n_samples, idx0 + ns_n)
                    seg_len = idx1 - idx0
                    if seg_len > 0:
                        fade_len = min(int(sr * 0.04), seg_len // 4)
                        env = np.ones(seg_len, dtype=np.float32)
                        env[:fade_len] = np.linspace(0, 1, fade_len)
                        env[-fade_len:] = np.linspace(1, 0, fade_len)
                        
                        # Completely pause / mute base video audio during EMG playback
                        duck_mask = (1.0 - env)[:, np.newaxis]
                        mixed[idx0:idx1] = mixed[idx0:idx1] * duck_mask + ns_audio[:seg_len] * env[:, np.newaxis]
                t_sec += cycle_time

        # 8. Camcorder AGC & soft saturation limiter
        saturated = np.tanh(mixed * 1.15) / 1.15

        # Convert back to int16
        out_int16 = np.clip(saturated * 32767.0, -32767.0, 32767.0).astype(np.int16)
        dbg(f"Audio DSP: Processing complete.", "AUDIO")
        return out_int16

    @staticmethod
    def load_emg_audio(emg_path, sr=44100, ffmpeg=None):
        """
        Decode emg.mp3 to a float32 stereo numpy array at 44100 Hz using FFmpeg.
        Returns None if the file doesn't exist or decode fails.
        """
        if not emg_path or not os.path.exists(emg_path):
            dbg(f"EMG audio file not found: {emg_path}", "AUDIO")
            return None
        ff_bin = ffmpeg or "ffmpeg"
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"_emg_decoded_{int(time.time())}.wav")
            cmd = [ff_bin, "-y", "-i", emg_path, "-vn", "-ac", "2", "-ar", str(sr), tmp]
            subprocess.run(cmd, capture_output=True, timeout=30)
            if not os.path.exists(tmp) or os.path.getsize(tmp) < 500:
                dbg("EMG decode produced no output", "AUDIO")
                return None
            sr_out, raw = wavfile.read(tmp)
            try:
                os.remove(tmp)
            except Exception:
                pass
            if raw.dtype == np.int16:
                audio_f = raw.astype(np.float32) / 32768.0
            elif raw.dtype == np.int32:
                audio_f = raw.astype(np.float32) / 2147483648.0
            else:
                audio_f = raw.astype(np.float32)
            if audio_f.ndim == 1:
                audio_f = np.column_stack((audio_f, audio_f))
            dbg(f"EMG audio loaded: {len(audio_f)/sr_out:.2f}s @ {sr_out}Hz stereo", "AUDIO")
            return audio_f
        except Exception as e:
            dbg(f"EMG audio load failed: {e}", "ERROR")
            return None




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
        # Generate believable "slightly wrong" / uncanny pseudo-words rather than full foreign phrases
        vowels = ['a', 'e', 'i', 'o', 'u', 'ea', 'oe', 'ai', 'y', 'ou', 'ee']
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'sh', 'th', 'ch', 'bl', 'st', 'cl', 'pr', 'tr']
        res = []
        is_vow = rng.random() < 0.35
        while len("".join(res)) < word_len:
            if is_vow:
                res.append(rng.choice(vowels))
            else:
                res.append(rng.choice(consonants))
            is_vow = not is_vow
        out = "".join(res)[:word_len]
        return out.capitalize() if rng.random() < 0.25 else out

    @staticmethod
    def corrupt_actual_frame_text(bgr_img, rng, intensity=0.85, frame_idx=0, fps=30.0):
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # ── STEP 0: Multi-scale text region detection ──
        # Detect high-contrast text strokes via morphological gradient + thresholding
        scale_factor = 2
        gray_small = cv2.resize(gray, (w // scale_factor, h // scale_factor), interpolation=cv2.INTER_LINEAR)
        
        # Morphological gradient captures text edges accurately across all font weights
        kernel_grad = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_grad = cv2.morphologyEx(gray_small, cv2.MORPH_GRADIENT, kernel_grad)
        
        # Horizontal connecting element groups character glyphs into full line bounding boxes
        kernel_conn = cv2.getStructuringElement(cv2.MORPH_RECT, (14, 3))
        connected_small = cv2.morphologyEx(morph_grad, cv2.MORPH_CLOSE, kernel_conn)
        
        # Adaptive thresholding to capture clean binary text clusters
        _, thresh_small = cv2.threshold(connected_small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh_small = cv2.dilate(thresh_small, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2)))
        
        contours_small, _ = cv2.findContours(thresh_small, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Collect valid text bounding boxes
        text_boxes = []
        for cnt in contours_small:
            sx, sy, sbw, sbh = cv2.boundingRect(cnt)
            bx, by = sx * scale_factor, sy * scale_factor
            bw, bh = sbw * scale_factor, sbh * scale_factor
            aspect = bw / float(max(1, bh))
            area = bw * bh
            
            # Filter out whole-screen background noise or microscopic dots
            if (15 < bw < w * 0.98 and 8 < bh < h * 0.45 and aspect > 0.8 and area > 200):
                if rng.random() <= intensity:
                    text_boxes.append((bx, by, bw, bh))

        if not text_boxes:
            return bgr_img

        # Sort text boxes top-to-bottom so lines are processed coherently
        text_boxes.sort(key=lambda b: (b[1], b[0]))

        # ── STEP 1: Fully clean and inpaint detected text regions on base image ──
        out = bgr_img.copy()
        box_data = []

        for (bx, by, bw, bh) in text_boxes[:6]:
            # Extended bounding area to fully encompass character ascenders and descenders
            px = max(6, int(bw * 0.08))
            py = max(8, int(bh * 0.35))
            rx = max(0, bx - px);      ry = max(0, by - py)
            rw = min(w - rx, bw + px * 2); rh = min(h - ry, bh + py * 2)

            local_patch = out[ry:ry+rh, rx:rx+rw]
            if local_patch.size == 0:
                continue

            local_gray = cv2.cvtColor(local_patch, cv2.COLOR_BGR2GRAY)
            # Find the actual text pixels inside the patch using local thresholding
            # Determine if background is light or dark
            mean_lum = np.mean(local_gray)
            is_light_bg = mean_lum > 128

            if is_light_bg:
                # Text is dark pixels on light background
                _, text_mask = cv2.threshold(local_gray, int(mean_lum * 0.85), 255, cv2.THRESH_BINARY_INV)
            else:
                # Text is light pixels on dark background
                _, text_mask = cv2.threshold(local_gray, int(mean_lum * 1.15), 255, cv2.THRESH_BINARY)

            # Dilate text mask to ensure entire character strokes are erased
            text_mask = cv2.dilate(text_mask, np.ones((5, 5), np.uint8))

            # Fast localized inpainting (radius 3 for speed)
            local_clean = cv2.inpaint(local_patch, text_mask, 3, cv2.INPAINT_TELEA)
            out[ry:ry+rh, rx:rx+rw] = local_clean

            box_data.append((bx, by, bw, bh, rx, ry, rw, rh, is_light_bg))

        # ── STEP 2: Render corrupted replacement text on the clean background ──
        pil_img = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        font_candidates = ["arial.ttf", "arialbd.ttf", "calibri.ttf", "verdana.ttf",
                           "times.ttf", "trebuc.ttf"]

        for (bx, by, bw, bh, rx, ry, rw, rh, is_light_bg) in box_data:
            if is_light_bg:
                fg = (rng.randint(0, 30), rng.randint(0, 30), rng.randint(0, 30))
            else:
                fg = (rng.randint(220, 255), rng.randint(220, 255), rng.randint(220, 255))

            # Estimate word count from bbox width/height ratio
            est_words = max(1, int(round(bw / max(1, bh * 3.5))))
            words = [LocalGlyphCorruptor.generate_phonetic_mutation(
                        rng.randint(3, 8), rng) for _ in range(est_words)]
            replacement = " ".join(words)

            f_size = max(11, int(bh * rng.uniform(0.65, 0.90)))
            font = None
            for fc in [rng.choice(font_candidates), "arial.ttf"]:
                try:
                    font = ImageFont.truetype(fc, f_size); break
                except Exception:
                    continue
            if font is None:
                font = ImageFont.load_default()

            tx = bx + rng.randint(0, max(1, int(bw * 0.03)))
            ty = by + max(0, int((bh - f_size) / 2)) + rng.randint(-1, 1)
            draw.text((tx, ty), replacement, fill=fg, font=font)

        # ── STEP 3: Apply Kane Pixels melting drip & glyph stretch distortions ──
        out = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        for (bx, by, bw, bh, rx, ry, rw, rh, _) in box_data:
            patch = out[ry:ry+rh, rx:rx+rw].copy()
            if patch.size == 0:
                continue

            # 1. Razor serration (horizontal slice jitter on replacement glyphs)
            if intensity > 0.35:
                sw = max(2, int(rh * 0.15))
                for sp in range(0, rw, sw * 2):
                    ep = min(rw, sp + sw)
                    sft = rng.choice([-1, 1]) * rng.randint(0, max(1, int(rh * 0.06)))
                    Ms = np.float32([[1, 0, 0], [0, 1, sft]])
                    patch[:, sp:ep] = cv2.warpAffine(
                        patch[:, sp:ep], Ms, (ep - sp, rh), borderMode=cv2.BORDER_REFLECT)

            # 2. Downward viscous melting / glyph drip effect (Kane Pixels Found Footage text melt)
            if intensity > 0.40 and rng.random() < 0.75:
                melt_grid_y, melt_grid_x = np.mgrid[0:rh, 0:rw].astype(np.float32)
                # Vertical drip waves pulling glyph strokes downward
                drip_amp = max(2.0, rh * 0.18 * intensity)
                freq = rng.uniform(2.5, 5.0)
                phase = rng.uniform(0, 6.28)
                drip_offset = drip_amp * np.sin(melt_grid_x / max(1.0, rw) * np.pi * freq + phase)
                drip_offset = np.clip(drip_offset, -2, drip_amp)
                
                # Weight drip so it affects bottom half of glyphs more than top (melting downward)
                vert_weight = (melt_grid_y / max(1.0, rh)) ** 1.3
                src_y = np.clip(melt_grid_y - drip_offset * vert_weight, 0, rh - 1).astype(np.float32)
                src_x = melt_grid_x.copy()
                
                melted = cv2.remap(patch, src_x, src_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                patch = cv2.addWeighted(patch, 0.30, melted, 0.70, 0)

            out[ry:ry+rh, rx:rx+rw] = patch

        return out



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
# 3b. BACKROOMS ENVIRONMENT OBJECT HALLUCINATOR
# Detects large furniture/architectural objects in the scene and applies
# backrooms-style distortion, removal, or replacement effects.
# Works on any video — camera panning a room, walking through a hallway, etc.
# Effects: perspective warp, erase-to-background, ghost duplication, phantom
#          doorway/staircase insertion in walls.
# ─────────────────────────────────────────────────────────────────────────────
class LocalEnvironmentHallucinator:

    # Aspect ratios and size bands that suggest furniture/architectural features:
    # wide flat: tables, desks, shelves  (aspect 1.5–8, area 3–30% of frame)
    # tall thin: bookshelves, doors, windows  (aspect 0.15–0.65, area 2–25%)
    # squarish: chairs, monitors, boxes  (aspect 0.65–1.5, area 2–18%)
    _OBJ_MIN_AREA_FRAC = 0.015   # 1.5% of frame minimum
    _OBJ_MAX_AREA_FRAC = 0.40    # 40% max (anything larger is probably the wall itself)

    @staticmethod
    def _detect_objects(bgr_img, rng):
        """
        Returns a list of (x, y, w, h) bounding rects for furniture-scale objects
        found via Canny edge detection + contour area filtering.
        Skips very thin text-like regions (aspect > 10 or bh < 15px).
        """
        h, w = bgr_img.shape[:2]
        frame_area = w * h
        min_area = frame_area * LocalEnvironmentHallucinator._OBJ_MIN_AREA_FRAC
        max_area = frame_area * LocalEnvironmentHallucinator._OBJ_MAX_AREA_FRAC

        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blur, 30, 90)
        # Close gaps so furniture outlines form solid blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            bx, by, bw, bh = cv2.boundingRect(cnt)
            if bw < 20 or bh < 15:
                continue
            aspect = bw / float(bh)
            if aspect > 12:   # skip text-like horizontal strips
                continue
            objects.append((bx, by, bw, bh))

        # Shuffle so each frame applies to different objects
        rng.shuffle(objects)
        return objects[:6]   # process at most 6 objects per frame

    @staticmethod
    def _sample_background_patch(bgr_img, x, y, bw, bh, rng):
        """Sample a background color patch from outside the object region."""
        h, w = bgr_img.shape[:2]
        # Try sampling from edges of the frame or adjacent region
        sample_x = rng.randint(0, max(1, w - bw - 1)) if rng.random() < 0.5 else max(0, x - bw)
        sample_y = rng.randint(0, max(1, h - bh - 1))
        sx0, sy0 = max(0, sample_x), max(0, sample_y)
        sx1, sy1 = min(w, sx0 + bw), min(h, sy0 + bh)
        patch = bgr_img[sy0:sy1, sx0:sx1].copy()
        if patch.shape[0] != bh or patch.shape[1] != bw:
            patch = cv2.resize(patch, (bw, bh), interpolation=cv2.INTER_LINEAR)
        return patch

    @staticmethod
    def _warp_perspective_object(patch, rng, intensity):
        """
        Apply a subtle perspective warp to a furniture patch — like a chair tilting
        toward the viewer or a bookcase slightly angling away into a wrong dimension.
        """
        bh, bw = patch.shape[:2]
        max_shift = int(min(bw, bh) * 0.18 * intensity)
        if max_shift < 2:
            return patch

        src = np.float32([[0, 0], [bw, 0], [bw, bh], [0, bh]])
        # Randomly perturb each corner slightly — stronger on one side than another
        def jitter():
            return [rng.randint(-max_shift, max_shift), rng.randint(-max_shift, max_shift)]

        dst = np.float32([
            [0 + rng.randint(0, max_shift),       jitter()[1]],
            [bw - rng.randint(0, max_shift),      jitter()[1]],
            [bw - rng.randint(0, max_shift // 2), bh - rng.randint(0, max_shift)],
            [0  + rng.randint(0, max_shift // 2), bh - rng.randint(0, max_shift)],
        ])
        M = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(patch, M, (bw, bh), borderMode=cv2.BORDER_REFLECT)

    @staticmethod
    def apply_environment_hallucination(bgr_img, rng, intensity=0.80):
        """
        Main entry point. Detects furniture-scale objects and applies a random
        backrooms effect to each: distort, erase, ghost-duplicate, or phantom insert.
        """
        if intensity < 0.05:
            return bgr_img

        h, w = bgr_img.shape[:2]
        objects = LocalEnvironmentHallucinator._detect_objects(bgr_img, rng)
        if not objects:
            return bgr_img

        out = bgr_img.copy()
        dbg(f"EnvHallucinator: found {len(objects)} objects to corrupt", "STILL")

        for (bx, by, bw, bh) in objects:
            # Skip if area is invalid
            if bw < 4 or bh < 4:
                continue
            if by + bh > h or bx + bw > w:
                continue

            patch = out[by:by+bh, bx:bx+bw].copy()
            if patch.size == 0:
                continue

            roll = rng.random()

            # ── EFFECT A: PERSPECTIVE DISTORTION (chair tilts, shelf angles wrong) ──
            if roll < 0.35:
                warped = LocalEnvironmentHallucinator._warp_perspective_object(patch, rng, intensity)
                # Blend warped back — not 100% so the ghosting shows through
                blend = cv2.addWeighted(patch, 0.25, warped, 0.75, 0)
                out[by:by+bh, bx:bx+bw] = blend
                dbg(f"  → perspective warp at ({bx},{by}) {bw}x{bh}", "STILL")

            # ── EFFECT B: ERASE/REMOVE (object vanishes, background fills in) ──
            elif roll < 0.55:
                bg_patch = LocalEnvironmentHallucinator._sample_background_patch(
                    bgr_img, bx, by, bw, bh, rng
                )
                # Smear background color with slight noise so it doesn't look like copy-paste
                noise = np.random.randint(-12, 12, bg_patch.shape, dtype=np.int16)
                erased = np.clip(bg_patch.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                # Feather the edges so it blends with surroundings
                mask = np.zeros((bh, bw), dtype=np.float32)
                pad = max(2, min(bh, bw) // 6)
                mask[pad:-pad, pad:-pad] = 1.0
                mask = cv2.GaussianBlur(mask, (pad * 2 + 1, pad * 2 + 1), 0)
                for c in range(3):
                    out[by:by+bh, bx:bx+bw, c] = (
                        patch[:, :, c] * (1.0 - mask) + erased[:, :, c] * mask
                    ).astype(np.uint8)
                dbg(f"  → erase object at ({bx},{by}) {bw}x{bh}", "STILL")

            # ── EFFECT C: GHOST DUPLICATE (copy of object appears shifted — backrooms doubling) ──
            elif roll < 0.75:
                # Shift the duplicate to an adjacent position
                shift_x = rng.choice([-1, 1]) * rng.randint(int(bw * 0.15), int(bw * 0.60))
                shift_y = rng.choice([-1, 1]) * rng.randint(5, max(6, int(bh * 0.25)))
                gx0 = max(0, bx + shift_x)
                gy0 = max(0, by + shift_y)
                gx1 = min(w, gx0 + bw)
                gy1 = min(h, gy0 + bh)
                gw = gx1 - gx0
                gh = gy1 - gy0
                if gw > 10 and gh > 10:
                    ghost_patch = cv2.resize(patch[:gh, :gw], (gw, gh))
                    # Slightly desaturate and darken the ghost for uncanny doubling effect
                    gray_ghost = cv2.cvtColor(ghost_patch, cv2.COLOR_BGR2GRAY)
                    ghost_tinted = cv2.merge([
                        (gray_ghost * 0.55).astype(np.uint8),
                        (gray_ghost * 0.62).astype(np.uint8),
                        (gray_ghost * 0.50).astype(np.uint8),
                    ])
                    ghost_alpha = 0.45 * intensity
                    out[gy0:gy1, gx0:gx1] = cv2.addWeighted(
                        out[gy0:gy1, gx0:gx1], 1.0 - ghost_alpha,
                        ghost_tinted, ghost_alpha, 0
                    )
                dbg(f"  → ghost duplicate at ({bx},{by}) shifted ({shift_x},{shift_y})", "STILL")

            # ── EFFECT D: PHANTOM DOORWAY / ARCHITECTURAL INSERT ──
            # Cut a door/window shaped rectangle into an object, filled with a
            # dark backrooms-adjacent corridor color — like a passage that shouldn't exist.
            else:
                door_w = max(8, int(bw * rng.uniform(0.25, 0.55)))
                door_h = max(12, int(bh * rng.uniform(0.45, 0.85)))
                door_x = bx + rng.randint(0, max(1, bw - door_w))
                door_y = by + rng.randint(0, max(1, bh - door_h))
                dx0, dy0 = max(0, door_x), max(0, door_y)
                dx1, dy1 = min(w, dx0 + door_w), min(h, dy0 + door_h)
                if dx1 - dx0 > 4 and dy1 - dy0 > 4:
                    # Sample average color of the image and darken it significantly
                    mean_col = bgr_img[dy0:dy1, dx0:dx1].mean(axis=(0, 1))
                    corridor_col = np.clip(mean_col * 0.20 + np.array([5, 8, 3]), 0, 40).astype(np.uint8)
                    door_fill = np.full((dy1 - dy0, dx1 - dx0, 3), corridor_col, dtype=np.uint8)
                    # Add subtle noise streaks to the corridor fill
                    noise_streaks = np.random.randint(0, 8, door_fill.shape, dtype=np.uint8)
                    door_fill = np.clip(door_fill.astype(np.int16) + noise_streaks, 0, 50).astype(np.uint8)
                    # Feathered blend
                    feather = np.ones((dy1 - dy0, dx1 - dx0), dtype=np.float32) * intensity * 0.85
                    pad = max(1, min(dy1 - dy0, dx1 - dx0) // 8)
                    feather[:pad, :] = np.linspace(0, 1, pad)[:, np.newaxis]
                    feather[-pad:, :] = np.linspace(1, 0, pad)[:, np.newaxis]
                    for c in range(3):
                        out[dy0:dy1, dx0:dx1, c] = (
                            out[dy0:dy1, dx0:dx1, c].astype(np.float32) * (1.0 - feather) +
                            door_fill[:, :, c].astype(np.float32) * feather
                        ).clip(0, 255).astype(np.uint8)
                dbg(f"  → phantom doorway in object at ({bx},{by})", "STILL")

        return out


# ─────────────────────────────────────────────────────────────────────────────
# 5. BACKROOMS COLOR GRADE
# Boosts saturation, maps toward the iconic yellow-beige fluorescent palette,
# and applies a warm color cast to shadows — the "wrong" lighting of the Backrooms.
# ─────────────────────────────────────────────────────────────────────────────
class BackroomsColorGrade:
    @staticmethod
    def apply(bgr_img, intensity=0.80):
        """
        Applies the Backrooms color grade:
        1. Saturation boost (oversaturated fluorescent look)
        2. Color map toward yellow-beige-cream palette (wallpaper, carpet tones)
        3. Warm shadow cast — everything feels like it's lit by dying fluorescents
        """
        if intensity < 0.02:
            return bgr_img

        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV).astype(np.float32)

        # Boost saturation
        # Saturation: half the original boost for a dreamier, less garish look
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 + intensity * 0.25), 0, 255)
        # Slight value lift — dreamy softness in the midtones
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + intensity * 0.08), 0, 255)

        graded = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

        # Dreamy channel balance: green & blue lowered by quarter, red neutral
        graded[:, :, 0] = np.clip(graded[:, :, 0] * 0.75, 0, 255)   # B −25%
        graded[:, :, 1] = np.clip(graded[:, :, 1] * 0.75, 0, 255)   # G −25%
        # Red left untouched (neutral — no warm push, no cool push)

        # Blend: moderate application
        blend_amt = min(0.65, intensity * 0.70)
        out = cv2.addWeighted(bgr_img.astype(np.float32), 1.0 - blend_amt, graded, blend_amt, 0)
        return np.clip(out, 0, 255).astype(np.uint8)



# ─────────────────────────────────────────────────────────────────────────────
# 6. GENERATIONAL DIGITAL DEGRADATION ("Deep Fried" Decay)
# Simulates recursive meme/share image degradation via JPEG re-encoding,
# heavy grain injection, and HSV contrast/saturation crushing.
# ─────────────────────────────────────────────────────────────────────────────
class GenerationalDegradation:
    @staticmethod
    def apply(bgr_img, rng, intensity=0.80):
        """
        Runs the image through multiple generations of lossy digital decay:
        1. N rounds of JPEG encode/decode at decreasing quality (blocking artifacts)
        2. Heavy random grain noise layered on top
        3. HSV contrast crushing + saturation clipping (the 'deep-fried' look)
        """
        if intensity < 0.05:
            return bgr_img

        h, w = bgr_img.shape[:2]
        # Work at half resolution for the slow JPEG + grain passes — resize back at end
        sw, sh = max(4, w // 2), max(4, h // 2)
        small = cv2.resize(bgr_img, (sw, sh), interpolation=cv2.INTER_LINEAR)

        # ── 1. Single JPEG generation pass (max 1 — was 1-3) ──
        quality = max(8, int(40 - intensity * 28))
        ret, buf = cv2.imencode('.jpg', small, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if ret and buf is not None:
            decoded = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if decoded is not None and decoded.shape == small.shape:
                small = decoded

        # ── 2. Grain noise (at half-res — fast, then upscale smears it nicely) ──
        grain = int(intensity * 28)
        if grain > 0:
            noise = np.random.randint(-grain, grain, small.shape, dtype=np.int16)
            small = np.clip(small.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Upscale back to full resolution
        out = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)

        # ── 3. HSV contrast & saturation crush at full-res (pure numpy — fast) ──
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 + intensity * 1.10), 0, 255)
        v = hsv[:, :, 2]
        lift = intensity * 14.0
        crush = 255.0 - intensity * 18.0
        v = np.clip((v - lift) / max(0.001, (crush - lift)), 0, 1) * 255.0
        hsv[:, :, 2] = np.clip(v, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)



# ─────────────────────────────────────────────────────────────────────────────
# 7. UNCANNY FACE DISTORTION & GLOWING OCULAR FLARES
# Uses OpenCV built-in Haar cascade classifiers — zero additional installs.
# Rubber-band warp hollows out facial geometry; radial caustic flares replace eyes.
# ─────────────────────────────────────────────────────────────────────────────
class FaceDistortionEngine:
    """
    Face detection + rubber-band warp + glowing ocular flares.
    OpenCV 5.0 dropped CascadeClassifier — uses FaceDetectorYN (YuNet ONNX) instead.
    Downloads the ~320KB model file on first use and caches it to temp dir.
    Falls back to skin-color YCrCb blob detection if the model can't be fetched.
    """
    _detector    = None   # cv2.FaceDetectorYN instance or None
    _use_yunet   = None   # True = yunet loaded, False = skin fallback, None = not tried
    _MODEL_URL   = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    _MODEL_CACHE = os.path.join(tempfile.gettempdir(), "yunet_face_2023mar.onnx")

    @classmethod
    def _ensure_detector(cls, input_w, input_h):
        """
        Initialize face detector. Returns True if a detector is ready, False if not.
        Tries in order: YuNet ONNX (cv2.FaceDetectorYN), then marks skin-fallback mode.
        """
        if cls._use_yunet is not None:
            # Already initialized — update input size if using YuNet
            if cls._use_yunet and cls._detector is not None:
                try:
                    cls._detector.setInputSize((input_w, input_h))
                except Exception:
                    pass
            return True   # either yunet or skin-fallback is ready

        # ── Try to load YuNet ONNX ──
        try:
            _YN = getattr(cv2, 'FaceDetectorYN_create', None)
            if _YN is None:
                raise AttributeError("FaceDetectorYN_create not in cv2")

            # Download model if not cached
            model_path = cls._MODEL_CACHE
            if not os.path.exists(model_path) or os.path.getsize(model_path) < 10000:
                dbg(f"Downloading YuNet face model ({cls._MODEL_URL})...", "FACE")
                try:
                    urllib.request.urlretrieve(cls._MODEL_URL, model_path)
                    dbg(f"YuNet model downloaded: {os.path.getsize(model_path)} bytes", "FACE")
                except Exception as dl_err:
                    dbg(f"YuNet model download failed: {dl_err} — using skin-fallback", "FACE")
                    cls._use_yunet = False
                    return True

            if not os.path.exists(model_path) or os.path.getsize(model_path) < 10000:
                cls._use_yunet = False
                return True

            cls._detector = _YN(
                model_path, "",
                (input_w, input_h),
                score_threshold=0.60,
                nms_threshold=0.30,
                top_k=10
            )
            cls._use_yunet = True
            dbg(f"YuNet face detector loaded OK (cv2 {cv2.__version__})", "FACE")

        except Exception as e:
            dbg(f"YuNet init failed: {e} — using skin-color fallback", "FACE")
            cls._use_yunet = False

        return True

    @staticmethod
    def _detect_faces_skin(bgr_img):
        """
        Skin-color blob fallback: YCrCb thresholding → find large flesh-toned blobs.
        Returns list of (x, y, w, h) similar to haar/yunet output.
        """
        h, w = bgr_img.shape[:2]
        ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
        # Standard skin range in YCrCb
        skin = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
        skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((12, 12), np.uint8))
        skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN,  np.ones((6,  6),  np.uint8))
        contours, _ = cv2.findContours(skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        faces = []
        frame_area = w * h
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < frame_area * 0.006 or area > frame_area * 0.55:
                continue
            bx, by, bw, bh = cv2.boundingRect(cnt)
            aspect = bw / max(bh, 1)
            if aspect < 0.35 or aspect > 2.2:
                continue
            faces.append((bx, by, bw, bh))
        return faces[:4]

    @staticmethod
    def _rubber_band_warp(patch, rng, intensity):
        """Radial stretch from face center — hollows out features, uncanny valley."""
        bh, bw = patch.shape[:2]
        if bh < 8 or bw < 8:
            return patch
        cx, cy = bw * 0.5, bh * 0.5
        Y, X = np.mgrid[0:bh, 0:bw].astype(np.float32)
        dx = X - cx
        dy = Y - cy
        norm_dist = np.sqrt(dx**2 + dy**2) / max(cx, cy)
        radial = 1.0 + intensity * rng.uniform(0.10, 0.28) * (norm_dist ** 1.6)
        src_x = np.clip(cx + dx * radial + rng.uniform(-bw*0.03, bw*0.03)*intensity, 0, bw-1).astype(np.float32)
        src_y = np.clip(cy + dy * radial + rng.uniform(-bh*0.025, bh*0.025)*intensity, 0, bh-1).astype(np.float32)
        return cv2.remap(patch, src_x, src_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    @staticmethod
    def _eye_flare(canvas, cx, cy, r, color_mode):
        """Additive radial caustic flare over an eye center point."""
        flare = np.zeros_like(canvas, dtype=np.uint8)
        r = max(3, r)
        cols = [(0, 20, 80), (0, 0, 180), (0, 0, 240), (80, 100, 255)] if color_mode == 'red' \
               else [(0, 50, 80), (0, 150, 220), (0, 210, 255), (100, 240, 255)]
        for i, col in enumerate(cols):
            cv2.circle(flare, (cx, cy), max(1, r * (4 - i)), col, -1, cv2.LINE_AA)
        cv2.circle(flare, (cx, cy), max(1, r // 3), (200, 230, 255), -1, cv2.LINE_AA)
        cv2.line(flare, (cx - r*5, cy), (cx + r*5, cy), cols[2], max(1, r // 3), cv2.LINE_AA)
        return cv2.add(canvas, flare)

    @staticmethod
    def apply(bgr_img, rng, intensity=0.80):
        if intensity < 0.05:
            return bgr_img

        h, w = bgr_img.shape[:2]
        FaceDistortionEngine._ensure_detector(w, h)

        # Detect faces
        faces = []
        try:
            if FaceDistortionEngine._use_yunet and FaceDistortionEngine._detector is not None:
                # YuNet: detect() returns (nfaces, Nx15 array) with cols [x,y,w,h, ...]
                FaceDistortionEngine._detector.setInputSize((w, h))
                _, detections = FaceDistortionEngine._detector.detect(bgr_img)
                if detections is not None:
                    for d in detections:
                        fx, fy, fw, fh = int(d[0]), int(d[1]), int(d[2]), int(d[3])
                        faces.append((fx, fy, fw, fh))
            else:
                # Skin-color blob fallback
                faces = FaceDistortionEngine._detect_faces_skin(bgr_img)
        except Exception as e:
            dbg(f"Face detect error: {e}", "FACE")
            return bgr_img

        if not faces:
            return bgr_img

        out = bgr_img.copy()
        color_mode = rng.choice(['red', 'yellow'])

        for (fx, fy, fw, fh) in faces:
            fx = max(0, min(w - 1, fx)); fy = max(0, min(h - 1, fy))
            fw = min(fw, w - fx);        fh = min(fh, h - fy)
            if fw < 12 or fh < 12:
                continue

            roi = out[fy:fy+fh, fx:fx+fw].copy()
            warped = FaceDistortionEngine._rubber_band_warp(roi, rng, intensity)
            pad = max(4, min(fw, fh) // 7)
            mask = np.zeros((fh, fw), dtype=np.float32)
            mask[pad:-pad, pad:-pad] = 1.0
            mask = cv2.GaussianBlur(mask, (pad*2+1, pad*2+1), 0)[:, :, np.newaxis]
            blend_amt = min(0.90, intensity)
            out[fy:fy+fh, fx:fx+fw] = np.clip(
                roi.astype(np.float32) * (1 - mask * blend_amt) +
                warped.astype(np.float32) * (mask * blend_amt), 0, 255
            ).astype(np.uint8)
            # No eye flare effects

        return out


# ─────────────────────────────────────────────────────────────────────────────
# 8. NON-EUCLIDEAN BACKGROUND WARP
# Detects background regions (low edge density) and applies sinusoidal
# displacement-map warping to make hallways feel infinite and ceilings wrong.
# ─────────────────────────────────────────────────────────────────────────────
class NonEuclideanWarp:
    @staticmethod
    def _background_mask(bgr_img):
        """Low-edge-density areas = background/walls/floors — computed at quarter-res for speed."""
        h, w = bgr_img.shape[:2]
        # Canny + dilate at quarter resolution (28x28 kernel → 7x7 at 1/4 scale, same effect)
        qw, qh = max(2, w // 4), max(2, h // 4)
        small  = cv2.resize(bgr_img, (qw, qh), interpolation=cv2.INTER_LINEAR)
        gray   = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        edges  = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 25, 70)
        dilated = cv2.dilate(edges, np.ones((7, 7), np.uint8))
        bg_small = np.clip(1.0 - dilated.astype(np.float32) / 255.0, 0, 1)
        bg_small = cv2.GaussianBlur(bg_small, (7, 7), 0)
        # Upsample mask back to full resolution
        return cv2.resize(bg_small, (w, h), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def apply(bgr_img, rng, intensity=0.80, t_sec=0.0):
        """
        Stretches detected background geometry via sinusoidal displacement maps:
        - Horizontal corridor stretch (hallway pulls away from viewer)
        - Radial breathing expansion (room inhales/exhales)
        - Slow vertical ceiling/floor pull
        Only applied inside the background mask, leaving subjects untouched.
        """
        if intensity < 0.05:
            return bgr_img

        h, w = bgr_img.shape[:2]
        bg = NonEuclideanWarp._background_mask(bgr_img)
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)

        x_n = X / max(w, 1)
        y_n = Y / max(h, 1)
        cx, cy = w * 0.5, h * 0.5

        # Horizontal corridor stretch (slow phase drift over time)
        ph = t_sec * 0.12 + rng.uniform(0, 0.4)
        warp_x = intensity * w * 0.048 * np.sin(y_n * np.pi * 2.1 + ph)

        # Vertical ceiling/floor pull
        pv = t_sec * 0.07
        warp_y = intensity * h * 0.032 * np.sin(x_n * np.pi * 1.6 + pv)

        # Radial breathing — room subtly expands/contracts
        dx = X - cx; dy = Y - cy
        dist = np.sqrt(dx**2 + dy**2) / max(w, h)
        breathe = intensity * 0.028 * np.sin(dist * np.pi * 1.8 + t_sec * 0.18)
        warp_x += dx * breathe
        warp_y += dy * breathe

        # Apply warp only inside background mask
        src_x = np.clip(X + warp_x * bg, 0, w-1).astype(np.float32)
        src_y = np.clip(Y + warp_y * bg, 0, h-1).astype(np.float32)
        warped = cv2.remap(bgr_img, src_x, src_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        alpha = (bg * min(0.88, intensity))[:, :, np.newaxis]
        out = bgr_img.astype(np.float32) * (1.0 - alpha) + warped.astype(np.float32) * alpha
        return np.clip(out, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
# 9. "NOCLIPPING" TEARS
# Detects flat floor/ceiling planes via horizontal edge dominance and briefly
# overrides them with pure black static — reality breaking apart.
# ─────────────────────────────────────────────────────────────────────────────
class NoclippingEffect:
    @staticmethod
    def _floor_planes(bgr_img):
        """Find candidate floor/ceiling strips: rows with dominant horizontal edges."""
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        sx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
        sy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
        horiz_dom = (sy > sx * 1.4).astype(np.float32)  # more horizontal = floor/ceiling

        planes = []
        # Search bottom 55% of frame (floor), top 20% (ceiling)
        for region_y0, region_y1 in [(int(h*0.45), h), (0, int(h*0.20))]:
            row_d = np.mean(horiz_dom[region_y0:region_y1, :], axis=1)
            in_p = False; ps = 0
            for i, d in enumerate(row_d):
                if d > 0.28 and not in_p:
                    ps = i; in_p = True
                elif d < 0.12 and in_p:
                    if i - ps > 6:
                        planes.append((region_y0 + ps, region_y0 + i))
                    in_p = False
        return planes[:3]

    @staticmethod
    def apply(bgr_img, rng, intensity=0.80):
        """Sporadic black-static tears on floor/ceiling geometry — noclip glitch."""
        if intensity < 0.05 or rng.random() > intensity * 0.12:
            return bgr_img

        h, w = bgr_img.shape[:2]
        out = bgr_img.copy()
        planes = NoclippingEffect._floor_planes(bgr_img)

        # Only fire if we genuinely detected a floor/ceiling plane — no unconditional fallback
        if not planes:
            return bgr_img

        for (y0, y1) in planes:
            if y1 <= y0:
                continue
            rh = y1 - y0
            # Black static: mostly black with very faint pixel noise
            static = np.random.randint(0, 14, (rh, w, 3), dtype=np.uint8)
            # Feather the top edge
            feather_r = max(2, rh // 5)
            for fi in range(min(feather_r, rh)):
                a = fi / feather_r
                out[y0 + fi, :] = np.clip(
                    out[y0 + fi, :].astype(np.float32) * (1 - a) + static[fi] * a, 0, 255
                ).astype(np.uint8)
            if feather_r < rh:
                out[y0 + feather_r:y1, :] = static[feather_r:, :]

# ─────────────────────────────────────────────────────────────────────────────
# 10. BACKROOMS EXPERIMENTAL AI DIFFUSION ENGINE
# Uses locally trained Stable Diffusion 1.5 + LoRA weights from
# C:\Users\rucki\Downloads\misremembered-diffusion-1.5
# ─────────────────────────────────────────────────────────────────────────────
class BackroomsDiffusionEngine:
    _pipe = None
    _is_loading = False
    _lock = threading.Lock()
    DEFAULT_MODEL_DIR = r"C:\Users\rucki\Downloads\misremembered-diffusion-1.5"

    @classmethod
    def is_available(cls):
        try:
            import torch
            import diffusers
            return True
        except Exception:
            return False

    @classmethod
    def load_pipeline(cls, model_dir=None, progress_cb=None):
        if cls._pipe is not None:
            return cls._pipe

        with cls._lock:
            if cls._pipe is not None:
                return cls._pipe
            cls._is_loading = True
            try:
                import torch
                from diffusers import StableDiffusionImg2ImgPipeline, EulerAncestralDiscreteScheduler

                target_dir = model_dir or cls.DEFAULT_MODEL_DIR
                lora_path = os.path.join(target_dir, "pytorch_lora_weights.safetensors")
                if not os.path.exists(lora_path):
                    cand = glob.glob(os.path.join(target_dir, "*.safetensors"))
                    if cand:
                        lora_path = cand[0]

                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32

                if progress_cb:
                    progress_cb("Loading base SD 1.5 pipeline...")
                dbg(f"Loading Base SD 1.5 on {device} ({dtype})...", "AI_DIFF")

                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=dtype,
                    safety_checker=None
                )
                pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

                if device == "cuda":
                    pipe = pipe.to("cuda")
                    pipe.enable_attention_slicing()

                if os.path.exists(lora_path):
                    if progress_cb:
                        progress_cb(f"Injecting LoRA: {os.path.basename(lora_path)}...")
                    dbg(f"Injecting LoRA weights from {lora_path}...", "AI_DIFF")
                    pipe.load_lora_weights(os.path.dirname(lora_path), weight_name=os.path.basename(lora_path))
                    dbg("LoRA injected successfully into UNet/TextEncoder!", "AI_DIFF")

                cls._pipe = pipe
                return cls._pipe
            except Exception as e:
                dbg(f"Failed to load diffusion pipeline: {e}", "AI_DIFF_ERROR")
                raise e
            finally:
                cls._is_loading = False

    @classmethod
    def reconstruct_frame(cls, bgr_img, strength=0.54, guidance_scale=7.5, lora_scale=0.88, steps=20, prompt=None, neg_prompt=None):
        if cls._pipe is None:
            cls.load_pipeline()

        import torch
        pipe = cls._pipe
        h, w = bgr_img.shape[:2]

        # Convert OpenCV BGR to PIL Image
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        pil_init = Image.fromarray(rgb)

        # Scale maintaining aspect ratio, capped at 768px for fast inference
        MAX_DIM = 768
        scale = min(1.0, MAX_DIM / max(w, h))
        target_w = max(64, int(round(w * scale / 64) * 64))
        target_h = max(64, int(round(h * scale / 64) * 64))
        init_sd = pil_init.resize((target_w, target_h), Image.Resampling.LANCZOS)

        p = prompt or (
            "anomalous 3D meme and room inside the complex, "
            "corrupted mutated text, duplicated instanced letters and misspelled wrong words, "
            "blurry smeared glyphs, misplaced letters trailing off, "
            "a frozen still life human figure standing in the room, "
            "physical anatomical still life sculpture with misplaced limbs and eyes, "
            "floating trees, instanced duplicated furniture placed in wrong locations, "
            "office chairs and tables severed and clipped halfway into the floor and walls, "
            "broken physical geometry, backrooms-complex style"
        )

        np_prompt = neg_prompt or (
            "perfect clean readable text, crisp typography, correctly spelled words, "
            "painted illustration, painting, brush strokes, watercolor, 2d drawing, cartoon, "
            "flat shading, smooth clay smear, white haze, overexposed, washed out colors"
        )

        with torch.inference_mode():
            try:
                res_pil = pipe(
                    prompt=p,
                    negative_prompt=np_prompt,
                    image=init_sd,
                    strength=float(strength),
                    guidance_scale=float(guidance_scale),
                    num_inference_steps=int(steps),
                    cross_attention_kwargs={"scale": float(lora_scale)}
                ).images[0]
            except Exception:
                res_pil = pipe(
                    prompt=p,
                    negative_prompt=np_prompt,
                    image=init_sd,
                    strength=float(strength),
                    guidance_scale=float(guidance_scale),
                    num_inference_steps=int(steps)
                ).images[0]

        # Resize back to exact original frame dimensions and convert to BGR
        res_full = res_pil.resize((w, h), Image.Resampling.LANCZOS)
        return cv2.cvtColor(np.array(res_full), cv2.COLOR_RGB2BGR)



# ─────────────────────────────────────────────────────────────────────────────
# 10. MASTER COMPOSITE ENGINE
# Green Light time pause + electric cracks, visual interrupts, and Forgets corruption
# ─────────────────────────────────────────────────────────────────────────────
class MisrememberedEngine:
    def __init__(self):
        self.seed = random.randint(0, 0xFFFFFFFF)
        self.use_still_life = True
        self.frozen_green_frame = None
        # ── Performance: frame-skip caches ──
        # Heavy effects are computed every N frames and reused in between.
        self._face_cache      = None   # cached face-warped result
        self._face_cache_fi   = -999
        self._env_cache       = None   # cached environment hallucination result
        self._env_cache_fi    = -999
        self._warp_cache      = None   # cached non-euclidean warp result
        self._warp_cache_fi   = -999

    def set_seed(self, seed_val):
        self.seed = seed_val

    def generate_green_light_cracks(self, w, h, progress, rng):
        """
        Kane Pixels Green Light — Realistic jagged branching glass fractures & electric veins.
        Generates realistic jagged fracture pathways originating from screen stress points
        that branch outward like broken windshield glass or lightning fissures.
        """
        crack_rng = random.Random(rng.randint(0, 0xFFFFFF))
        overlay = np.zeros((h, w, 3), dtype=np.uint8)

        # Number of main fracture trunks scaling with progress
        num_trunks = int(4 + 8 * progress)
        
        # Origin stress points around screen borders and corners
        origins = [
            (0, crack_rng.randint(int(h * 0.2), int(h * 0.8))),
            (w - 1, crack_rng.randint(int(h * 0.2), int(h * 0.8))),
            (crack_rng.randint(int(w * 0.2), int(w * 0.8)), 0),
            (crack_rng.randint(int(w * 0.2), int(w * 0.8)), h - 1),
            (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)
        ]

        def draw_jagged_branch(x0, y0, target_x, target_y, depth, cur_alpha):
            if depth <= 0 or cur_alpha < 0.05:
                return
            
            # Interpolate with high-frequency perpendicular random jitter
            dist = np.hypot(target_x - x0, target_y - y0)
            steps = max(3, int(dist / 18))
            points = [(int(x0), int(y0))]
            
            curr_x, curr_y = float(x0), float(y0)
            dx = (target_x - x0) / steps
            dy = (target_y - y0) / steps

            for s in range(1, steps + 1):
                if s == steps:
                    nx, ny = float(target_x), float(target_y)
                else:
                    jitter = (1.0 - (s / steps) * 0.3) * 16.0
                    nx = curr_x + dx + crack_rng.uniform(-jitter, jitter)
                    ny = curr_y + dy + crack_rng.uniform(-jitter, jitter)
                
                pt_curr = (int(np.clip(curr_x, 0, w - 1)), int(np.clip(curr_y, 0, h - 1)))
                pt_next = (int(np.clip(nx, 0, w - 1)), int(np.clip(ny, 0, h - 1)))
                
                # Outer green glow
                cv2.line(overlay, pt_curr, pt_next, (0, int(90 * cur_alpha), 0), 4, cv2.LINE_AA)
                # Emerald vein
                cv2.line(overlay, pt_curr, pt_next, (0, int(220 * cur_alpha), int(50 * cur_alpha)), 2, cv2.LINE_AA)
                # Pure white-yellow core crack
                cv2.line(overlay, pt_curr, pt_next, (int(160 * cur_alpha), int(255 * cur_alpha), int(200 * cur_alpha)), 1, cv2.LINE_AA)

                # Fork sub-branches
                if depth > 1 and crack_rng.random() < 0.38:
                    fork_angle = crack_rng.uniform(-0.9, 0.9)
                    fork_len = dist * crack_rng.uniform(0.25, 0.55)
                    fx = nx + np.cos(fork_angle) * fork_len
                    fy = ny + np.sin(fork_angle) * fork_len
                    draw_jagged_branch(nx, ny, fx, fy, depth - 1, cur_alpha * 0.75)

                curr_x, curr_y = nx, ny

        # Draw main fracture trunks
        for i in range(num_trunks):
            orig_x, orig_y = crack_rng.choice(origins)
            # Target random interior point
            tx = crack_rng.randint(int(w * 0.15), int(w * 0.85))
            ty = crack_rng.randint(int(h * 0.15), int(h * 0.85))
            branch_alpha = min(1.0, progress * 1.3)
            draw_jagged_branch(orig_x, orig_y, tx, ty, depth=3, cur_alpha=branch_alpha)

        # Cross-fissure micro-cracks
        if progress > 0.4:
            n_micro = int(6 + 12 * progress)
            for _ in range(n_micro):
                mx0 = crack_rng.randint(0, w - 1)
                my0 = crack_rng.randint(0, h - 1)
                mx1 = mx0 + crack_rng.randint(-80, 80)
                my1 = my0 + crack_rng.randint(-80, 80)
                draw_jagged_branch(mx0, my0, mx1, my1, depth=1, cur_alpha=progress * 0.6)

        return overlay

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
            # Sporadic 0.5s static snow burst
            if 6.8 <= cycle_time < 7.3:
                return self.render_static_screen(w, h)
            # Longer 1.8s No Signal event (12.8s - 14.6s)
            elif 12.8 <= cycle_time < 14.6:
                lang = NO_SIGNAL_LANGS[(self.seed + int(t_sec / 18.0)) % len(NO_SIGNAL_LANGS)]
                return self.render_no_signal_screen(w, h, lang)
            # Sporadic 0.6s No Video OSD
            elif 17.4 <= cycle_time < 18.0:
                return self.render_no_video_screen(w, h)

        # ── 2. THE GREEN LIGHT EVENT (Full-screen green wash + Voronoi cracked-glass mesh) ──
        if green_v > 0.10 and is_video:
            green_cycle = t_sec % 22.0
            green_start = 9.0
            green_dur = 2.4

            if green_start <= green_cycle < (green_start + green_dur):
                dt = green_cycle - green_start
                # Capture the freeze frame on first entry
                if self.frozen_green_frame is None or dt < 0.1:
                    self.frozen_green_frame = frame.copy()

                # Use frozen frame while cracks are building; revert to live on fade-out
                out_base = self.frozen_green_frame.copy() if dt < 1.3 else frame.copy()

                # Crack progress: 0→1 over first 1.3s, then 1→0 over the remaining 1.1s
                prog = (dt / 1.3) if dt < 1.3 else max(0.0, 1.0 - ((dt - 1.3) / 1.1))

                # ── Deep emerald-green screen wash (whole frame goes green) ──
                # Boost green channel, suppress red and blue — amount scales with progress
                green_strength = prog * green_v
                tinted = out_base.astype(np.float32)
                tinted[:, :, 0] = np.clip(tinted[:, :, 0] * (1.0 - green_strength * 0.75), 0, 255)   # kill blue
                tinted[:, :, 1] = np.clip(tinted[:, :, 1] * (1.0 + green_strength * 1.20), 0, 255)   # boost green
                tinted[:, :, 2] = np.clip(tinted[:, :, 2] * (1.0 - green_strength * 0.60), 0, 255)   # suppress red
                # Add solid dark-green additive wash so even dark areas go green
                tinted[:, :, 1] = np.clip(tinted[:, :, 1] + green_strength * 55.0, 0, 255)
                tinted_frame = tinted.astype(np.uint8)

                # ── Voronoi cracked-glass seam overlay ──
                cracks = self.generate_green_light_cracks(w, h, prog, rng)
                return cv2.add(tinted_frame, cracks)
            else:
                self.frozen_green_frame = None

        out = frame.copy()

        # ── 3. BACKROOMS COLOR GRADE (photo + video) ──
        if master_v > 0.08:
            out = BackroomsColorGrade.apply(out, intensity=master_v * 0.72)

        # ══════════════════════════════════════════════════════════
        # PHOTO-ONLY EFFECTS — heavy spatial operations that cause
        # visible frame-to-frame stuttering in video and are too
        # slow per-frame for reasonable export times.
        # ══════════════════════════════════════════════════════════
        # ══════════════════════════════════════════════════════════
        # PHOTO-ONLY EFFECTS — heavy DNN operations (YuNet)
        # ══════════════════════════════════════════════════════════
        if not is_video:
            # ── FACE DISTORTION + YuNet detection (photo only) ──
            if still_v > 0.05:
                out = FaceDistortionEngine.apply(out, rng, intensity=still_v * master_v)

            # ── ENVIRONMENT OBJECT HALLUCINATION (photo only) ──
            if still_v > 0.05:
                out = LocalEnvironmentHallucinator.apply_environment_hallucination(
                    out, rng, intensity=still_v * master_v * 0.90
                )

        # ══════════════════════════════════════════════════════════
        # PHOTO + VIDEO EFFECTS (Smooth & Optimized)
        # ══════════════════════════════════════════════════════════

        # ── NON-EUCLIDEAN BACKGROUND / OBJECT STRETCH ──
        # In videos, triggers as a sudden 1.2s reality-stretching anomaly event (once every 12s)
        # In photos, applies standard static displacement
        if still_v > 0.05:
            if is_video:
                warp_cycle = t_sec % 12.0
                # Anomaly surge window: 4.0s to 5.2s in each 12s loop (1.2s duration)
                if 4.0 <= warp_cycle < 5.2:
                    dt_w = (warp_cycle - 4.0) / 1.2 # 0.0 to 1.0
                    warp_env = np.sin(dt_w * np.pi) ** 1.5 # smooth bell curve envelope
                    out = NonEuclideanWarp.apply(out, rng, intensity=still_v * master_v * warp_env * 0.90, t_sec=t_sec)
            else:
                out = NonEuclideanWarp.apply(out, rng, intensity=still_v * master_v * 0.75, t_sec=0.0)

        # ── STILL LIFE ANATOMICAL RECONSTRUCTION (fast skin blob — both) ──
        if self.use_still_life and still_v > 0.05:
            out = LocalStillLifeEngine.apply_still_life_reconstruction(
                out, rng, intensity=still_v * master_v, gloss=gloss_v
            )

        # ── GENERATIONAL DIGITAL DEGRADATION (both) ──
        if master_v > 0.25:
            out = GenerationalDegradation.apply(out, rng, intensity=master_v * 0.55)

        # ── EXPERIMENTAL AI DIFFUSION ENGINE (if enabled) ──
        use_diff = sliders.get("use_diffusion", 0) == 1
        if use_diff and BackroomsDiffusionEngine.is_available():
            try:
                diff_str = sliders.get("diff_strength", 54) / 100.0
                diff_lora = sliders.get("diff_lora_scale", 85) / 100.0
                diff_guid = sliders.get("diff_guidance", 75) / 10.0
                diff_steps = sliders.get("diff_steps", 20)
                out = BackroomsDiffusionEngine.reconstruct_frame(
                    out,
                    strength=diff_str,
                    guidance_scale=diff_guid,
                    lora_scale=diff_lora,
                    steps=diff_steps
                )
            except Exception as e:
                dbg(f"Diffusion processing failed on frame: {e}", "AI_DIFF_WARN")

        # ── KANE PIXELS "FORGETS" TEXT CORRUPTOR SUITE (both) ──
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

        self.telemetry_lbl = ctk.CTkLabel(seed_box, text="RAM: -- / -- GB", font=ctk.CTkFont(family="Courier New", size=10), text_color="#00ff66", fg_color="#181a20", corner_radius=4, padx=8, pady=2)
        self.telemetry_lbl.pack(side="left", padx=8)

        self.seed_btn = ctk.CTkButton(seed_box, text="↻ RE-SEED", font=ctk.CTkFont(family="Courier New", size=11), width=90, height=28, fg_color="#181a20", hover_color="#262a36", border_width=1, border_color="#2e3444", text_color="#00ff66", command=self.re_seed)
        self.seed_btn.pack(side="left", padx=6)

        self.seed_lbl = ctk.CTkLabel(seed_box, text=f"SEED: {self.engine.seed:08X}", font=ctk.CTkFont(family="Courier New", size=11), text_color="#9ca3af")
        self.seed_lbl.pack(side="left", padx=6)

        self._update_telemetry_loop()

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
        self.tab_diffusion = self.tabs.add("AI DIFFUSION")
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

        # ── AI DIFFUSION TAB (EXPERIMENTAL SD 1.5 + LORA) ──
        diff_switch_frame = ctk.CTkFrame(self.tab_diffusion, fg_color="#181c26", corner_radius=6, border_width=1, border_color="#2b3242")
        diff_switch_frame.pack(fill="x", pady=(2, 6), padx=2)

        self.diffusion_switch = ctk.CTkSwitch(
            diff_switch_frame, text="EXPERIMENTAL AI DIFFUSION", font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            progress_color="#00ff66", button_color="#ffffff", text_color="#00ff66",
            command=self.toggle_diffusion
        )
        self.diffusion_switch.pack(side="top", anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(diff_switch_frame, text="misremembered-diffusion-1.5 LoRA model", font=ctk.CTkFont(family="Courier New", size=9), text_color="#9ca3af").pack(side="top", anchor="w", padx=10, pady=(0, 6))

        # Explicit Load Model Action Frame
        load_frame = ctk.CTkFrame(self.tab_diffusion, fg_color="#13161f", corner_radius=6, border_width=1, border_color="#1f2432")
        load_frame.pack(fill="x", pady=(0, 6), padx=2)

        self.load_model_btn = ctk.CTkButton(
            load_frame, text="⚡ LOAD MODEL INTO VRAM", font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            fg_color="#1f2430", hover_color="#2b3242", border_width=1, border_color="#00ff66", text_color="#00ff66",
            height=30, command=self.load_diffusion_model_btn_click
        )
        self.load_model_btn.pack(fill="x", padx=8, pady=(6, 4))

        self.diff_status_lbl = ctk.CTkLabel(load_frame, text="STATUS: Model not loaded in VRAM (Click above)", font=ctk.CTkFont(family="Courier New", size=9), text_color="#9ca3af")
        self.diff_status_lbl.pack(anchor="w", padx=8, pady=(0, 6))

        diff_sliders = [
            ("Diffusion Img2Img Strength", "diff_strength", 10, 90, 54, "#ff3344"),
            ("LoRA Weight Scale", "diff_lora_scale", 10, 100, 85, "#00ff66"),
            ("Guidance Scale (CFG)", "diff_guidance", 30, 150, 75, "#ff3344"),
            ("Inference Steps (EulerA)", "diff_steps", 10, 50, 20, "#00ff66"),
        ]
        for title, key, mn, mx, df, clr in diff_sliders:
            self._make_slider_group(self.tab_diffusion, title, key, mn, mx, df, clr)

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
        d = {k: int(v.get()) for k, v in self.slider_vars.items()}
        d["use_diffusion"] = 1 if (hasattr(self, 'diffusion_switch') and self.diffusion_switch.get() == 1) else 0
        return d

    def _update_telemetry_loop(self):
        try:
            total_r, avail_r, load_pct, vram_info = get_system_memory_status()
            used_r = round(total_r - avail_r, 1)
            self.telemetry_lbl.configure(text=f"RAM: {used_r}/{total_r}GB ({load_pct}%) | {vram_info}")
        except Exception:
            pass
        self.after(2000, self._update_telemetry_loop)

    def toggle_diffusion(self):
        use_diff = self.diffusion_switch.get() == 1
        if use_diff:
            if not BackroomsDiffusionEngine.is_available():
                messagebox.showwarning(
                    "PyTorch / Diffusers Required",
                    "The experimental AI Diffusion engine requires 'torch' and 'diffusers'.\n\n"
                    "Install with: pip install torch torchvision diffusers transformers accelerate safetensors"
                )
                self.diffusion_switch.deselect()
                return

            if BackroomsDiffusionEngine._pipe is None and not BackroomsDiffusionEngine._is_loading:
                self.load_diffusion_model_btn_click()
            else:
                self.add_log("AI Diffusion Engine enabled for reconstruction.", "info")
                self.refresh_preview()
        else:
            self.add_log("AI Diffusion Engine disabled. Reverting to real-time procedural engine.", "info")
            self.refresh_preview()

    def load_diffusion_model_btn_click(self):
        if not BackroomsDiffusionEngine.is_available():
            messagebox.showwarning(
                "PyTorch / Diffusers Required",
                "The experimental AI Diffusion engine requires 'torch' and 'diffusers'.\n\n"
                "Install with: pip install torch torchvision diffusers transformers accelerate safetensors"
            )
            return

        if BackroomsDiffusionEngine._is_loading:
            self.add_log("Model is already loading in the background, please wait...", "warn")
            return

        if BackroomsDiffusionEngine._pipe is not None:
            self.add_log("Model is already loaded and ready in VRAM/RAM!", "info")
            self.diff_status_lbl.configure(text="STATUS: ● Model Active & Loaded in VRAM", text_color="#00ff66")
            return

        self.load_model_btn.configure(state="disabled", text="⏳ LOADING MODEL...")
        self.diff_status_lbl.configure(text="STATUS: ⏳ Initializing PyTorch & loading LoRA...", text_color="#ffcc00")
        self.add_log("Starting on-demand load of misremembered-diffusion-1.5...", "alert")
        threading.Thread(target=self._async_load_diffusion, daemon=True).start()

    def _async_load_diffusion(self):
        try:
            BackroomsDiffusionEngine.load_pipeline(progress_cb=lambda m: self.add_log(m, "info"))
            self.add_log("AI Diffusion Pipeline Ready in VRAM/RAM!", "info")
            self.after(0, lambda: (
                self.load_model_btn.configure(state="normal", text="✓ MODEL LOADED (CLICK TO RE-CHECK)"),
                self.diff_status_lbl.configure(text="STATUS: ● Model Active & Loaded in VRAM", text_color="#00ff66"),
                self.diffusion_switch.select(),
                self.refresh_preview()
            ))
        except Exception as e:
            self.add_log(f"Diffusion load error: {e}", "warn")
            self.after(0, lambda: (
                self.load_model_btn.configure(state="normal", text="⚡ LOAD MODEL INTO VRAM"),
                self.diff_status_lbl.configure(text=f"ERROR: {e}", text_color="#ff3344"),
                self.diffusion_switch.deselect()
            ))

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
            self.processed_image_bgr = self.engine.process_frame(self.original_image_bgr, rng, sliders, frame_idx=0, fps=0)
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

            is_diffusion = (sliders.get("use_diffusion", 0) == 1) and BackroomsDiffusionEngine.is_available()

            # Dynamic FPS Target: 24 FPS when AI diffusion is on to avoid overloading GPU/VRAM, 30 FPS otherwise
            target_fps_cap = 24.0 if is_diffusion else 30.0
            fps = min(target_fps_cap, raw_fps)
            frame_step = max(1, int(round(raw_fps / fps))) if raw_fps > (target_fps_cap + 4.0) else 1
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            raw_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
            total_frames = max(1, raw_total_frames // frame_step)

            target_w, target_h = orig_w, orig_h
            max_res = 768 if is_diffusion else 1280
            if orig_w > max_res or orig_h > max_res:
                scale = float(max_res) / max(orig_w, orig_h)
                target_w = int(orig_w * scale)
                target_h = int(orig_h * scale)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(temp_video, fourcc, fps, (target_w, target_h))

            frame_idx = 0
            raw_idx = 0
            start_t = time.time()

            if is_diffusion:
                est_seconds = int(total_frames * 0.45) # ~0.45s per frame on CUDA
                self.add_log(f"AI Diffusion Video Export Enabled: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f} FPS ({total_frames} frames).", "alert")
                self.add_log(f"Notice: AI neural diffusion is running per-frame. This will take a while (Estimated: ~{est_seconds // 60}m {est_seconds % 60}s)...", "warn")
                dbg(f"AI Diffusion Video Export started: {target_w}x{target_h} @ {fps:.1f}fps, total={total_frames}, est={est_seconds}s", "EXPORT")
            else:
                self.add_log(f"Reconstruction Export: {orig_w}x{orig_h} ({raw_fps:.1f}fps) -> {target_w}x{target_h} @ {fps:.1f} FPS ({total_frames} frames)...", "alert")
                dbg(f"Video Export started: {orig_w}x{orig_h} -> {target_w}x{target_h} @ {fps:.1f}fps (step={frame_step}), total={total_frames}", "EXPORT")

            log_interval = 5 if is_diffusion else 30

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_step > 1 and (raw_idx % frame_step != 0):
                    raw_idx += 1
                    continue
                raw_idx += 1

                if orig_w != target_w or orig_h != target_h:
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

                # Identical deterministic temporal seed ensures 100% parity with preview!
                frame_rng = random.Random(seed + int(frame_idx / (fps * 2.0)))
                _orig_sl = self.engine.use_still_life
                self.engine.use_still_life = use_still_life
                out = self.engine.process_frame(frame, frame_rng, sliders, frame_idx, fps)
                self.engine.use_still_life = _orig_sl
                writer.write(out)
                frame_idx += 1

                if frame_idx % log_interval == 0 or frame_idx == total_frames:
                    prog = frame_idx / float(total_frames)
                    elapsed = time.time() - start_t
                    cur_fps = frame_idx / max(0.001, elapsed)
                    eta = int((total_frames - frame_idx) / max(0.1, cur_fps))
                    eta_str = f"{eta // 60}m {eta % 60}s" if eta >= 60 else f"{eta}s"
                    self.after(0, lambda p=prog, i=frame_idx, tot=total_frames, f=cur_fps, e=eta_str: (
                        self.progress_bar.set(p),
                        self.add_log(f"Frame {i}/{tot} ({int(p*100)}%) — {f:.2f} FPS — ETA {e}")
                    ))

            cap.release()
            writer.release()
            dbg(f"Video frame rendering complete ({total_frames} frames).", "EXPORT")

            # ── AUDIO PROCESSING WITH KANE PIXELS DSP ──
            if FFMPEG:
                self.add_log("Processing Backrooms audio DSP (tape wow, liminal reverb, fluorescent hum, ambient drone, EMG)...", "info")
                ext_cmd = [FFMPEG, "-y", "-i", in_path, "-vn", "-ac", "2", "-ar", "44100", temp_in_wav]
                subprocess.run(ext_cmd, capture_output=True, timeout=60)

                # Load EMG audio for No Signal injection — sits alongside the source video/app
                emg_candidates = [
                    os.path.join(os.path.dirname(in_path), "emg.mp3"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "emg.mp3"),
                    r"C:\Users\rucki\Downloads\Miscellaneous\Misremembered_Media\emg.mp3",
                ]
                emg_audio_f = None
                for emg_path in emg_candidates:
                    emg_audio_f = KanePixelsAudioDSP.load_emg_audio(emg_path, sr=44100, ffmpeg=FFMPEG)
                    if emg_audio_f is not None:
                        self.add_log(f"EMG audio loaded for No Signal: {os.path.basename(emg_path)}", "info")
                        break
                if emg_audio_f is None:
                    self.add_log("EMG audio not found — using procedural No Signal jingle", "warn")

                has_audio = os.path.exists(temp_in_wav) and os.path.getsize(temp_in_wav) > 1000

                if has_audio:
                    try:
                        sr, raw_audio = wavfile.read(temp_in_wav)
                        proc_audio = KanePixelsAudioDSP.process_full_audio(
                            raw_audio, sr=sr, seed=seed, sliders=sliders,
                            fps=fps, total_frames=total_frames,
                            emg_audio_f=emg_audio_f
                        )
                        wavfile.write(temp_out_wav, sr, proc_audio)
                    except Exception as e:
                        dbg(f"Audio DSP error on input audio: {e}", "ERROR")
                        has_audio = False

                if not has_audio:
                    # No source audio — synthesize a full atmospheric layer from scratch
                    sr = 44100
                    duration_s = max(1.0, total_frames / float(fps))
                    n_samples = int(sr * duration_s)
                    dbg(f"Synthesizing {duration_s:.1f}s full Backrooms atmospheric audio (no source audio)...", "AUDIO")
                    hum = KanePixelsAudioDSP.synthesize_fluorescent_hum(n_samples, sr=sr, gain=0.045)
                    ambient = KanePixelsAudioDSP.synthesize_liminal_ambient(n_samples, sr=sr, gain=0.048)
                    combined = np.clip((hum + ambient) * 32767.0, -32767.0, 32767.0).astype(np.int16)
                    wavfile.write(temp_out_wav, sr, combined)

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
