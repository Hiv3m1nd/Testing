"""Procedural score, sound design and final mix (48 kHz stereo).

Everything is synthesized here: additive string pads, Karplus-Strong plucked
lyre/guqin, inharmonic gongs and singing bowls, frame drums, a breathy ney
flute for Parthia, impacts, whooshes, chisel taps, wind. Cues are placed from
the narration timeline. The music bus is side-chain ducked under the voice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from numba import njit
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt, sosfiltfilt

sys.path.insert(0, str(Path(__file__).parent))
from timeline import TL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
DUR = 173.6
N = int(DUR * SR)
rng = np.random.default_rng(2024)


def hz(note):
    """'D3' / 'Bb2' / 'F#4' -> Hz."""
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[note[0]]
    i = 1
    if note[1] in "#b":
        n += 1 if note[1] == "#" else -1
        i = 2
    octave = int(note[i:])
    return 440.0 * 2 ** ((n + 12 * (octave + 1) - 69) / 12)


def env_adsr(n, a, r, sustain=1.0):
    e = np.ones(n, np.float32) * sustain
    na, nr = int(a * SR), int(r * SR)
    na, nr = min(na, n), min(nr, n)
    if na:
        e[:na] = np.linspace(0, sustain, na) ** 1.5
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def lowpass(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def highpass(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2), np.float32)

    def add(self, t, sig, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], -1)
        i = int(t * SR)
        if i >= N:
            return
        j = min(N, i + len(sig))
        if i < 0:
            sig = sig[-i:]
            i = 0
            j = min(N, len(sig))
        self.x[i:j] += sig[: j - i] * gain


# ----------------------------------------------------------------------------- instruments
def pad(freqs, dur, attack=2.5, release=3.0, bright=0.5, voices=3, detune=0.12):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros((n, 2), np.float32)
    for f in freqs:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) * detune * 12
            ff = f * 2 ** (cents / 1200)
            lfo = 1 + 0.0025 * np.sin(2 * np.pi * (0.13 + 0.05 * v) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * ff * np.cumsum(lfo) / SR
            sig = np.zeros(n, np.float32)
            nh = int(min(14, 7000 / ff))
            for h in range(1, nh + 1):
                sig += (np.sin(h * ph + rng.uniform(0, 6)) * (1 / h) * np.exp(-h * (1 - bright) * 0.45)).astype(np.float32)
            pan = (v / max(1, voices - 1) - 0.5) * 0.9
            out[:, 0] += sig * np.cos((pan + 1) * np.pi / 4)
            out[:, 1] += sig * np.sin((pan + 1) * np.pi / 4)
    out *= env_adsr(n, attack, release)[:, None] / (len(freqs) * voices) * 0.6
    return out


@njit(cache=True)
def _ks(n, period, damp, seed_noise, bright):
    buf = seed_noise[:period].copy()
    out = np.zeros(n, np.float32)
    prev = 0.0
    for i in range(n):
        j = i % period
        x = buf[j]
        out[i] = x
        nxt = buf[(i + 1) % period]
        y = damp * (bright * x + (1 - bright) * 0.5 * (x + nxt))
        y = 0.5 * (y + prev)
        prev = y
        buf[j] = y
    return out


def pluck(f, dur=3.0, damp=0.996, bright=0.4, bend=0.0):
    n = int(dur * SR)
    period = max(2, int(SR / f))
    noise = rng.uniform(-1, 1, period + 2).astype(np.float32)
    noise = np.convolve(noise, np.ones(3) / 3, "same").astype(np.float32)
    sig = _ks(n, period, damp, noise, bright)
    if bend:
        idx = np.arange(n) * (1 + bend * (1 - np.exp(-np.arange(n) / (0.25 * SR))))
        sig = np.interp(np.clip(idx, 0, n - 1), np.arange(n), sig).astype(np.float32)
    sig *= env_adsr(n, 0.002, 0.4)
    return sig * 0.5


def gong(f=90.0, dur=7.0, strike=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    ratios = [1.0, 1.52, 2.03, 2.48, 2.97, 3.56, 4.12, 4.9, 5.73]
    sig = np.zeros(n, np.float32)
    for k, r in enumerate(ratios):
        glide = 1 - 0.006 * np.exp(-t * 2)
        decay = np.exp(-t / (dur * (0.5 - 0.04 * k)))
        swell = 1 - np.exp(-t / (0.05 + 0.06 * k))
        sig += (np.sin(2 * np.pi * f * r * glide * t + rng.uniform(0, 6)) * decay * swell / (1 + k * 0.6)).astype(np.float32)
    hit = lowpass(rng.normal(0, 1, n).astype(np.float32), 900) * np.exp(-t / 0.06)
    return (sig * 0.35 + hit * 0.25 * strike).astype(np.float32)


def bowl(f=660.0, dur=6.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for r, a in [(1, 1.0), (2.71, 0.5), (5.15, 0.25), (8.3, 0.12)]:
        beat = 1 + 0.4 * np.sin(2 * np.pi * (0.8 + r * 0.3) * t)
        sig += (a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dur / (1 + r * 0.4))) * beat).astype(np.float32)
    return sig * env_adsr(n, 0.004, 0.5) * 0.18


def drum(f0=110.0, dur=0.9, tone=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f0 * (0.55 + 0.45 * np.exp(-t / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.22) * tone
    skin = bandpass(rng.normal(0, 1, n).astype(np.float32), 200, 2500) * np.exp(-t / 0.02) * 0.4
    return (body + skin).astype(np.float32) * 0.6


def boom(dur=4.0, f0=62.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f0 * (0.5 + 0.5 * np.exp(-t / 0.4))
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1)
    crack = lowpass(rng.normal(0, 1, n).astype(np.float32), 2500) * np.exp(-t / 0.08)
    tail = lowpass(rng.normal(0, 1, n).astype(np.float32), 400) * np.exp(-t / 1.4) * 0.3
    return (sub * 0.9 + crack * 0.35 + tail).astype(np.float32)


def riser(dur=2.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32)
    steps = 40
    for k in range(steps):
        a, b = k * n // steps, (k + 1) * n // steps
        fc = 300 * (25 ** (k / steps))
        out[a:b] = bandpass(noise, fc * 0.7, min(fc * 1.4, 20000))[a:b]
    return out * (t / dur) ** 2.2 * 0.5


def whoosh(dur=1.2, up=True):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32)
    steps = 30
    for k in range(steps):
        a, b = k * n // steps, (k + 1) * n // steps
        u = k / steps
        fc = 300 + 2400 * (np.sin(np.pi * u) if up else u)
        out[a:b] = bandpass(noise, fc * 0.6, fc * 1.6)[a:b]
    return out * np.sin(np.pi * t / dur) ** 2 * 0.45


def chisel():
    n = int(0.25 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for f, a in [(3100, 1), (4700, 0.6), (6900, 0.4)]:
        sig += a * np.sin(2 * np.pi * f * rng.uniform(0.97, 1.03) * t) * np.exp(-t / 0.03)
    sig += highpass(rng.normal(0, 1, n).astype(np.float32), 2000) * np.exp(-t / 0.008) * 0.6
    sig += np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.02) * 0.5
    return sig.astype(np.float32) * 0.25


def shimmer(dur=3.0, base=1320.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for k in range(8):
        f = base * (1 + 0.5 * k) * rng.uniform(0.995, 1.005)
        st = rng.uniform(0, 0.4)
        e = np.clip((t - st) / 0.01, 0, 1) * np.exp(-np.clip(t - st, 0, None) / 1.2)
        sig += np.sin(2 * np.pi * f * t) * e / (1 + k * 0.5)
    return sig.astype(np.float32) * 0.08


def wind(dur):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.normal(0, 1, n).astype(np.float32)
    w = lowpass(noise, 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t) * np.sin(2 * np.pi * 0.07 * t + 1))
    return (w * env_adsr(n, 2.0, 2.0) * 0.18).astype(np.float32)


def ney(notes, start_dur=0.0):
    """Breathy end-blown flute line: list of (note, duration)."""
    total = sum(d for _, d in notes)
    n = int(total * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = np.zeros(n, np.float32)
    amp = np.zeros(n, np.float32)
    i = 0
    for k, (note, d) in enumerate(notes):
        m = int(d * SR)
        target = hz(note) if note else 0.0
        f[i:i + m] = target
        if note:
            amp[i:i + m] = env_adsr(m, 0.12, min(0.35, d * 0.4)) * 0.9
        i += m
    # portamento + vibrato
    f = np.maximum.accumulate(f) * 0 + f
    sm = np.convolve(np.where(f > 0, f, np.nan_to_num(np.where(f > 0, f, 0))), np.ones(1200) / 1200, "same")
    f_sm = np.where(f > 0, sm, 0).astype(np.float32)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t % 1.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f_sm * vib) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    breath = bandpass(rng.normal(0, 1, n).astype(np.float32), 900, 4000) * 0.35
    return ((tone + breath) * amp * 0.22).astype(np.float32)


def reverb_ir(seconds=3.5, damp=3000):
    n = int(seconds * SR)
    t = np.arange(n, dtype=np.float32) / SR
    irs = []
    for ch in range(2):
        noise = np.random.default_rng(ch + 7).normal(0, 1, n).astype(np.float32)
        noise = lowpass(noise, damp)
        irs.append(noise * np.exp(-t / (seconds / 6.5)))
    ir = np.stack(irs, -1)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(x, ir, wet=0.35):
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], -1)
    return x * (1 - wet) + y * wet * 2.2


# ----------------------------------------------------------------------------- the score
CHORDS = {
    "Dm": ["D3", "A3", "D4", "F4"], "Bb": ["Bb2", "F3", "D4", "F4"], "Gm": ["G2", "D3", "Bb3", "G4"],
    "A": ["A2", "E3", "C#4", "A4"], "F": ["F2", "C3", "A3", "F4"], "C": ["C3", "G3", "E4", "G4"],
    "Am": ["A2", "E3", "C4", "E4"], "Dm9": ["D3", "A3", "E4", "F4"], "Asus": ["A2", "E3", "D4", "A4"],
    "Eb": ["Eb3", "Bb3", "G4"], "Am7": ["A2", "G3", "C4", "E4"],
}


def compose():
    T = TL()
    music, sfx = Bus(), Bus()

    def chord_seq(seq, gain=0.55, bright=0.45):
        for name, t0, t1 in seq:
            dur = t1 - t0 + 2.5
            music.add(t0 - 0.6, pad([hz(n) for n in CHORDS[name]], dur, attack=1.6, release=2.4, bright=bright), gain)

    def arps(t0, t1, notes, step, gain=0.25, damp=0.996, bright=0.45, bend=0.0, pan_spread=0.5):
        t, k = t0, 0
        while t < t1:
            nt = notes[k % len(notes)]
            if nt:
                music.add(t, pluck(hz(nt), 3.0, damp, bright, bend), gain * rng.uniform(0.75, 1.0),
                          pan=rng.uniform(-pan_spread, pan_spread))
            t += step
            k += 1

    def drone(t0, t1, note="D2", gain=0.35):
        f = hz(note)
        n = int((t1 - t0) * SR)
        tt = np.arange(n, dtype=np.float32) / SR
        s = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2 * tt + 1) +
             0.2 * np.sin(2 * np.pi * f * 3.01 * tt)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.09 * tt))
        music.add(t0, (s * env_adsr(n, 3.0, 3.0)).astype(np.float32), gain * 0.55)

    w1 = T.w(0, "1")
    # 1. cold open
    drone(0.0, 6.5, "D1", 0.45)
    music.add(0.0, pad([hz("D5"), hz("A5"), hz("E6")], 6.0, attack=3.0, release=2.5, bright=0.2), 0.3)
    sfx.add(w1 - 2.0, riser(2.0), 0.5)
    sfx.add(w1 - 0.02, highpass(boom(5.0, 55), 40), 0.55)
    sfx.add(w1, shimmer(4.0, 1175), 1.0)
    # 2. calendar
    cal = [("Dm", 5.0, 10.6), ("Bb", 10.6, 15.6), ("Gm", 15.6, 21.0), ("A", 21.0, 24.6), ("Dm", 24.6, 27.4)]
    chord_seq(cal, 0.5)
    for name, a, b in cal:
        notes = CHORDS[name][1:] + [CHORDS[name][2]]
        arps(a + 0.4, b, [n.replace("3", "4").replace("2", "3") for n in notes], 0.75, 0.18)
    drone(5.0, 27.5, "D2", 0.25)
    sfx.add(T.w(1, "five") - 0.3, whoosh(1.6), 0.5)
    sfx.add(T.w(2, "Jesus") - 0.6, whoosh(1.4), 0.4)
    sfx.add(T.w(2, "wrong"), bowl(880, 4), 0.6)
    sfx.add(T.w(3, "Herod"), drum(70, 1.5), 0.6)
    sfx.add(T.w(4, "zero") + 0.2, boom(3.0, 70), 0.45)
    # 3. inscription: chisel taps while letters are cut
    drone(27.0, 36.6, "D2", 0.3)
    music.add(27.2, pad([hz(n) for n in ["D3", "A3", "F4"]], 9.5, attack=2.0, release=2.5, bright=0.3), 0.4)
    for word, endword, n in (("Gaius", "Caesar", 9), ("Lucius", "Paullus", 16), ("consuls", "consuls", 3)):
        a, b = T.w(6, word), T.w(6, endword, end=True) + 0.3
        for k in range(n):
            tt = a + (b - a) * (k + rng.uniform(0, 0.6)) / n
            sfx.add(tt, chisel(), rng.uniform(0.5, 0.9), pan=rng.uniform(-0.3, 0.3))
    # 4. Yuanshi: gong at the seal, guqin as the brush writes
    th = T.w(7, "Han")
    sfx.add(th - 0.02, gong(82, 8.0), 0.9)
    drone(36.0, 44.6, "A1", 0.3)
    music.add(36.0, pad([hz(n) for n in ["A2", "E3", "D4", "E4"]], 8.6, attack=2.0, release=2.0, bright=0.3), 0.45)
    pent = ["A3", "C4", "D4", "E4", "G4", "A4", "C5", "D5"]
    ty = T.w(7, "Yuanshi")
    for k, nt in enumerate(["E4", "D4", "A3", "C4", "D4", "E4", "G4", "A4"]):
        music.add(ty - 0.3 + k * 0.42, pluck(hz(nt), 4.0, 0.9975, 0.6, bend=-0.01 if k % 3 == 0 else 0.0), 0.35,
                  pan=rng.uniform(-0.4, 0.4))
    for k in range(4):
        sfx.add(ty - 0.1 + [0, 0.45, 1.2, 1.65][k] + (T.w(7, "Original") - ty) * (k >= 2) - 1.2 * (k >= 2),
                whoosh(0.7), 0.25)
    # 5. two empires: building pulse
    emp = [("Dm", 44.0, 49.6), ("F", 49.6, 55.4), ("C", 55.4, 58.6), ("Gm", 58.6, 61.0), ("A", 61.0, 62.7)]
    chord_seq(emp, 0.55, 0.5)
    drone(44.0, 62.8, "D2", 0.3)
    t, k = 47.0, 0
    while t < 62.4:
        sfx.add(t, drum(95 if k % 2 == 0 else 120, 0.8), 0.32 + 0.25 * (t - 47) / 15)
        t += 0.75 if t < 56 else 0.375
        k += 1
    arps(50.0, 62.4, ["D4", "F4", "A4", "C5", "A4", "F4"], 0.375, 0.15)
    sfx.add(T.e(10) - 1.6, riser(1.9), 0.7)
    sfx.add(T.e(10) + 0.72, boom(5.0, 50), 1.0)
    # 6. Rome
    rome = [("Dm", 62.8, 66.0), ("Bb", 66.0, 69.4), ("F", 69.4, 72.0), ("C", 72.0, 74.6)]
    chord_seq(rome, 0.55, 0.55)
    drone(62.8, 74.8, "D2", 0.3)
    for name, a, b in rome:
        arps(a, b, [n.replace("2", "4").replace("3", "4") for n in CHORDS[name]], 0.25, 0.14)
    sfx.add(T.s(12) - 0.3, shimmer(3.0, 1568), 0.9)
    # 7. journey east: travelling ostinato
    jour = [("Dm", 74.6, 79.0), ("Bb", 79.0, 85.2), ("Gm", 85.2, 91.0), ("Eb", 91.0, 98.0), ("Dm", 98.0, 104.9)]
    chord_seq(jour, 0.45, 0.4)
    t = 74.8
    while t < 104.7:
        music.add(t, pluck(hz("D2"), 0.8, 0.99, 0.3), 0.32)
        t += 0.3
    for tt in (T.s(14) + 0.2, T.s(15) + 0.4, T.s(19) + 0.2):
        sfx.add(tt, whoosh(1.8), 0.55)
    phrase = [("D5", 0.6), ("Eb5", 0.3), ("F#5", 0.9), ("G5", 0.5), ("F#5", 0.4), ("Eb5", 0.6), ("D5", 1.6), (None, 0.8),
              ("A4", 0.5), ("Bb4", 0.4), ("C5", 0.5), ("D5", 1.8)]
    music.add(T.w(15, "Parthia") - 0.2, ney(phrase), 0.9, pan=0.2)
    music.add(T.s(17) + 0.6, ney([("A4", 0.6), ("Bb4", 0.4), ("C5", 0.5), ("D5", 0.8), ("Eb5", 0.4), ("D5", 1.6)]), 0.7,
              pan=-0.2)
    sfx.add(T.s(16) - 0.3, shimmer(3.5, 1320), 0.9)
    sfx.add(T.s(18), shimmer(3.0, 1760), 0.8)
    # trade: drums and bright plucks
    trade = [("Dm", 104.9, 109.9), ("Bb", 109.9, 113.9), ("F", 113.9, 116.4), ("A", 116.4, 118.8)]
    chord_seq(trade, 0.5, 0.55)
    t, k = 105.0, 0
    while t < 118.4:
        sfx.add(t, drum(100 if k % 4 in (0, 3) else 140, 0.6, 0.8), 0.35 if k % 4 == 0 else 0.22)
        t += 0.3
        k += 1
    arps(105.0, 118.4, ["D4", "A4", "F4", "A4", "E5", "A4", "F4", "A4"], 0.15, 0.1)
    sfx.add(T.w(20, "Strabo") - 0.1, shimmer(2.5, 1046), 0.8)
    sfx.add(T.e(20) - 0.4, whoosh(1.8), 0.7)
    # 8. Chang'an: wind, guqin, soft gong
    sfx.add(118.6, wind(11.0), 0.9)
    sfx.add(118.9, gong(110, 7.0, 0.6), 0.55)
    music.add(118.8, pad([hz(n) for n in ["A2", "E3", "A3", "D4"]], 10.5, attack=2.0, release=2.0, bright=0.3), 0.5)
    seq = ["A3", "C4", "D4", "E4", "G4", "E4", "D4", "C4", "A3", "G3", "A3", None, "E4", "D4", "C4", "A3"]
    for k, nt in enumerate(seq):
        if nt:
            music.add(119.4 + k * 0.6, pluck(hz(nt), 3.5, 0.9975, 0.65, bend=-0.012 if k % 4 == 1 else 0), 0.3,
                      pan=rng.uniform(-0.3, 0.3))
    sfx.add(T.w(22, "Wang") - 0.1, gong(70, 6.0, 0.8), 0.6)
    # 9. the white pheasant
    music.add(128.8, pad([hz(n) for n in ["A4", "E5", "B5"]], 12.0, attack=3.0, release=3.0, bright=0.2), 0.35)
    drone(128.8, 149.8, "A1", 0.28)
    sfx.add(T.s(23) + 0.1, bowl(784, 6), 0.8)
    sfx.add(T.w(24, "Duke") - 0.1, bowl(587, 7), 0.8)
    for k, word in enumerate(("Duke", "Secures", "Han")):
        sfx.add(T.w(25, word) - 0.1, whoosh(0.6), 0.25)
    sfx.add(T.s(25) - 0.05, gong(62, 8.0, 1.0), 0.9)
    tens = pad([hz("A1"), hz("Bb1"), hz("E2")], 6.0, attack=0.6, release=2.0, bright=0.6)
    music.add(T.s(26) - 0.1, tens, 0.7)
    sfx.add(T.w(26, "arranged") - 0.2, boom(3.0, 45), 0.5)
    # 10. the close
    close = [("Dm9", 149.2, 153.6), ("Bb", 153.6, 156.9), ("Gm", 156.9, 160.6)]
    chord_seq(close, 0.5, 0.35)
    drone(149.2, 160.8, "D2", 0.25)
    arps(149.6, 160.4, ["A4", "D5", "E5", "F5", "E5", "D5"], 0.5, 0.12)
    sfx.add(T.w(28, "Rome") - 0.1, boom(2.5, 60), 0.35)
    sfx.add(T.w(28, "China") - 0.1, gong(98, 4.0, 0.5), 0.4)
    # 11. next year: heartbeat, then the lamp goes out
    tn = T.w(30, "not") + 0.1
    music.add(160.4, pad([hz(n) for n in CHORDS["Asus"]], tn - 160.4 + 0.3, attack=1.5, release=0.25, bright=0.45), 0.55)
    t = 160.8
    while t < tn - 0.1:
        sfx.add(t, drum(65, 0.9), 0.55)
        sfx.add(t + 0.22, drum(58, 0.9), 0.35)
        t += 0.86
    sfx.add(T.w(29, "count") - 0.2, shimmer(2.5, 1318), 0.5)
    sfx.add(tn, whoosh(0.6, up=False), 0.6)
    sfx.add(tn + 0.05, boom(4.0, 40), 0.7)
    # 12. end card
    te = T.e(30) - 0.2
    music.add(te + 0.3, pad([hz(n) for n in ["D2", "A2", "D3", "F3", "A3", "E4"]], DUR - te, attack=1.2, release=2.0,
                            bright=0.4), 0.6)
    sfx.add(te + 0.3, bowl(1175, 5), 0.6)
    sfx.add(te + 0.3, boom(4.0, 48), 0.5)
    return music, sfx


def loudness_env(x, win=0.05):
    n = int(win * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, "same"))
    return e


@njit(cache=True)
def _smooth_env(target, att, rel):
    out = np.empty_like(target)
    y = 0.0
    for i in range(len(target)):
        x = target[i]
        k = att if x > y else rel
        y = y + (x - y) * k
        out[i] = y
    return out


def target_ratio_gain(voice, bed, speech_db, gap_db, hop=0.05, win=1.2):
    """Gain curve for a music/SFX bed so that, perceptually (>150 Hz), it sits `speech_db`
    under the voice while she speaks and at most `gap_db` under typical voice level in gaps."""
    v = highpass(voice, 150)
    b = highpass(bed.mean(1), 150)
    H_ = int(hop * SR)
    W_ = int(win * SR)
    nfr = N // H_
    vdb = np.full(nfr, -120.0)
    bdb = np.full(nfr, -120.0)
    for i in range(nfr):
        a, c = max(0, i * H_ - W_ // 2), min(N, i * H_ + W_ // 2)
        vdb[i] = 10 * np.log10(np.mean(v[a:c] ** 2) + 1e-12)
        bdb[i] = 10 * np.log10(np.mean(b[a:c] ** 2) + 1e-12)
    speaking = vdb > np.percentile(vdb, 30)
    typical = np.median(vdb[speaking])
    target = np.where(speaking, vdb - speech_db, typical - gap_db)
    g_db = np.minimum(0.0, target - bdb)
    # smooth: fast to duck, slow to recover
    g = np.empty_like(g_db)
    y = 0.0
    for i, x in enumerate(g_db):
        y = x if x < y else y + (x - y) * 0.08
        g[i] = y
    g = np.convolve(g, np.ones(5) / 5, "same")
    gain = 10 ** (np.interp(np.arange(N) / H_, np.arange(nfr), g) / 20)
    return gain.astype(np.float32)


def mix():
    music, sfx = compose()
    nar, sr = sf.read(ROOT / "build" / "narration.wav", dtype="float32")
    nar = resample_poly(nar, SR, sr).astype(np.float32)
    nar = np.pad(nar, (0, max(0, N - len(nar))))[:N]
    # voice: clean up lows, gentle presence lift, light compression
    nar = highpass(nar, 75)
    nar = nar + 0.12 * bandpass(nar, 2500, 6000)   # ~+1 dB presence
    nar = nar / (np.abs(nar).max() + 1e-9) * 0.7
    ir = reverb_ir(3.8)
    m = reverb(music.x, ir, 0.38) * 0.42
    s = reverb(sfx.x, reverb_ir(2.4, 5000), 0.25) * 0.55
    m = highpass(m.T, 45).T
    s = highpass(s.T, 32).T
    m = m * target_ratio_gain(nar, m, 11.0, 5.0)[:, None]
    s = s * target_ratio_gain(nar, s, 13.0, 0.0)[:, None]
    vo = np.stack([nar, nar], -1)
    vo = vo + reverb(vo, reverb_ir(0.9, 6000), 0.06) * 0.0
    master = vo * 1.0 + m + s
    # gentle bus limiting
    peak = np.abs(master).max()
    master = master / peak * 0.95
    over = np.abs(master) > 0.8
    master[over] = np.sign(master[over]) * (0.8 + 0.15 * np.tanh((np.abs(master[over]) - 0.8) / 0.15))
    fade = np.ones(N, np.float32)
    fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
    master *= fade[:, None]
    out = ROOT / "build"
    sf.write(out / "mix_premaster.wav", master.astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "music_stem.wav", m.astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "sfx_stem.wav", s.astype(np.float32), SR, subtype="FLOAT")
    print("mixed", master.shape)


if __name__ == "__main__":
    mix()
