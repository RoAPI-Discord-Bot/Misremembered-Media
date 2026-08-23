/**
 * MISREMEMBERED MEDIA // Uncanny Media Reconstruction Engine
 * Media corruption, periodic reality shifts, weighted audio pitch intervals (20%/45%/35%),
 * and static image feature duplication (angled displacement SpongeBob effect).
 */

document.addEventListener('DOMContentLoaded', () => {

    console.log('%c[MISREMEMBERED MEDIA] Engine Initialization Started', 'color: #00ff66; font-weight: bold; font-size: 14px;');

    // --- DOM ELEMENT REFERENCES ---
    const dropZone = document.getElementById('dropZone');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const fileInput = document.getElementById('fileInput');
    
    const glitchCanvas = document.getElementById('glitchCanvas');
    const ctx = glitchCanvas.getContext('2d', { willReadFrequently: true });
    
    const sourceVideo = document.getElementById('sourceVideo');
    const sourceAudio = document.getElementById('sourceAudio');
    const sourceImage = document.getElementById('sourceImage');

    const audioSpectrumCanvas = document.getElementById('audioSpectrumCanvas');
    const specCtx = audioSpectrumCanvas ? audioSpectrumCanvas.getContext('2d') : null;

    const spatialRadarCanvas = document.getElementById('spatialRadarCanvas');
    const radarCtx = spatialRadarCanvas ? spatialRadarCanvas.getContext('2d') : null;

    // Controls & Displays
    const btnPlayPause = document.getElementById('btnPlayPause');
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');
    const btnMute = document.getElementById('btnMute');
    const btnSnapshotImage = document.getElementById('btnSnapshotImage');
    const btnProcessFullFile = document.getElementById('btnProcessFullFile');
    const seekSlider = document.getElementById('seekSlider');
    const currentTimeDisplay = document.getElementById('currentTime');
    const durationTimeDisplay = document.getElementById('durationTime');
    const mediaTitle = document.getElementById('mediaTitle');
    const spatialCoords = document.getElementById('spatialCoords');
    const stabilityDisplay = document.getElementById('stabilityDisplay');
    const entityStatus = document.getElementById('entityStatus');
    const logContent = document.getElementById('logContent');
    const seedDisplay = document.getElementById('seedDisplay');
    const btnRegenerateSeed = document.getElementById('btnRegenerateSeed');
    const processingTimeText = document.getElementById('processingTimeText');

    // Processing Overlay Elements
    const processingOverlay = document.getElementById('processingOverlay');
    const processingTitle = document.getElementById('processingTitle');
    const processingSubtitle = document.getElementById('processingSubtitle');
    const processingProgressBar = document.getElementById('processingProgressBar');
    const processingPercentText = document.getElementById('processingPercentText');

    // Preview Card Elements
    const previewCard = document.getElementById('previewCard');
    const previewMediaContainer = document.getElementById('previewMediaContainer');
    const btnDownloadPayload = document.getElementById('btnDownloadPayload');
    const btnClosePreview = document.getElementById('btnClosePreview');
    const previewSubtext = document.getElementById('previewSubtext');

    // Sliders
    const masterIntensitySlider = document.getElementById('masterIntensity');
    const audioDropoutsSlider = document.getElementById('audioDropouts');
    const pitchDriftSlider = document.getElementById('pitchDrift');
    const spatialTeleportSlider = document.getElementById('spatialTeleport');
    const compressionDistortSlider = document.getElementById('compressionDistort');
    const phonemeStutterSlider = document.getElementById('phonemeStutter');
    const entityWhispersSlider = document.getElementById('entityWhispers');
    const liminalReverbSlider = document.getElementById('liminalReverb');
    const audioGainBoostSlider = document.getElementById('audioGainBoost');
    const flawedMirroringSlider = document.getElementById('flawedMirroring');
    const chromaticAberrationSlider = document.getElementById('chromaticAberration');
    const pixelSliceSlider = document.getElementById('pixelSlice');

    // Value Labels
    const masterIntensityVal = document.getElementById('masterIntensityVal');
    const audioDropoutsVal = document.getElementById('audioDropoutsVal');
    const pitchDriftVal = document.getElementById('pitchDriftVal');
    const spatialTeleportVal = document.getElementById('spatialTeleportVal');
    const compressionDistortVal = document.getElementById('compressionDistortVal');
    const phonemeStutterVal = document.getElementById('phonemeStutterVal');
    const entityWhispersVal = document.getElementById('entityWhispersVal');
    const liminalReverbVal = document.getElementById('liminalReverbVal');
    const audioGainBoostVal = document.getElementById('audioGainBoostVal');
    const flawedMirroringVal = document.getElementById('flawedMirroringVal');
    const chromaticVal = document.getElementById('chromaticVal');
    const pixelSliceVal = document.getElementById('pixelSliceVal');

    // Toggles
    const toggleInvertFlash = document.getElementById('toggleInvertFlash');
    const toggleJitterUI = document.getElementById('toggleJitterUI');
    const toggleMisrememberedText = document.getElementById('toggleMisrememberedText');
    const toggleObjectMelt = document.getElementById('toggleObjectMelt');
    const toggleMemoryDegrading = document.getElementById('toggleMemoryDegrading');
    const btnSynthesizeDemo = document.getElementById('btnSynthesizeDemo');

    // Settings Drawer
    const btnToggleSettings = document.getElementById('btnToggleSettings');
    const btnCloseSettings = document.getElementById('btnCloseSettings');
    const controlPanel = document.getElementById('controlPanel');
    const drawerBackdrop = document.getElementById('drawerBackdrop');

    // Upload button (control bar only)
    const btnUploadControl = document.getElementById('btnUploadControl');

    function openSettingsDrawer() {
        console.log('[DEBUG] Opening Settings Drawer');
        if (controlPanel) controlPanel.classList.add('drawer-open');
        if (drawerBackdrop) drawerBackdrop.classList.add('open');
    }
    function closeSettingsDrawer() {
        console.log('[DEBUG] Closing Settings Drawer');
        if (controlPanel) controlPanel.classList.remove('drawer-open');
        if (drawerBackdrop) drawerBackdrop.classList.remove('open');
    }

    if (btnToggleSettings) btnToggleSettings.addEventListener('click', (e) => { e.stopPropagation(); openSettingsDrawer(); });
    if (btnCloseSettings) btnCloseSettings.addEventListener('click', (e) => { e.stopPropagation(); closeSettingsDrawer(); });
    if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeSettingsDrawer);

    // Prevent clicks inside controlPanel from propagating to backdrop and closing drawer!
    if (controlPanel) {
        controlPanel.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // --- STATE VARIABLES ---
    let mediaType = null; // 'image' | 'video' | 'audio'
    let isPlaying = false;
    let isMuted = false;
    let currentFile = null;
    let rawAudioArrayBuffer = null;

    // Web Audio Engine State
    let audioCtx = null;
    let audioSourceNode = null;
    let pannerNode = null;
    let waveShaperNode = null;
    let filterNode = null;
    let mainGainNode = null;
    let ringModOsc = null;
    let ringModGain = null;
    
    let voiceDoubleDelay = null;
    let voiceDoubleGain = null;

    let whisperBufferSource = null;
    let whisperFormant1 = null;
    let whisperFormant2 = null;
    let whisperGain = null;

    let reverbDelay1 = null;
    let reverbDelay2 = null;
    let reverbFeedback = null;
    let reverbGain = null;

    let tapeWarpLFO = null;
    let tapeWarpLFOGain = null;
    let muffleFilter = null;
    let tapeWarmthFilter = null;
    let spatialMonoUntil = 0;

    let stutterDelay = null;
    let stutterGain = null;
    let stutterFeedback = null;
    let bitCrushNode = null;

    let agcGainNode = null;
    let compressorNode = null;
    let analyserNode = null;
    let streamDestination = null;

    let isAudioBlackout = false;
    let lastBlackoutTime = 0;
    let lastStutterTime = 0;
    let lastMuffleTime = 0;
    let lastWarpBurstTime = 0;

    let mediaRecorder = null;
    let recordedChunks = [];
    let isBatchExporting = false;

    let animFrameId = null;
    let currentPitchBend = 1.0;
    let targetPitchBend = 1.0;
    let panX = 0;
    let panY = 0;
    let panAngle = 0;

    // --- PERIODIC PITCH & DISTORTION WINDOW STATE ---
    let lastPitchIntervalTime = 0;
    let currentPitchIntervalDuration = 4000;

    let lastDistortionWindowTime = 0;
    let isDistortionWindowActive = false;
    let currentWindowDuration = 3000;

    // --- REVERB WINDOW STATE (not always on) ---
    let lastReverbWindowTime = 0;
    let isReverbWindowActive = true;
    let currentReverbWindowDuration = 5000;

    // --- RANDOM LEVEL FLUCTUATION STATE ---
    let lastLevelFlucTime = 0;
    let targetLevelMult = 1.0;
    let currentLevelMult = 1.0;

    // --- MEMORY WHISPER STATE ---
    let memoryWhisperDelay = null;
    let memoryWhisperFilter1 = null;
    let memoryWhisperFilter2 = null;
    let memoryWhisperFilter3 = null;
    let memoryWhisperGain = null;
    let isWhisperActive = false;
    let lastWhisperTime = 0;

    // --- MEMORY ECHO STATE ---
    let _suppressNextVideoError = false;
    let frameHistory = [];

    // --- VISUAL INTERRUPT EVENTS (no_video / static / no_signal) ---
    let activeVisualEvent = null;  // { type: 'no_video'|'static'|'no_signal', endMs, lang }
    let noSignalMusicNodes = [];   // oscillator refs so we can stop them
    let lastFrameTimeMs = 0;       // throttle expensive pixel ops
    let mriScanStartTime = 0;      // Backrooms MRI sweep start
    let mriScanEndTime = 0;        // Backrooms MRI sweep end

    const NO_SIGNAL_LANGS = [
        'אין אות',          // Hebrew
        '신호 없음',        // Korean
        '信号なし',          // Japanese
        '无信号',            // Chinese Simplified
        'Kein Signal',      // German
        'Нет сигнала',      // Russian
        'Pas de signal',    // French
        'Sin señal',        // Spanish
        'Sem sinal',        // Portuguese
        'Geen signaal',     // Dutch
        'Ei signaalia',     // Finnish
        'لا يوجد إشارة',     // Arabic
        'Không có tín hiệu', // Vietnamese
        'Hakuna ishara',    // Swahili
        'Aucun signal',     // Belgian French
        'Senza segnale',    // Italian
        'Ingen signal',     // Swedish/Danish
        'संकेत नहीं',         // Hindi
        'Pagsignal na wala', // Filipino
        'Χωρίς σήμα',       // Greek
        'Brak sygnału',      // Polish
        'Sinyal yok',        // Turkish
        'Bez signálu',      // Czech
        'Nincs jel',        // Hungarian
        'ไม่มีสัญญาณ'       // Thai
    ];
    let lastCaptureVideoTime = -1;
    let lastVideoTimeSeen = 0;
    let replayState = null;
    let lastReplayBurstTime = -99999;
    let outroFiredForThisPlay = false;
    const FRAME_HISTORY_MAX_SECONDS = 6;
    const FRAME_CAPTURE_INTERVAL = 0.15;

    // --- TEXT & FEATURE DUPLICATION STATE ---
    let textCandidateBlocks = [];
    let lastTextScanTime = 0;
    let trackedFaces = [];
    let lastFaceScanTime = 0;

    // --- SEED & DETERMINISTIC RANDOMIZATION ---
    // mulberry32: fast, high-quality seeded PRNG
    function mulberry32(seed) {
        return function() {
            seed |= 0; seed = seed + 0x6D2B79F5 | 0;
            let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }

    let currentSeed = Math.floor(Math.random() * 0xFFFFFFFF);
    let seededRng = mulberry32(currentSeed);
    // Per-frame RNG: re-seeded each frame from currentSeed XOR frameCount
    // so the same seed always produces the same distortion sequence.
    let frameCount = 0;
    let frameRng = mulberry32(currentSeed);
    function resetFrameRng() {
        // XOR with frameCount so each frame is deterministic but unique
        frameRng = mulberry32((currentSeed ^ (frameCount * 0x9E3779B9)) >>> 0);
    }
    let distortionSchedule = []; // pre-computed event list [{time, type, ...}]
    let scheduleIndex = 0;       // consumed index during playback
    // coherence spike state
    let coherenceSpike = 0;      // 0-100% override, fades over time
    let lastCoherenceSpikeTime = 0;

    function resetSeed(newSeed) {
        currentSeed = newSeed !== undefined ? newSeed : Math.floor(Math.random() * 0xFFFFFFFF);
        seededRng = mulberry32(currentSeed);
        if (seedDisplay) seedDisplay.textContent = 'SEED: ' + currentSeed.toString(16).toUpperCase().padStart(8, '0');
        console.log('[SEED] New seed:', currentSeed.toString(16).toUpperCase());
    }

    // Pre-compute a full distortion schedule for a given duration (seconds) from current seed
    function generateDistortionSchedule(duration) {
        const rng = mulberry32(currentSeed); // fresh rng from seed — not seededRng so we don't advance it
        const events = [];
        const highSalienceTimes = []; // track pitch and blackout timestamps for minimum 1.5s spacing

        // Longer videos forget & decay faster over time (duration factor)
        const densityFactor = Math.min(2.5, 1.0 + (duration / 90.0));

        function isTooCloseToHighSalience(time, minDist = 1.5) {
            return highSalienceTimes.some(t => Math.abs(t - time) < minDist);
        }

        // Pitch events (minimum 1.5s spacing from other high-salience events)
        let t = 2;
        while (t < duration) {
            const interval = (3.5 + rng() * 3.5) / densityFactor;
            t += interval;
            if (t >= duration) break;
            if (isTooCloseToHighSalience(t, 1.5)) continue;

            const roll = seededRng();
            let rate, label;
            if (roll < 0.15) {
                // 15%: accurate (near-normal pitch)
                rate = 0.97 + (seededRng() - 0.5) * 0.06; label = 'accurate';
            } else if (roll < 0.60) {
                // 45%: extreme (much wider range than before — deeper lows, higher highs)
                rate = seededRng() < 0.5
                    ? (1.12 + seededRng() * 0.30)   // 1.12–1.42× (faster/higher)
                    : (0.18 + seededRng() * 0.30);  // 0.18–0.48× (very slow/demonic)
                label = rate > 1 ? 'tension' : 'demonic';
            } else {
                // 40%: lethargic/dragging
                rate = 0.65 + seededRng() * 0.22; label = 'lethargic';
            }
            events.push({ time: t, type: 'pitch', rate, label });
            highSalienceTimes.push(t);
        }

        // Blackout events (enforce 1.5s minimum gap from pitch events)
        t = 4;
        while (t < duration) {
            t += (6 + rng() * 8) / densityFactor;
            if (t >= duration) break;
            if (rng() < (0.30 * densityFactor)) {
                if (isTooCloseToHighSalience(t, 1.5)) continue;
                const dur = 0.8 + rng() * 2.2;
                const whisperVol = 0.45 + rng() * 0.35;
                events.push({ time: t, type: 'blackout', duration: dur, whisperVol });
                highSalienceTimes.push(t);
            }
        }

        // Reverb window toggles
        t = 0;
        let reverbOn = true;
        while (t < duration) {
            const winLen = reverbOn ? (4 + rng() * 6) : (5 + rng() * 7);
            t += winLen;
            if (t >= duration) break;
            reverbOn = !reverbOn;
            events.push({ time: t, type: 'reverb', active: reverbOn, level: 0.4 + rng() * 0.6 });
        }

        // Level fluctuation events
        t = 1;
        while (t < duration) {
            t += 2.2 + rng() * 3.5;
            if (t >= duration) break;
            if (rng() < 0.25) {
                const fluctType = Math.floor(rng() * 4);
                events.push({ time: t, type: 'level', fluctType, mult: rng() });
            }
        }

        // Coherence spikes (the % jumps to 50-70% briefly)
        t = 5;
        while (t < duration) {
            t += 8 + rng() * 15;
            if (t >= duration) break;
            if (rng() < 0.4) {
                events.push({ time: t, type: 'coherence', value: 50 + rng() * 25, duration: 2 + rng() * 4 });
            }
        }

        // Visual interrupt events: no_video, static, no_signal, complex_generated
        // Spaced every 24-42s
        t = 12;
        while (t < duration - 10) {
            t += 24 + rng() * 18;
            if (t >= duration - 5) break;
            const vRoll = rng();
            let vType;
            if (vRoll < 0.25) vType = 'no_video';
            else if (vRoll < 0.50) vType = 'static';
            else if (vRoll < 0.75) vType = 'no_signal';
            else vType = 'complex_generated';
            const vDur = (vType === 'no_signal' || vType === 'complex_generated') ? (2.5 + rng() * 2.0) : (0.8 + rng() * 1.2);
            const langIdx = Math.floor(rng() * 25);
            events.push({ time: t, type: 'visual_event', vType, duration: vDur, langIdx });
        }

        // Music substitution events: complex recurring synthesized motif replacing media audio
        t = 15;
        while (t < duration - 8) {
            t += 22 + rng() * 25;
            if (t >= duration - 5) break;
            if (rng() < 0.38) {
                events.push({ time: t, type: 'music_substitution', duration: 3.5 + rng() * 3.0 });
            }
        }

        events.sort((a, b) => a.time - b.time);
        console.log(`[SCHEDULE] Generated ${events.length} spaced events for ${duration.toFixed(1)}s from seed ${currentSeed.toString(16).toUpperCase()}`);
        return events;
    }

    // ─── PROGRESSIVE TITLE DEGRADATION ──────────────────────────────────────────
    // Corrupts mediaTitle progressively based on prog (0.0 to 1.0)
    // 0.0-0.20: correct
    // 0.20-0.45: a few wrong chars
    // 0.45-0.70: heavy lookalike replacement + mirrors
    // 0.70-0.85: mostly garbled
    // 0.85-1.00: random foreign-language noise
    const DECAY_LANGS = ['신호 없음','לא זוכר','信号なし','Pamiętam cię','Нет сигнала','لا أتذكر','Brak sygnału','Χωρίς σήμα','ไม่มีสัญญาณ','Nincs jel'];
    let lastTitleUpdateTime = 0;
    function updateDegradingTitle(baseName, prog) {
        if (!mediaTitle || !baseName) return;
        if (performance.now() - lastTitleUpdateTime < 800) return; // update ~1x/sec
        lastTitleUpdateTime = performance.now();

        const lookalikes = { 'A':'Ꭺ','B':'ᗷ','C':'ℂ','D':'ᴅ','E':'Ε','F':'Ƒ','G':'ɢ','H':'Ħ','I':'Ι','J':'ʝ','K':'Ҡ','L':'ᒐ','M':'Ϻ','N':'И','O':'Ο','P':'Ƥ','R':'Я','S':'Ƨ','T':'Ƭ','U':'Ʊ','W':'Ш','X':'Χ','Y':'Ψ','Z':'Ƶ' };
        const glitch = ['꒐','ꓸ','ⴵ','ꔦ','ʬ','ꑔ','ꓢ','ꓣ','ꓪ','ꓫ','ꑊ'];
        const base = ('MONITORING: ' + baseName.toUpperCase().replace(/\.[^/.]+$/, ''));

        if (prog < 0.20) {
            mediaTitle.textContent = base;
            return;
        }
        if (prog > 0.85) {
            // Random foreign language + pure noise
            const lang = DECAY_LANGS[Math.floor(Math.random() * DECAY_LANGS.length)];
            const noise = glitch.map(() => glitch[Math.floor(Math.random()*glitch.length)]).join('');
            mediaTitle.textContent = `${lang} ${noise}`;
            return;
        }

        // How many chars to corrupt
        const corruptChance = (prog - 0.20) / 0.65; // 0 to 1
        let result = '';
        for (const ch of base) {
            const r = Math.random();
            if (r < corruptChance * 0.6 && lookalikes[ch]) result += lookalikes[ch];
            else if (r < corruptChance * 0.15) result += glitch[Math.floor(Math.random()*glitch.length)];
            else if (r < corruptChance * 0.08) result += ch === ch.toUpperCase() ? ch.toLowerCase() : ch.toUpperCase();
            else result += ch;
        }
        // Mirror a chunk of it when prog > 0.55
        if (prog > 0.55) {
            const mid = Math.floor(result.length / 2);
            result = result.slice(0, mid) + result.slice(mid).split('').reverse().join('');
        }
        mediaTitle.textContent = result;
    }

    // Misremember a filename: the FIRST few chars stay correct, corruption RAMPS UP left-to-right
    // so the beginning is readable and the end is completely garbled — like a memory fading out
    function misrememberFilename(originalName, ext) {
        const lookalikes = {
            'A':'Ꭺ','B':'ᗷ','C':'ℂ','D':'ᴅ','E':'Ε','F':'Ƒ','G':'ɢ','H':'Ħ','I':'Ι',
            'J':'ʝ','K':'Ҡ','L':'ᒐ','M':'Ϻ','N':'И','O':'Ο','P':'Ƥ','Q':'Ɋ','R':'Я',
            'S':'Ƨ','T':'Ƭ','U':'Ʊ','V':'ᐯ','W':'Ш','X':'Χ','Y':'Ψ','Z':'Ƶ',
            '0':'০','1':'𝟏','2':'२','3':'Ɛ','4':'५','5':'Ƽ','6':'б','7':'7','8':'੪','9':'৯',
            '_':'_','-':'-',' ':' '
        };
        const glitchChars = ['꒐','ꓸ','ⴵ','ꔦ','ʬ','ꑔ','ꓢ','ꓣ','ꓤ','ꓪ','ꓫ','ꓬ','ꑊ','ꑩ'];
        const base = originalName.toUpperCase().replace(/\.[^/.]+$/, '');
        const len = base.length;

        let result = '';
        for (let i = 0; i < len; i++) {
            const ch = base[i];
            // Corruption probability ramps from ~0% at i=0 to ~95% at i=len-1
            const corruptionChance = Math.pow(i / Math.max(1, len - 1), 1.4);
            const r = Math.random();

            if (r < corruptionChance * 0.55 && lookalikes[ch]) {
                result += lookalikes[ch];
            } else if (r < corruptionChance * 0.75) {
                result += glitchChars[Math.floor(Math.random() * glitchChars.length)];
            } else if (r < corruptionChance * 0.80 && i > len * 0.6) {
                // Deep in the name: insert an extra glitch char
                result += ch + glitchChars[Math.floor(Math.random() * glitchChars.length)];
            } else {
                result += ch;
            }
        }
        // Append a misremembered tag that is also heavily corrupted
        const tag = '_' + ['MISREM3MBERED','MISЯЕMЕᗷ3ᴿED','MΙꓢᴿEᴍEᗷᴿEᴅ','ᴍIƧЯEᴍEᗷЯED'][Math.floor(Math.random() * 4)];
        return result + tag + (ext || '');
    }

    resetSeed(); // initialize seed on load

    // --- INITIALIZATION ---
    function initCanvasSize() {
        if (!glitchCanvas || !glitchCanvas.parentElement) return;
        const rect = glitchCanvas.parentElement.getBoundingClientRect();
        glitchCanvas.width = rect.width || 800;
        glitchCanvas.height = rect.height || 480;

        if (audioSpectrumCanvas) {
            audioSpectrumCanvas.width = audioSpectrumCanvas.parentElement.clientWidth || 300;
            audioSpectrumCanvas.height = 60;
        }

        if (spatialRadarCanvas) {
            spatialRadarCanvas.width = 120;
            spatialRadarCanvas.height = 80;
        }
    }

    window.addEventListener('resize', initCanvasSize);
    initCanvasSize();

    // Regenerate seed button
    if (btnRegenerateSeed) {
        btnRegenerateSeed.addEventListener('click', (e) => {
            e.stopPropagation();
            // Check if there's a manual seed input
            const seedInput = document.getElementById('seedInput');
            if (seedInput && seedInput.value.trim()) {
                const parsed = parseInt(seedInput.value.trim(), 16) || parseInt(seedInput.value.trim(), 10);
                if (!isNaN(parsed) && parsed > 0) {
                    resetSeed(parsed >>> 0);
                } else {
                    resetSeed();
                }
            } else {
                resetSeed();
            }
            if (seedInput) seedInput.value = currentSeed.toString(16).toUpperCase().padStart(8, '0');
            frameCount = 0;
            if (sourceVideo.duration) { distortionSchedule = generateDistortionSchedule(sourceVideo.duration); scheduleIndex = 0; }
            else if (sourceAudio.duration) { distortionSchedule = generateDistortionSchedule(sourceAudio.duration); scheduleIndex = 0; }
            addLog(`SEED SET: ${currentSeed.toString(16).toUpperCase().padStart(8,'0')} — schedule regenerated`, 'alert');
        });
    }

    // --- LOGGING & CONSOLE DEBUG UTILITY ---
    function addLog(msg, type = 'normal') {
        console.log(`[ENGINE LOG] (${type}): ${msg}`);
        if (!logContent) return;
        const now = new Date();
        const timestamp = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0').slice(0, 2);
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        div.textContent = `[${timestamp}] ${msg}`;
        logContent.appendChild(div);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function getSliderValue(sliderEl, fallback = 50) {
        return (sliderEl && sliderEl.value !== undefined) ? parseInt(sliderEl.value) : fallback;
    }

    // --- WEB AUDIO API ARCHITECTURE ---
    function initAudioContext() {
        if (audioCtx) return;
        
        console.log('%c[AUDIO] Initializing WebAudio API Engine', 'color: #00e5ff; font-weight: bold;');
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioCtx();

        analyserNode = audioCtx.createAnalyser();
        analyserNode.fftSize = 256;

        compressorNode = audioCtx.createDynamicsCompressor();
        compressorNode.threshold.value = -3.0;  // Brickwall ceiling at -3dB to prevent ear rape
        compressorNode.knee.value = 4.0;
        compressorNode.ratio.value = 20.0;       // Hard limiter to keep loud moments at comfortable volume
        compressorNode.attack.value = 0.003;
        compressorNode.release.value = 0.10;

        agcGainNode = audioCtx.createGain();
        agcGainNode.gain.value = getSliderValue(audioGainBoostSlider, 100) / 100;

        mainGainNode = audioCtx.createGain();
        mainGainNode.gain.value = 1.0;

        if (audioCtx.createStereoPanner) {
            pannerNode = audioCtx.createStereoPanner();
        } else {
            pannerNode = audioCtx.createPanner();
            pannerNode.panningModel = 'equalpower';
        }

        waveShaperNode = audioCtx.createWaveShaper();
        waveShaperNode.oversample = '4x';
        updateWaveShaperCurve(getSliderValue(compressionDistortSlider, 35));

        // --- EQ TOPOLOGY: Subtle warmth & presence without harsh static hiss ---
        vocalScoopFilter = audioCtx.createBiquadFilter();
        vocalScoopFilter.type = 'peaking';
        vocalScoopFilter.frequency.value = 2200;
        vocalScoopFilter.Q.value = 1.2;
        vocalScoopFilter.gain.value = -2.0;

        coldShelfFilter = audioCtx.createBiquadFilter();
        coldShelfFilter.type = 'highshelf';
        coldShelfFilter.frequency.value = 7000;
        coldShelfFilter.gain.value = 1.0;

        tapeWarmthFilter = audioCtx.createBiquadFilter();
        tapeWarmthFilter.type = 'lowpass';
        tapeWarmthFilter.frequency.value = 11500;
        tapeWarmthFilter.Q.value = 0.7;

        ringModOsc = audioCtx.createOscillator();
        ringModOsc.frequency.value = 42;
        ringModGain = audioCtx.createGain();
        ringModGain.gain.value = 0.02;  // subtle texture, zero drone
        ringModOsc.start();

        voiceDoubleDelay = audioCtx.createDelay(1.0);
        voiceDoubleDelay.delayTime.value = 0.045;
        voiceDoubleGain = audioCtx.createGain();
        voiceDoubleGain.gain.value = (getSliderValue(phonemeStutterSlider, 70) / 100) * 0.6;

        stutterDelay = audioCtx.createDelay(1.0);
        stutterDelay.delayTime.value = 0.12;
        stutterGain = audioCtx.createGain();
        stutterGain.gain.value = 0.0;
        stutterFeedback = audioCtx.createGain();
        stutterFeedback.gain.value = 0.28;  // lower feedback so stutters don't compound
        stutterDelay.connect(stutterFeedback);
        stutterFeedback.connect(stutterDelay);

        tapeWarpLFO = audioCtx.createOscillator();
        tapeWarpLFO.type = 'sine';
        tapeWarpLFO.frequency.value = 0.8 + Math.random() * 1.5;
        tapeWarpLFOGain = audioCtx.createGain();
        tapeWarpLFOGain.gain.value = 0.018;
        tapeWarpLFO.connect(tapeWarpLFOGain);
        tapeWarpLFOGain.connect(vocalScoopFilter.detune);
        tapeWarpLFO.start();

        bitCrushNode = audioCtx.createWaveShaper();
        bitCrushNode.curve = createBitCrushCurve(32);
        bitCrushNode.oversample = 'none';

        reverbDelay1 = audioCtx.createDelay(3.0);
        reverbDelay1.delayTime.value = 0.22;
        reverbDelay2 = audioCtx.createDelay(3.0);
        reverbDelay2.delayTime.value = 0.51;

        reverbFeedback = audioCtx.createGain();
        reverbFeedback.gain.value = 0.38;  // decays in ~1-2s, not infinite ring

        reverbGain = audioCtx.createGain();
        reverbGain.gain.value = 0;

        reverbDelay1.connect(reverbDelay2);
        reverbDelay2.connect(reverbFeedback);
        reverbFeedback.connect(reverbDelay1);
        reverbDelay2.connect(reverbGain);
        // Start reverb dry — it will surface periodically
        reverbGain.gain.value = 0;

        // --- MEMORY WHISPER: long delay of actual audio → heavy bandpass = ghostly whispered speech ---
        // The source audio itself is fed into a 2.5-4s delay, then squeezed through narrow bandpass
        // filters tuned to 500-3500Hz (whisper/consonant range), making it sound like someone
        // quietly whispering what was just playing — like trying to remember.
        memoryWhisperDelay = audioCtx.createDelay(5.0);
        memoryWhisperDelay.delayTime.value = 2.5 + Math.random() * 1.5;

        memoryWhisperFilter1 = audioCtx.createBiquadFilter();
        memoryWhisperFilter1.type = 'bandpass';
        memoryWhisperFilter1.frequency.value = 800;
        memoryWhisperFilter1.Q.value = 1.8;

        memoryWhisperFilter2 = audioCtx.createBiquadFilter();
        memoryWhisperFilter2.type = 'bandpass';
        memoryWhisperFilter2.frequency.value = 2200;
        memoryWhisperFilter2.Q.value = 2.5;

        memoryWhisperFilter3 = audioCtx.createBiquadFilter();
        memoryWhisperFilter3.type = 'highpass';
        memoryWhisperFilter3.frequency.value = 300;
        memoryWhisperFilter3.Q.value = 0.7;

        memoryWhisperGain = audioCtx.createGain();
        memoryWhisperGain.gain.value = 0; // starts silent, surfaces during quiet moments

        memoryWhisperDelay.connect(memoryWhisperFilter1);
        memoryWhisperFilter1.connect(memoryWhisperFilter2);
        memoryWhisperFilter2.connect(memoryWhisperFilter3);
        memoryWhisperFilter3.connect(memoryWhisperGain);
        // Whisper bypasses reverb and goes direct to panner (intimate, close-sounding)
        // Connection to pannerNode is done in setupAudioNodesForSource

        createWhisperSynthesizer();

        streamDestination = audioCtx.createMediaStreamDestination();
        preloadEmgBuffer();
        addLog('UNCANNY AUDIO ENGINE: Pitch intervals (20%/45%/35%), periodic reverb, memory whisper online.', 'normal');
    }

    function createWhisperSynthesizer() {
        const bufferSize = audioCtx.sampleRate * 2;
        const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;

        for (let i = 0; i < bufferSize; i++) {
            const white = Math.random() * 2 - 1;
            b0 = 0.99886 * b0 + white * 0.0555179;
            b1 = 0.99332 * b1 + white * 0.0750759;
            b2 = 0.96900 * b2 + white * 0.1538520;
            b3 = 0.86650 * b3 + white * 0.3104856;
            b4 = 0.55000 * b4 + white * 0.5329522;
            b5 = -0.7616 * b5 - white * 0.0168980;
            output[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
            output[i] *= 0.11;
            b6 = white * 0.115926;
        }

        whisperBufferSource = audioCtx.createBufferSource();
        whisperBufferSource.buffer = noiseBuffer;
        whisperBufferSource.loop = true;

        whisperFormant1 = audioCtx.createBiquadFilter();
        whisperFormant1.type = 'bandpass';
        whisperFormant1.frequency.value = 700;
        whisperFormant1.Q.value = 6;

        whisperFormant2 = audioCtx.createBiquadFilter();
        whisperFormant2.type = 'bandpass';
        whisperFormant2.frequency.value = 1800;
        whisperFormant2.Q.value = 8;

        whisperGain = audioCtx.createGain();
        whisperGain.gain.value = 0.0; // starts silent — sidechained strictly to blackout event windows

        whisperBufferSource.connect(whisperFormant1);
        whisperFormant1.connect(whisperFormant2);
        whisperFormant2.connect(whisperGain);

        whisperGain.connect(reverbDelay1);
        whisperGain.connect(pannerNode);

        whisperBufferSource.start();
    }

    function createDistortionCurve(amount) {
        const n_samples = 44100;
        const curve = new Float32Array(n_samples);
        // Drive ranges smoothly from 1.0 (clean) to 3.0 (warm saturation)
        const drive = 1.0 + (amount / 100) * 2.0;
        const norm = Math.tanh(drive);
        for (let i = 0; i < n_samples; ++i) {
            const x = (i * 2) / n_samples - 1;
            // Noise floor gate (|x| < 0.003) mutes quiet mic hiss / noise floor entirely
            if (Math.abs(x) < 0.003) {
                curve[i] = 0;
            } else {
                // Smooth hyperbolic tangent soft saturation — 1:1 linear for quiet audio,
                // smooth warm saturation for loud audio without digital clipping or ear rape.
                curve[i] = Math.tanh(x * drive) / norm;
            }
        }
        return curve;
    }

    function createBitCrushCurve(steps) {
        const n_samples = 4096;
        const curve = new Float32Array(n_samples);
        for (let i = 0; i < n_samples; i++) {
            const x = (i * 2) / n_samples - 1;
            curve[i] = Math.round(x * steps) / steps;
        }
        return curve;
    }

    function updateWaveShaperCurve(intensityVal) {
        if (!waveShaperNode) return;
        waveShaperNode.curve = createDistortionCurve(intensityVal);
    }

    let videoAudioSourceNode = null;
    let audioElementSourceNode = null;

    function setupAudioNodesForSource(mediaElement) {
        initAudioContext();
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        let currentSourceNode = null;

        if (mediaElement === sourceVideo) {
            if (!videoAudioSourceNode) {
                try {
                    videoAudioSourceNode = audioCtx.createMediaElementSource(sourceVideo);
                } catch (e) {
                    console.error('[AUDIO ERR] Could not create video MediaElementSource:', e);
                }
            }
            currentSourceNode = videoAudioSourceNode;
        } else if (mediaElement === sourceAudio) {
            if (!audioElementSourceNode) {
                try {
                    audioElementSourceNode = audioCtx.createMediaElementSource(sourceAudio);
                } catch (e) {
                    console.error('[AUDIO ERR] Could not create audio MediaElementSource:', e);
                }
            }
            currentSourceNode = audioElementSourceNode;
        }

        if (!currentSourceNode) return;
        audioSourceNode = currentSourceNode;

        try { audioSourceNode.disconnect(); } catch (e) {}

        audioSourceNode.connect(bitCrushNode);
        bitCrushNode.connect(waveShaperNode);
        waveShaperNode.connect(vocalScoopFilter);
        vocalScoopFilter.connect(coldShelfFilter);
        coldShelfFilter.connect(tapeWarmthFilter);
        tapeWarmthFilter.connect(mainGainNode);

        coldShelfFilter.connect(stutterDelay);
        stutterDelay.connect(stutterGain);
        stutterGain.connect(mainGainNode);

        coldShelfFilter.connect(voiceDoubleDelay);
        voiceDoubleDelay.connect(voiceDoubleGain);
        voiceDoubleGain.connect(mainGainNode);

        mainGainNode.connect(pannerNode);

        ringModOsc.connect(ringModGain);
        ringModGain.connect(vocalScoopFilter.frequency);

        coldShelfFilter.connect(reverbDelay1);
        reverbGain.connect(pannerNode);

        // Memory whisper: tap from source → long delay → bandpass filters → quiet gain → panner
        if (memoryWhisperDelay) {
            audioSourceNode.connect(memoryWhisperDelay);
            memoryWhisperGain.connect(pannerNode);
        }

        pannerNode.connect(agcGainNode);
        agcGainNode.connect(compressorNode);
        compressorNode.connect(analyserNode);

        analyserNode.connect(audioCtx.destination);
        analyserNode.connect(streamDestination);

        mediaElement.addEventListener('timeupdate', handleEndFade);
    }

    let endFadeArmed = false;
    let endFightFired = false;
    function handleEndFade() {
        const el = mediaType === 'video' ? sourceVideo : sourceAudio;
        if (!el || !el.duration || !audioCtx) return;

        const remaining = el.duration - el.currentTime;

        if (remaining < 4.0 && !endFadeArmed) {
            endFadeArmed = true;
            endFightFired = false;
            addLog('SIGNAL FADING: Reconstruction losing coherence...', 'danger');
        }

        if (endFadeArmed && remaining > 0) {
            const fadeRatio = Math.max(0, remaining / 4.0);
            if (agcGainNode && !isAudioBlackout) {
                const targetGain = (getSliderValue(audioGainBoostSlider, 150) / 100) * (0.05 + fadeRatio * 0.95);
                agcGainNode.gain.setTargetAtTime(targetGain, audioCtx.currentTime, 0.4);
            }

            if (remaining < 1.5 && !endFightFired) {
                endFightFired = true;
                if (mainGainNode) mainGainNode.gain.setValueAtTime(1.4, audioCtx.currentTime);
                if (bitCrushNode) bitCrushNode.curve = createBitCrushCurve(10);
                if (ringModGain) ringModGain.gain.setValueAtTime(0.25, audioCtx.currentTime);
                addLog('SIGNAL FAILURE: Final frequency burst before silence.', 'danger');
                setTimeout(() => {
                    if (mainGainNode) mainGainNode.gain.setValueAtTime(1.0, audioCtx.currentTime);
                    if (bitCrushNode) bitCrushNode.curve = createBitCrushCurve(48);
                    if (ringModGain) ringModGain.gain.setValueAtTime(0.06, audioCtx.currentTime);
                }, 600);
            }
        }

        if (remaining <= 0) {
            endFadeArmed = false;
            endFightFired = false;
            if (agcGainNode) agcGainNode.gain.setValueAtTime(getSliderValue(audioGainBoostSlider, 150) / 100, audioCtx.currentTime);
        }
    }

    // --- SCHEDULED PITCH & AUDIO ANOMALY SYSTEM ---
    // Consumes pre-computed distortionSchedule events so preview and export are deterministic
    // and match each other perfectly with the same seed.
    function processAudioAnomalies(now) {
        if (!isPlaying || !audioCtx) return;

        let masterVal = getSliderValue(masterIntensitySlider, 85) / 100;
        const pitchVal = getSliderValue(pitchDriftSlider, 80) / 100;
        const spatialVal = getSliderValue(spatialTeleportSlider, 80) / 100;
        const reverbSliderVal = getSliderValue(liminalReverbSlider, 85) / 100;

        // Get current media position in seconds
        const el = mediaType === 'video' ? sourceVideo : sourceAudio;
        const mediaPos = el ? el.currentTime : 0;
        const duration = el && el.duration ? el.duration : 1;

        // MEMORY DEGRADATION MODE OVERRIDE FOR AUDIO & SCHEDULE:
        if (toggleMemoryDegrading && toggleMemoryDegrading.checked) {
            const prog = mediaPos / duration;
            if (prog < 0.20) {
                masterVal = 0.0; // 100% crystal clear for first 20%
            } else {
                const degFactor = (prog - 0.20) / 0.80; // 0.0 to 1.0
                masterVal = masterVal * (degFactor * 4.0); // Ramps up to 4.0x extreme degradation
                
                // Final 15% breakdown: apply heavy bitcrushing, noise & demonic pitch drop
                if (prog > 0.85 && bitCrushNode && audioCtx) {
                    bitCrushNode.curve = createBitCrushCurve(4 + Math.floor((1.0 - prog) * 40)); // heavy crushing down to 4-bit
                    if (muffleFilter) muffleFilter.frequency.setTargetAtTime(300 + (1.0 - prog) * 4000, audioCtx.currentTime, 0.1);
                    if (ringModGain) ringModGain.gain.setTargetAtTime(0.40, audioCtx.currentTime, 0.1);
                }
            }
        }

        // Consume all scheduled events that have arrived by now
        while (scheduleIndex < distortionSchedule.length && distortionSchedule[scheduleIndex].time <= mediaPos) {
            const ev = distortionSchedule[scheduleIndex];
            scheduleIndex++;

            if (masterVal <= 0.01) continue; // Skip audio events during clean start

            if (ev.type === 'pitch') {
                targetPitchBend = 1.0 + (ev.rate - 1.0) * pitchVal * masterVal;
                // INSTANT PITCH SNAP: set current pitch directly
                currentPitchBend = targetPitchBend;
                if (sourceVideo && mediaType === 'video') sourceVideo.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend));
                else if (sourceAudio && mediaType === 'audio') sourceAudio.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend));

                const labels = { accurate: 'normal', tension: 'alert', demonic: 'danger', lethargic: 'alert' };
                addLog(`PITCH SNAP [${ev.label}]: ${ev.rate.toFixed(2)}x`, labels[ev.label] || 'alert');
            }

            else if (ev.type === 'blackout') {
                if (!isAudioBlackout) {
                    isAudioBlackout = true;
                    if (mainGainNode) mainGainNode.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.12);
                    if (entityStatus) entityStatus.textContent = 'SIGNAL LOST';
                    addLog('SIGNAL DROPOUT: Dead silence — memory surfacing...', 'danger');
                    
                    // ANOMALY ARBITRATION: duck secondary ambient oscillators during blackout
                    if (ringModGain) ringModGain.gain.setTargetAtTime(0.02, audioCtx.currentTime, 0.1);
                    if (tapeWarpLFOGain) tapeWarpLFOGain.gain.setTargetAtTime(0.002, audioCtx.currentTime, 0.1);

                    // SIDECHAIN WHISPER: swell whisper synth & memory whisper ONLY during blackout
                    if (whisperGain) {
                        const targetWVol = (getSliderValue(entityWhispersSlider, 80) / 100) * 0.55;
                        whisperGain.gain.setTargetAtTime(targetWVol, audioCtx.currentTime, 0.3);
                    }

                    if (memoryWhisperGain && !isWhisperActive) {
                        isWhisperActive = true;
                        memoryWhisperGain.gain.setTargetAtTime(ev.whisperVol, audioCtx.currentTime, 0.4);
                        if (memoryWhisperDelay) memoryWhisperDelay.delayTime.setValueAtTime(2.0 + seededRng() * 2.0, audioCtx.currentTime);
                        if (memoryWhisperFilter1) memoryWhisperFilter1.frequency.setTargetAtTime(600 + seededRng() * 600, audioCtx.currentTime, 0.8);
                        if (memoryWhisperFilter2) memoryWhisperFilter2.frequency.setTargetAtTime(1800 + seededRng() * 800, audioCtx.currentTime, 0.8);
                    }

                    setTimeout(() => {
                        isAudioBlackout = false;
                        isWhisperActive = false;
                        if (mainGainNode) mainGainNode.gain.setTargetAtTime(currentLevelMult, audioCtx.currentTime, 0.25);
                        if (memoryWhisperGain) memoryWhisperGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.6);
                        if (whisperGain) whisperGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.6);
                        if (ringModGain) ringModGain.gain.setTargetAtTime(0.02, audioCtx.currentTime, 0.4);
                        if (tapeWarpLFOGain) tapeWarpLFOGain.gain.setTargetAtTime(0.003, audioCtx.currentTime, 0.4);
                        if (entityStatus) entityStatus.textContent = 'UNCANNY RECONSTRUCTION';
                        addLog('SIGNAL RECOVERY: Transmission re-engaged', 'alert');
                    }, ev.duration * 1000);
                }
            }

            else if (ev.type === 'reverb') {
                if (ev.active) {
                    if (reverbGain) reverbGain.gain.setTargetAtTime(reverbSliderVal * ev.level * 0.5, audioCtx.currentTime, 0.8);
                } else {
                    if (reverbGain) reverbGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 1.2);
                }
            }

            else if (ev.type === 'level') {
                const fluctTypes = [
                    () => { targetLevelMult = 1.1 + ev.mult * 0.2; setTimeout(() => { targetLevelMult = 0.6 + ev.mult * 0.3; }, 300); setTimeout(() => { targetLevelMult = 0.9 + ev.mult * 0.2; }, 900); },
                    () => { targetLevelMult = 0.3 + ev.mult * 0.3; setTimeout(() => { targetLevelMult = 0.9 + ev.mult * 0.2; }, 1200); },
                    () => { targetLevelMult = 0.0; setTimeout(() => { targetLevelMult = 1.0 + ev.mult * 0.2; }, 200 + ev.mult * 300); },
                    () => { targetLevelMult = 1.1 + ev.mult * 0.2; setTimeout(() => { targetLevelMult = 0.8 + ev.mult * 0.2; }, 800); }
                ];
                (fluctTypes[ev.fluctType] || fluctTypes[0])();
            }

            else if (ev.type === 'coherence') {
                coherenceSpike = ev.value;
                lastCoherenceSpikeTime = now;
                addLog(`COHERENCE SURGE: ${ev.value.toFixed(0)}% — signal stabilizing briefly`, 'alert');
                setTimeout(() => { coherenceSpike = 0; }, ev.duration * 1000);
            }

            else if (ev.type === 'music_substitution') {
                triggerMusicSubstitutionEvent(ev.duration);
            }

            else if (ev.type === 'visual_event') {
                triggerVisualInterruptEvent(ev.vType, ev.duration, ev.langIdx);
            }
        }

        // Smooth level multiplier
        if (!isAudioBlackout) {
            currentLevelMult += (targetLevelMult - currentLevelMult) * 0.06;
            if (mainGainNode) mainGainNode.gain.setTargetAtTime(currentLevelMult, audioCtx.currentTime, 0.05);
        }

        // Keep playbackRate synced to target pitch snap
        if (sourceVideo && mediaType === 'video' && sourceVideo.playbackRate !== Math.max(0.25, Math.min(2.2, currentPitchBend))) {
            sourceVideo.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend));
        } else if (sourceAudio && mediaType === 'audio' && sourceAudio.playbackRate !== Math.max(0.25, Math.min(2.2, currentPitchBend))) {
            sourceAudio.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend));
        }

        // Formant drift on noise whisper synth
        if (whisperFormant1 && Math.random() < 0.08) {
            const vowelF1 = [270, 390, 530, 660, 730][Math.floor(Math.random() * 5)];
            const vowelF2 = [2290, 1990, 1840, 1720, 1090][Math.floor(Math.random() * 5)];
            whisperFormant1.frequency.setTargetAtTime(vowelF1 + Math.random() * 200, audioCtx.currentTime, 0.3);
            whisperFormant2.frequency.setTargetAtTime(vowelF2 + Math.random() * 300, audioCtx.currentTime, 0.3);
        }

        // Tape Warble Burst
        if (tapeWarpLFO && (now - lastWarpBurstTime > 3000) && Math.random() < 0.04 * masterVal) {
            lastWarpBurstTime = now;
            tapeWarpLFO.frequency.setValueAtTime(2 + Math.random() * 8, audioCtx.currentTime);
            tapeWarpLFOGain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            setTimeout(() => {
                if (tapeWarpLFO) tapeWarpLFO.frequency.setTargetAtTime(0.8 + Math.random() * 1.5, audioCtx.currentTime, 0.5);
                if (tapeWarpLFOGain) tapeWarpLFOGain.gain.setTargetAtTime(0.018, audioCtx.currentTime, 0.5);
            }, 400 + Math.random() * 600);
        }

        // Phoneme Stutter
        const stutterVal = getSliderValue(phonemeStutterSlider, 70) / 100;
        if (stutterDelay && (now - lastStutterTime > 2500) && Math.random() < 0.05 * stutterVal * masterVal) {
            lastStutterTime = now;
            stutterDelay.delayTime.setValueAtTime([80,120,180,250][Math.floor(Math.random()*4)] / 1000, audioCtx.currentTime);
            stutterGain.gain.setValueAtTime(0.7, audioCtx.currentTime);
            stutterFeedback.gain.setValueAtTime(0.6 + Math.random() * 0.2, audioCtx.currentTime);
            setTimeout(() => { if (stutterGain) stutterGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.1); }, 300 + Math.random() * 700);
        }

        // ── CONTINUOUS AUDIO DEGRADATION: new per-frame effects beyond pitch ──────
        // These happen every frame based on masterVal — not just on scheduled events.

        // 1. FILTER SWEEP: muffle filter slowly closes down as distortion increases
        if (tapeWarmthFilter && audioCtx && masterVal > 0.15) {
            const sweepFreq = 12000 - masterVal * 9000 * (0.5 + 0.5 * Math.sin(now * 0.001));
            tapeWarmthFilter.frequency.setTargetAtTime(Math.max(400, sweepFreq), audioCtx.currentTime, 0.3);
        }

        // 2. DISTORTION RAMPING: waveshaper drive increases with masterVal
        if (masterVal > 0.3 && Math.random() < 0.015 * masterVal) {
            const distAmount = 20 + masterVal * 120;
            if (waveShaperNode) waveShaperNode.curve = createDistortionCurve(distAmount);
            setTimeout(() => { if (waveShaperNode) updateWaveShaperCurve(getSliderValue(compressionDistortSlider, 35)); }, 400 + Math.random() * 600);
        }

        // 3. CRACKLE / NOISE BURST: inject a brief pop/crackle into the gain chain
        if (audioCtx && mainGainNode && masterVal > 0.2 && Math.random() < 0.012 * masterVal) {
            const crackleGain = audioCtx.createGain();
            crackleGain.gain.setValueAtTime(0.3 + masterVal * 0.5, audioCtx.currentTime);
            crackleGain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.06);
            const noiseLen = Math.floor(audioCtx.sampleRate * 0.06);
            const noiseBuf = audioCtx.createBuffer(1, noiseLen, audioCtx.sampleRate);
            const nd = noiseBuf.getChannelData(0);
            for (let i = 0; i < noiseLen; i++) nd[i] = (Math.random() * 2 - 1);
            const noiseSrc = audioCtx.createBufferSource();
            noiseSrc.buffer = noiseBuf;
            noiseSrc.connect(crackleGain);
            crackleGain.connect(pannerNode || audioCtx.destination);
            noiseSrc.start();
        }

        // 4. RING MOD SWELL: ring mod frequency wobbles erratically at high distortion
        if (ringModOsc && ringModGain && masterVal > 0.4) {
            const wobble = 20 + masterVal * 180 + Math.sin(now * 0.003) * 60;
            ringModOsc.frequency.setTargetAtTime(wobble, audioCtx.currentTime, 0.2);
            ringModGain.gain.setTargetAtTime(0.02 + masterVal * 0.18, audioCtx.currentTime, 0.2);
        }

        // 5. SPEED WOBBLE: rapid micro-stutters in playback rate (separate from pitch events)
        const wobbleEl = mediaType === 'video' ? sourceVideo : sourceAudio;
        if (wobbleEl && masterVal > 0.5 && Math.random() < 0.018 * masterVal) {
            const wobbleRate = currentPitchBend * (0.75 + Math.random() * 0.55);
            wobbleEl.playbackRate = Math.max(0.1, Math.min(2.8, wobbleRate));
            setTimeout(() => { if (wobbleEl) wobbleEl.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend)); }, 80 + Math.random() * 160);
        }

        // 3D Spatial Rotation
        panAngle += 0.04 * (1 + spatialVal * 2.5);
        if (pannerNode) {
            let pX = Math.cos(panAngle) * spatialVal;
            if (Math.random() < 0.04 * spatialVal) pX = (Math.random() > 0.5 ? 1 : -1) * (0.6 + Math.random() * 0.4);
            panX = pX;
            panY = Math.sin(panAngle * 1.5) * spatialVal;
            if (pannerNode.pan) pannerNode.pan.setValueAtTime(panX, audioCtx.currentTime);
            else if (pannerNode.setPosition) pannerNode.setPosition(panX * 3, 0, panY * 3);
            if (spatialCoords) spatialCoords.textContent = `PAN X: ${panX.toFixed(2)} | PAN Y: ${panY.toFixed(2)}`;
        }

        // Update UI Stability (coherence spike takes priority)
        if (stabilityDisplay && Math.random() < 0.2) {
            let stab;
            if (coherenceSpike > 0) {
                stab = coherenceSpike.toFixed(1);
                stabilityDisplay.textContent = `${stab}% [SURGE]`;
            } else {
                stab = Math.max(1, 100 - (masterVal * 85 + Math.random() * 15)).toFixed(1);
                stabilityDisplay.textContent = `${stab}% [${parseFloat(stab) < 20 ? 'CRITICAL' : 'DECAY'}]`;
            }
        }
    }

    let _lastEntityDecayTime = 0;  // tracks periodic in-playback decay
    const ENTITY_DECAY_INTERVAL_MS = 12000; // fire a decay cycle every ~12 seconds during playback

    // --- MEMORY ECHO REPLAY ---
    function captureFrameSnapshot() {
        if (mediaType !== 'video' || sourceVideo.readyState < 2) return;
        const vt = sourceVideo.currentTime;
        const nowMs = performance.now();

        if (vt < lastVideoTimeSeen - 0.5) {
            // Video looped — full decay cycle + rescan with fresh frame data
            frameHistory = [];
            outroFiredForThisPlay = false;
            lastCaptureVideoTime = -1;
            triggerEntityDecayCycle();
            _lastEntityDecayTime = nowMs;
        } else if (nowMs - _lastEntityDecayTime > ENTITY_DECAY_INTERVAL_MS && memoryEntities.length > 0) {
            // Periodic in-playback decay: mutate 1-2 entities roughly every 12s
            triggerEntityDecayCycle();
            _lastEntityDecayTime = nowMs;
        }
        lastVideoTimeSeen = vt;

        if (lastCaptureVideoTime >= 0 && Math.abs(vt - lastCaptureVideoTime) < FRAME_CAPTURE_INTERVAL) return;
        lastCaptureVideoTime = vt;

        try {
            const sw = Math.max(64, Math.floor(glitchCanvas.width / 2));
            const sh = Math.max(36, Math.floor(glitchCanvas.height / 2));
            const snapCanvas = document.createElement('canvas');
            snapCanvas.width = sw;
            snapCanvas.height = sh;
            const sctx = snapCanvas.getContext('2d');
            sctx.drawImage(sourceVideo, 0, 0, sw, sh);
            frameHistory.push({ t: vt, canvas: snapCanvas });
            while (frameHistory.length && (vt - frameHistory[0].t) > FRAME_HISTORY_MAX_SECONDS) {
                frameHistory.shift();
            }
        } catch (e) {}
    }

    function startReplay(now, isOutro) {
        if (frameHistory.length < 3) return;
        const mode = isOutro ? 'reverse' : (Math.random() < 0.5 ? 'reverse' : 'forward');
        replayState = {
            startPerf: now,
            duration: 850 + Math.random() * 300,
            mode,
            isOutro,
            frames: frameHistory.slice(-Math.min(frameHistory.length, 24))
        };
    }

    function maybeTriggerReplayBurst(now) {
        if (mediaType !== 'video' || !isPlaying || replayState) return;
        if (!sourceVideo.duration || isNaN(sourceVideo.duration)) return;
        const remaining = sourceVideo.duration - sourceVideo.currentTime;

        if (remaining <= 1.2 && remaining > 0.1 && !outroFiredForThisPlay) {
            outroFiredForThisPlay = true;
            startReplay(now, true);
            return;
        }

        if (now - lastReplayBurstTime > 20000 && Math.random() < 0.005) {
            lastReplayBurstTime = now;
            startReplay(now, false);
        }
    }

    function drawReplayFrame(w, h, now) {
        if (!replayState || !replayState.frames.length) return;
        const elapsed = now - replayState.startPerf;
        const progress = Math.min(1, elapsed / replayState.duration);
        const frames = replayState.frames;

        let idx = replayState.mode === 'reverse'
            ? Math.floor((1 - progress) * (frames.length - 1))
            : Math.floor(progress * (frames.length - 1));
        idx = Math.max(0, Math.min(frames.length - 1, idx));
        const snap = frames[idx].canvas;

        ctx.save();
        ctx.translate(w, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(snap, 0, 0, w, h);
        ctx.restore();

        if (elapsed >= replayState.duration) {
            replayState = null;
        }
    }

    // --- ENHANCED FEATURE & FACE/TEXT REGION DETECTION ---
    function scanForTextCandidates(w, h) {
        console.log(`[DEBUG SCAN] Scanning for high-contrast feature/face/text candidate regions (${w}x${h})`);
        
        // Multi-scale grid blocks to detect both fine details (eyes, text) and larger regions (faces, logos)
        const blockSizes = [
            { w: 24, h: 20 },
            { w: 36, h: 30 }
        ];
        
        const candidates = [];
        try {
            const imgData = ctx.getImageData(0, 0, w, h);
            const data = imgData.data;
            const lum = (idx) => 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];

            for (const bs of blockSizes) {
                for (let by = 0; by < h - bs.h; by += bs.h) {
                    for (let bx = 0; bx < w - bs.w; bx += bs.w) {
                        const p1 = (by * w + bx) * 4;
                        const p2 = (by * w + (bx + bs.w - 1)) * 4;
                        const p3 = ((by + bs.h - 1) * w + bx) * 4;
                        const p4 = ((by + bs.h - 1) * w + (bx + bs.w - 1)) * 4;
                        const pc = ((by + (bs.h >> 1)) * w + (bx + (bs.w >> 1))) * 4;

                        const lums = [lum(p1), lum(p2), lum(p3), lum(p4), lum(pc)];
                        const mn = Math.min(...lums), mx = Math.max(...lums);

                        // Lower threshold (28) to aggressively catch white-on-black meme text, high-contrast logos
                        if (mx - mn > 28) {
                            candidates.push({ x: bx, y: by, w: bs.w, h: bs.h, contrast: mx - mn });
                        }
                    }
                }
            }
        } catch (e) {
            console.error('[DEBUG SCAN ERROR]', e);
        }

        // Sort by contrast (highest = text, logos, eyes)
        candidates.sort((a, b) => b.contrast - a.contrast);
        // Keep top 120 — more coverage means more regions for text/faces
        if (candidates.length > 120) candidates.length = 120;
        textCandidateBlocks = candidates;
    }

    // =========================================================================
    // PERSON & FACIAL LANDMARK DETECTION ENGINE (Pure Canvas / 100% Compatible)
    // Detects human subjects and extracts precise landmarks: Eyes, Nose, Mouth, Cheeks
    // =========================================================================
    function detectPersonFaces(w, h) {
        if (w < 40 || h < 40) return [];
        try {
            const step = Math.max(3, Math.floor(Math.min(w, h) / 130));
            const imgData = ctx.getImageData(0, 0, w, h);
            const data = imgData.data;

            const gridW = Math.floor(w / step);
            const gridH = Math.floor(h / step);
            const skinGrid = new Uint8Array(gridW * gridH);

            let skinPixelCount = 0;
            for (let gy = 0; gy < gridH; gy++) {
                const py = gy * step;
                for (let gx = 0; gx < gridW; gx++) {
                    const px = gx * step;
                    const idx = (py * w + px) * 4;
                    const r = data[idx];
                    const g = data[idx + 1];
                    const b = data[idx + 2];

                    // Combined RGB + YCbCr human skin tone classification across skin tones
                    const max = Math.max(r, g, b);
                    const min = Math.min(r, g, b);
                    const isRgbSkin = (r > 42) && (g > 25) && (b > 15) &&
                                      (max - min > 10) && (r > g) && (r > b) &&
                                      (Math.abs(r - g) > 8);

                    const cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b;
                    const cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b;
                    const isYcbcrSkin = (cb >= 70 && cb <= 140) && (cr >= 125 && cr <= 185);

                    if (isRgbSkin || isYcbcrSkin) {
                        skinGrid[gy * gridW + gx] = 1;
                        skinPixelCount++;
                    }
                }
            }

            if (skinPixelCount < 30) return [];

            // Flood-fill connected skin regions to isolate face/head clusters
            const clusters = [];
            const visited = new Uint8Array(gridW * gridH);

            for (let gy = 0; gy < gridH; gy++) {
                for (let gx = 0; gx < gridW; gx++) {
                    const gIdx = gy * gridW + gx;
                    if (skinGrid[gIdx] === 1 && visited[gIdx] === 0) {
                        let cMinX = gx, cMaxX = gx;
                        let cMinY = gy, cMaxY = gy;
                        let count = 0;
                        const queue = [gx, gy];
                        visited[gIdx] = 1;

                        let head = 0;
                        while (head < queue.length) {
                            const curX = queue[head++];
                            const curY = queue[head++];
                            count++;

                            if (curX < cMinX) cMinX = curX;
                            if (curX > cMaxX) cMaxX = curX;
                            if (curY < cMinY) cMinY = curY;
                            if (curY > cMaxY) cMaxY = curY;

                            const neighbors = [
                                [curX + 1, curY], [curX - 1, curY],
                                [curX, curY + 1], [curX, curY - 1]
                            ];
                            for (const [nx, ny] of neighbors) {
                                if (nx >= 0 && nx < gridW && ny >= 0 && ny < gridH) {
                                    const nIdx = ny * gridW + nx;
                                    if (skinGrid[nIdx] === 1 && visited[nIdx] === 0) {
                                        visited[nIdx] = 1;
                                        queue.push(nx, ny);
                                    }
                                }
                            }
                        }

                        const boxW = (cMaxX - cMinX + 1) * step;
                        const boxH = (cMaxY - cMinY + 1) * step;
                        const boxX = cMinX * step;
                        const boxY = cMinY * step;
                        const aspect = boxH / Math.max(1, boxW);

                        // Match face proportions: roughly 0.65 to 2.2 aspect ratio, minimum dimension 45px
                        if (count >= 35 && boxW >= 45 && boxH >= 45 && aspect >= 0.65 && aspect <= 2.2) {
                            clusters.push({
                                x: boxX,
                                y: boxY,
                                w: boxW,
                                h: boxH,
                                count
                            });
                        }
                    }
                }
            }

            clusters.sort((a, b) => b.count - a.count);
            const faces = [];

            for (const c of clusters.slice(0, 3)) {
                const fx = c.x;
                const fy = c.y;
                const fw = c.w;
                const fh = c.h;

                // Calibrate facial landmark bounding boxes relative to head geometry
                const eyesRegion = {
                    left:  { x: Math.round(fx + fw * 0.18), y: Math.round(fy + fh * 0.26), w: Math.round(fw * 0.28), h: Math.round(fh * 0.20) },
                    right: { x: Math.round(fx + fw * 0.54), y: Math.round(fy + fh * 0.26), w: Math.round(fw * 0.28), h: Math.round(fh * 0.20) }
                };

                const noseRegion = {
                    x: Math.round(fx + fw * 0.28),
                    y: Math.round(fy + fh * 0.42),
                    w: Math.round(fw * 0.44),
                    h: Math.round(fh * 0.26)
                };

                const mouthRegion = {
                    x: Math.round(fx + fw * 0.22),
                    y: Math.round(fy + fh * 0.65),
                    w: Math.round(fw * 0.56),
                    h: Math.round(fh * 0.22)
                };

                const leftCheek = {
                    x: Math.round(fx + fw * 0.04),
                    y: Math.round(fy + fh * 0.40),
                    w: Math.round(fw * 0.32),
                    h: Math.round(fh * 0.38)
                };

                const rightCheek = {
                    x: Math.round(fx + fw * 0.64),
                    y: Math.round(fy + fh * 0.40),
                    w: Math.round(fw * 0.32),
                    h: Math.round(fh * 0.38)
                };

                faces.push({
                    x: fx, y: fy, w: fw, h: fh,
                    eyes: eyesRegion,
                    nose: noseRegion,
                    mouth: mouthRegion,
                    leftCheek,
                    rightCheek
                });
            }

            return faces;
        } catch (e) {
            console.warn('[FACE SCAN ERROR]', e);
            return [];
        }
    }

    // =========================================================================
    // BILINEAR SAMPLER FOR PHOTOSHOP-GRADE SMOOTH LIQUIFY WARP
    // =========================================================================
    function sampleBilinear(data, w, h, x, y) {
        const x0 = Math.floor(x);
        const y0 = Math.floor(y);
        const x1 = Math.min(w - 1, x0 + 1);
        const y1 = Math.min(h - 1, y0 + 1);
        const fx = x - x0;
        const fy = y - y0;

        const cx0 = Math.max(0, Math.min(w - 1, x0));
        const cy0 = Math.max(0, Math.min(h - 1, y0));

        const i00 = (cy0 * w + cx0) * 4;
        const i10 = (cy0 * w + x1) * 4;
        const i01 = (y1 * w + cx0) * 4;
        const i11 = (y1 * w + x1) * 4;

        const w00 = (1 - fx) * (1 - fy);
        const w10 = fx * (1 - fy);
        const w01 = (1 - fx) * fy;
        const w11 = fx * fy;

        return [
            data[i00] * w00 + data[i10] * w10 + data[i01] * w01 + data[i11] * w11,
            data[i00 + 1] * w00 + data[i10 + 1] * w10 + data[i01 + 1] * w01 + data[i11 + 1] * w11,
            data[i00 + 2] * w00 + data[i10 + 2] * w10 + data[i01 + 2] * w01 + data[i11 + 2] * w11,
            data[i00 + 3] * w00 + data[i10 + 3] * w10 + data[i01 + 3] * w01 + data[i11 + 3] * w11
        ];
    }

    // =========================================================================
    // UNCANNY FACIAL MISREMEMBERING MORPH (Photoshop Liquify Forward Smudge)
    // Seamlessly pulls/smudges the nose, nostril cavity, and upper lip horizontally
    // across the cheek with continuous bilinear skin interpolation (Kane Pixels effect)
    // =========================================================================
    // =========================================================================
    // UNCANNY FACIAL MISREMEMBERING — CASCADE NOSE STAMP + EYE SHIFT
    // Exactly replicates the reference image:
    //   - The nose is duplicated 3-4 times cascading diagonally downward, each
    //     copy slightly overlapping the previous, with soft radial feathering
    //   - One eye is subtly lifted upward and blended back in
    //   - Everything else stays completely untouched / photographic
    // =========================================================================
    function applyUncannyFaceMorph(face, w, h, intensity, now) {
        if (!face) return;
        try {
            const fw = face.w;
            const fh = face.h;
            const nose = face.nose;

            // ── PASS 1: Cascading Nose Duplication ──────────────────────────
            // Extract a region around the nose (wider than the nose landmark alone)
            const noseRegX = Math.max(0, nose.x - Math.round(nose.w * 0.25));
            const noseRegY = Math.max(0, nose.y - Math.round(nose.h * 0.15));
            const noseRegW = Math.min(w - noseRegX, Math.round(nose.w * 1.5));
            const noseRegH = Math.min(h - noseRegY, Math.round(nose.h * 1.4));

            if (noseRegW > 10 && noseRegH > 10) {
                // Build an offscreen canvas with the nose pixel data + soft radial edge mask
                const noseCanvas = document.createElement('canvas');
                noseCanvas.width  = noseRegW;
                noseCanvas.height = noseRegH;
                const nCtx = noseCanvas.getContext('2d');

                // Draw the exact nose pixels onto the offscreen canvas
                nCtx.drawImage(glitchCanvas, noseRegX, noseRegY, noseRegW, noseRegH, 0, 0, noseRegW, noseRegH);

                // Soft radial gradient mask so copies blend seamlessly (no hard box edges)
                nCtx.globalCompositeOperation = 'destination-in';
                const grad = nCtx.createRadialGradient(
                    noseRegW * 0.5, noseRegH * 0.5, Math.min(noseRegW, noseRegH) * 0.08,
                    noseRegW * 0.5, noseRegH * 0.5, Math.min(noseRegW, noseRegH) * 0.58
                );
                grad.addColorStop(0,   'rgba(0,0,0,1)');
                grad.addColorStop(0.5, 'rgba(0,0,0,0.92)');
                grad.addColorStop(1,   'rgba(0,0,0,0)');
                nCtx.fillStyle = grad;
                nCtx.fillRect(0, 0, noseRegW, noseRegH);

                // Determine diagonal direction: angled slightly toward lower-cheek/jaw
                // The angle in the reference is roughly 10-18° below horizontal
                const stepX = Math.round(noseRegW * 0.18);   // rightward per step
                const stepY = Math.round(noseRegH * 0.72);   // downward per step (dominant)
                const angle  = -0.18; // subtle CCW tilt so copies look naturally diagonal

                const numCopies = 4; // 4 copies creates 3 overlapping steps below the original

                for (let i = 1; i <= numCopies; i++) {
                    const destX = noseRegX + stepX * i;
                    const destY = noseRegY + stepY * i;
                    // First copy is most opaque, fades out toward the bottom
                    const alpha = Math.max(0.10, 0.82 - i * 0.16);

                    // Clip stamp to canvas bounds
                    if (destX + noseRegW < 0 || destX > w) continue;
                    if (destY + noseRegH < 0 || destY > h) continue;

                    ctx.save();
                    ctx.globalAlpha = alpha;
                    ctx.translate(destX + noseRegW * 0.5, destY + noseRegH * 0.5);
                    ctx.rotate(angle * i * 0.4);  // small cumulative tilt per step
                    ctx.drawImage(noseCanvas, -noseRegW * 0.5, -noseRegH * 0.5);
                    ctx.restore();
                }
            }

            // ── PASS 2: Asymmetric Eye Lift ──────────────────────────────────
            // Pick the eye that's closer to the camera / more visible (larger region)
            const eyes = face.eyes;
            const leftArea  = eyes.left.w  * eyes.left.h;
            const rightArea = eyes.right.w * eyes.right.h;
            const targetEye = leftArea >= rightArea ? eyes.left : eyes.right;

            const ex = Math.max(0, targetEye.x - Math.round(targetEye.w * 0.2));
            const ey = Math.max(0, targetEye.y - Math.round(targetEye.h * 0.2));
            const ew = Math.min(w - ex, Math.round(targetEye.w * 1.4));
            const eh = Math.min(h - ey, Math.round(targetEye.h * 1.4));

            if (ew > 8 && eh > 8) {
                const eyeCanvas = document.createElement('canvas');
                eyeCanvas.width  = ew;
                eyeCanvas.height = eh;
                const eCtx = eyeCanvas.getContext('2d');

                eCtx.drawImage(glitchCanvas, ex, ey, ew, eh, 0, 0, ew, eh);

                // Soft radial edge blend
                eCtx.globalCompositeOperation = 'destination-in';
                const eGrad = eCtx.createRadialGradient(
                    ew * 0.5, eh * 0.5, Math.min(ew, eh) * 0.08,
                    ew * 0.5, eh * 0.5, Math.min(ew, eh) * 0.52
                );
                eGrad.addColorStop(0,   'rgba(0,0,0,1)');
                eGrad.addColorStop(0.6, 'rgba(0,0,0,0.88)');
                eGrad.addColorStop(1,   'rgba(0,0,0,0)');
                eCtx.fillStyle = eGrad;
                eCtx.fillRect(0, 0, ew, eh);

                // Lift upward — this creates the "wrong eye height" uncanny look
                const liftY = Math.round(eh * 0.28);  // lift ~28% of eye height

                ctx.save();
                ctx.globalAlpha = 0.90;
                ctx.drawImage(eyeCanvas, ex, ey - liftY);
                ctx.restore();
            }

        } catch (e) {
            console.warn('[FACE MORPH ERR]', e);
        }
    }

    // ─── CORE SYSTEM: ENTITY MEMORY MODEL (Per-Entity Drift, Duplication, Rotation, & Erasure) ───
    let memoryEntities = [];
    let insertedEntities = [];
    let globalDecayLevel = 0;
    let _wakeLock = null; // Screen Wake Lock handle (keeps mobile screen on during processing)

    function scanForObjectCandidates(w, h) {
        // Larger, lower-frequency block sizes for furniture, hardware, wall fixtures, speakers
        const blockSizes = [
            { w: 64, h: 50 },
            { w: 96, h: 72 },
            { w: 128, h: 96 }
        ];

        const candidates = [];
        try {
            const imgData = ctx.getImageData(0, 0, w, h);
            const data = imgData.data;
            const lum = (idx) => 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];

            for (const bs of blockSizes) {
                // Dense 3x3 step grid — catches contrast at any interior point
                const stepY = Math.max(12, Math.floor(bs.h * 0.4));
                const stepX = Math.max(12, Math.floor(bs.w * 0.4));
                for (let by = 0; by < h - bs.h; by += stepY) {
                    for (let bx = 0; bx < w - bs.w; bx += stepX) {
                        // Sample a 3x3 grid within the block (9 points)
                        const hw = bs.w >> 1, hh = bs.h >> 1;
                        const pts = [
                            (by * w + bx) * 4,
                            (by * w + bx + hw) * 4,
                            (by * w + bx + bs.w - 1) * 4,
                            ((by + hh) * w + bx) * 4,
                            ((by + hh) * w + bx + hw) * 4,
                            ((by + hh) * w + bx + bs.w - 1) * 4,
                            ((by + bs.h - 1) * w + bx) * 4,
                            ((by + bs.h - 1) * w + bx + hw) * 4,
                            ((by + bs.h - 1) * w + bx + bs.w - 1) * 4
                        ];
                        const lums = pts.map(lum);
                        const mn = Math.min(...lums), mx = Math.max(...lums);

                        // Lowered threshold: 8 instead of 20 — captures subtle gradients in dim scenes
                        if (mx - mn > 8) {
                            candidates.push({ x: bx, y: by, w: bs.w, h: bs.h, contrast: mx - mn });
                        }
                    }
                }
            }
        } catch (e) {}

        candidates.sort((a, b) => b.contrast - a.contrast);
        if (candidates.length > 30) candidates.length = 30;
        return candidates;
    }

    function initializeMemoryEntities(w, h) {
        memoryEntities = [];
        insertedEntities = [];
        globalDecayLevel = 0;

        if (w <= 0 || h <= 0) return;

        scanForTextCandidates(w, h);
        const objectCandidates = scanForObjectCandidates(w, h);

        // 1. Text & High-Contrast Features (up to 8)
        for (let i = 0; i < Math.min(8, textCandidateBlocks.length); i++) {
            const b = textCandidateBlocks[i];
            createMemoryEntity('text', b.x, b.y, b.w, b.h, w, h);
        }

        // 2. Hardware / Fixtures / Furniture (up to 6)
        for (let i = 0; i < Math.min(6, objectCandidates.length); i++) {
            const b = objectCandidates[i];
            const type = (i % 2 === 0) ? 'hardware' : 'object';
            createMemoryEntity(type, b.x, b.y, b.w, b.h, w, h);
        }

        // 3. FALLBACK: if the scene is very dark/uniform and contrast scan found nothing,
        //    seed at least 6 random-positioned entities so the system always has something to decay.
        //    These are seeded from real canvas pixels at those positions.
        if (memoryEntities.length === 0) {
            addLog('[ENTITY MEMORY ENGINE] Low-contrast scene — seeding fallback entities from random regions', 'normal');
            const fallbackTypes = ['text', 'hardware', 'object', 'hardware', 'text', 'object'];
            for (let f = 0; f < 6; f++) {
                const fw = 80 + Math.floor(Math.random() * 100);
                const fh = 60 + Math.floor(Math.random() * 80);
                const fx = Math.floor(Math.random() * Math.max(1, w - fw));
                const fy = Math.floor(Math.random() * Math.max(1, h - fh));
                createMemoryEntity(fallbackTypes[f], fx, fy, fw, fh, w, h);
            }
        }

        addLog(`[ENTITY MEMORY ENGINE] Salience detection complete: ${memoryEntities.length} tracked entities`, 'alert');
    }

    function createMemoryEntity(type, x, y, w, h, canvasW, canvasH) {
        const rx = Math.max(0, Math.min(canvasW - 10, x));
        const ry = Math.max(0, Math.min(canvasH - 10, y));
        const rw = Math.min(canvasW - rx, Math.max(10, w));
        const rh = Math.min(canvasH - ry, Math.max(10, h));

        // Offscreen canvas containing pristine pixels from base frame with gradient alpha edge feathering
        const sourceCanvas = document.createElement('canvas');
        sourceCanvas.width = rw;
        sourceCanvas.height = rh;
        const sCtx = sourceCanvas.getContext('2d');

        try {
            sCtx.drawImage(glitchCanvas, rx, ry, rw, rh, 0, 0, rw, rh);

            // 6px linear gradient alpha feathering around edges to avoid hard box seams
            const featherMargin = Math.min(6, Math.floor(Math.min(rw, rh) / 4));
            if (featherMargin > 2) {
                const imgData = sCtx.getImageData(0, 0, rw, rh);
                const d = imgData.data;
                for (let py = 0; py < rh; py++) {
                    for (let px = 0; px < rw; px++) {
                        const distLeft = px;
                        const distRight = rw - 1 - px;
                        const distTop = py;
                        const distBottom = rh - 1 - py;
                        const minDist = Math.min(distLeft, distRight, distTop, distBottom);
                        if (minDist < featherMargin) {
                            const alphaFactor = minDist / featherMargin;
                            const idx = (py * rw + px) * 4 + 3;
                            d[idx] = Math.round(d[idx] * alphaFactor);
                        }
                    }
                }
                sCtx.putImageData(imgData, 0, 0);
            }
        } catch(e) {}

        memoryEntities.push({
            id: 'entity_' + Math.random().toString(36).substr(2, 7),
            type: type, // 'text' | 'object' | 'hardware'
            baseRect: { x: rx, y: ry, w: rw, h: rh },
            decayLevel: 0,
            transform: {
                mirrorX: false,
                mirrorY: false,
                rotation: 0,
                duplicated: false,
                dupOffset: { x: 0, y: 0 },
                opacity: 1.0
            },
            sourceCanvas: sourceCanvas
        });
    }

    function triggerEntityDecayCycle() {
        globalDecayLevel++;
        if (!memoryEntities.length) return;

        const activeEntities = memoryEntities.filter(e => e.transform.opacity > 0);
        if (!activeEntities.length) return;

        // Pick 1-2 entities to mutate per repetition cycle using seeded RNG
        const numMutations = 1 + (frameRng() < 0.4 ? 1 : 0);

        for (let m = 0; m < numMutations; m++) {
            const currentActive = memoryEntities.filter(e => e.transform.opacity > 0);
            if (!currentActive.length) break;

            // Prioritize text at low decay levels, hardware/objects at mid levels
            currentActive.sort((a, b) => {
                const order = { 'text': 1, 'hardware': 2, 'object': 3 };
                return (order[a.type] || 3) - (order[b.type] || 3);
            });

            const targetIndex = Math.floor(frameRng() * Math.min(currentActive.length, 4));
            const entity = currentActive[targetIndex];
            if (!entity) continue;

            entity.decayLevel++;
            const dL = entity.decayLevel;

            // 1. Low decay -> mirrorX or mirrorY flip
            if (dL <= 2) {
                if (frameRng() < 0.6) entity.transform.mirrorX = !entity.transform.mirrorX;
                else entity.transform.mirrorY = !entity.transform.mirrorY;
                addLog(`[ENTITY DECAY] '${entity.type}' (${entity.id}) flipped (mirrorX:${entity.transform.mirrorX}, mirrorY:${entity.transform.mirrorY})`, 'alert');
            }
            // 2. Mid decay -> duplicated = true with spatial offset echo
            else if (dL <= 4) {
                entity.transform.duplicated = true;
                entity.transform.dupOffset = {
                    x: Math.round((frameRng() - 0.5) * 36),
                    y: Math.round((frameRng() - 0.5) * 28)
                };
                addLog(`[ENTITY DECAY] '${entity.type}' (${entity.id}) duplicated with echo offset (${entity.transform.dupOffset.x}px, ${entity.transform.dupOffset.y}px)`, 'alert');
            }
            // 3. Mid-high decay -> rotation tilt
            else if (dL <= 6) {
                const rotDelta = (frameRng() - 0.5) * 0.26;
                entity.transform.rotation += rotDelta;
                addLog(`[ENTITY DECAY] '${entity.type}' (${entity.id}) rotated by ${(rotDelta * 180 / Math.PI).toFixed(1)}°`, 'alert');
            }
            // 4. High decay -> opacity ramps down to 0 for total erasure!
            else {
                entity.transform.opacity = Math.max(0, entity.transform.opacity - 0.4);
                addLog(`[ENTITY DECAY] '${entity.type}' (${entity.id}) fading to erasure (opacity: ${entity.transform.opacity.toFixed(2)})`, 'danger');

                // Object Insertion: when entity is erased, insert a procedural silhouette into its region
                if (entity.transform.opacity <= 0) {
                    triggerObjectInsertion(entity.baseRect);
                }
            }
        }
    }

    function triggerObjectInsertion(baseRect) {
        const types = ['speaker_cone', 'chair_back', 'cabinet_edge', 'conduit_junction'];
        const sType = types[Math.floor(frameRng() * types.length)];

        insertedEntities.push({
            id: 'inserted_' + Math.random().toString(36).substr(2, 7),
            type: 'inserted',
            silhouetteType: sType,
            baseRect: { ...baseRect },
            opacity: 0.1 // Starts near-invisible, ramps UP over repetitions
        });
        addLog(`[OBJECT INSERTION] Complex inserted procedural structure '${sType}' into erased region`, 'alert');
    }

    function renderInsertedEntitySilhouette(ctx, entity) {
        const { x, y, w, h } = entity.baseRect;
        ctx.save();
        ctx.globalAlpha = Math.min(1.0, entity.opacity);
        ctx.strokeStyle = 'rgba(45, 38, 24, 0.85)';
        ctx.fillStyle = 'rgba(28, 24, 16, 0.70)';
        ctx.lineWidth = 2;

        const cx = x + w / 2;
        const cy = y + h / 2;

        if (entity.silhouetteType === 'speaker_cone') {
            const radius = Math.min(w, h) * 0.4;
            ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy, radius * 0.5, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy, radius * 0.2, 0, Math.PI * 2); ctx.fillStyle = '#0a0a0a'; ctx.fill();
        } else if (entity.silhouetteType === 'chair_back') {
            ctx.beginPath();
            ctx.rect(x + w * 0.15, y + h * 0.1, w * 0.7, h * 0.8);
            ctx.fill(); ctx.stroke();
            const numSlats = 3;
            for (let i = 1; i <= numSlats; i++) {
                const sx = x + w * 0.15 + (w * 0.7 * (i / (numSlats + 1)));
                ctx.beginPath(); ctx.moveTo(sx, y + h * 0.2); ctx.lineTo(sx, y + h * 0.7); ctx.stroke();
            }
        } else if (entity.silhouetteType === 'cabinet_edge') {
            ctx.beginPath(); ctx.rect(x, y, w, h); ctx.fill(); ctx.stroke();
            ctx.beginPath(); ctx.rect(x + 4, y + 4, w - 8, h - 8); ctx.stroke();
            ctx.fillStyle = '#665533';
            ctx.fillRect(x + 6, y + 8, 4, 4);
            ctx.fillRect(x + 6, y + h - 12, 4, 4);
        } else {
            ctx.beginPath(); ctx.rect(cx - 6, y, 12, h); ctx.fill(); ctx.stroke();
            ctx.fillStyle = '#776644';
            ctx.fillRect(cx - 10, y + h * 0.25, 20, 6);
            ctx.fillRect(cx - 10, y + h * 0.75, 20, 6);
        }
        ctx.restore();
    }

    function renderMemoryEntities(ctx, now) {
        if (!memoryEntities.length && !insertedEntities.length) return;

        for (const e of memoryEntities) {
            if (e.transform.opacity <= 0) continue; // Erased / fully forgotten

            const { x, y, w, h } = e.baseRect;
            const cx = x + w / 2;
            const cy = y + h / 2;

            ctx.save();
            ctx.globalAlpha = e.transform.opacity;

            ctx.translate(cx, cy);
            if (e.transform.rotation !== 0) ctx.rotate(e.transform.rotation);
            ctx.scale(e.transform.mirrorX ? -1 : 1, e.transform.mirrorY ? -1 : 1);
            ctx.translate(-cx, -cy);

            try {
                ctx.drawImage(e.sourceCanvas, x, y, w, h);
            } catch(err) {}

            ctx.restore();

            // Duplicated echo pass
            if (e.transform.duplicated) {
                ctx.save();
                ctx.globalAlpha = e.transform.opacity * 0.55;
                const ox = x + e.transform.dupOffset.x;
                const oy = y + e.transform.dupOffset.y;
                const dcx = ox + w / 2;
                const dcy = oy + h / 2;

                ctx.translate(dcx, dcy);
                if (e.transform.rotation !== 0) ctx.rotate(e.transform.rotation);
                ctx.scale(e.transform.mirrorX ? -1 : 1, e.transform.mirrorY ? -1 : 1);
                ctx.translate(-dcx, -dcy);

                try {
                    ctx.drawImage(e.sourceCanvas, ox, oy, w, h);
                } catch(err) {}

                ctx.restore();
            }
        }

        // Render inserted procedural silhouettes
        for (const inst of insertedEntities) {
            if (inst.opacity < 1.0) inst.opacity = Math.min(1.0, inst.opacity + 0.05);
            renderInsertedEntitySilhouette(ctx, inst);
        }
    }

    function applyMisrememberedTextGlitch(w, h, intensity, now) {
        if (!textCandidateBlocks.length) return;
        // Always run on at least 4 blocks; scale up with intensity
        const count = Math.max(4, Math.floor(4 + (intensity / 100) * 10));

        for (let i = 0; i < count; i++) {
            const b = textCandidateBlocks[Math.floor(Math.random() * textCandidateBlocks.length)];
            if (!b) continue;

            try {
                const glitchMode = Math.random();

                if (glitchMode < 0.45) {
                    // Backrooms Mirror-Ghost: horizontally flip region
                    ctx.save();
                    ctx.globalAlpha = 0.72;
                    ctx.translate(b.x + b.w, b.y);
                    ctx.scale(-1, 1);
                    ctx.drawImage(glitchCanvas, b.x, b.y, b.w, b.h, 0, 0, b.w, b.h);
                    ctx.restore();
                    ctx.save();
                    ctx.globalAlpha = 0.35;
                    ctx.drawImage(glitchCanvas, b.x, b.y, b.w, b.h, b.x + 2, b.y + 3, b.w, b.h);
                    ctx.restore();
                } else if (glitchMode < 0.72) {
                    // Downward melt duplication
                    const numSteps = 3 + Math.floor(Math.random() * 4);
                    const stepDx = (Math.random() - 0.5) * 14;
                    const stepDy = 7 + Math.random() * 13;
                    const angle = (Math.random() - 0.5) * 0.22;
                    ctx.save();
                    for (let s = 0; s < numSteps; s++) {
                        const sx = b.x + s * stepDx;
                        const sy = b.y + s * stepDy;
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(sx, sy, b.w, b.h);
                        ctx.clip();
                        ctx.translate(sx + b.w / 2, sy + b.h / 2);
                        ctx.rotate(angle * s);
                        ctx.translate(-(sx + b.w / 2), -(sy + b.h / 2));
                        ctx.globalAlpha = Math.max(0.12, 1.0 - s * 0.2);
                        ctx.drawImage(glitchCanvas, b.x, b.y, b.w, b.h, sx, sy, b.w, b.h);
                        ctx.restore();
                    }
                    ctx.restore();
                } else {
                    // Both: mirrored + melted ghost simultaneously
                    ctx.save();
                    ctx.globalAlpha = 0.55;
                    ctx.translate(b.x + b.w, b.y);
                    ctx.scale(-1, 1);
                    ctx.drawImage(glitchCanvas, b.x, b.y, b.w, b.h, 0, 0, b.w, b.h);
                    ctx.restore();
                    ctx.save();
                    ctx.globalAlpha = 0.45;
                    ctx.drawImage(glitchCanvas, b.x, b.y, b.w, b.h, b.x, b.y + 9, b.w, b.h);
                    ctx.restore();
                }
            } catch (e) {}
        }
    }

    // --- BAND-LEVEL POSTER MELT (the "MISSING poster" effect) ---
    // Groups detected contrast blocks into horizontal text-line bands, then
    // applies full-band distortions: vertical flip overlay, mirror ghost, or wax-column drip.
    function applyPosterBandMelt(w, h, now) {
        if (!textCandidateBlocks.length) return;

        // Sort blocks by Y and cluster into horizontal text-line bands
        const byY = [...textCandidateBlocks].sort((a, b2) => a.y - b2.y);
        const bands = [];
        for (const b of byY) {
            let placed = false;
            for (const band of bands) {
                if (Math.abs(b.y - band.cy) < 28) {
                    band.xMin = Math.min(band.xMin, b.x);
                    band.xMax = Math.max(band.xMax, b.x + b.w);
                    band.cy = (band.cy * band.cnt + b.y) / (band.cnt + 1);
                    band.bh = Math.max(band.bh, b.h);
                    band.cnt++;
                    placed = true;
                    break;
                }
            }
            if (!placed) bands.push({ cy: b.y, xMin: b.x, xMax: b.x + b.w, bh: b.h, cnt: 1 });
        }

        // Only use bands that look like text lines (multiple blocks side by side)
        const textBands = bands.filter(bd => bd.cnt >= 2 && (bd.xMax - bd.xMin) > 30);
        if (!textBands.length) return;

        // Pick 1-2 bands per call
        const numBands = 1 + (Math.random() < 0.35 ? 1 : 0);
        for (let i = 0; i < numBands; i++) {
            const band = textBands[Math.floor(Math.random() * textBands.length)];
            const padding = 6;
            const bx = Math.max(0, Math.floor(band.xMin) - padding);
            const bw = Math.min(w - bx, Math.floor(band.xMax - band.xMin) + padding * 2);
            const lineH = Math.max(18, Math.floor(band.bh * 2.2));
            const by = Math.max(0, Math.floor(band.cy) - Math.floor(lineH * 0.3));
            const bh = Math.min(h - by, lineH);

            if (bw < 20 || bh < 8) continue;

            const mode = Math.random();
            try {
                if (mode < 0.38) {
                    // VERTICAL FLIP OVERLAY — the whole text line is flipped upside-down
                    // and overlaid at partial opacity ("MISSING" inverted effect)
                    ctx.save();
                    ctx.globalAlpha = 0.60 + Math.random() * 0.28;
                    ctx.translate(bx, by + bh);
                    ctx.scale(1, -1);
                    ctx.drawImage(glitchCanvas, bx, by, bw, bh, 0, 0, bw, bh);
                    ctx.restore();
                    // Faint second ghost shifted down
                    ctx.save();
                    ctx.globalAlpha = 0.22;
                    ctx.translate(bx, by + bh + 6);
                    ctx.scale(1, -1);
                    ctx.drawImage(glitchCanvas, bx, by, bw, bh, 0, 0, bw, bh);
                    ctx.restore();

                } else if (mode < 0.68) {
                    // HORIZONTAL MIRROR GHOST — text mirrored left-right and overlaid
                    // creates the "letters appear backwards" name-plate effect
                    ctx.save();
                    ctx.globalAlpha = 0.65 + Math.random() * 0.25;
                    ctx.translate(bx + bw, by);
                    ctx.scale(-1, 1);
                    ctx.drawImage(glitchCanvas, bx, by, bw, bh, 0, 0, bw, bh);
                    ctx.restore();
                    // Ghost of original slightly offset
                    ctx.save();
                    ctx.globalAlpha = 0.28;
                    ctx.drawImage(glitchCanvas, bx, by, bw, bh, bx + 4, by + 2, bw, bh);
                    ctx.restore();

                } else {
                    // WAX COLUMN DRIP — organic drip curves instead of square box clips
                    const sliceH = Math.max(3, Math.floor(bh * 0.22));
                    const srcSliceY = by + bh - sliceH;
                    const dripH = Math.floor(16 + Math.random() * 32);

                    ctx.save();
                    // Create an organic rounded drip mask path
                    ctx.beginPath();
                    ctx.moveTo(bx, srcSliceY);
                    const cols = 5;
                    const colW = bw / cols;
                    for (let c = 0; c < cols; c++) {
                        const cx1 = bx + c * colW + colW * 0.5;
                        const cy1 = srcSliceY + dripH + (Math.random() - 0.3) * 15;
                        const cx2 = bx + (c + 1) * colW;
                        const cy2 = srcSliceY;
                        ctx.quadraticCurveTo(cx1, cy1, cx2, cy2);
                    }
                    ctx.lineTo(bx + bw, srcSliceY + dripH + 20);
                    ctx.lineTo(bx, srcSliceY + dripH + 20);
                    ctx.closePath();
                    ctx.clip();

                    // Draw the bottom slice of the text stretched downward into drip drops
                    for (let step = 0; step < 4; step++) {
                        const alpha = 0.55 - step * 0.12;
                        const offsetY = step * Math.floor(dripH / 4);
                        const stretchScale = 1.0 + step * 0.45;
                        ctx.globalAlpha = Math.max(0, alpha);
                        ctx.drawImage(
                            glitchCanvas,
                            bx, srcSliceY, bw, sliceH,
                            bx + (Math.random() - 0.5) * 4,
                            srcSliceY + offsetY,
                            bw, Math.ceil(sliceH * stretchScale)
                        );
                    }
                    ctx.restore();
                }
            } catch (e) {}
        }
    }

    // --- VISUAL INTERRUPT EVENTS ---
    let vhsTrackingJitterUntil = 0;

    function triggerVisualInterruptEvent(vType, durationSec, langIdx) {
        // Stop any previous no_signal music
        stopNoSignalMusic();

        // 0.2s V-sync tracking jitter roll before cut
        vhsTrackingJitterUntil = performance.now() + 200;

        const lang = NO_SIGNAL_LANGS[langIdx % NO_SIGNAL_LANGS.length];
        activeVisualEvent = { type: vType, endMs: performance.now() + durationSec * 1000, lang };

        const labels = { no_video: 'NO VIDEO', static: 'STATIC INTERFERENCE', no_signal: 'NO SIGNAL', complex_generated: 'COMPLEX GENERATED FEED' };
        addLog(`VISUAL INTERRUPT: ${labels[vType] || vType} — ${durationSec.toFixed(1)}s`, 'danger');

        if (vType === 'no_signal') {
            playNoSignalMusic();
            if (sourceVideo) sourceVideo.muted = true;
            if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.05);
        }
        if (vType === 'complex_generated') {
            if (sourceVideo) sourceVideo.muted = true;
            if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.05);
            playComplexGeneratedAmbience();
        }
        // For no_video: keep video audio, duck slightly
        if (vType === 'no_video') {
            if (sourceVideo) sourceVideo.muted = false;
            if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(0.7, audioCtx.currentTime, 0.1);
        }
        // For static: mute video audio completely + play static noise burst
        if (vType === 'static') {
            if (sourceVideo) sourceVideo.muted = true;
            if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.05);
            playStaticNoise(durationSec);
        }
    }

    let staticNoiseNodes = [];
    function playStaticNoise(durationSec) {
        if (!audioCtx) return;
        try {
            const bufferSize = audioCtx.sampleRate * Math.min(durationSec, 4);
            const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
            const data = buffer.getChannelData(0);
            let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0;
            for (let i = 0; i < bufferSize; i++) {
                const white = Math.random() * 2 - 1;
                b0 = 0.99886*b0 + white*0.0555179;
                b1 = 0.99332*b1 + white*0.0750759;
                b2 = 0.96900*b2 + white*0.1538520;
                b3 = 0.86650*b3 + white*0.3104856;
                b4 = 0.55000*b4 + white*0.5329522;
                b5 = -0.7616*b5 - white*0.0168980;
                data[i] = (b0+b1+b2+b3+b4+b5+white*0.5362) * 0.14;
            }
            const src = audioCtx.createBufferSource();
            src.buffer = buffer;
            const g = audioCtx.createGain();
            g.gain.setValueAtTime(0.5, audioCtx.currentTime);
            g.gain.setTargetAtTime(0.0, audioCtx.currentTime + durationSec - 0.2, 0.1);
            src.connect(g);
            g.connect(audioCtx.destination);
            if (streamDestination) g.connect(streamDestination);
            src.start();
            src.stop(audioCtx.currentTime + durationSec);
            staticNoiseNodes.push(src);
        } catch(e) {}
    }

    let noSignalAudioEl = null;
    function stopNoSignalMusic() {
        for (const n of noSignalMusicNodes) {
            try { n.stop(); } catch(e) {}
        }
        noSignalMusicNodes = [];
        for (const n of staticNoiseNodes) {
            try { n.stop(); } catch(e) {}
        }
        staticNoiseNodes = [];
        if (noSignalAudioEl) {
            noSignalAudioEl.pause();
            noSignalAudioEl.currentTime = 0;
            noSignalAudioEl = null;
        }
        if (noSignalAudioSourceNode) {
            try { noSignalAudioSourceNode.stop(); } catch(e) {}
            try { noSignalAudioSourceNode.disconnect(); } catch(e) {}
            noSignalAudioSourceNode = null;
        }
        stopComplexGeneratedAmbience();
        // Unmute video audio element and restore gain level
        if (sourceVideo) sourceVideo.muted = false;
        if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(1.0, audioCtx.currentTime, 0.15);
    }

    let noSignalAudioSourceNode = null;
    let emgAudioBuffer = null;

    // Pre-fetch emg.mp3 into an AudioBuffer so it can be routed into streamDestination reliably
    async function preloadEmgBuffer() {
        if (emgAudioBuffer || !audioCtx) return;
        try {
            const resp = await fetch('emg.mp3');
            const arrayBuf = await resp.arrayBuffer();
            emgAudioBuffer = await audioCtx.decodeAudioData(arrayBuf);
        } catch(e) {
            console.error('[EMG PRELOAD ERR]', e);
        }
    }

    function playNoSignalMusic() {
        if (!audioCtx) return;
        stopNoSignalMusic();

        // 1. Live preview fallback using HTML Audio element
        try {
            noSignalAudioEl = new Audio('emg.mp3');
            noSignalAudioEl.volume = 1.0;
            noSignalAudioEl.loop = true;
            noSignalAudioEl.play().catch(() => {});
        } catch(e) {}

        // 2. Direct Web Audio API node routing into streamDestination (FOR EXPORT RECORDING)
        if (emgAudioBuffer) {
            try {
                const bufSource = audioCtx.createBufferSource();
                bufSource.buffer = emgAudioBuffer;
                bufSource.loop = true;
                const gain = audioCtx.createGain();
                gain.gain.value = 1.85; // 2.5x gain boost so EMG audio is loud & punchy
                bufSource.connect(gain);
                gain.connect(audioCtx.destination);
                if (streamDestination) gain.connect(streamDestination);
                bufSource.start();
                noSignalAudioSourceNode = bufSource;
            } catch(e) {}
        } else {
            preloadEmgBuffer();
        }
    }

    // Render a low-quality degraded no_signal blue screen
    function renderNoSignalScreen(w, h, lang) {
        // Pixelate to low-res (every 4x4 block same color) then scale up
        const pxW = Math.floor(w / 4), pxH = Math.floor(h / 4);
        ctx.fillStyle = '#0000b4';
        ctx.fillRect(0, 0, w, h);

        // Add luminance noise over the blue
        const imgData = ctx.getImageData(0, 0, w, h);
        const d = imgData.data;
        for (let i = 0; i < d.length; i += 4) {
            const n = (Math.random() - 0.5) * 38;
            d[i]   = Math.max(0, Math.min(255, d[i]   + n));
            d[i+1] = Math.max(0, Math.min(255, d[i+1] + n));
            d[i+2] = Math.max(0, Math.min(255, d[i+2] + n));
        }
        ctx.putImageData(imgData, 0, 0);

        // Subtle horizontal analog raster
        for (let y = 0; y < h; y += 4) {
            ctx.fillStyle = 'rgba(0,0,0,0.05)';
            ctx.fillRect(0, y, w, 1);
        }

        // Occasional horizontal roll band
        if (Math.random() < 0.25) {
            const bandY = Math.floor(Math.random() * h);
            ctx.fillStyle = `rgba(255,255,255,${0.03 + Math.random() * 0.08})`;
            ctx.fillRect(0, bandY, w, 2 + Math.random() * 6);
        }

        // Text drawn blocky / low-res: draw on temp small canvas, scale up
        const fontSize = Math.max(10, Math.floor(pxW / 7));
        ctx.save();
        ctx.imageSmoothingEnabled = false;
        ctx.font = `bold ${fontSize}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = 'rgba(0,0,60,0.7)';
        ctx.fillText(lang, w / 2 + 1, h / 2 + 1);
        ctx.fillStyle = '#ffffff';
        ctx.fillText(lang, w / 2, h / 2);

        ctx.font = `${Math.max(8, Math.floor(pxW / 18))}px monospace`;
        ctx.textAlign = 'right';
        ctx.textBaseline = 'top';
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.fillText('CH 03', w - 8, 8);
        ctx.restore();
    }

    // ─── PROCEDURAL COMPLEX-GENERATED FEED & SYNTHESIZED MUSIC SUBSTITUTION ───
    let complexAmbienceOsc = null;
    let complexAmbienceGain = null;

    function renderComplexGeneratedFrame(w, h, now) {
        ctx.save();

        // Liminal carpet/wall yellow-grey base
        ctx.fillStyle = '#baa85c';
        ctx.fillRect(0, 0, w, h);

        // Vanishing point in perspective center
        const vpX = w * 0.5 + Math.sin(now * 0.0006) * 12;
        const vpY = h * 0.45 + Math.cos(now * 0.0008) * 8;

        // Wall, ceiling, floor perspective lines
        ctx.strokeStyle = 'rgba(75, 65, 25, 0.75)';
        ctx.lineWidth = 3;

        ctx.beginPath();
        ctx.moveTo(0, 0); ctx.lineTo(vpX, vpY);
        ctx.moveTo(w, 0); ctx.lineTo(vpX, vpY);
        ctx.moveTo(0, h); ctx.lineTo(vpX, vpY);
        ctx.moveTo(w, h); ctx.lineTo(vpX, vpY);
        ctx.stroke();

        // Receding corridor door frames
        const numFrames = 5;
        for (let i = 1; i <= numFrames; i++) {
            const t = (i / numFrames);
            const fw = w * (1 - t * 0.78);
            const fh = h * (1 - t * 0.78);
            const fx = vpX - fw * 0.5;
            const fy = vpY - fh * 0.5;

            ctx.strokeStyle = `rgba(55, 45, 18, ${0.85 - t * 0.45})`;
            ctx.strokeRect(fx, fy, fw, fh);
        }

        // Tiled wallpaper pattern simulation
        ctx.fillStyle = 'rgba(130, 115, 50, 0.22)';
        for (let py = 0; py < h; py += 32) {
            for (let px = 0; px < w; px += 24) {
                if (((px / 24) + (py / 32)) % 2 === 0) {
                    ctx.fillRect(px, py, 12, 16);
                }
            }
        }

        // Overhead fluorescent light strip
        const lightW = w * 0.28;
        const lightX = vpX - lightW * 0.5;
        ctx.fillStyle = 'rgba(255, 250, 210, 0.90)';
        ctx.fillRect(lightX, Math.max(10, vpY * 0.18), lightW, 8);
        ctx.shadowColor = 'rgba(255, 245, 180, 0.8)';
        ctx.shadowBlur = 20;
        ctx.fillRect(lightX, Math.max(10, vpY * 0.18), lightW, 8);

        // OSD Status
        ctx.font = '12px monospace';
        ctx.fillStyle = 'rgba(0, 255, 102, 0.85)';
        ctx.fillText('[ASYNC FEED // COMPLEX GENERATED ENVIRONMENT]', 20, 30);

        ctx.restore();
    }

    function playComplexGeneratedAmbience() {
        if (!audioCtx) return;
        try {
            if (!complexAmbienceOsc) {
                complexAmbienceOsc = audioCtx.createOscillator();
                complexAmbienceOsc.type = 'sawtooth';
                complexAmbienceOsc.frequency.value = 52.8;

                const lpf = audioCtx.createBiquadFilter();
                lpf.type = 'lowpass';
                lpf.frequency.value = 240;

                complexAmbienceGain = audioCtx.createGain();
                complexAmbienceGain.gain.value = 0.28;

                complexAmbienceOsc.connect(lpf);
                lpf.connect(complexAmbienceGain);
                complexAmbienceGain.connect(pannerNode || audioCtx.destination);
                if (streamDestination) complexAmbienceGain.connect(streamDestination);
                complexAmbienceOsc.start();
            } else {
                complexAmbienceGain.gain.setTargetAtTime(0.28, audioCtx.currentTime, 0.2);
            }
        } catch(e) {}
    }

    function stopComplexGeneratedAmbience() {
        if (complexAmbienceGain && audioCtx) {
            complexAmbienceGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.3);
        }
    }

    // Music substitution synth: seed-locked recurring detuned motif
    let musicSubGain = null;
    let musicSubOsc1 = null;
    let musicSubOsc2 = null;
    let musicSubLFO = null;

    function createComplexGeneratedMusicSynth() {
        if (!audioCtx || musicSubGain) return;

        try {
            musicSubGain = audioCtx.createGain();
            musicSubGain.gain.value = 0.0;

            const baseFreq = 146.83; // D3
            const motifFreqs = [baseFreq, baseFreq * 1.2, baseFreq * 1.5, baseFreq * 1.75];
            const seedIndex = Math.floor(seededRng() * motifFreqs.length);
            const targetFreq = motifFreqs[seedIndex];

            musicSubOsc1 = audioCtx.createOscillator();
            musicSubOsc1.type = 'sine';
            musicSubOsc1.frequency.value = targetFreq;

            musicSubOsc2 = audioCtx.createOscillator();
            musicSubOsc2.type = 'triangle';
            musicSubOsc2.frequency.value = targetFreq * 1.006;

            musicSubLFO = audioCtx.createOscillator();
            musicSubLFO.type = 'sine';
            musicSubLFO.frequency.value = 0.35;

            const lfoGain = audioCtx.createGain();
            lfoGain.gain.value = 4.0;
            musicSubLFO.connect(lfoGain);
            lfoGain.connect(musicSubOsc1.detune);

            const filter = audioCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.value = 650;

            musicSubOsc1.connect(filter);
            musicSubOsc2.connect(filter);
            filter.connect(musicSubGain);

            musicSubGain.connect(pannerNode || audioCtx.destination);
            if (streamDestination) musicSubGain.connect(streamDestination);

            musicSubOsc1.start();
            musicSubOsc2.start();
            musicSubLFO.start();
            addLog('[MUSIC SUBSTITUTION SYNTH] Initialized copyright-clean motif synth', 'normal');
        } catch(e) {}
    }

    function triggerMusicSubstitutionEvent(durationSeconds) {
        if (!audioCtx) return;
        createComplexGeneratedMusicSynth();

        if (mainGainNode) mainGainNode.gain.setTargetAtTime(0.04, audioCtx.currentTime, 0.2);
        if (musicSubGain) musicSubGain.gain.setTargetAtTime(0.35, audioCtx.currentTime, 0.3);

        addLog(`[MUSIC SUBSTITUTION] Media audio replaced by Complex recurring motif (${durationSeconds.toFixed(1)}s)`, 'alert');

        setTimeout(() => {
            if (mainGainNode) mainGainNode.gain.setTargetAtTime(1.0, audioCtx.currentTime, 0.4);
            if (musicSubGain) musicSubGain.gain.setTargetAtTime(0.0, audioCtx.currentTime, 0.5);
        }, durationSeconds * 1000);
    }

    // Render low-quality VHS "NO VIDEO" — solid pitch black screen with OSD corner text
    function renderNoVideoScreen(w, h, now) {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        // Scanlines
        for (let y = 0; y < h; y += 3) {
            ctx.fillStyle = 'rgba(255,255,255,0.04)';
            ctx.fillRect(0, y, w, 1);
        }

        // Chromatic split on the black area
        const now2 = performance.now();
        if (Math.random() < 0.3) {
            ctx.fillStyle = `rgba(255,0,0,0.04)`;
            ctx.fillRect(Math.random()*w*0.1, 0, w, h);
        }

        ctx.save();
        ctx.imageSmoothingEnabled = false;
        const fontSize = Math.max(10, Math.floor(w / 40));
        ctx.font = `bold ${fontSize}px "Courier New", monospace`;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        const margin = Math.max(10, Math.floor(w * 0.03));

        ctx.fillStyle = 'rgba(0,0,0,0.9)';
        ctx.fillText('PLAY  \u25B6', margin+1, margin+1);
        ctx.fillText('NO VIDEO', margin+1, margin + fontSize * 1.8 + 1);
        ctx.fillStyle = '#e8ee22';
        ctx.fillText('PLAY  \u25B6', margin, margin);
        ctx.fillText('NO VIDEO', margin, margin + fontSize * 1.8);

        const sec = sourceVideo && sourceVideo.currentTime ? Math.floor(sourceVideo.currentTime) : Math.floor(now / 1000);
        const hrs = Math.floor(sec/3600).toString().padStart(2,'0');
        const mins = Math.floor((sec%3600)/60).toString().padStart(2,'0');
        const secs = (sec%60).toString().padStart(2,'0');
        ctx.fillStyle = 'rgba(0,0,0,0.9)';
        ctx.fillText(`SP -${hrs}:${mins}:${secs}`, margin+1, h - margin - fontSize + 1);
        ctx.fillStyle = '#e8ee22';
        ctx.fillText(`SP -${hrs}:${mins}:${secs}`, margin, h - margin - fontSize);
        ctx.restore();
    }

    // Render degraded low-quality analog TV static
    function renderStaticFrame(w, h) {
        // Render at 1/3 scale then upscale (pixelated) for chunky low-fi look
        const sw = Math.floor(w / 3), sh = Math.floor(h / 3);
        const imgData = ctx.createImageData(sw, sh);
        const d = imgData.data;
        for (let i = 0; i < d.length; i += 4) {
            const v = Math.random() * 255 | 0;
            d[i] = v; d[i+1] = v; d[i+2] = v; d[i+3] = 255;
        }
        // Write to temp canvas, then scale up blocky
        if (!_videoBlitCanvas) { _videoBlitCanvas = document.createElement('canvas'); }
        _videoBlitCanvas.width = sw;
        _videoBlitCanvas.height = sh;
        const tc = _videoBlitCanvas.getContext('2d');
        tc.putImageData(imgData, 0, 0);
        ctx.save();
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(_videoBlitCanvas, 0, 0, sw, sh, 0, 0, w, h);
        ctx.restore();
        // Rolling band
        ctx.fillStyle = `rgba(255,255,255,${0.06 + Math.random() * 0.10})`;
        const bandY = Math.random() * h;
        ctx.fillRect(0, bandY, w, 4 + Math.random() * 14);
        // Subtle analog scanlines
        for (let y = 0; y < h; y += 4) {
            ctx.fillStyle = 'rgba(0,0,0,0.05)';
            ctx.fillRect(0, y, w, 1);
        }
    }

    // --- PERIODIC DISTORTION WINDOW SCHEDULER ---
    function checkDistortionActive(now) {
        if (now - lastDistortionWindowTime > currentWindowDuration) {
            lastDistortionWindowTime = now;
            isDistortionWindowActive = !isDistortionWindowActive;
            currentWindowDuration = isDistortionWindowActive 
                ? (2000 + Math.random() * 2500)  // 2 - 4.5s distortion window
                : (4500 + Math.random() * 4500); // 4.5 - 9s clean window
        }
        return isDistortionWindowActive;
    }

    // --- VISUAL CORRUPTION CANVAS RENDER LOOP (FOR VIDEO & AUDIO) ---
    // Off-screen scratch canvas — always kept alive to blit video frames
    // even when sourceVideo is visibility:hidden or off-screen.
    let _videoBlitCanvas = null;
    let _videoBlitCtx = null;

    function getVideoBlitCtx(w, h) {
        if (!_videoBlitCanvas) {
            _videoBlitCanvas = document.createElement('canvas');
        }
        if (_videoBlitCanvas.width !== w || _videoBlitCanvas.height !== h) {
            _videoBlitCanvas.width = w;
            _videoBlitCanvas.height = h;
        }
        if (!_videoBlitCtx) _videoBlitCtx = _videoBlitCanvas.getContext('2d');
        return _videoBlitCtx;
    }

    let _lastExportFrameTime = 0;
    const EXPORT_TARGET_MS = 1000 / 29.97; // ~33.4ms = 30fps budget

    function renderFrame(now) {
        animFrameId = requestAnimationFrame(renderFrame);

        // During export: enforce 30fps cap so rendering stays within the MediaRecorder
        // frame budget. Frames that finish faster than 33ms are skipped (canvas is unchanged
        // so captureStream just repeats the last frame — no drop, no stutter).
        if (isBatchExporting) {
            if (now - _lastExportFrameTime < EXPORT_TARGET_MS - 2) return;
            _lastExportFrameTime = now;
        }

        frameCount++;
        resetFrameRng();

        processAudioAnomalies(now);

        const w = glitchCanvas.width;
        const h = glitchCanvas.height;

        ctx.clearRect(0, 0, w, h);

        let hasFrame = false;

        if (mediaType === 'video') {
            if (sourceVideo.videoWidth > 0) {
                captureFrameSnapshot();
                maybeTriggerReplayBurst(now);

                if (replayState) {
                    drawReplayFrame(w, h, now);
                } else {
                    // Blit through an intermediate 2D canvas to bypass any
                    // compositor-taint issue when sourceVideo is off-screen.
                    try {
                        const blitCtx = getVideoBlitCtx(w, h);
                        blitCtx.drawImage(sourceVideo, 0, 0, w, h);
                        ctx.drawImage(_videoBlitCanvas, 0, 0);
                    } catch (e) {
                        try { ctx.drawImage(sourceVideo, 0, 0, w, h); } catch (e2) {}
                    }

                    // --- BACKROOMS COMPLEX MRI ANALYSIS SWEEP ---
                    // When loading / playing media, a green/amber radar laser beam sweeps top-to-bottom
                    // like ASYNC / Backrooms Complex scanning memory files for anomaly targets
                    if (now < mriScanEndTime) {
                        const progress = (now - mriScanStartTime) / 1800; // 1.8s sweep
                        const scanY = Math.floor((progress % 1.0) * h);
                        
                        // Horizontal green/amber MRI laser beam
                        const laserGrad = ctx.createLinearGradient(0, scanY - 12, 0, scanY + 12);
                        laserGrad.addColorStop(0, 'rgba(0, 255, 102, 0)');
                        laserGrad.addColorStop(0.5, 'rgba(0, 255, 102, 0.75)');
                        laserGrad.addColorStop(1, 'rgba(0, 255, 102, 0)');
                        ctx.fillStyle = laserGrad;
                        ctx.fillRect(0, scanY - 12, w, 24);

                        // Bright center core line
                        ctx.fillStyle = '#00ff66';
                        ctx.fillRect(0, scanY, w, 2);

                        // OSD readout
                        ctx.font = '11px monospace';
                        ctx.fillStyle = '#00ff66';
                        ctx.fillText(`[ASYNC MRI SCAN] ANOMALY DETECTED AT Y:${scanY}px`, 15, scanY - 16);
                    }
                }
                hasFrame = true;
            }
        } else if (mediaType === 'audio') {
            renderLiminalAudioGraphics(w, h, now);
            hasFrame = true;
        }

        if (!hasFrame) return;

        // --- VISUAL INTERRUPT EVENTS (no_video / static / no_signal / complex_generated) ---
        // These override normal video rendering
        if (activeVisualEvent) {
            if (now > activeVisualEvent.endMs) {
                // Event expired — restore audio
                stopNoSignalMusic(); // also clears static nodes + restores mainGainNode to 1.0
                activeVisualEvent = null;
            } else {
                // 0.2s V-sync tracking jitter roll before clean event cut
                if (now < vhsTrackingJitterUntil) {
                    applyPixelSlicing(w, h, 0.9);
                }
                const { type, lang } = activeVisualEvent;
                if (type === 'no_video') {
                    renderNoVideoScreen(w, h, now);
                } else if (type === 'static') {
                    renderStaticFrame(w, h);
                } else if (type === 'no_signal') {
                    renderNoSignalScreen(w, h, lang);
                } else if (type === 'complex_generated') {
                    renderComplexGeneratedFrame(w, h, now);
                }
                // Skip normal distortion — the visual event IS the frame
                updateTimeline();
                renderAudioSpectrum();
                renderSpatialRadar();
                return;
            }
        }

        // --- CORE SYSTEM: ENTITY MEMORY MODEL OVERLAY ---
        // Layer tracked salient feature entities (text, hardware, fixtures) with compounding drift & erasure over untouched base
        renderMemoryEntities(ctx, now);

        // --- PERIODIC DISTORTION WINDOW CHECK ---
        const chromaticPx = getSliderValue(chromaticAberrationSlider, 28);
        const pixelSliceFreq = getSliderValue(pixelSliceSlider, 75) / 100;
        const flawedMirrorVal = getSliderValue(flawedMirroringSlider, 80);
        let masterVal = getSliderValue(masterIntensitySlider, 85) / 100;

        // MEMORY DEGRADATION MODE:
        // Intensity scales dynamically over media duration (0.0 at start -> 4.0x extreme collapse near end)
        let degradationProg = 0;
        if (toggleMemoryDegrading && toggleMemoryDegrading.checked) {
            if (mediaType === 'video' && sourceVideo && sourceVideo.duration) {
                degradationProg = sourceVideo.currentTime / sourceVideo.duration;
            } else if (mediaType === 'audio' && sourceAudio && sourceAudio.duration) {
                degradationProg = sourceAudio.currentTime / sourceAudio.duration;
            }
            
            if (degradationProg < 0.20) {
                masterVal = 0.0; // 100% crystal clean visual start
            } else {
                const degFactor = (degradationProg - 0.20) / 0.80; // 0.0 to 1.0
                masterVal = masterVal * (degFactor * 4.0); // Ramps up to 4.0x
            }
        }

        const isWarpingActive = checkDistortionActive(now);

        const dt = now - lastFrameTimeMs;
        lastFrameTimeMs = now;

        // Periodic Face & Person Scan (every 300ms)
        if (now - lastFaceScanTime > 300) {
            lastFaceScanTime = now;
            trackedFaces = detectPersonFaces(w, h);
        }

        const isDegrading = toggleMemoryDegrading && toggleMemoryDegrading.checked;

        // --- UNCANNY ANOMALY PROCESSING (WARPING OR MEMORY DEGRADATION) ---
        if (isWarpingActive || isDegrading) {
            // 1. PERSON / FACE ANOMALY: If a human is on screen, apply authentic Kane Pixels facial morphing
            if (trackedFaces.length > 0 && masterVal > 0.04) {
                for (const face of trackedFaces) {
                    applyUncannyFaceMorph(face, w, h, masterVal, now);
                }
            } else {
                // 2. ENVIRONMENT ANOMALIES: For rooms, hallways, furniture, apply subtle regional memory drift
                const numRegions = 1 + (masterVal > 0.7 ? 1 : 0);
                for (let ri = 0; ri < numRegions; ri++) {
                    const rw = Math.floor(w * (0.20 + Math.random() * 0.25));
                    const rh = Math.floor(h * (0.20 + Math.random() * 0.25));
                    const rx = Math.floor(Math.random() * (w - rw));
                    const ry = Math.floor(Math.random() * (h - rh));

                    const opRoll = (ri + Math.floor(now / 700)) % 3;
                    if (opRoll === 0) applyPixelSmearRegion(rx, ry, rw, rh, masterVal, now);
                    else if (opRoll === 1) applyTextSagRegion(rx, ry, rw, rh, masterVal, now);
                    else if (opRoll === 2 && Math.random() < 0.4) applyBlockEchoRegion(rx, ry, rw, rh, masterVal, now);
                }
            }

            if (frameRng() < 0.08 * masterVal) applyObjectStretch(w, h, masterVal, now);

            if (flawedMirrorVal > 0 && frameRng() < 0.04) {
                applyFlawedInPlaceMirroring(w, h, flawedMirrorVal, now);
                if (pannerNode && audioCtx) {
                    spatialMonoUntil = now + 700;
                    pannerNode.pan.setTargetAtTime(0, audioCtx.currentTime, 0.05);
                    if (tapeWarmthFilter) tapeWarmthFilter.frequency.setTargetAtTime(6500, audioCtx.currentTime, 0.1);
                }
            }
            if (pannerNode && audioCtx && now > spatialMonoUntil && spatialMonoUntil > 0) {
                pannerNode.pan.setTargetAtTime(0, audioCtx.currentTime, 0.4);
                if (tapeWarmthFilter) tapeWarmthFilter.frequency.setTargetAtTime(11500, audioCtx.currentTime, 0.35);
                spatialMonoUntil = 0;
            }
        }

        // TEXT DISTORTION: scaled by masterVal when memory degrading is active
        if (toggleMisrememberedText && toggleMisrememberedText.checked) {
            if (now - lastTextScanTime > 200) {
                lastTextScanTime = now;
                scanForTextCandidates(w, h);
            }
            if (masterVal > 0.05) {
                // If faces are present, filter out text candidate blocks inside face bounding boxes
                if (trackedFaces.length > 0) {
                    textCandidateBlocks = textCandidateBlocks.filter(b => {
                        return !trackedFaces.some(f => 
                            b.x < f.x + f.w && b.x + b.w > f.x &&
                            b.y < f.y + f.h && b.y + b.h > f.y
                        );
                    });
                }
                applyMisrememberedTextGlitch(w, h, flawedMirrorVal, now);
                if (frameRng() < 0.85 * Math.min(1.0, masterVal)) applyPosterBandMelt(w, h, now);
            }
        }

        // FINAL DEGRADATION BREAKDOWN: In the last 15% of playback, apply extreme visual+audio destruction
        if (isDegrading && degradationProg > 0.85) {
            const collapseIntensity = (degradationProg - 0.85) / 0.15; // 0.0 to 1.0

            // ── EXTREME AUDIO COLLAPSE ────────────────────────────────────────────────
            if (audioCtx && !isAudioBlackout) {
                // Bitcrush ramps from ~20 steps down to 3 steps (pure square wave noise)
                const crushSteps = Math.max(3, Math.round(22 - collapseIntensity * 19));
                if (bitCrushNode && Math.random() < 0.04) bitCrushNode.curve = createBitCrushCurve(crushSteps);

                // Low-pass filter slams shut — audio becomes muffled underwater then silent noise
                const collapsedFreq = Math.max(200, 6000 - collapseIntensity * 5800);
                if (tapeWarmthFilter) tapeWarmthFilter.frequency.setTargetAtTime(collapsedFreq, audioCtx.currentTime, 0.08);

                // Ring mod goes demonic: high freq metallic screech
                if (ringModOsc && ringModGain) {
                    const demonicFreq = 800 + collapseIntensity * 3200 + Math.sin(now * 0.004) * 400;
                    ringModOsc.frequency.setTargetAtTime(demonicFreq, audioCtx.currentTime, 0.05);
                    ringModGain.gain.setTargetAtTime(0.08 + collapseIntensity * 0.55, audioCtx.currentTime, 0.05);
                }

                // Heavy crackle/noise bursts: fire much more frequently at the end
                if (Math.random() < 0.08 + collapseIntensity * 0.55) {
                    const crackleGain = audioCtx.createGain();
                    crackleGain.gain.setValueAtTime(0.4 + collapseIntensity * 0.9, audioCtx.currentTime);
                    crackleGain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.04 + Math.random() * 0.12);
                    const noiseLen = Math.floor(audioCtx.sampleRate * (0.04 + collapseIntensity * 0.18));
                    const noiseBuf = audioCtx.createBuffer(1, noiseLen, audioCtx.sampleRate);
                    const nd = noiseBuf.getChannelData(0);
                    for (let i = 0; i < noiseLen; i++) nd[i] = Math.random() * 2 - 1;
                    const nSrc = audioCtx.createBufferSource();
                    nSrc.buffer = noiseBuf;
                    nSrc.connect(crackleGain);
                    crackleGain.connect(pannerNode || audioCtx.destination);
                    nSrc.start();
                }

                // Speed collapse: playback rate becomes erratic, slows to crawl then spikes
                const collapseEl = mediaType === 'video' ? sourceVideo : sourceAudio;
                if (collapseEl && Math.random() < 0.06 + collapseIntensity * 0.35) {
                    const collapseRate = collapseIntensity > 0.6
                        ? (Math.random() < 0.5 ? 0.05 + Math.random() * 0.2 : 1.8 + Math.random() * 1.2)
                        : currentPitchBend * (0.5 + Math.random() * 0.9);
                    collapseEl.playbackRate = Math.max(0.05, Math.min(3.0, collapseRate));
                    setTimeout(() => { if (collapseEl) collapseEl.playbackRate = Math.max(0.25, Math.min(2.2, currentPitchBend)); }, 60 + Math.random() * 200);
                }

                // Distortion curve: maxed hard clip at full collapse
                if (waveShaperNode && Math.random() < 0.05) {
                    waveShaperNode.curve = createDistortionCurve(40 + collapseIntensity * 200);
                    setTimeout(() => { if (waveShaperNode) updateWaveShaperCurve(getSliderValue(compressionDistortSlider, 35)); }, 200 + Math.random() * 400);
                }
            }

            // ── EXTREME VISUAL COLLAPSE ───────────────────────────────────────────────
            // Full-frame pixel sort destroys spatial coherence
            applyPixelSortRegion(0, 0, w, h, 0.8 + collapseIntensity * 0.2);
            applyRealityTear(w, h, 1.5 + collapseIntensity * 2.5);
            applyPosterBandMelt(w, h, now);
            // Extreme pixelation: downscale then upscale for that disintegrating look
            if (collapseIntensity > 0.3) {
                try {
                    const pixFactor = Math.max(2, Math.floor(6 + collapseIntensity * 16));
                    const sw = Math.max(1, Math.floor(w / pixFactor));
                    const sh = Math.max(1, Math.floor(h / pixFactor));
                    const offC = document.createElement('canvas');
                    offC.width = sw; offC.height = sh;
                    const offCtx2 = offC.getContext('2d');
                    offCtx2.drawImage(glitchCanvas, 0, 0, sw, sh);
                    ctx.save(); ctx.imageSmoothingEnabled = false;
                    ctx.drawImage(offC, 0, 0, sw, sh, 0, 0, w, h);
                    ctx.restore();
                } catch(e) {}
            }
            // Static coverage ramps up to near-full at the very end
            if (Math.random() < 0.30 + collapseIntensity * 0.55) {
                ctx.save();
                ctx.globalAlpha = collapseIntensity * 0.85;
                renderStaticFrame(w, h);
                ctx.restore();
            }
            // Update degrading title
            updateDegradingTitle(currentFile ? currentFile.name : '', degradationProg);
        } else if (isDegrading) {
            updateDegradingTitle(currentFile ? currentFile.name : '', degradationProg);
        }

        updateTimeline();
        renderAudioSpectrum();
        renderSpatialRadar();

        if (isBatchExporting && mediaType === 'video' && sourceVideo.duration) {
            const pct = Math.floor((sourceVideo.currentTime / sourceVideo.duration) * 100);
            processingProgressBar.style.width = `${pct}%`;
            processingPercentText.textContent = `${pct}%`;
        }
    }

    // =========================================================
    // WEBGL FRAGMENT SHADER POST-PROCESSING ENGINE
    // Hardware-accelerated GPU MRI Slice Tears, Luminance Depth Occlusion & CRT Scanlines
    // =========================================================
    let webglCanvas = null;
    let gl = null;
    let glProgram = null;
    let glTexture = null;
    let glPositionBuffer = null;
    let uResolutionLoc, uTimeLoc, uIntensityLoc, uChromaticLoc, uWarpActiveLoc;

    function initWebGLShaderEngine() {
        if (webglCanvas) return;
        webglCanvas = document.createElement('canvas');
        gl = webglCanvas.getContext('webgl') || webglCanvas.getContext('experimental-webgl');
        if (!gl) {
            console.warn('[WEBGL] WebGL context unavailable — falling back to standard 2D canvas pipeline.');
            return;
        }

        const vsSource = `
            attribute vec2 a_position;
            varying vec2 v_texCoord;
            void main() {
                gl_Position = vec4(a_position, 0.0, 1.0);
                v_texCoord = vec2((a_position.x + 1.0) * 0.5, (a_position.y + 1.0) * 0.5);
            }
        `;

        const fsSource = `
            precision mediump float;
            uniform sampler2D u_image;
            uniform vec2 u_resolution;
            uniform float u_time;
            uniform float u_intensity;
            uniform float u_chromatic;
            uniform float u_warpActive;
            varying vec2 v_texCoord;

            float rand(vec2 co) {
                return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
            }

            void main() {
                vec2 uv = v_texCoord;

                if (u_warpActive > 0.5) {
                    // MRI Slice Displacement (Scanline band shifts)
                    float slice = floor(uv.y * 40.0);
                    float noiseVal = rand(vec2(slice, floor(u_time * 10.0)));
                    if (noiseVal < 0.3 * u_intensity) {
                        uv.x += (rand(vec2(slice, u_time)) - 0.5) * 0.07 * u_intensity;
                    }

                    // Pseudo Depth-Aware Shadow Occlusion Displacement
                    vec4 sampleCol = texture2D(u_image, uv);
                    float lum = dot(sampleCol.rgb, vec3(0.299, 0.587, 0.114));
                    if (lum < 0.20 && rand(uv + u_time) < 0.15 * u_intensity) {
                        uv.y += (rand(uv) - 0.5) * 0.04 * u_intensity;
                    }
                }

                // Hardware Chromatic Aberration
                float shift = (u_chromatic / u_resolution.x) * (0.6 + u_intensity * 0.4);
                float r = texture2D(u_image, vec2(uv.x + shift, uv.y)).r;
                float g = texture2D(u_image, uv).g;
                float b = texture2D(u_image, vec2(uv.x - shift, uv.y)).b;

                // Subtle Liminal Analog Haze
                float scanline = sin(uv.y * u_resolution.y * 1.2) * 0.006;
                vec3 finalCol = clamp(vec3(r, g, b) - scanline, 0.0, 1.0);

                // OPAQUE ALPHA FIX: Always set alpha = 1.0 so output is never black/transparent
                gl_FragColor = vec4(finalCol, 1.0);
            }
        `;

        function createShader(gl, type, source) {
            const shader = gl.createShader(type);
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                console.error('[WEBGL ERR]', gl.getShaderInfoLog(shader));
                gl.deleteShader(shader);
                return null;
            }
            return shader;
        }

        const vertShader = createShader(gl, gl.VERTEX_SHADER, vsSource);
        const fragShader = createShader(gl, gl.FRAGMENT_SHADER, fsSource);
        if (!vertShader || !fragShader) return;

        glProgram = gl.createProgram();
        gl.attachShader(glProgram, vertShader);
        gl.attachShader(glProgram, fragShader);
        gl.linkProgram(glProgram);
        gl.useProgram(glProgram);

        glPositionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, glPositionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1, -1,  1, -1, -1,  1,
            -1,  1,  1, -1,  1,  1
        ]), gl.STATIC_DRAW);

        const aPositionLoc = gl.getAttribLocation(glProgram, 'a_position');
        gl.enableVertexAttribArray(aPositionLoc);
        gl.vertexAttribPointer(aPositionLoc, 2, gl.FLOAT, false, 0, 0);

        uResolutionLoc = gl.getUniformLocation(glProgram, 'u_resolution');
        uTimeLoc = gl.getUniformLocation(glProgram, 'u_time');
        uIntensityLoc = gl.getUniformLocation(glProgram, 'u_intensity');
        uChromaticLoc = gl.getUniformLocation(glProgram, 'u_chromatic');
        uWarpActiveLoc = gl.getUniformLocation(glProgram, 'u_warpActive');

        glTexture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, glTexture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

        console.log('%c[WEBGL] WebGL Fragment Shader Post-Processing Engine Online', 'color: #00ff88; font-weight: bold;');
    }

    function applyWebGLShaderPass(targetCanvas, intensityVal, chromaticPx, isWarpingActive, now) {
        if (!gl || !glProgram) {
            initWebGLShaderEngine();
            if (!gl || !glProgram) return;
        }

        const w = targetCanvas.width;
        const h = targetCanvas.height;
        if (w === 0 || h === 0) return;

        if (webglCanvas.width !== w || webglCanvas.height !== h) {
            webglCanvas.width = w;
            webglCanvas.height = h;
            gl.viewport(0, 0, w, h);
        }

        try {
            gl.useProgram(glProgram);
            gl.uniform2f(uResolutionLoc, w, h);
            gl.uniform1f(uTimeLoc, (now % 100000) / 1000.0);
            gl.uniform1f(uIntensityLoc, intensityVal);
            gl.uniform1f(uChromaticLoc, chromaticPx);
            gl.uniform1f(uWarpActiveLoc, isWarpingActive ? 1.0 : 0.0);

            gl.activeTexture(gl.TEXTURE0);
            gl.bindTexture(gl.TEXTURE_2D, glTexture);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
            gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, targetCanvas);

            gl.drawArrays(gl.TRIANGLES, 0, 6);

            // Stamp opaque WebGL shader output back onto main canvas
            ctx.save();
            ctx.globalCompositeOperation = 'source-over';
            ctx.drawImage(webglCanvas, 0, 0, w, h);
            ctx.restore();
        } catch (e) {
            console.warn('[WEBGL WARN] Shader pass fallback:', e);
        }
    }

    // =========================================================
    // STATIC IMAGE DISTORTION ENGINE (NO CONTINUOUS MOVING LOOP)
    // Feature Duplication & Angled Offset (The SpongeBob Effect)
    // =========================================================
    function processStaticImage(file) {
        console.log('%c[IMAGE ENGINE] Processing Static Image Distortion (SpongeBob Angled Feature Duplication)', 'color: #ffb000; font-weight: bold; font-size: 13px;');
        mediaType = 'image';

        // Cancel any active animation frame loop so images don't continuously move!
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
            console.log('[DEBUG] Cancelled requestAnimationFrame loop for static image mode.');
        }

        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            sourceImage.src = img.src;

            let w = img.naturalWidth || 800;
            let h = img.naturalHeight || 600;
            if (w > 1280) { h = Math.round(h * (1280 / w)); w = 1280; }
            if (h > 720) { w = Math.round(w * (720 / h)); h = 720; }
            glitchCanvas.width = w;
            glitchCanvas.height = h;

            console.log(`[DEBUG IMAGE] Resized Canvas: ${w}x${h}`);

            // 1. Draw base original image onto canvas
            ctx.clearRect(0, 0, w, h);
            ctx.drawImage(img, 0, 0, w, h);

            const masterVal = getSliderValue(masterIntensitySlider, 85) / 100;
            const flawedMirrorVal = getSliderValue(flawedMirroringSlider, 80);
            const chromaticPx = getSliderValue(chromaticAberrationSlider, 28);

            // 2. Detect Human Subjects & Facial Landmarks
            const detectedPersons = detectPersonFaces(w, h);

            if (detectedPersons.length > 0) {
                console.log(`%c[IMAGE ENGINE] Detected ${detectedPersons.length} human subject(s) — applying Photoshop-grade Liquify Facial Smear`, 'color: #38ef7d; font-weight: bold;');
                addLog(`[PERSON DETECTED] Uncanny facial anatomical reconstruction active on ${detectedPersons.length} subject(s)`, 'alert');

                // Apply Photoshop-grade Liquify Facial Morph to each detected human face
                for (const face of detectedPersons) {
                    applyUncannyFaceMorph(face, w, h, masterVal, performance.now());
                }
            } else {
                console.log('[IMAGE ENGINE] Non-human / Environment subject — applying Entity Memory Model');
                // Entity Memory Model: scan image for salient features (furniture, fixtures, doors, wallpaper)
                initializeMemoryEntities(w, h);
                scanForTextCandidates(w, h);

                if (textCandidateBlocks.length > 0) {
                    const numDuplications = 2 + Math.floor(Math.random() * 3);
                    for (let d = 0; d < numDuplications; d++) {
                        const block = textCandidateBlocks[Math.floor(Math.random() * textCandidateBlocks.length)];
                        if (!block) continue;

                        const featureW = Math.min(w - block.x, Math.max(32, block.w * 2.5));
                        const featureH = Math.min(h - block.y, Math.max(28, block.h * 2.5));
                        const fx = Math.max(0, block.x - Math.floor(block.w * 0.4));
                        const fy = Math.max(0, block.y - Math.floor(block.h * 0.4));
                        const dx = fx + (12 + Math.random() * 35);
                        const dy = fy + (15 + Math.random() * 40);
                        const angle = (Math.random() - 0.5) * 0.25;

                        const offCanvas = document.createElement('canvas');
                        offCanvas.width = featureW;
                        offCanvas.height = featureH;
                        const offCtx = offCanvas.getContext('2d');
                        offCtx.drawImage(glitchCanvas, fx, fy, featureW, featureH, 0, 0, featureW, featureH);

                        offCtx.globalCompositeOperation = 'destination-in';
                        const grad = offCtx.createRadialGradient(
                            featureW / 2, featureH / 2, Math.min(featureW, featureH) * 0.15,
                            featureW / 2, featureH / 2, Math.min(featureW, featureH) * 0.5
                        );
                        grad.addColorStop(0, 'rgba(0,0,0,1)');
                        grad.addColorStop(0.7, 'rgba(0,0,0,0.85)');
                        grad.addColorStop(1, 'rgba(0,0,0,0)');
                        offCtx.fillStyle = grad;
                        offCtx.fillRect(0, 0, featureW, featureH);

                        ctx.save();
                        ctx.translate(dx + featureW / 2, dy + featureH / 2);
                        ctx.rotate(angle);
                        ctx.globalAlpha = 0.85;
                        ctx.drawImage(offCanvas, -featureW / 2, -featureH / 2);
                        ctx.restore();
                    }
                }

                if (toggleMisrememberedText && toggleMisrememberedText.checked) {
                    applyMisrememberedTextGlitch(w, h, flawedMirrorVal, performance.now());
                }
            }

            // (No chromatic aberration on portraits — it causes rainbow color banding)

            // 7. Enable Snapshot and Preview Downloads
            btnSnapshotImage.disabled = false;
            btnProcessFullFile.disabled = false;
            const dataUrl = glitchCanvas.toDataURL('image/png');
            previewMediaContainer.innerHTML = `<img src="${dataUrl}" alt="Misremembered Static Image" style="max-width:100%; max-height:300px; border-radius:4px;">`;
            btnDownloadPayload.href = dataUrl;
            btnDownloadPayload.download = currentFile ? currentFile.name.replace(/\.[^/.]+$/, "") + "_MISREMEMBERED.png" : "MISREMEMBERED_IMAGE.png";
            previewSubtext.textContent = 'Static misremembered image rendered with feature duplication, angled offsets, and symbol distortion.';
            previewCard.style.display = 'flex';

            addLog('STATIC IMAGE RECONSTRUCTION: Rendered with feature duplication & angled displacement.', 'normal');
        };
        img.src = URL.createObjectURL(file);
    }

    // --- VISUAL DISTORTION HELPER FUNCTIONS ---
    // --- TARGETED SUB-REGION PIXEL OPERATIONS ---

    // FACE / OBJECT COLUMN WAX MELT: shifts individual pixel columns downward by varying amounts
    // creating organic liquid dripping along edges of faces and objects.
    function applyFaceColumnMelt(rx, ry, rw, rh, intensity, now) {
        try {
            if (rw < 8 || rh < 8) return;
            const imgData = ctx.getImageData(rx, ry, rw, rh);
            const src = new Uint8ClampedArray(imgData.data);
            const dst = imgData.data;
            const t = now * 0.00025;

            for (let x = 0; x < rw; x++) {
                // Each column drips by a different amount — sine wave + noise creates organic drip profile
                const drip = Math.round(
                    Math.sin(x * 0.18 + t) * intensity * 12 +
                    Math.sin(x * 0.07 + t * 1.7) * intensity * 8 +
                    Math.random() * intensity * 4
                );
                if (drip <= 0) continue;
                // Shift column downward: copy pixels from (y - drip) into y
                for (let y = rh - 1; y >= 0; y--) {
                    const di = (y * rw + x) * 4;
                    const sy = Math.max(0, y - drip);
                    const si = (sy * rw + x) * 4;
                    dst[di]   = src[si];
                    dst[di+1] = src[si+1];
                    dst[di+2] = src[si+2];
                }
            }
            ctx.putImageData(imgData, rx, ry);
        } catch (e) {}
    }
    // Each function operates on a sub-rect (rx,ry,rw,rh) of the canvas
    // rather than the full frame — dramatically reduces getImageData cost
    // and makes distortion look localised to specific objects/areas.

    function applyPixelSmearRegion(rx, ry, rw, rh, masterVal, now) {
        try {
            const imgData = ctx.getImageData(rx, ry, rw, rh);
            const src = new Uint8ClampedArray(imgData.data);
            const dst = imgData.data;
            const smearAmt = Math.floor(4 + masterVal * 20);
            const t = now * 0.0002;
            for (let y = 0; y < rh; y++) {
                const rowSmear = Math.round(Math.sin((ry + y) * 0.031 + t) * smearAmt * 0.7);
                for (let x = 0; x < rw; x++) {
                    const srcX = Math.max(0, Math.min(rw - 1, x - rowSmear));
                    const si = (y * rw + srcX) * 4;
                    const di = (y * rw + x) * 4;
                    dst[di]     = src[si]     * 0.8 + src[di]     * 0.2;
                    dst[di + 1] = src[si + 1] * 0.8 + src[di + 1] * 0.2;
                    dst[di + 2] = src[si + 2] * 0.8 + src[di + 2] * 0.2;
                }
            }
            ctx.putImageData(imgData, rx, ry);
        } catch (e) {}
    }

    function applyTextSagRegion(rx, ry, rw, rh, masterVal, now) {
        try {
            const rowStep = 2;
            const sagTime = now * 0.00045;
            const amplitude = 4 + masterVal * 14;
            const frequency = 0.022 + masterVal * 0.025;
            const imgData = ctx.getImageData(rx, ry, rw, rh);
            const src = new Uint8ClampedArray(imgData.data);
            const dst = imgData.data;
            for (let y = rowStep; y < rh - rowStep; y += rowStep) {
                const sagOffset = Math.round(
                    Math.sin((ry + y) * frequency + sagTime) * amplitude +
                    Math.sin((ry + y) * frequency * 0.41 + sagTime * 2.3) * amplitude * 0.5
                );
                if (sagOffset === 0) continue;
                for (let dy = 0; dy < rowStep; dy++) {
                    const dstRow = y + dy;
                    if (dstRow >= rh) break;
                    for (let x = 0; x < rw; x++) {
                        const srcX = Math.max(0, Math.min(rw - 1, x - sagOffset));
                        const si = (y * rw + srcX) * 4;
                        const di = (dstRow * rw + x) * 4;
                        dst[di]     = src[si];
                        dst[di + 1] = src[si + 1];
                        dst[di + 2] = src[si + 2];
                    }
                }
            }
            ctx.putImageData(imgData, rx, ry);
        } catch (e) {}
    }

    function applyBlockEchoRegion(rx, ry, rw, rh, masterVal, now) {
        try {
            const numEchoes = 1 + Math.floor(masterVal * 2);
            const t = now * 0.0001;
            for (let e = 0; e < numEchoes; e++) {
                const bw = Math.min(rw, 30 + Math.floor(Math.random() * 80));
                const bh = Math.min(rh, 15 + Math.floor(Math.random() * 50));
                if (bw < 4 || bh < 4) continue;
                const dstX = rx + Math.floor(Math.random() * Math.max(1, rw - bw));
                const dstY = ry + Math.floor(Math.random() * Math.max(1, rh - bh));
                const offsetX = Math.round(Math.sin(t + e * 1.7) * rw * 0.4);
                const offsetY = Math.round(Math.cos(t * 0.8 + e * 2.3) * rh * 0.4);
                const srcX = Math.max(0, Math.min(glitchCanvas.width - bw - 1, dstX + offsetX));
                const srcY = Math.max(0, Math.min(glitchCanvas.height - bh - 1, dstY + offsetY));
                const srcPatch = ctx.getImageData(srcX, srcY, bw, bh);
                const dstPatch = ctx.getImageData(dstX, dstY, bw, bh);
                const sd = srcPatch.data, dd = dstPatch.data;
                const blendAmt = 0.4 + masterVal * 0.3;
                for (let i = 0; i < sd.length; i += 4) {
                    dd[i]     = dd[i]     * (1 - blendAmt) + sd[i]     * blendAmt;
                    dd[i + 1] = dd[i + 1] * (1 - blendAmt) + sd[i + 1] * blendAmt;
                    dd[i + 2] = dd[i + 2] * (1 - blendAmt) + sd[i + 2] * blendAmt;
                }
                ctx.putImageData(dstPatch, dstX, dstY);
            }
        } catch (e) {}
    }

    function applyPixelSortRegion(rx, ry, rw, rh, masterVal) {
        try {
            if (rw < 4 || rh < 4) return;
            const numCols = 2 + Math.floor(masterVal * 5);
            const imgData = ctx.getImageData(rx, ry, rw, rh);
            const data = imgData.data;
            for (let c = 0; c < numCols; c++) {
                const col = Math.floor(Math.random() * Math.max(1, rw - 4));
                const colW = 1 + Math.floor(Math.random() * 3);
                const sortStart = Math.floor(Math.random() * rh * 0.5);
                const sortLen = 10 + Math.floor(Math.random() * (rh * 0.6));
                const sortEnd = Math.min(rh, sortStart + sortLen);
                const pixels = [];
                for (let y = sortStart; y < sortEnd; y++) {
                    for (let cx = col; cx < Math.min(col + colW, rw); cx++) {
                        const i = (y * rw + cx) * 4;
                        pixels.push({ y, cx, r: data[i], g: data[i+1], b: data[i+2],
                            br: data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114 });
                    }
                }
                pixels.sort((a, b) => a.br - b.br);
                let pi = 0;
                for (let y = sortStart; y < sortEnd; y++) {
                    for (let cx = col; cx < Math.min(col + colW, rw); cx++) {
                        if (pi >= pixels.length) break;
                        const i = (y * rw + cx) * 4;
                        data[i] = pixels[pi].r; data[i+1] = pixels[pi].g; data[i+2] = pixels[pi].b;
                        pi++;
                    }
                }
            }
            ctx.putImageData(imgData, rx, ry);
        } catch (e) {}
    }

    // Keep legacy full-canvas versions for backward compat (used by applyMisrememberedTextGlitch)
    function applyPixelSmear(w, h, masterVal, now) { applyPixelSmearRegion(0, 0, w, h, masterVal, now); }
    function applyTextSag(w, h, masterVal, now) { applyTextSagRegion(0, 0, w, h, masterVal, now); }
    function applyBlockEcho(w, h, masterVal, now) { applyBlockEchoRegion(0, 0, w, h, masterVal, now); }
    function applyPixelSort(w, h, masterVal) { applyPixelSortRegion(0, 0, w, h, masterVal); }

    // Backrooms Object & Architecture Vertical Stretch
    // Inspired by Kane Pixels Backrooms geometry anomalies (e.g. chairs/walls unnaturally tall/stretched upwards)
    function applyObjectStretch(w, h, masterVal, now) {
        try {
            const numStretches = 1 + Math.floor(masterVal * 3);
            for (let s = 0; s < numStretches; s++) {
                // Select a bounding region (e.g. an object, chair, wall segment, or face)
                const rw = Math.floor(w * (0.15 + Math.random() * 0.35));
                const rh = Math.floor(h * (0.20 + Math.random() * 0.40));
                const rx = Math.floor(Math.random() * (w - rw));
                const ry = Math.floor(Math.random() * (h - rh));

                // 70% probability vertical extreme stretch (like Backrooms high-back chairs/tall walls)
                const stretchAxis = Math.random() < 0.70 ? 'v' : 'h';
                const stretchMult = 2.0 + Math.random() * 3.5; // 2x to 5.5x stretch

                let dstW = rw;
                let dstH = rh;
                let drawY = ry;
                let drawX = rx;

                if (stretchAxis === 'v') {
                    dstH = Math.min(h, Math.floor(rh * stretchMult));
                    // Stretch upwards from origin
                    drawY = Math.max(0, ry - (dstH - rh));
                } else {
                    dstW = Math.min(w, Math.floor(rw * stretchMult));
                    drawX = Math.max(0, rx - Math.floor((dstW - rw) / 2));
                }

                ctx.save();
                ctx.beginPath();
                ctx.rect(drawX, drawY, dstW, dstH);
                ctx.clip();
                ctx.globalAlpha = 0.92;
                ctx.drawImage(glitchCanvas, rx, ry, rw, rh, drawX, drawY, dstW, dstH);
                ctx.restore();
            }
        } catch (e) {}
    }

    // AUTHENTIC ANALOG TAPE WARMTH (Subtle VHS Luma/Chroma drift - NO RAINBOW / NEON GLITCH)
    function applyAnalogTapeWarmth(w, h, masterVal) {
        try {
            const imgData = ctx.getImageData(0, 0, w, h);
            const data = imgData.data;
            const shift = Math.floor(1 + masterVal * 2) * 4;

            // Very subtle Y/C tape delay (slight red-blue micro offset)
            for (let i = 0; i < data.length; i += 4) {
                if (i + shift < data.length) data[i] = Math.round(data[i] * 0.96 + data[i + shift] * 0.04);
            }
            ctx.putImageData(imgData, 0, 0);
        } catch (e) {}
    }

    function applyRealityTear(w, h, masterVal) {
        try {
            const tearY = Math.floor(Math.random() * (h - 30));
            const tearH = 3 + Math.floor(Math.random() * (10 + masterVal * 15));
            const srcY  = Math.floor(Math.random() * (h - tearH));
            const shiftX = Math.floor((Math.random() - 0.5) * w * 0.4);

            const srcBand = ctx.getImageData(0, srcY, w, tearH);
            const dstBand = ctx.getImageData(0, tearY, w, tearH);
            const sd = srcBand.data;
            const dd = dstBand.data;

            const blend = 0.55 + masterVal * 0.35;
            for (let y = 0; y < tearH; y++) {
                for (let x = 0; x < w; x++) {
                    const srcX = Math.max(0, Math.min(w-1, x + shiftX));
                    const si = (y * w + srcX) * 4;
                    const di = (y * w + x) * 4;
                    dd[di]     = dd[di]     * (1-blend) + sd[si]     * blend;
                    dd[di + 1] = dd[di + 1] * (1-blend) + sd[si + 1] * blend;
                    dd[di + 2] = dd[di + 2] * (1-blend) + sd[si + 2] * blend;
                }
            }
            ctx.putImageData(dstBand, 0, tearY);
        } catch (e) {}
    }

    function applyFlawedInPlaceMirroring(w, h, intensity, now) {
        try {
            // BACKROOMS ARCHITECTURAL MIRRORING:
            // Duplicates half of the frame (horizontally or vertically) onto the other half,
            // creating wrong/impossible liminal geometry (like endless server racks or hallway corners).
            ctx.save();
            const mode = Math.random();
            if (mode < 0.45) {
                // Horizontal mirror (left half mirrored onto right half)
                ctx.translate(w, 0);
                ctx.scale(-1, 1);
                ctx.drawImage(glitchCanvas, 0, 0, w / 2, h, 0, 0, w / 2, h);
            } else if (mode < 0.80) {
                // Vertical mirror (top half mirrored onto bottom half - server rack floor/ceiling effect)
                ctx.translate(0, h);
                ctx.scale(1, -1);
                ctx.drawImage(glitchCanvas, 0, 0, w, h / 2, 0, 0, w, h / 2);
            } else {
                // Quadrant mirror (top-left mirrored into 4 corners)
                ctx.translate(w, h);
                ctx.scale(-1, -1);
                ctx.drawImage(glitchCanvas, 0, 0, w / 2, h / 2, 0, 0, w / 2, h / 2);
            }
            ctx.restore();
        } catch (e) {}
    }

    function applyChromaticAberration(w, h, offset) {
        try {
            const imgData = ctx.getImageData(0, 0, w, h);
            const data = imgData.data;
            const copyData = new Uint8ClampedArray(data);
            const shift = Math.floor(offset) * 4;

            for (let i = 0; i < data.length; i += 4) {
                if (i + shift < data.length) data[i] = copyData[i + shift];
                if (i - shift >= 0) data[i + 2] = copyData[i - shift + 2];
            }
            ctx.putImageData(imgData, 0, 0);
        } catch (e) {}
    }

    function applyPixelSlicing(w, h, sliceFreq) {
        const numSlices = Math.floor(Math.random() * 4 * sliceFreq) + 1;
        for (let i = 0; i < numSlices; i++) {
            const sliceY = Math.floor(Math.random() * (h - 20));
            const sliceHeight = Math.floor(Math.random() * 20) + 3;
            const offsetX = (Math.random() - 0.5) * 60 * sliceFreq;
            try {
                const sliceData = ctx.getImageData(0, sliceY, w, sliceHeight);
                ctx.putImageData(sliceData, offsetX, sliceY);
            } catch (e) {}
        }
    }

    function renderLiminalAudioGraphics(w, h, now) {
        ctx.fillStyle = '#05070a';
        ctx.fillRect(0, 0, w, h);

        ctx.save();
        ctx.strokeStyle = 'rgba(255, 51, 68, 0.2)';
        ctx.lineWidth = 1;

        const horizonY = h * 0.45;
        const centerX = w / 2;

        for (let x = -w; x <= w * 2; x += 40) {
            ctx.beginPath();
            ctx.moveTo(centerX, horizonY);
            ctx.lineTo(x, h);
            ctx.stroke();
        }

        const timeOffset = (now * 0.05) % 30;
        for (let y = horizonY; y < h; y += 15 + (y - horizonY) * 0.1) {
            ctx.beginPath();
            ctx.moveTo(0, y + timeOffset);
            ctx.lineTo(w, y + timeOffset);
            ctx.stroke();
        }

        ctx.fillStyle = '#ff3344';
        ctx.font = '24px "VT323", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('UNCANNY AUDIO RECONSTRUCTION // PERIODIC PITCH DRIFT ACTIVE', w / 2, horizonY - 30);

        ctx.restore();
    }

    function renderAudioSpectrum() {
        if (!specCtx || !analyserNode) return;

        const w = audioSpectrumCanvas.width;
        const h = audioSpectrumCanvas.height;

        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserNode.getByteFrequencyData(dataArray);

        specCtx.fillStyle = 'rgba(2, 4, 6, 0.85)';
        specCtx.fillRect(0, 0, w, h);

        const barWidth = (w / bufferLength) * 1.5;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * h;
            specCtx.fillStyle = isAudioBlackout ? '#ff3344' : (i % 2 === 0 ? '#00ff66' : '#ffb000');
            specCtx.fillRect(x, h - barHeight, barWidth - 1, barHeight);
            x += barWidth;
        }
    }

    function renderSpatialRadar() {
        if (!radarCtx) return;

        const w = spatialRadarCanvas.width;
        const h = spatialRadarCanvas.height;
        const cx = w / 2;
        const cy = h / 2;

        radarCtx.fillStyle = 'rgba(2, 4, 6, 0.85)';
        radarCtx.fillRect(0, 0, w, h);

        radarCtx.strokeStyle = 'rgba(0, 255, 102, 0.25)';
        radarCtx.lineWidth = 1;
        radarCtx.beginPath();
        radarCtx.arc(cx, cy, 15, 0, Math.PI * 2);
        radarCtx.arc(cx, cy, 30, 0, Math.PI * 2);
        radarCtx.stroke();

        radarCtx.beginPath();
        radarCtx.moveTo(cx, 0); radarCtx.lineTo(cx, h);
        radarCtx.moveTo(0, cy); radarCtx.lineTo(w, cy);
        radarCtx.stroke();

        const blipX = cx + panX * 28;
        const blipY = cy + panY * 20;

        radarCtx.fillStyle = '#ff3344';
        radarCtx.beginPath();
        radarCtx.arc(blipX, blipY, 4, 0, Math.PI * 2);
        radarCtx.fill();

        radarCtx.strokeStyle = 'rgba(255, 51, 68, 0.6)';
        radarCtx.beginPath();
        radarCtx.arc(blipX, blipY, 7, 0, Math.PI * 2);
        radarCtx.stroke();

        const radarText = document.getElementById('radarTargetText');
        const pitchText = document.getElementById('pitchFreqText');

        if (radarText) {
            const isBehind = panY < 0;
            radarText.textContent = `TARGET: ${isBehind ? 'BEHIND' : 'IN FRONT'} (${panX > 0 ? 'R' : 'L'})`;
        }
        if (pitchText) {
            const st = (Math.log2(currentPitchBend) * 12).toFixed(1);
            pitchText.textContent = `PITCH SHIFT: ${st > 0 ? '+' : ''}${st} st`;
        }
    }

    function formatTime(seconds) {
        if (isNaN(seconds)) return '00:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    function updateTimeline() {
        let el = mediaType === 'video' ? sourceVideo : (mediaType === 'audio' ? sourceAudio : null);
        if (!el || !el.duration) return;

        currentTimeDisplay.textContent = formatTime(el.currentTime);
        durationTimeDisplay.textContent = formatTime(el.duration);
        seekSlider.value = (el.currentTime / el.duration) * 100;
    }

    seekSlider.addEventListener('input', () => {
        let el = mediaType === 'video' ? sourceVideo : (mediaType === 'audio' ? sourceAudio : null);
        if (el && el.duration) {
            el.currentTime = (seekSlider.value / 100) * el.duration;
        }
    });

    // --- MEDIA FILE INGESTION WITH CLEAN UNLIMITED SWAPPING ---
    function handleFile(file) {
        if (!file) return;
        console.log('%c[MEDIA FILE LOADED]', 'color: #ff3344; font-weight: bold; font-size: 13px;', file.name, file.type);
        currentFile = file;

        // 1. CLEAN RESET of all prior active playback & animation loops
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
        }

        if (sourceVideo) {
            sourceVideo.pause();
            sourceVideo.src = '';
            sourceVideo.load(); // flush error state; a Code 4 may fire here — suppressed below
        }
        if (sourceAudio) {
            sourceAudio.pause();
            sourceAudio.src = '';
            sourceAudio.load();
        }
        if (sourceImage) {
            sourceImage.removeAttribute('src');
        }

        _suppressNextVideoError = true; // the empty-src load fires Code 4 — ignore it
        setTimeout(() => { _suppressNextVideoError = false; }, 500);

        // Release any existing wake lock when swapping files
        if (_wakeLock) { try { _wakeLock.release(); } catch(e) {} _wakeLock = null; }

        // Reset state variables
        isPlaying = false;
        isAudioBlackout = false;
        targetPitchBend = 1.0;
        currentPitchBend = 1.0;
        frameHistory = [];
        lastCaptureVideoTime = -1;
        lastVideoTimeSeen = 0;
        replayState = null;
        lastReplayBurstTime = -99999;
        outroFiredForThisPlay = false;
        textCandidateBlocks = [];
        lastTextScanTime = 0;
        memoryEntities = [];
        insertedEntities = [];
        globalDecayLevel = 0;
        _lastEntityDecayTime = 0;
        trackedFaces = [];
        lastFaceScanTime = 0;

        // Clear canvas
        ctx.clearRect(0, 0, glitchCanvas.width, glitchCanvas.height);

        const reader = new FileReader();
        reader.onload = (e) => {
            rawAudioArrayBuffer = e.target.result;
        };
        reader.readAsArrayBuffer(file);

        const url = URL.createObjectURL(file);
        const ext = file.name.split('.').pop().toLowerCase();
        const type = file.type;

        uploadPlaceholder.style.display = 'none';
        btnPlayPause.disabled = false;
        btnMute.disabled = false;
        btnSnapshotImage.disabled = false;
        btnProcessFullFile.disabled = false;
        seekSlider.disabled = false;

        mediaTitle.textContent = `MONITORING: ${file.name.toUpperCase()}`;

        // Generate fresh seed for every new file upload so preview matches export
        resetSeed();
        frameCount = 0;

        const isVideo = type.startsWith('video/') || ['avi', 'mp4', 'mkv', 'mov', 'webm', 'ogv', 'm4v', '3gp', 'qt'].includes(ext);
        const isAudio = type.startsWith('audio/') || ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(ext);
        const isImage = type.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'].includes(ext);

        if (isVideo) {
            console.log('[DEBUG] Mode set to VIDEO');
            mediaType = 'video';
            sourceVideo.src = url;

            let videoLoadedSuccessfully = false;

            const handleCodecError = (reason) => {
                if (videoLoadedSuccessfully) return;
                uploadPlaceholder.style.display = 'flex';
                btnPlayPause.disabled = true;
                btnProcessFullFile.disabled = true;
                addLog(`PHONE VIDEO CODEC ALERT: '${file.name}' uses HEVC / H.265 (iPhone/Android default) or an unsupported codec.`, 'danger');
                alert(`⚠️ UNABLE TO LOAD PHONE VIDEO ⚠️\n\n'${file.name}' is recorded in HEVC / H.265 (default high-efficiency format on iPhone & Android).\n\nDesktop Chrome & Windows Media Engine cannot decode HEVC/H.265 natively without paid OS extensions.\n\n💡 HOW TO FIX:\n1. On iPhone: Settings ➔ Camera ➔ Formats ➔ select 'Most Compatible' (H.264 MP4).\n2. On Android: Camera Settings ➔ Video format ➔ select 'H.264 / Standard MP4'.\n3. Or convert this file to standard H.264 MP4 using any free online converter.`);
            };

            const videoLoadTimeout = setTimeout(() => {
                if (!videoLoadedSuccessfully && sourceVideo.readyState < 1) {
                    handleCodecError('timeout');
                }
            }, 3500);

            const onVideoMetadata = () => {
                videoLoadedSuccessfully = true;
                clearTimeout(videoLoadTimeout);
                let vw = sourceVideo.videoWidth || 1920;
                let vh = sourceVideo.videoHeight || 1080;
                glitchCanvas.width = vw;
                glitchCanvas.height = vh;
                distortionSchedule = generateDistortionSchedule(sourceVideo.duration || 10);
                mriScanStartTime = performance.now();
                mriScanEndTime = mriScanStartTime + 1800; // 1.8s ASYNC MRI scan sweep
                addLog(`[ASYNC SCANNER] Initialized MRI analysis sweep on target '${file.name}'`, 'normal');

                // Wake lock: keep screen awake during video processing (mobile)
                if ('wakeLock' in navigator) {
                    navigator.wakeLock.request('screen').then(wl => {
                        _wakeLock = wl;
                        _wakeLock.addEventListener('release', () => { _wakeLock = null; });
                    }).catch(() => {});
                }

                // Audio nodes set up here — AFTER metadata is confirmed healthy
                setupAudioNodesForSource(sourceVideo);

                // Seek to first frame and paint it immediately
                try { sourceVideo.currentTime = 0.05; } catch (e) {}

                // Paint on seeked (works even before play starts)
                // Entity Memory Model scan runs AFTER the first real frame is on the canvas
                const firstFramePaint = () => {
                    try {
                        const blitCtx = getVideoBlitCtx(vw, vh);
                        blitCtx.drawImage(sourceVideo, 0, 0, vw, vh);
                        ctx.drawImage(_videoBlitCanvas, 0, 0);
                    } catch(e) { try { ctx.drawImage(sourceVideo, 0, 0, vw, vh); } catch(e2) {} }
                    // NOW the canvas has real pixels — scan for entities
                    initializeMemoryEntities(vw, vh);
                    // Also schedule a rescan 2s into playback (better pixel data, scene has changed)
                    setTimeout(() => {
                        if (mediaType === 'video' && memoryEntities.length < 4) {
                            addLog('[ENTITY MEMORY ENGINE] Rescanning for entities with live frame data...', 'normal');
                            initializeMemoryEntities(vw, vh);
                        }
                    }, 2000);
                };
                sourceVideo.addEventListener('seeked', firstFramePaint, { once: true });

                sourceVideo.play().then(() => {
                    isPlaying = true;
                    playIcon.textContent = '⏸';
                    playText.textContent = 'PAUSE';
                    addLog('Video playback started.', 'normal');
                }).catch(err => {
                    console.warn('[AUTOPLAY] Video play paused/blocked by browser:', err);
                    isPlaying = false;
                    playIcon.textContent = '▶';
                    playText.textContent = 'PLAY';
                    if (err && err.name === 'NotSupportedError') {
                        handleCodecError('NotSupportedError');
                    } else {
                        addLog('Click PLAY to start video playback.', 'normal');
                    }
                });
            };

            sourceVideo.addEventListener('error', () => handleCodecError('element_error'), { once: true });

            if (sourceVideo.readyState >= 1 && sourceVideo.videoWidth > 0) {
                onVideoMetadata();
            } else {
                sourceVideo.addEventListener('loadedmetadata', onVideoMetadata, { once: true });
                sourceVideo.addEventListener('loadeddata', onVideoMetadata, { once: true });
            }
            sourceVideo.load();
            addLog(`Loaded Video File: ${file.name}`, 'normal');
        } else if (isAudio) {
            console.log('[DEBUG] Mode set to AUDIO');
            mediaType = 'audio';
            sourceAudio.src = url;
            sourceAudio.load();
            setupAudioNodesForSource(sourceAudio);
            sourceAudio.addEventListener('loadedmetadata', () => {
                distortionSchedule = generateDistortionSchedule(sourceAudio.duration || 10);
                scheduleIndex = 0;
                // Entity Memory Model: audio has no visual frame but initialize with display canvas dims
                initializeMemoryEntities(glitchCanvas.width || 800, glitchCanvas.height || 400);
                // Wake lock for audio processing
                if ('wakeLock' in navigator) {
                    navigator.wakeLock.request('screen').then(wl => {
                        _wakeLock = wl;
                        _wakeLock.addEventListener('release', () => { _wakeLock = null; });
                    }).catch(() => {});
                }
            }, { once: true });
            addLog(`Loaded Audio File: ${file.name}`, 'normal');
        } else if (isImage) {
            console.log('[DEBUG] Mode set to STATIC IMAGE');
            mediaType = 'image';
            btnPlayPause.disabled = true;
            seekSlider.disabled = true;
            addLog(`Loaded Image File: ${file.name}`, 'normal');
            processStaticImage(file);
            return; // STOP animation loop for images!
        }

        if (!animFrameId) {
            renderFrame(performance.now());
        }
    }

    sourceVideo.addEventListener('error', () => {
        if (_suppressNextVideoError) return;
        const err = sourceVideo.error;
        if (!sourceVideo.src || sourceVideo.src === window.location.href) return; // ignore empty/cleared src resets
        let errorMsg = `DECODE ALERT: Browser HTML5 media engine failed to decode video file (Code ${err ? err.code : 'unknown'}).`;
        if (err && (err.code === 4 || err.code === 3)) {
            errorMsg = `DECODE ALERT: Video format/codec not supported by browser (e.g., H.265/HEVC MP4 from Pixel/iPhone). Please convert to standard H.264 AVC MP4.`;
        }
        addLog(errorMsg, 'danger');
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadPlaceholder.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        uploadPlaceholder.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadPlaceholder.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    uploadPlaceholder.addEventListener('click', () => {
        fileInput.click();
    });

    // Control bar "LOAD MEDIA" button
    if (btnUploadControl) {
        btnUploadControl.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            fileInput.click();
        });
    }

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    });

    btnPlayPause.addEventListener('click', () => {
        if (isPlaying) {
            isPlaying = false;
            try {
                if (mediaType === 'video' && sourceVideo && sourceVideo.src) sourceVideo.pause();
                if (mediaType === 'audio' && sourceAudio && sourceAudio.src) sourceAudio.pause();
            } catch (e) {}
            playIcon.textContent = '▶';
            playText.textContent = 'PLAY';
            addLog('Playback paused.', 'normal');
            // Echo-fade on pause: freeze frame ghost that decays over 1.5s
            if (mediaType === 'video' && mainGainNode && audioCtx) {
                mainGainNode.gain.setTargetAtTime(0.0, audioCtx.currentTime + 0.05, 0.35);
            }
        } else {
            if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
            // Restore audio gain after echo-fade pause
            if (mainGainNode && audioCtx) mainGainNode.gain.setTargetAtTime(1.0, audioCtx.currentTime, 0.15);
            let playPromise = null;
            try {
                if (mediaType === 'video' && sourceVideo && sourceVideo.src && sourceVideo.readyState >= 1) playPromise = sourceVideo.play();
                else if (mediaType === 'audio' && sourceAudio && sourceAudio.src && sourceAudio.readyState >= 1) playPromise = sourceAudio.play();
            } catch (e) {
                console.warn('[PLAYBACK ERROR]', e);
            }

            if (playPromise) {
                playPromise.then(() => {
                    isPlaying = true;
                    playIcon.textContent = '⏸';
                    playText.textContent = 'PAUSE';
                    addLog('Playback resumed.', 'normal');
                }).catch(err => {
                    isPlaying = false;
                    playIcon.textContent = '▶';
                    playText.textContent = 'PLAY';
                    console.warn('[PLAYBACK ERROR]', err);
                    addLog(`PLAYBACK NOTICE: ${err.message || 'Media pending load'}.`, 'warning');
                });
            }
        }
    });

    btnMute.addEventListener('click', () => {
        isMuted = !isMuted;
        if (sourceVideo) sourceVideo.muted = isMuted;
        if (sourceAudio) sourceAudio.muted = isMuted;
        btnMute.textContent = isMuted ? '🔇' : '🔊';
    });

    btnSnapshotImage.addEventListener('click', () => {
        const dataUrl = glitchCanvas.toDataURL('image/png');
        previewMediaContainer.innerHTML = `<img src="${dataUrl}" alt="Corrupted Frame Snapshot">`;
        btnDownloadPayload.href = dataUrl;
        btnDownloadPayload.download = `MISREMEMBERED_SNAPSHOT_${Date.now()}.png`;
        previewSubtext.textContent = 'PNG Image Snapshot captured from reconstruction canvas.';
        previewCard.style.display = 'flex';
        addLog('SNAPSHOT CAPTURED: Saved to preview card.', 'alert');
    });

    btnClosePreview.addEventListener('click', () => {
        previewCard.style.display = 'none';
        previewMediaContainer.innerHTML = '';
    });

    // --- AUTOMATED BATCH FULL-FILE PROCESSOR & DOWNLOADER ---
    btnProcessFullFile.addEventListener('click', async () => {
        if (!currentFile && mediaType !== 'audio') return;

        initAudioContext();
        isBatchExporting = true;
        processingOverlay.style.display = 'flex';
        processingProgressBar.style.width = '0%';
        processingPercentText.textContent = '0%';
        processingTitle.textContent = `PROCESSING ENTIRE ${mediaType.toUpperCase()} FILE...`;
        processingSubtitle.textContent = 'Applying Audio Pitch Drift, Feature Duplication & Reality Shifts';

        // Show tab focus / wake lock reminder
        const processingTip = document.getElementById('processingTip');
        if (processingTip) processingTip.style.display = 'flex';

        addLog(`BATCH EXPORT STARTED: Processing entire ${mediaType.toUpperCase()} file...`, 'danger');

        if (mediaType === 'audio') {
            await processFullAudioFile();
        } else if (mediaType === 'video') {
            await processFullVideoFile();
        } else if (mediaType === 'image') {
            await processFullImageFile();
        }

        // Hide tip once done
        if (processingTip) processingTip.style.display = 'none';
        // Release wake lock now that encoding is done
        if (_wakeLock) { try { _wakeLock.release(); } catch(e) {} _wakeLock = null; }
    });

    async function processFullAudioFile() {
        try {
            let bufferToProcess = null;

            if (rawAudioArrayBuffer) {
                bufferToProcess = await audioCtx.decodeAudioData(rawAudioArrayBuffer.slice(0));
            } else if (sourceAudio.src) {
                const resp = await fetch(sourceAudio.src);
                const ab = await resp.arrayBuffer();
                bufferToProcess = await audioCtx.decodeAudioData(ab);
            }

            if (!bufferToProcess) throw new Error('Audio buffer unavailable');

            const sampleRate = bufferToProcess.sampleRate;
            const length = bufferToProcess.length;
            const duration = bufferToProcess.duration;

            processingProgressBar.style.width = '25%';
            processingPercentText.textContent = '25%';

            const OfflineCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
            const offlineCtx = new OfflineCtx(2, length, sampleRate);

            const srcNode = offlineCtx.createBufferSource();
            srcNode.buffer = bufferToProcess;

            const shaperNode = offlineCtx.createWaveShaper();
            shaperNode.curve = createDistortionCurve(60);

            const filtNode = offlineCtx.createBiquadFilter();
            filtNode.type = 'lowpass';
            filtNode.frequency.value = 1800;

            const mainG = offlineCtx.createGain();
            mainG.gain.value = 1.0;

            const dropoutFreq = getSliderValue(audioDropoutsSlider, 75) / 100;
            if (dropoutFreq > 0) {
                for (let t = 2; t < duration - 2; t += 4 + Math.random() * 4) {
                    if (Math.random() < dropoutFreq) {
                        mainG.gain.setValueAtTime(0.0, t);
                        mainG.gain.setValueAtTime(1.0, t + 0.8 + Math.random() * 0.8);
                    }
                }
            }

            const panner = offlineCtx.createStereoPanner ? offlineCtx.createStereoPanner() : offlineCtx.createPanner();

            const revDelay1 = offlineCtx.createDelay(2.0); revDelay1.delayTime.value = 0.18;
            const revDelay2 = offlineCtx.createDelay(2.0); revDelay2.delayTime.value = 0.42;
            const revFeedback = offlineCtx.createGain(); revFeedback.gain.value = 0.65;
            const revGain = offlineCtx.createGain(); revGain.gain.value = (getSliderValue(liminalReverbSlider, 85)) / 100;

            revDelay1.connect(revDelay2);
            revDelay2.connect(revFeedback);
            revFeedback.connect(revDelay1);
            revDelay2.connect(revGain);

            const gainComp = offlineCtx.createGain();
            gainComp.gain.value = (getSliderValue(audioGainBoostSlider, 150)) / 100;

            const comp = offlineCtx.createDynamicsCompressor();
            comp.threshold.value = -24; comp.knee.value = 30; comp.ratio.value = 12;

            srcNode.connect(shaperNode);
            shaperNode.connect(filtNode);
            filtNode.connect(mainG);
            mainG.connect(panner);
            filtNode.connect(revDelay1);
            revGain.connect(panner);

            panner.connect(gainComp);
            gainComp.connect(comp);
            comp.connect(offlineCtx.destination);

            const pitchVal = getSliderValue(pitchDriftSlider, 80) / 100;
            const masterVal = getSliderValue(masterIntensitySlider, 85) / 100;
            
            // DETERMINISTIC AUDIO EXPORT: consume the seeded distortionSchedule
            for (const ev of distortionSchedule) {
                if (ev.time >= duration) continue;

                if (ev.type === 'pitch') {
                    const actualRate = 1.0 + (ev.rate - 1.0) * pitchVal * masterVal;
                    srcNode.playbackRate.setValueAtTime(Math.max(0.25, Math.min(2.2, actualRate)), ev.time);
                } else if (ev.type === 'blackout') {
                    mainG.gain.setValueAtTime(0.0, ev.time);
                    mainG.gain.setValueAtTime(1.0, Math.min(duration, ev.time + ev.duration));
                } else if (ev.type === 'reverb') {
                    if (ev.active) {
                        revGain.gain.setValueAtTime((getSliderValue(liminalReverbSlider, 85) / 100) * ev.level, ev.time);
                    } else {
                        revGain.gain.setValueAtTime(0.0, ev.time);
                    }
                }
            }

            const spatialVal = getSliderValue(spatialTeleportSlider, 80) / 100;
            if (panner.pan) {
                for (let t = 0; t < duration; t += 0.5) {
                    panner.pan.setValueAtTime(Math.sin(t * 1.5) * spatialVal, t);
                }
            }

            srcNode.start(0);

            processingProgressBar.style.width = '60%';
            processingPercentText.textContent = '60%';

            const renderedBuffer = await offlineCtx.startRendering();

            processingProgressBar.style.width = '90%';
            processingPercentText.textContent = '90%';

            const wavBlob = bufferToWav(renderedBuffer);
            const downloadUrl = URL.createObjectURL(wavBlob);

            const fileName = misrememberFilename(currentFile ? currentFile.name : 'AUDIO', '.wav');

            triggerDownload(downloadUrl, fileName);

            previewMediaContainer.innerHTML = `<audio src="${downloadUrl}" controls style="width:100%;"></audio>`;
            btnDownloadPayload.href = downloadUrl;
            btnDownloadPayload.download = fileName;
            previewSubtext.textContent = 'Entire audio rendered with pitch drift, blackouts & memory whisper.';
            previewCard.style.display = 'flex';

            processingOverlay.style.display = 'none';
            isBatchExporting = false;
            addLog(`BATCH AUDIO COMPLETE: ${fileName}`, 'alert');

        } catch (e) {
            processingOverlay.style.display = 'none';
            isBatchExporting = false;
            addLog(`AUDIO BATCH ERROR: ${e.message}`, 'danger');
        }
    }

    function patchMp4Timescale(arrayBuffer, speedMult) {
        if (!arrayBuffer || arrayBuffer.byteLength < 32) return arrayBuffer;
        const view = new DataView(arrayBuffer);
        const bytes = new Uint8Array(arrayBuffer);
        for (let i = 0; i < bytes.length - 12; i++) {
            if (bytes[i] === 0x6D && bytes[i+1] === 0x76 && bytes[i+2] === 0x68 && bytes[i+3] === 0x64) { // 'mvhd'
                const version = bytes[i + 4];
                const tsOffset = version === 0 ? i + 16 : i + 24;
                try {
                    const origTs = view.getUint32(tsOffset, false);
                    if (origTs > 0 && origTs < 1000000) {
                        const newTs = Math.max(1, Math.round(origTs / speedMult));
                        view.setUint32(tsOffset, newTs, false);
                    }
                } catch (e) {}
                break;
            }
        }
        return arrayBuffer;
    }

    async function processFullVideoFile() {
        if (!sourceVideo || !sourceVideo.duration) {
            processingOverlay.style.display = 'none';
            isBatchExporting = false;
            return;
        }

        const totalDuration = sourceVideo.duration;

        // Reset schedule to start from beginning so export matches preview
        scheduleIndex = 0;
        currentPitchBend = 1.0;
        targetPitchBend = 1.0;
        isAudioBlackout = false;
        targetLevelMult = 1.0;
        currentLevelMult = 1.0;
        coherenceSpike = 0;

        recordedChunks = [];
        const canvasStream = glitchCanvas.captureStream(30);

        let combinedStream = canvasStream;
        if (streamDestination && streamDestination.stream && streamDestination.stream.getAudioTracks().length > 0) {
            combinedStream = new MediaStream([
                ...canvasStream.getVideoTracks(),
                ...streamDestination.stream.getAudioTracks()
            ]);
        }

        // MP4 export — try H.264/AAC first (Chrome 130+ on Windows supports it natively)
        // Fall back to WebM only if MP4 is truly unsupported, but always save as .mp4
        const candidateMimes = [
            'video/mp4;codecs=avc1.42E01E,mp4a.40.2',
            'video/mp4;codecs=avc1,mp4a.40.2',
            'video/mp4;codecs=h264,aac',
            'video/mp4',
            'video/webm;codecs=vp9,opus',
            'video/webm'
        ];
        const chosenMime = candidateMimes.find(t => {
            try { return MediaRecorder.isTypeSupported(t); } catch(e) { return false; }
        }) || '';

        // Export at real-time (1.0×) — faster export causes frame drops → stuttery output
        const EXPORT_SPEED_MULT = 1.0;

        try {
            // 8 Mbps video bitrate: high enough that the encoder doesn't introduce its own stutter
            mediaRecorder = new MediaRecorder(combinedStream, {
                mimeType: chosenMime,
                videoBitsPerSecond: 8_000_000
            });
        } catch (e) {
            mediaRecorder = new MediaRecorder(combinedStream, { videoBitsPerSecond: 8_000_000 });
        }

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) recordedChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            sourceVideo.loop = true;
            sourceVideo.playbackRate = 1.0;

            // Use the actual recorded mime type for the blob so the container is correct
            const actualMime = mediaRecorder.mimeType || chosenMime || 'video/mp4';
            const finalBlob = new Blob(recordedChunks, { type: actualMime });

            const downloadUrl = URL.createObjectURL(finalBlob);
            // Always name .mp4 — on Chrome 130+ Windows this is genuinely H.264 MP4;
            // on older browsers it's still WebM bytes in an .mp4 wrapper but that's
            // unavoidable without ffmpeg.wasm transcoding.
            const fileName = misrememberFilename(currentFile ? currentFile.name : 'VIDEO', '.mp4');

            triggerDownload(downloadUrl, fileName);

            previewMediaContainer.innerHTML = `<video src="${downloadUrl}" controls style="max-width:100%; max-height:280px;"></video>`;
            btnDownloadPayload.href = downloadUrl;
            btnDownloadPayload.download = fileName;
            previewSubtext.textContent = `Full distorted video — ${actualMime.includes('mp4') ? 'MP4 H.264' : 'WebM'} — complete.`;
            previewCard.style.display = 'flex';

            processingOverlay.style.display = 'none';
            isBatchExporting = false;
            addLog(`BATCH VIDEO COMPLETE: Saved as MP4 — seed ${currentSeed.toString(16).toUpperCase()}`, 'alert');
        };

        function stopExportRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
        }

        // --- 1.0x REAL-TIME EXPORT ---
        // Guarantees 100% valid MP4 container with seekable index and true video length
        sourceVideo.loop = false;
        sourceVideo.currentTime = 0;
        sourceVideo.playbackRate = 1.0;
        isPlaying = true;
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();

        await new Promise(resolve => {
            const onSeeked = () => { sourceVideo.removeEventListener('seeked', onSeeked); resolve(); };
            sourceVideo.addEventListener('seeked', onSeeked, { once: true });
            setTimeout(resolve, 200);
        });

        if (processingTimeText) processingTimeText.textContent = `Recording ~${Math.ceil(totalDuration)}s of video...`;
        processingSubtitle.textContent = `EXPORTING FULL VIDEO • SEED: ${currentSeed.toString(16).toUpperCase()} • Format: MP4`;

        mediaRecorder.start(500);
        try {
            await sourceVideo.play();
        } catch (playErr) {
            console.warn('[EXPORT] Video play warning:', playErr);
        }

        sourceVideo.addEventListener('ended', stopExportRecording, { once: true });

        const watchdogInterval = setInterval(() => {
            if (!isBatchExporting) { clearInterval(watchdogInterval); return; }
            const pct = Math.floor((sourceVideo.currentTime / totalDuration) * 100);
            processingProgressBar.style.width = `${pct}%`;
            processingPercentText.textContent = `${pct}%`;
            const remainingSecs = Math.max(0, totalDuration - sourceVideo.currentTime);
            if (processingTimeText) {
                processingTimeText.textContent = `Processing • ~${Math.ceil(remainingSecs)}s remaining`;
            }
            if (remainingSecs <= 0.1 || sourceVideo.ended || sourceVideo.paused) {
                clearInterval(watchdogInterval);
                setTimeout(stopExportRecording, 500);
            }
        }, 300);
    }

    async function processFullImageFile() {
        processingProgressBar.style.width = '100%';
        processingPercentText.textContent = '100%';

        setTimeout(() => {
            const dataUrl = glitchCanvas.toDataURL('image/png');
            const fileName = misrememberFilename(currentFile ? currentFile.name : 'IMAGE', '.png');

            triggerDownload(dataUrl, fileName);

            previewMediaContainer.innerHTML = `<img src="${dataUrl}" alt="Misremembered Image">`;
            btnDownloadPayload.href = dataUrl;
            btnDownloadPayload.download = fileName;
            previewSubtext.textContent = 'Static image rendered with feature duplication & angled displacement.';
            previewCard.style.display = 'flex';

            processingOverlay.style.display = 'none';
            isBatchExporting = false;
            addLog(`BATCH IMAGE COMPLETE: ${fileName}`, 'alert');
        }, 400);
    }

    function triggerDownload(url, filename) {
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => document.body.removeChild(a), 150);
    }

    // --- SYNTHESIZE DEMO ---
    btnSynthesizeDemo.addEventListener('click', () => {
        initAudioContext();
        addLog('Synthesizing Liminal Space Anomaly Buffer...', 'alert');

        const sampleRate = audioCtx.sampleRate;
        const duration = 12;
        const buffer = audioCtx.createBuffer(2, sampleRate * duration, sampleRate);

        for (let channel = 0; channel < 2; channel++) {
            const data = buffer.getChannelData(channel);
            for (let i = 0; i < data.length; i++) {
                const t = i / sampleRate;
                const freq1 = 220 + Math.sin(t * 0.5) * 3;
                const freq2 = 261.63 + Math.cos(t * 0.7) * 4;
                const freq3 = 329.63 + Math.sin(t * 1.1) * 6;

                let sample = (Math.sin(2 * Math.PI * freq1 * t) * 0.35 +
                              Math.sin(2 * Math.PI * freq2 * t) * 0.3 +
                              Math.sin(2 * Math.PI * freq3 * t) * 0.25) * 0.5;

                if (Math.random() < 0.003) {
                    sample += (Math.random() - 0.5) * 0.8;
                }

                data[i] = sample;
            }
        }

        const wavBlob = bufferToWav(buffer);
        const file = new File([wavBlob], "ANOMALY_RECORDING_0049.WAV", { type: "audio/wav" });
        handleFile(file);
    });

    function bufferToWav(abuffer) {
        const numOfChan = abuffer.numberOfChannels;
        const length = abuffer.length * numOfChan * 2 + 44;
        const buffer = new ArrayBuffer(length);
        const view = new DataView(buffer);
        let channels = [], i, sample, offset = 0, pos = 0;

        function setUint16(data) { view.setUint16(pos, data, true); pos += 2; }
        function setUint32(data) { view.setUint32(pos, data, true); pos += 4; }

        setUint32(0x46464952); setUint32(length - 8); setUint32(0x45564157);
        setUint32(0x20746d66); setUint32(16); setUint16(1); setUint16(numOfChan);
        setUint32(abuffer.sampleRate); setUint32(abuffer.sampleRate * 2 * numOfChan);
        setUint16(numOfChan * 2); setUint16(16); setUint32(0x61746164); setUint32(length - pos - 4);

        for (i = 0; i < abuffer.numberOfChannels; i++) channels.push(abuffer.getChannelData(i));

        while (offset < abuffer.length) {
            for (i = 0; i < numOfChan; i++) {
                sample = Math.max(-1, Math.min(1, channels[i][offset]));
                sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
                view.setInt16(pos, sample, true);
                pos += 2;
            }
            offset++;
        }
        return new Blob([buffer], { type: "audio/wav" });
    }

    // --- SLIDER EVENT HANDLERS ---
    function bindSlider(slider, badge, unit = '%', fn = null) {
        if (!slider || !badge) return;
        slider.addEventListener('input', () => {
            badge.textContent = `${slider.value}${unit}`;
            if (fn) fn(slider.value);
        });
    }

    bindSlider(masterIntensitySlider, masterIntensityVal, '%');
    bindSlider(audioDropoutsSlider, audioDropoutsVal, '%');
    bindSlider(pitchDriftSlider, pitchDriftVal, '%');
    bindSlider(spatialTeleportSlider, spatialTeleportVal, '%');
    bindSlider(compressionDistortSlider, compressionDistortVal, '%', (val) => updateWaveShaperCurve(val));
    bindSlider(phonemeStutterSlider, phonemeStutterVal, '%', (val) => {
        if (voiceDoubleGain) voiceDoubleGain.gain.value = (parseInt(val) / 100) * 0.5;
    });
    bindSlider(entityWhispersSlider, entityWhispersVal, '% [ACTIVE]', (val) => {
        if (whisperGain) whisperGain.gain.value = (parseInt(val) / 100) * 0.45;
    });
    bindSlider(liminalReverbSlider, liminalReverbVal, '% [CAVERN]', (val) => {
        if (reverbGain) reverbGain.gain.value = parseInt(val) / 100;
    });
    bindSlider(audioGainBoostSlider, audioGainBoostVal, '% [COMP]', (val) => {
        if (agcGainNode) agcGainNode.gain.value = parseInt(val) / 100;
    });
    bindSlider(flawedMirroringSlider, flawedMirroringVal, '%');
    bindSlider(chromaticAberrationSlider, chromaticVal, 'px');
    bindSlider(pixelSliceSlider, pixelSliceVal, '%');

    addLog('Misremembered Media Engine ready. Console debug statements active.', 'normal');
    console.log('%c[MISREMEMBERED MEDIA] Ready for media upload & processing.', 'color: #00ff66; font-weight: bold;');
});
