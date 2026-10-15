"""Score, sound design and mix for the cold open (48 kHz stereo, all synthesised here).

Instruments: bowed string ensemble (additive saw voices through body formants, bow noise,
vibrato), low brass (brightness follows dynamics), formant choir, Karplus-Strong lyre for
Gaius's theme (D minor, as established for the film), taiko and timpani, sub boom, cymbal,
reverse swell. Sound: torch fire (roar + crackle), footsteps on gravel, the flame guttering
and going out, wind, chisel strikes, a struck silver coin.

The music is placed from the narration's word timings (build/timeline.json)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from numba import njit
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
TL = json.load(open(ROOT / "build" / "timeline.json"))
DUR = 48.2
N = int(DUR * SR)
rng = np.random.default_rng(1720)


def word(line_id, w, which=0):
    for l in TL["lines"]:
        if l["id"] == line_id:
            hits = [x for x in l["words"] if x["w"].lower().strip(",.:") == w.lower()]
            return hits[which]["s"]
    raise KeyError((line_id, w))


def hz(note):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[note[0]]
    i = 1
    if len(note) > 2 and note[1] in "#b":
        n += 1 if note[1] == "#" else -1
        i = 2
    return 440.0 * 2 ** ((n + 12 * (int(note[i:]) + 1) - 69) / 12)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def env(n, a, r, curve=1.5):
    e = np.ones(n, np.float32)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    if na:
        e[:na] = np.linspace(0, 1, na) ** curve
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e


def shape(n, points):
    """Piecewise-linear envelope from [(t, level), ...] in seconds."""
    t = np.arange(n) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs).astype(np.float32)


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2), np.float32)

    def add(self, t, sig, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], -1)
        i = int(round(t * SR))
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(N, i + len(sig))
        if j > i:
            self.x[i:j] += sig[: j - i] * gain


# ============================================================================ instruments
def strings(notes, dur, a=1.5, r=2.0, bright=0.55, voices=5, dyn=None, vib=0.004):
    """Bowed ensemble: each note gets `voices` detuned saw voices with slow vibrato, bow noise and body formants."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros((n, 2), np.float32)
    for note in notes:
        f0 = hz(note) if isinstance(note, str) else note
        for v in range(voices):
            det = 2 ** (rng.normal(0, 6) / 1200)
            vr = rng.uniform(4.6, 5.8)
            vd = vib * np.clip(t / 0.8, 0, 1)
            fm = f0 * det * (1 + vd * np.sin(2 * np.pi * vr * t + rng.uniform(0, 6)))
            ph = 2 * np.pi * np.cumsum(fm) / SR
            sig = np.zeros(n, np.float32)
            nh = int(min(40, 9000 / f0))
            for h in range(1, nh + 1):
                sig += (np.sin(h * ph + rng.uniform(0, 6)) / h * np.exp(-h * (1 - bright) * 0.12)).astype(np.float32)
            pan = (v / max(1, voices - 1) - 0.5) * 1.2
            out[:, 0] += sig * np.cos((pan + 1) * np.pi / 4)
            out[:, 1] += sig * np.sin((pan + 1) * np.pi / 4)
    # body resonances + bow noise
    body = 0.6 * out + 0.5 * bp(out, 250, 500) + 0.35 * bp(out, 900, 1400) + 0.25 * bp(out, 2500, 3500)
    bow = bp(rng.normal(0, 1, (n, 2)).astype(np.float32), 1500, 6000) * 0.02
    sig = (body + bow) / (len(notes) * voices) * 0.9
    e = env(n, a, r)
    if dyn is not None:
        e = e * dyn[:n]
    sig *= e[:, None]
    return lp(sig, 2500 + 6000 * bright).astype(np.float32)


def brass(notes, dur, a=0.08, r=1.5, dyn=None, growl=0.3):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    e = env(n, a, r)
    if dyn is not None:
        e = e * dyn[:n]
    out = np.zeros(n, np.float32)
    for note in notes:
        f0 = hz(note)
        for v in range(3):
            fm = f0 * 2 ** (rng.normal(0, 5) / 1200) * (1 + 0.002 * np.sin(2 * np.pi * 5 * t))
            ph = 2 * np.pi * np.cumsum(fm) / SR
            for h in range(1, int(min(30, 7000 / f0)) + 1):
                amp = (1 / h) * np.exp(-h / (1.5 + 9 * e))           # brighter when louder
                out += (np.sin(h * ph + v) * amp).astype(np.float32)
    out += growl * bp(rng.normal(0, 1, n).astype(np.float32), 60, 300) * e * 0.3
    out = out * e / (len(notes) * 3) * 0.8
    return np.stack([out, out], -1)


def choir(notes, dur, a=1.5, r=2.5, dyn=None, vowel=(700, 1150, 2800)):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    src = np.zeros((n, 2), np.float32)
    for note in notes:
        f0 = hz(note)
        for v in range(6):
            fm = f0 * 2 ** (rng.normal(0, 9) / 1200) * (1 + 0.005 * np.sin(2 * np.pi * rng.uniform(4.5, 6) * t))
            ph = np.cumsum(fm) / SR
            saw = (2 * (ph % 1.0) - 1).astype(np.float32)
            pan = (v / 5 - 0.5) * 1.4
            src[:, 0] += saw * np.cos((pan + 1) * np.pi / 4)
            src[:, 1] += saw * np.sin((pan + 1) * np.pi / 4)
    f1, f2, f3 = vowel
    out = bp(src, f1 * 0.8, f1 * 1.25) * 1.0 + bp(src, f2 * 0.85, f2 * 1.15) * 0.5 + bp(src, f3 * 0.9, f3 * 1.1) * 0.25
    out += bp(rng.normal(0, 1, (n, 2)).astype(np.float32), 2000, 7000) * 0.03
    e = env(n, a, r)
    if dyn is not None:
        e = e * dyn[:n]
    return (out * e[:, None] / (len(notes) * 6) * 1.6).astype(np.float32)


@njit(cache=True)
def _ks(n, period, damp, noise, bright):
    buf = noise[:period].copy()
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


def lyre(note, dur=4.0, damp=0.9975, bright=0.55):
    f = hz(note)
    n = int(dur * SR)
    period = max(2, int(round(SR / f)))
    noise = rng.uniform(-1, 1, period + 2).astype(np.float32)
    sig = _ks(n, period, damp, noise, bright)
    # gut-string body: a little low-mid warmth, soft attack click
    sig = sig + 0.4 * bp(sig, 180, 700)
    sig *= env(n, 0.003, 0.6)
    return (sig * 0.5).astype(np.float32)


def taiko(f0=70.0, dur=2.5, tone=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f0 * (0.62 + 0.38 * np.exp(-t / 0.07))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45) * tone
    body2 = np.sin(2 * np.pi * np.cumsum(f * 1.58) / SR) * np.exp(-t / 0.25) * 0.3
    skin = bp(rng.normal(0, 1, n).astype(np.float32), 120, 1800) * np.exp(-t / 0.035) * 0.6
    return (body + body2 + skin).astype(np.float32) * 0.7


def boom(dur=5.0, f0=48.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f0 * (0.5 + 0.5 * np.exp(-t / 0.35))
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.6)
    crack = lp(rng.normal(0, 1, n).astype(np.float32), 3000) * np.exp(-t / 0.06)
    tail = lp(rng.normal(0, 1, n).astype(np.float32), 300) * np.exp(-t / 2.0) * 0.35
    return (sub * 1.0 + crack * 0.3 + tail).astype(np.float32)


def crash(dur=5.0, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    x = hp(rng.normal(0, 1, (n, 2)).astype(np.float32), 3500) * np.exp(-t / 1.6)[:, None]
    x += bp(rng.normal(0, 1, (n, 2)).astype(np.float32), 600, 3000) * (np.exp(-t / 0.3) * 0.5)[:, None]
    return (x * 0.25 * bright).astype(np.float32)


def swell(dur=2.0):
    """Reverse cymbal + rising filtered noise, peaking at the end."""
    c = crash(dur + 1.0)[::-1][-int(dur * SR):]
    n = len(c)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32)
    steps = 40
    for k in range(steps):
        a, b = k * n // steps, (k + 1) * n // steps
        fc = 200 * (30 ** (k / steps))
        out[a:b] = bp(noise, fc * 0.7, min(fc * 1.5, 20000))[a:b]
    out *= (t / dur) ** 2.5 * 0.35
    return (c * 1.4 + out[:, None]).astype(np.float32)


def low_piano(note, dur=7.0):
    f = hz(note)
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    B = 0.0004
    for h in range(1, 16):
        fh = f * h * np.sqrt(1 + B * h * h)
        sig += (np.sin(2 * np.pi * fh * t) / h ** 0.9 * np.exp(-t * (0.35 + 0.15 * h))).astype(np.float32)
    ham = lp(rng.normal(0, 1, n).astype(np.float32), 1200) * np.exp(-t / 0.01) * 0.3
    return (sig * 0.25 + ham).astype(np.float32)


# ============================================================================ sound design
def fire(dur, level):
    """Torch fire: low roar, hiss, and random crackles. level: per-sample envelope (0..1)."""
    n = int(dur * SR)
    roar = lp(rng.normal(0, 1, n).astype(np.float32), 180) * 1.8
    roar *= 1 + 0.35 * lp(rng.normal(0, 1, n).astype(np.float32), 6) * 8
    hiss = bp(rng.normal(0, 1, n).astype(np.float32), 2000, 8000) * 0.10
    crack = np.zeros(n, np.float32)
    k = 0
    while k < n:
        k += int(rng.exponential(0.09) * SR) + 1
        if k >= n:
            break
        m = int(rng.uniform(0.002, 0.02) * SR)
        burst = rng.normal(0, 1, m).astype(np.float32) * np.exp(-np.arange(m) / (m * 0.25))
        burst = bp(burst, rng.uniform(800, 2500), rng.uniform(4000, 11000)) * rng.uniform(0.2, 1.4) ** 2
        crack[k:k + m] += burst[: n - k]
    sig = (roar * 0.25 + hiss + crack * 0.7) * level[:n]
    return sig.astype(np.float32)


def footsteps(times, gains):
    out = np.zeros(N, np.float32)
    for t0, g in zip(times, gains):
        m = int(0.22 * SR)
        x = np.zeros(m, np.float32)
        # a crunch is many tiny grain clicks
        for _ in range(60):
            i = int(rng.beta(1.5, 4) * m * 0.8)
            l = int(rng.uniform(0.0005, 0.003) * SR)
            x[i:i + l] += rng.normal(0, 1, min(l, m - i)).astype(np.float32) * rng.uniform(0.2, 1)
        x = bp(x, 700, 7000) * np.exp(-np.arange(m) / (0.07 * SR))
        x += lp(rng.normal(0, 1, m).astype(np.float32), 200) * np.exp(-np.arange(m) / (0.02 * SR)) * 0.8
        i0 = int(t0 * SR)
        j = min(N, i0 + m)
        out[i0:j] += x[: j - i0] * g
    return out


def extinguish(dur=1.6):
    """The flame dies: a last flutter, a soft whoomp and a hiss of smoke."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    flutter = lp(rng.normal(0, 1, n).astype(np.float32), 400) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t)) * np.exp(-t / 0.35)
    whoomp = lp(rng.normal(0, 1, n).astype(np.float32), 250) * np.exp(-((t - 0.25) / 0.12) ** 2) * 2.0
    hiss = bp(rng.normal(0, 1, n).astype(np.float32), 2500, 7000) * np.exp(-t / 0.6) * 0.15
    return (flutter * 0.8 + whoomp + hiss).astype(np.float32) * 0.5


def wind(dur, seed=3):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(r.normal(0, 1, (n, 2)).astype(np.float32), 600)
    gust = (0.55 + 0.45 * np.sin(2 * np.pi * 0.09 * t + 1) * np.sin(2 * np.pi * 0.05 * t))[:, None]
    whistle = bp(r.normal(0, 1, (n, 2)).astype(np.float32), 900, 1400) * 0.15 * gust
    return ((x * gust + whistle) * 0.18).astype(np.float32)


def chisel():
    n = int(0.4 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for f, a in [(2900, 1), (4300, 0.6), (6100, 0.4), (8200, 0.2)]:
        sig += a * np.sin(2 * np.pi * f * rng.uniform(0.97, 1.03) * t) * np.exp(-t / 0.05)
    sig += hp(rng.normal(0, 1, n).astype(np.float32), 2000) * np.exp(-t / 0.01) * 0.7
    sig += np.sin(2 * np.pi * 160 * t) * np.exp(-t / 0.03) * 0.8
    return sig.astype(np.float32) * 0.25


def coin_ring(dur=4.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    f0 = 2150.0
    for r, a, d in [(1.0, 1.0, 1.6), (2.31, 0.55, 1.1), (3.98, 0.4, 0.8), (5.71, 0.25, 0.5), (8.1, 0.15, 0.3)]:
        beat = 1 + 0.25 * np.sin(2 * np.pi * (3 + r) * t)
        sig += (a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / d) * beat).astype(np.float32)
    clink = hp(rng.normal(0, 1, n).astype(np.float32), 3000) * np.exp(-t / 0.004)
    return (sig * 0.10 + clink * 0.3).astype(np.float32)


def shimmer(dur=3.0, base=1760.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for k in range(9):
        f = base * (1 + 0.5 * k) * rng.uniform(0.995, 1.005)
        st = rng.uniform(0, 0.3)
        e = np.clip((t - st) / 0.01, 0, 1) * np.exp(-np.clip(t - st, 0, None) / 1.0)
        sig += np.sin(2 * np.pi * f * t) * e / (1 + k * 0.5)
    return sig.astype(np.float32) * 0.06


# ============================================================================ extra voices for the cold open
def crickets(dur, seed=4):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros((n, 2), np.float32)
    for c in range(5):
        f = r.uniform(3800, 4700)
        pan = r.uniform(-0.8, 0.8)
        period = r.uniform(0.75, 1.3)
        t0 = r.uniform(0, period)
        amp = r.uniform(0.4, 1.0)
        tt = t0
        while tt < dur:
            for p in range(3):                      # a chirp = three quick pulses
                i = int((tt + p * 0.045) * SR)
                m = int(0.03 * SR)
                if i + m >= n:
                    break
                k = np.arange(m) / SR
                pulse = np.sin(2 * np.pi * f * k) * np.sin(np.pi * k / 0.03) ** 2 * amp
                out[i:i + m, 0] += pulse * np.cos((pan + 1) * np.pi / 4)
                out[i:i + m, 1] += pulse * np.sin((pan + 1) * np.pi / 4)
            tt += period * r.uniform(0.85, 1.15)
    return out * 0.012


def modal_drum(f0=55.0, dur=4.0, strike=1.0):
    """Membrane modes (Bessel ratios) with a pitch drop and skin noise."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.zeros(n, np.float32)
    for r, a, d in ((1.0, 1.0, 0.9), (1.59, 0.55, 0.5), (2.14, 0.35, 0.35), (2.30, 0.30, 0.3), (2.65, 0.2, 0.25),
                    (2.92, 0.15, 0.2)):
        f = f0 * r * (0.82 + 0.18 * np.exp(-t / 0.08))
        sig += (a * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / d)).astype(np.float32)
    skin = bp(rng.normal(0, 1, n).astype(np.float32), 90, 1500) * np.exp(-t / 0.03) * 0.5
    return ((sig + skin) * 0.55 * strike).astype(np.float32)


def stone_impact(dur=1.2):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    crack = bp(rng.normal(0, 1, n).astype(np.float32), 300, 5000) * np.exp(-t / 0.025)
    thock = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.12)
    grit = hp(rng.normal(0, 1, n).astype(np.float32), 2500) * np.exp(-t / 0.15) * 0.2
    return (crack * 0.8 + thock * 0.9 + grit).astype(np.float32)


def sub_sweep(dur=5.0, f0=52.0, f1=34.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return ((np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.exp(-t / 1.8) * env(n, 0.004, 0.8)).astype(np.float32)


def tremolo(x, rate=12.0, depth=0.6):
    n = len(x)
    t = np.arange(n) / SR
    m = 1 - depth * 0.5 * (1 + np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)))
    return (x * m[:, None]).astype(np.float32)


def panned(mono, pan_keys):
    """Mono -> stereo with pan automation [(t, pan)], equal power."""
    n = len(mono)
    t = np.arange(n) / SR
    ts, ps = zip(*pan_keys)
    p = np.interp(t, ts, ps)
    return np.stack([mono * np.cos((p + 1) * np.pi / 4) * 1.414, mono * np.sin((p + 1) * np.pi / 4) * 1.414], -1)


def reverse_swell(dur=1.3, note="D3"):
    """A reversed-reverb inhale: a reversed decaying chord-plus-noise."""
    n = int((dur + 2.5) * SR)
    t = np.arange(n) / SR
    x = strings([note, note.replace("3", "4")], dur + 2.5, a=0.01, r=2.4, bright=0.6, voices=4)
    x = x + (bp(rng.normal(0, 1, (n, 2)).astype(np.float32), 400, 6000) * np.exp(-t / 0.9)[:, None] * 0.15)
    y = reverb(x, reverb_ir(3.0, 5000, 3), 0.9)[::-1]
    y = y[-int(dur * SR):]
    return (y * (np.linspace(0, 1, len(y)) ** 2)[:, None]).astype(np.float32)


# ============================================================================ the cue sheet (production brief §7.2)
FRAG = ["D4", "F4", "A4", "G4"]      # the first four notes of Gaius's theme, left unresolved


def compose():
    """Returns (music cut on 'walk', music after the cut, sound effects, ambience)."""
    M, M2, S, A = Bus(), Bus(), Bus(), Bus()
    w = word
    tw = w("l5", "walk")
    th = w("l6", "home")
    tg = w("l7", "Gaius")
    # ---- M0 night: wind and crickets; M3 low air on the descent
    A.add(0.0, wind(DUR), 1.0)
    cr = crickets(DUR)
    cr *= shape(N, [(0, 0), (0.4, 0), (2.4, 1.0), (5.8, 1.0), (6.6, 0.6), (11.5, 0.6), (11.6, 0.0), (28.6, 0.0),
                    (29.0, 0.7), (th, 0.7), (th + 1.0, 0.25), (DUR, 0.25)])[:, None]
    A.add(0.0, cr, 1.0)
    air = bp(rng.normal(0, 1, int(6.0 * SR)).astype(np.float32), 60, 400) * shape(int(6.0 * SR), [(0, 0), (2.5, 1.0), (6.0, 0)])
    A.add(0.5, air, 0.35)
    # ---- M1 the drone: D1 + D2, slow swell
    d = shape(int(34.0 * SR), [(0, 0), (5.0, 0.8), (16.0, 0.9), (34.0, 1.0)])
    M.add(0.3, strings(["D2", "A2"], 34.0, a=4.0, r=0.5, bright=0.35, voices=6, dyn=d), 0.55)
    M.add(0.3, strings(["D1"], 34.0, a=4.0, r=0.5, bright=0.2, voices=3, dyn=d), 0.65)
    # ---- M2 the beacon kindles far away; the torch fire follows the torch through every shot
    ign = lp(rng.normal(0, 1, int(1.2 * SR)).astype(np.float32), 1200) * np.exp(-np.arange(int(1.2 * SR)) / (0.25 * SR))
    S.add(1.55, ign, 0.25)
    lv = shape(N, [(0, 0), (1.6, 0.0), (3.0, 0.10), (5.8, 0.18), (6.6, 1.0), (11.0, 1.0), (11.3, 0.55), (21.8, 0.55),
                   (22.0, 0.45), (25.2, 0.45), (25.5, 0.0), (28.6, 0.0), (28.9, 1.0), (tw, 1.0), (th - 0.9, 0.35),
                   (th - 0.2, 0.25), (th, 0.0)])
    pan_keys = [(0, 0.0), (5.8, 0.0), (6.6, -0.25), (11.0, -0.15), (11.4, 0.5), (16.4, -0.45), (16.6, -0.5),
                (22.0, 0.45), (22.4, -0.6), (23.2, 0.6), (24.0, -0.6), (24.8, 0.6), (25.4, 0.0), (28.9, -0.45),
                (tw, -0.45), (th, 0.05), (DUR, 0.0)]
    fire_m = fire(DUR, np.ones(N, np.float32))
    # receding: the torch walking away loses its highs as well as its level
    far = shape(N, [(0, 0), (tw, 0), (th, 1.0), (DUR, 1.0)])
    fire_m = fire_m * (1 - far * 0.6) + lp(fire_m, 1200) * far * 0.6
    S.add(0.0, panned(fire_m * lv, pan_keys), 1.5)
    # ---- M4 footsteps on gravel: the approach (camera and bearer walking), then him walking away
    st = np.arange(6.0, 11.4, 1 / 1.8)
    S.add(0.0, footsteps(st, np.full(len(st), 0.7)), 1.1, pan=-0.05)
    st2 = np.arange(tw + 0.15, th + 0.3, 1 / 1.7)
    S.add(0.0, footsteps(st2, 0.8 * np.exp(-(st2 - tw) / 1.4)), 1.2, pan=-0.2)
    # ---- M5 the tomb: a sub thump of stone
    S.add(w("l1", "tomb") - 0.03, sub_sweep(2.0, 40, 32), 0.45)
    # ---- M6 his face: divisi cellos, pp
    cel = shape(int(5.6 * SR), [(0, 0), (3.0, 1.0), (5.0, 0.8), (5.6, 0.6)])
    M.add(10.95, strings(["D3", "A3"], 5.6, a=3.0, r=0.8, bright=0.45, voices=6, dyn=cel), 0.20)
    # ---- M7 power: basses and low horns, Dm -> Bb/D on "Augustus", crescendo to 22.4
    ta = w("l3", "grandfather")
    crs = shape(int(7.0 * SR), [(0, 0.35), (6.2, 1.0), (7.0, 0.9)])
    M.add(ta, brass(["D2", "A2", "D3"], 1.0 + w("l3", "Augustus") - ta, a=0.4, r=0.4,
                    dyn=crs[: int((1.0 + w("l3", "Augustus") - ta) * SR)]), 0.28)
    t_au = w("l3", "Augustus")
    dur7 = 22.4 - t_au + 1.0
    crs2 = shape(int(dur7 * SR), [(0, 0.45), (dur7 - 1.0, 1.0), (dur7, 0.8)])
    M.add(t_au, brass(["D2", "Bb2", "D3", "F3"], dur7, a=0.5, r=0.8, dyn=crs2), 0.30)
    M.add(t_au, strings(["D2", "Bb2", "F3", "D4"], dur7, a=0.8, r=0.8, bright=0.55, dyn=crs2), 0.26)
    # ---- M8 his name, titles and future cut into the stone: chisel + a drum on D2, F2, A2
    for wd, note in (("name", "D2"), ("titles", "F2"), ("future", "A2")):
        t8 = w("l3", wd) - 0.03
        S.add(t8, chisel(), 1.0, pan=0.1)
        S.add(t8 + 0.07, chisel(), 0.55, pan=-0.1)
        M.add(t8, modal_drum(hz(note), 2.5), 0.55)
    # ---- M9 the coin: strings lift to Gm/D; one silver ring on "coins"
    t9 = 25.0
    lift = shape(int(3.5 * SR), [(0, 0.5), (2.0, 1.0), (3.5, 0.6)])
    M.add(t9, strings(["D3", "G3", "Bb3", "D4"], 3.5, a=0.6, r=1.2, bright=0.6, dyn=lift), 0.28)
    M.add(t9, brass(["G2", "D3"], 3.5, a=0.5, r=1.2, dyn=lift), 0.18)
    S.add(w("l4", "coins") - 0.02, coin_ring(3.5), 1.0, pan=0.15)
    # ---- M10 dread: a heartbeat that quickens from 66 to 76 bpm; strings in tremolo
    tt = 27.7
    while tt < tw - 0.1:
        u = (tt - 27.7) / (tw - 27.7)
        g = 0.35 + 0.45 * u
        M.add(tt, modal_drum(46, 1.2, 0.9), 0.55 * g)
        M.add(tt + 0.24, modal_drum(42, 1.0, 0.7), 0.35 * g)
        tt += 60.0 / (66 + 10 * u)
    tr_d = tw - 28.0
    trd = shape(int(tr_d * SR), [(0, 0.2), (tr_d, 0.6)])
    M.add(28.0, tremolo(strings(["D3", "A3"], tr_d, a=1.0, r=0.05, bright=0.5, dyn=trd)), 0.22)
    # ---- M11 rise: a D-Eb-E rub climbing an octave, with a riser, peaking into "walk"
    t11 = 30.4
    d11 = tw - t11
    rs = shape(int(d11 * SR), [(0, 0.15), (d11, 1.0)])
    for k, (lo, hi) in enumerate((("D3", "D4"), ("Eb3", "Eb4"), ("E3", "E4"))):
        f0, f1 = hz(lo), hz(hi)
        n11 = int(d11 * SR)
        gl = np.geomspace(f0, f1, n11)
        x = strings([float(f0)], d11, a=0.8, r=0.02, bright=0.6, voices=4, dyn=rs)
        # pitch glide by resampling a steady tone is costly; use a gliding saw stack instead
        ph = 2 * np.pi * np.cumsum(gl) / SR
        saw = sum(np.sin(h * ph) / h for h in range(1, 18)).astype(np.float32) * rs * 0.08
        M.add(t11, np.stack([saw, saw], -1) + x * 0.4, 0.30, pan=(k - 1) * 0.5)
    M.add(tw - 1.6, swell(1.6), 0.30)
    # ---- M12 everything stops on "walk" (applied in mix); M13/M14 the light dies
    gust = wind(3.0, seed=9) * shape(int(3.0 * SR), [(0, 0), (0.8, 2.0), (2.0, 1.2), (3.0, 0)])[:, None]
    A.add(th - 1.2, gust, 1.0)
    S.add(th - 0.25, extinguish(1.8), 1.0, pan=0.05)
    for k in range(3):
        tick = hp(rng.normal(0, 1, int(0.01 * SR)).astype(np.float32), 3000) * 0.3
        S.add(th + 0.35 + k * rng.uniform(0.15, 0.4), tick, 0.6, pan=rng.uniform(-0.3, 0.3))
    # ---- M15 the inhale; M16 THE hit on "Gaius"
    M2.add(tg - 1.3, reverse_swell(1.3, "D3"), 0.9)
    M2.add(tg - 0.05, sub_sweep(5.0, 52, 34), 1.15)
    M2.add(tg - 0.05, modal_drum(58, 4.0, 1.4), 0.95)
    M2.add(tg - 0.05, stone_impact(1.2), 0.6)
    # ---- M17 out of the tail, an open fifth; M18 the fragment, unresolved
    hold = shape(int(8.0 * SR), [(0, 0), (1.5, 1.0), (5.0, 0.8), (8.0, 0)])
    M2.add(40.2, strings(["D2", "A2", "D3"], 8.0, a=1.2, r=3.0, bright=0.4, voices=6, dyn=hold), 0.35)
    M2.add(40.2, brass(["D2", "A2"], 8.0, a=1.0, r=3.0, dyn=hold * 0.6), 0.15)
    t18 = w("l8", "boy") - 0.1
    gaps = [0.0, 0.62, 1.24, 1.95]
    for k, (note, dt) in enumerate(zip(FRAG, gaps)):
        dd = 6.0 if k == 3 else 3.5
        M2.add(t18 + dt, lyre(note, dd, damp=0.9985 if k == 3 else 0.9975), 0.55, pan=-0.1)
    M2.add(t18 + 1.95, strings(["G4"], 4.5, a=0.6, r=2.5, bright=0.4, voices=3), 0.10)
    return M, M2, S, A


# ============================================================================ mix
def reverb_ir(seconds=3.5, damp=3000, seed=7):
    n = int(seconds * SR)
    t = np.arange(n, dtype=np.float32) / SR
    r = np.random.default_rng(seed)
    ir = np.stack([lp(r.normal(0, 1, n).astype(np.float32), damp) * np.exp(-t / (seconds / 6.5)) for _ in range(2)], -1)
    ir[: int(0.015 * SR)] *= np.linspace(0, 1, int(0.015 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(x, ir, wet=0.35):
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], -1)
    return x * (1 - wet) + y * wet * 2.2


def duck_gain(voice, bed, speech_db, gap_db, hop=0.05, win=0.5, cut=150):
    v = hp(voice, 150)
    b = hp(bed.mean(1), cut) if cut else bed.mean(1)
    H_, W_ = int(hop * SR), int(win * SR)
    nfr = N // H_
    vdb, bdb = np.full(nfr, -120.0), np.full(nfr, -120.0)
    for i in range(nfr):
        a, c = max(0, i * H_ - W_ // 2), min(N, i * H_ + W_ // 2)
        vdb[i] = 10 * np.log10(np.mean(v[a:c] ** 2) + 1e-12)
        bdb[i] = 10 * np.log10(np.mean(b[a:c] ** 2) + 1e-12)
    speaking = vdb > np.percentile(vdb, 35)
    typical = np.median(vdb[speaking])
    target = np.where(speaking, vdb - speech_db, typical + gap_db)
    g_db = np.minimum(0.0, target - bdb)
    g = np.empty_like(g_db)
    y = 0.0
    for i, x in enumerate(g_db):
        y = x if x < y else y + (x - y) * 0.10
        g[i] = y
    g = np.convolve(g, np.ones(5) / 5, "same")
    return (10 ** (np.interp(np.arange(N) / H_, np.arange(nfr), g) / 20)).astype(np.float32)


def mix():
    M, M2, S, A = compose()
    nar, sr = sf.read(ROOT / "build" / "narration.wav", dtype="float32")
    nar = resample_poly(nar, SR, sr).astype(np.float32)
    nar = np.pad(nar, (0, max(0, N - len(nar))))[:N]
    nar = hp(nar, 75)
    nar = nar + 0.12 * bp(nar, 2500, 6000)
    nar = nar / (np.abs(nar).max() + 1e-9) * 0.7
    tw = word("l5", "walk")
    # M12: the music walks away. An 80 ms cut on the dry bus, so the hall tails still decay naturally.
    cut = shape(N, [(0, 1.0), (tw - 0.05, 1.0), (tw + 0.03, 0.0), (DUR, 0.0)])
    m_dry = M.x * cut[:, None]
    m = reverb(m_dry, reverb_ir(4.5, 4000), 0.40) * 0.55
    m2 = reverb(M2.x, reverb_ir(6.0, 3500, 21), 0.45) * 0.55      # the hit gets a cathedral tail
    s = reverb(S.x, reverb_ir(1.6, 6000, 11), 0.22) * 0.6
    amb = reverb(A.x, reverb_ir(1.2, 6000, 13), 0.2) * 0.7
    m, m2, s, amb = hp(m, 30), hp(m2, 25), hp(s, 35), hp(amb, 40)
    # band-split ducking: the speech band of the music sits ~14.5 dB under the voice; the low drone and
    # sub hits (which barely mask speech) keep their weight
    def duck_split(x, speech_db, gap_db):
        lo = lp(x, 220, 4)
        hi = x - lo
        return lo * duck_gain(nar, lo, 4.0, gap_db, cut=0)[:, None] + hi * duck_gain(nar, hi, speech_db, gap_db)[:, None]
    m = duck_split(m, 14.5, 3.0)
    m2 = duck_split(m2, 14.5, 6.0)
    s = s * duck_gain(nar, s, 16.5, 1.0)[:, None]
    amb = amb * duck_gain(nar, amb, 24.0, 12.0)[:, None]
    vo = np.stack([nar, nar], -1)
    vo = vo + reverb(vo, reverb_ir(1.2, 5000, 5), 1.0) * 0.04
    master = vo + m + m2 + s + amb
    peak = np.abs(master).max()
    master = master / peak * 0.95
    fade = np.ones(N, np.float32)
    fade[: int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
    fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)) ** 1.5
    master *= fade[:, None]
    out = ROOT / "build"
    sf.write(out / "mix_premaster.wav", master.astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "music_stem.wav", ((m + m2) / peak * 0.95).astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "sfx_stem.wav", ((s + amb) / peak * 0.95).astype(np.float32), SR, subtype="FLOAT")
    print("mixed", master.shape)


if __name__ == "__main__":
    mix()
