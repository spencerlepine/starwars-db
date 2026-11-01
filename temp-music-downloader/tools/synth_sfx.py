#!/usr/bin/env python3
"""Procedurally synthesize Star Wars-style reference sound effects.

These are original, self-made sounds (no samples), written to evoke the
signature sounds of the saga: lightsaber hum/ignite/swing/clash/retract,
"guy-wire" blaster bolts, astromech droid chatter, hyperspace jumps and a
starfighter fly-by howl. They are free to use in the game.

usage: tools/synth_sfx.py [OUT_DIR]   (default: sfx/synth)
Writes 44.1 kHz mono .wav, and .ogg too when ffmpeg is available.
Deterministic: a fixed seed per sound, so re-running gives identical files.
"""
import shutil, subprocess, sys, wave
from pathlib import Path

import numpy as np

SR = 44100
ROOT = Path(__file__).resolve().parent.parent


def t(dur):
    return np.arange(int(dur * SR)) / SR


def osc(freq, dur=None, kind="sin", phase=0.0):
    """Oscillator with a constant or per-sample frequency array."""
    f = np.full(int(dur * SR), float(freq)) if np.isscalar(freq) else np.asarray(freq, float)
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == "sin":
        return np.sin(ph)
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1
    raise ValueError(kind)


def band(x, lo, hi):
    """Brick-wall band-pass via FFT (fine for offline SFX)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def lowpass(x, hz):
    return band(x, 0, hz)


def env_adsr(n, a=0.01, d=0.05, s=0.8, r=0.1):
    a, d, r = (max(1, int(v * SR)) for v in (a, d, r))
    s_len = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a), np.linspace(1, s, d), np.full(s_len, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def fade(x, ms=8):
    n = int(ms / 1000 * SR)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


# --- lightsaber ---------------------------------------------------------

def saber_core(dur, base=92.0, rng=None, wobble=0.0):
    """Projector-motor hum: detuned buzz pair + harmonics + a little hiss."""
    rng = rng or np.random.default_rng(0)
    n = int(dur * SR)
    tt = t(dur)
    drift = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * tt) + wobble
    f = base * drift
    x = 0.55 * osc(f, kind="saw") + 0.45 * osc(f * 1.012, kind="saw")
    x += 0.35 * osc(f * 2, kind="sin") + 0.18 * osc(f * 3.01, kind="sin")
    x = lowpass(x, 1800)
    hiss = band(rng.standard_normal(n), 2500, 7000) * 0.05
    # slow "beating" amplitude like the old TV-set interference
    am = 0.85 + 0.15 * np.sin(2 * np.pi * 1.4 * tt)
    return (x * am + hiss)[:n]


def lightsaber_hum(dur=4.0):
    return fade(norm(saber_core(dur), 0.7), 60)


def lightsaber_ignite():
    rng = np.random.default_rng(1)
    dur = 1.6
    n = int(dur * SR)
    tt = t(dur)
    sweep = np.clip(tt / 0.35, 0, 1)
    pitch = 1 - 0.55 * (1 - sweep) ** 2          # pitch rises into the hum
    core = saber_core(dur, rng=rng, wobble=pitch - 1)
    snap = band(rng.standard_normal(n), 300, 6000) * np.exp(-tt / 0.06)
    crackle = band(rng.standard_normal(n), 1500, 9000) * np.exp(-tt / 0.25) * 0.4
    vol = np.clip(tt / 0.12, 0, 1) * np.where(tt > dur - 0.4, (dur - tt) / 0.4, 1)
    return fade(norm(core * vol * 0.8 + snap * 0.9 + crackle))


def lightsaber_retract():
    x = lightsaber_ignite()[::-1].copy()
    return fade(norm(x))


def lightsaber_swing(seed=2, speed=1.0):
    rng = np.random.default_rng(seed)
    dur = 0.9 / speed
    tt = t(dur)
    mid = dur * rng.uniform(0.4, 0.55)
    bump = np.exp(-((tt - mid) / (0.16 / speed)) ** 2)          # blade passes the "mic"
    doppler = 1 + 0.35 * np.tanh((mid - tt) * 9 * speed) * bump
    core = saber_core(dur, base=95, rng=rng, wobble=doppler - 1)
    whoosh = band(rng.standard_normal(len(tt)), 200, 2500) * bump * 0.5
    return fade(norm(core * (0.35 + 0.9 * bump) + whoosh), 20)


def lightsaber_clash(seed=3):
    rng = np.random.default_rng(seed)
    dur = 1.1
    n = int(dur * SR)
    tt = t(dur)
    burst = band(rng.standard_normal(n), 400, 9000) * np.exp(-tt / 0.09)
    sparks = (rng.random(n) < 0.004) * rng.standard_normal(n) * np.exp(-tt / 0.3)
    sparks = band(sparks, 2000, 12000) * 6
    ring = (osc(1430, dur) + 0.6 * osc(2210, dur) + 0.3 * osc(3390, dur)) * np.exp(-tt / 0.18) * 0.35
    hum = saber_core(dur, base=104, rng=rng) * np.exp(-tt / 0.6) * 0.5
    return fade(norm(burst + sparks + ring + hum))


# --- blasters -----------------------------------------------------------

def blaster(seed=4, f0=3800.0, f1=420.0, dur=0.42, ring=0.35):
    """Struck-guy-wire style 'pew': dispersive downward chirp + metallic ring."""
    rng = np.random.default_rng(seed)
    tt = t(dur)
    k = np.log(f0 / f1) / dur
    f = f0 * np.exp(-k * tt * rng.uniform(1.0, 1.3))
    chirp = osc(f) + 0.5 * osc(f * 1.5 + rng.uniform(-30, 30)) + 0.25 * osc(f * 0.5)
    env = np.exp(-tt / (dur * 0.35)) * np.clip(tt / 0.003, 0, 1)
    metal = (osc(f1 * 4.1, dur) + osc(f1 * 6.3, dur)) * np.exp(-tt / 0.12) * ring
    zap = band(rng.standard_normal(len(tt)), 2000, 8000) * np.exp(-tt / 0.02) * 0.4
    return fade(norm(chirp * env + metal * env + zap), 4)


def blaster_heavy():
    a = blaster(seed=5, f0=2400, f1=180, dur=0.6, ring=0.5)
    rng = np.random.default_rng(5)
    tt = t(0.6)
    thump = osc(70 * np.exp(-tt * 4), kind="sin") * np.exp(-tt / 0.15)
    tail = lowpass(rng.standard_normal(len(tt)), 900) * np.exp(-tt / 0.2) * 0.3
    return fade(norm(a + thump * 0.9 + tail))


# --- droids -------------------------------------------------------------

def droid_chatter(seed=6, syllables=7):
    """Astromech-style whistles: glides, trills and warbles between notes."""
    rng = np.random.default_rng(seed)
    parts = []
    for _ in range(syllables):
        kind = rng.choice(["glide", "trill", "blip", "warble"], p=[0.35, 0.25, 0.25, 0.15])
        d = {"glide": rng.uniform(0.12, 0.3), "trill": rng.uniform(0.15, 0.3),
             "blip": rng.uniform(0.04, 0.09), "warble": rng.uniform(0.2, 0.35)}[kind]
        tt = t(d)
        a, b = rng.uniform(900, 3600, 2)
        if kind == "glide":
            f = a * (b / a) ** (tt / d)
        elif kind == "trill":
            f = a * (1 + 0.18 * np.sign(np.sin(2 * np.pi * rng.uniform(18, 30) * tt)))
        elif kind == "warble":
            f = a * (1 + 0.25 * np.sin(2 * np.pi * rng.uniform(6, 12) * tt))
        else:
            f = np.full(len(tt), a)
        x = osc(f) + 0.12 * osc(f * 2)
        x *= env_adsr(len(x), 0.005, 0.02, 0.85, min(0.03, d / 3))
        parts.append(x)
        parts.append(np.zeros(int(rng.uniform(0.0, 0.07) * SR)))
    return fade(norm(np.concatenate(parts), 0.8))


def droid_scream():
    tt = t(0.9)
    f = 4200 - 2600 * (tt / 0.9) ** 0.6
    x = osc(f * (1 + 0.04 * np.sin(2 * np.pi * 22 * tt))) * env_adsr(len(tt), 0.01, 0.1, 0.9, 0.25)
    return fade(norm(x, 0.8))


# --- ships --------------------------------------------------------------

def hyperspace_jump():
    rng = np.random.default_rng(7)
    dur = 2.6
    n = int(dur * SR)
    tt = t(dur)
    rise = np.clip(tt / 1.9, 0, 1) ** 2
    noise = rng.standard_normal(n)
    # sweep a band of noise upwards by mixing several bands with moving weights
    x = sum(band(noise, lo, lo * 1.8) * np.exp(-((rise - i / 6) / 0.12) ** 2)
            for i, lo in enumerate([150, 260, 450, 800, 1400, 2400, 4000]))
    tone = osc(60 + 900 * rise, kind="saw") * 0.15 * rise
    boom_t = np.clip(tt - 1.95, 0, None)
    boom = osc(55 * np.exp(-boom_t * 3)) * np.exp(-boom_t / 0.25) * (tt > 1.95)
    vol = np.where(tt < 1.95, 0.2 + rise, np.exp(-(tt - 1.95) / 0.12))
    return fade(norm(x * vol + tone + boom * 1.2), 30)


def fighter_flyby_howl():
    """Twin-ion-engine style howl: harmonic scream + roar, with doppler."""
    rng = np.random.default_rng(8)
    dur = 2.4
    n = int(dur * SR)
    tt = t(dur)
    mid = 1.1
    closeness = np.exp(-((tt - mid) / 0.45) ** 2)
    doppler = 1 + 0.22 * np.tanh((mid - tt) * 3)
    f = 640 * doppler * (1 + 0.01 * np.sin(2 * np.pi * 7 * tt))
    scream = osc(f, kind="saw") * 0.5 + osc(f * 1.33) * 0.3 + osc(f * 2.02) * 0.2
    scream = band(scream, 300, 5000)
    roar = band(rng.standard_normal(n), 120, 1600) * 0.8
    return fade(norm((scream + roar) * (0.08 + closeness)), 40)


SOUNDS = {
    "lightsaber_hum_loop": lightsaber_hum,
    "lightsaber_ignite": lightsaber_ignite,
    "lightsaber_retract": lightsaber_retract,
    "lightsaber_swing_01": lambda: lightsaber_swing(2, 1.0),
    "lightsaber_swing_02": lambda: lightsaber_swing(12, 1.4),
    "lightsaber_clash_01": lambda: lightsaber_clash(3),
    "lightsaber_clash_02": lambda: lightsaber_clash(13),
    "blaster_bolt_01": lambda: blaster(4),
    "blaster_bolt_02": lambda: blaster(14, f0=4400, f1=520, dur=0.35),
    "blaster_bolt_03": lambda: blaster(24, f0=3200, f1=360, dur=0.5),
    "blaster_heavy_cannon": blaster_heavy,
    "droid_chatter_01": lambda: droid_chatter(6, 7),
    "droid_chatter_02": lambda: droid_chatter(16, 5),
    "droid_chatter_03": lambda: droid_chatter(26, 10),
    "droid_scream": droid_scream,
    "hyperspace_jump": hyperspace_jump,
    "starfighter_flyby_howl": fighter_flyby_howl,
}


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sfx" / "synth"
    out.mkdir(parents=True, exist_ok=True)
    ff = shutil.which("ffmpeg")
    for name, fn in SOUNDS.items():
        x = fn()
        wav = out / f"{name}.wav"
        write_wav(wav, x)
        if ff:
            subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis",
                            "-q:a", "5", str(out / f"{name}.ogg")], check=True)
            wav.unlink()
        print(f"{name}: {len(x) / SR:.2f}s")


if __name__ == "__main__":
    main()
