"""Post step: word-timed captions, coded music bed, cue-driven SFX, branding, encode.
python kit/blox/post.py PROJECTDIR

PROJECTDIR: timed.json, words.json ([[word, start, end], ...]), frames/00000.jpg ... (30 fps),
optional vo.wav (no file = music + SFX only). Writes PROJECTDIR/out/<project>.mp4 (h264, AAC 192k).
Deps: numpy, scipy, pillow; ffmpeg on PATH (or env FFMPEG).
Every SFX is synthesized here in numpy, so the kit ships no third-party audio.
"""
import os, sys, json, re, math, io, base64, shutil, subprocess, time
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.io import wavfile
from scipy.signal import resample_poly, lfilter, butter, sosfilt
from scipy.ndimage import minimum_filter1d, maximum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')
BRAND = os.path.join(ASSETS, 'brand')
FONT = os.path.join(BRAND, 'fonts', 'LilitaOne-Regular.ttf')
FFMPEG = os.environ.get('FFMPEG') or shutil.which('ffmpeg') or 'ffmpeg'
FPS, SR = 30, 48000
TAG_S = 0.6          # end card length
TAG_TEXT = 'made with Beta Version Blox Studio'
META = {'title': 'Made with Beta Version Blox Studio', 'comment': 'Made with Beta Version Blox Studio',
        'artist': 'Beta Version', 'description': 'Made with Beta Version Blox Studio', 'copyright': 'Beta Version'}


def norm(w): return re.sub(r"[^a-z0-9']", '', w.lower())


def load_words(d):
    p = os.path.join(d, 'words.json')
    if not os.path.exists(p): return []
    out = []
    for w in json.load(open(p, encoding='utf8')):
        if isinstance(w, dict): out.append((str(w['w']), float(w['s']), float(w['e'])))
        else: out.append((str(w[0]), float(w[1]), float(w[2])))
    return out


# ================================================================== audio helpers
def as2(x): x = np.asarray(x, np.float64); return np.stack([x, x], 1) if x.ndim == 1 else x
def db(x): return 20 * np.log10(np.maximum(x, 1e-12))
def nf(n): return 440 * 2 ** ((n - 69) / 12)
def _t(d): return np.arange(int(d * SR)) / SR
def trim_on(a, rel=-30):  # cut leading silence so sample 0 is the audible onset (SFX sync)
    m = np.abs(as2(a)).max(1); thr = m.max() * 10 ** (rel / 20); i = int(np.argmax(m >= thr)) if m.max() > 0 else 0
    return a[max(0, i - int(0.002 * SR)):]
def pan2(m, p):  # constant power, centre = unity per channel
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4; return np.stack([m * np.cos(a), m * np.sin(a)], 1) * np.sqrt(2)
def put(buf, a, t):
    a = as2(a); i = int(round(t * SR))
    if i < 0: a = a[-i:]; i = 0
    j = min(len(buf), i + len(a))
    if j > i: buf[i:j] += a[:j - i]
def filt(x, kind, f, order=2): return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x, axis=0)
def rms100(x):  # sliding 100 ms RMS in dB
    p = (as2(x) ** 2).mean(1); return db(np.sqrt(np.maximum(uniform_filter1d(p, int(0.1 * SR)), 0)))

# BS.1770-4 loudness + true peak (48 kHz)
def _kw(x):
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585], as2(x), axis=0)
    return lfilter([1, -2, 1], [1, -1.99004745483398, 0.99007225036621], y, axis=0)
def _ms(x, win, hop):
    p = (_kw(x) ** 2).sum(1); c = np.concatenate([[0], np.cumsum(p)]); w, h = int(win * SR), int(hop * SR)
    if len(p) < w: return np.array([c[-1] / max(len(p), 1)]), np.array([len(p) / 2 / SR])
    st = np.arange(0, len(p) - w + 1, h); return (c[st + w] - c[st]) / w, (st + w / 2) / SR
def lufs(x):
    z, _ = _ms(x, 0.4, 0.1); L = -0.691 + 10 * np.log10(z + 1e-20); z = z[L > -70]
    if not len(z): return -99.0
    rel = -0.691 + 10 * np.log10(z.mean()) - 10; z = z[-0.691 + 10 * np.log10(z) > rel]
    return float(-0.691 + 10 * np.log10(z.mean()))
def true_peak(x): return float(db(np.abs(resample_poly(as2(x), 4, 1, axis=0)).max()))
def limit(x, ceil=-1.0, look=0.005):  # look-ahead brickwall on 4x-oversampled peaks
    c = 10 ** (ceil / 20); up = np.abs(resample_poly(x, 4, 1, axis=0)).max(1)[:len(x) * 4]
    pk = up.reshape(len(x), 4).max(1); req = np.minimum(1.0, c / np.maximum(pk, 1e-9)); L = int(look * SR)
    g = uniform_filter1d(minimum_filter1d(req, 2 * L + 1), L + 1)
    g = np.minimum(g, uniform_filter1d(minimum_filter1d(g, 4 * L + 1), 2 * L + 1))
    return x * g[:, None]
def compress(x, thr=-24.0, ratio=3.0, att=0.005, rel=0.08):  # feed-forward RMS compressor (VO levelling)
    e = db(np.sqrt(uniform_filter1d((as2(x) ** 2).mean(1), int(0.01 * SR)) + 1e-12)); gr = np.minimum(0, (thr - e) * (1 - 1 / ratio))
    gr = uniform_filter1d(minimum_filter1d(gr, int(att * SR) * 2 + 1), int(rel * SR)); return as2(x) * (10 ** (gr / 20))[:, None]

def read_audio(p):
    """Any audio file -> mono float64 at SR (decoded by ffmpeg, so wav/mp3/flac all work)."""
    r = subprocess.run([FFMPEG, '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


# ================================================================== music: coded phonk-lite bed
TGT = dict(lufs=-14.0, tp=-1.0, ceil=-2.2, vo=-16.0, under=-25.0, sfx_under=6.0, impact=6.0, stack=2)
BPM = 132
LIGHT = {'playful', 'warm', 'triumph'}
MOOD_LVL = {'playful': -14.0, 'warm': -16.5, 'triumph': -13.0, 'suspense': -16.5, 'dark': -12.5, 'sad': -17.5, 'hit': -11.5, 'none': None}
MOOD_ALIAS = {'happy': 'playful', 'fun': 'playful', 'funny': 'playful', 'tense': 'suspense', 'scary': 'dark', 'storm': 'dark', 'drop': 'hit', 'impact': 'hit',
              'boom': 'hit', 'calm': 'warm', 'tender': 'warm', 'win': 'triumph', 'silence': 'none', 'out': 'none'}

def i_kick():
    t = _t(0.42); f = 47 + 125 * np.exp(-t * 32); s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    s[:240] += np.random.default_rng(1).standard_normal(240) * np.exp(-np.arange(240) / 40) * 0.35
    return np.tanh(1.6 * s) / np.tanh(1.6)
def i_clap(rng):
    t = _t(0.3); n = rng.standard_normal(len(t)); e = sum(np.exp(-np.maximum(t - d, 0) * 220) * (t >= d) for d in (0, 0.012, 0.024)) + 0.45 * np.exp(-t * 16)
    s = filt(n * e, 'bandpass', [900, 3800]); return s / np.abs(s).max()
def i_hat(rng, open_=False):
    t = _t(0.28 if open_ else 0.06); s = filt(rng.standard_normal(len(t)), 'highpass', 7000) * np.exp(-t * (11 if open_ else 75))
    return s / np.abs(s).max()
def i_808(f, d, f0=None):
    t = _t(d + 0.09); ff = f + (f0 - f) * np.exp(-t * 22) if f0 else f + 0 * t
    s = np.sin(2 * np.pi * np.cumsum(ff) / SR); s = np.tanh(2.4 * s) / np.tanh(2.4)
    e = np.minimum(1, t / 0.004) * np.exp(-t * 0.9) * np.clip((d + 0.09 - t) / 0.09, 0, 1); return s * e
def i_mallet(f, d=0.5):
    t = _t(d); return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4.0 * f * t) * np.exp(-t * 28) + 0.15 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 6.5) * np.minimum(1, t / 0.002)
def i_bell(f, d=0.35):
    t = _t(d); s = sum(a * (np.sin(2 * np.pi * f * r * t) + 0.25 * np.sin(2 * np.pi * 3 * f * r * t)) for r, a in ((1, 1), (1.4836, 0.7)))
    return filt(s * np.exp(-t * 11) * np.minimum(1, t / 0.0015), 'highpass', 300)
def i_pad(notes, d):
    t = _t(d + 0.4); out = np.zeros((len(t), 2))
    for q in notes:
        f = nf(q)
        for ch, det in ((0, -0.004), (1, 0.004)):
            ph = (f * (1 + det) * t) % 1.0; out[:, ch] += 2 * ph - 1
    e = np.minimum(1, t / 0.18) * np.clip((d + 0.4 - t) / 0.4, 0, 1); return filt(out, 'lowpass', 1400) * e[:, None] / max(len(notes), 1)

HOOK_L = [[69, 72, 74, 72, 69, None, 67, 69, 72, None, 69, 67, 65, None, 67, None],
          [69, 72, 74, 77, 74, None, 72, 74, 72, None, 69, 67, 69, None, None, None]]
HOOK_D = [[74, None, 77, 74, None, 72, 74, None, 69, None, 70, 69, None, 65, None, None],
          [74, None, 77, 79, None, 77, 74, None, 81, None, 79, 77, None, 76, None, None]]
HOOK_S = [[74, None, None, 75, None, None, 74, None, None, None, None, None, None, None, None, None],
          [74, None, None, 75, None, None, 77, None, None, None, 75, None, None, None, None, None]]
ARR = {  # arrangement states: kick steps, clap steps, hats, 808 mode, hook, pad level, low-pass
    'playful': dict(kick=[0, 7, 10], clap=[4, 12], hats='8roll', b='hit', hook=('mallet', HOOK_L), pad=0.5, lp=None),
    'triumph': dict(kick=[0, 7, 10], clap=[4, 12], hats='16', b='hit', hook=('mallet2', HOOK_L), pad=0.8, lp=None),
    'warm': dict(kick=[], clap=[], hats='4', b='long', hook=('mallet', [[q if i % 2 == 0 else None for i, q in enumerate(h)] for h in HOOK_L]), pad=1.0, lp=None),
    'suspense': dict(kick=[0, 10], clap=[], hats='8', b='pulse', hook=('bell', HOOK_S), pad=0.7, lp=1000),
    'dark': dict(kick=[0, 3, 10], clap=[8], hats='16', b='glide', hook=('bell', HOOK_D), pad=0.6, lp=None),
    'sad': dict(kick=[], clap=[], hats=None, b='long', hook=('mallet', [[q if i % 4 == 0 else None for i, q in enumerate(h)] for h in HOOK_D]), pad=1.0, lp=1800)}
ARR['hit'] = dict(ARR['dark'], accent=True)
CH_L = [((53, 57, 60), 29), ((50, 53, 57), 26), ((46, 50, 53), 34), ((48, 52, 55), 36)]   # F Dm Bb C
CH_D = [((50, 53, 57), 26), ((46, 50, 53), 34), ((43, 46, 50), 31), ((45, 49, 52), 33)]   # Dm Bb Gm A

def section(mood, d, seed=0):
    """One arrangement state for d seconds, downbeat at 0 (on the cut). Returns (N, 2)."""
    A = ARR[mood]; rng = np.random.default_rng(seed); st = 60 / BPM / 4; L = max(d, 16 * 4 * st) + 0.05
    n = int(np.ceil(L / st)); N = int((L + 1.5) * SR); drum = np.zeros((N, 2)); mel = np.zeros((N, 2))
    chords = CH_L if mood in LIGHT else CH_D; K = i_kick(); kicks = []
    for k in range(n):
        t = k * st; s16 = k % 16; bar = k // 16; ch, root = chords[bar % 4]
        if s16 in A['kick']: put(drum, K * (0.9 if s16 == 0 else 0.75), t); kicks.append(t)
        if s16 in A['clap']: put(drum, pan2(i_clap(rng) * 0.42, 0), t)
        h = A['hats']
        if h and ((h == '16') or (h in ('8', '8roll') and s16 % 2 == 0) or (h == '4' and s16 % 4 == 2) or (h == '8roll' and bar % 2 == 1 and s16 >= 12)):
            v = (0.13 if s16 % 4 == 2 else 0.08) * (0.7 if h == '4' else 1)
            if h == '8roll' and s16 >= 12 and bar % 2 == 1: v = 0.05 + 0.02 * (s16 - 12)
            put(drum, pan2(i_hat(rng) * v, 0.3 if s16 % 4 == 2 else -0.25), t)
        if mood == 'triumph' and s16 % 4 == 2: put(drum, pan2(i_hat(rng, True) * 0.05, 0.4), t)
        bm = A['b']
        if bm == 'hit' and s16 in A['kick']: put(mel, pan2(i_808(nf(root), 0.32 if s16 else 0.5) * 0.5, 0), t)
        if bm == 'pulse' and s16 in (0, 6, 10): put(mel, pan2(i_808(nf(26 + (1 if s16 == 6 and bar % 2 else 0)), 0.22) * 0.45, 0), t)
        if bm in ('long', 'glide') and s16 == 0:
            nxt = chords[(bar + 1) % 4][1]
            put(mel, pan2(i_808(nf(root), 16 * st * (0.85 if bm == 'glide' else 1.0)) * (0.45 if bm == 'glide' else 0.3), 0), t)
            if bm == 'glide': put(mel, pan2(i_808(nf(nxt), 2 * st, f0=nf(root + 12)) * 0.4, 0), t + 14 * st)
        if s16 % 2 == 0:
            inst, H = A['hook']; q = H[bar % 2][s16 // 2] if mood != 'sad' else H[(bar // 2) % 2][s16 // 2]
            if q is not None:
                a = i_bell(nf(q)) * 0.2 if inst == 'bell' else i_mallet(nf(q)) * 0.22
                if inst == 'mallet2': a = a + i_mallet(nf(q + 12)) * 0.1
                put(mel, pan2(a * 0.85, -0.15), t); put(mel, pan2(a * 0.3, 0.7), t + 3 * st)  # dotted-8th echo
        if s16 == 0 and A['pad']: put(mel, i_pad(ch, 16 * st) * 0.09 * A['pad'], t)
    if A.get('accent'):  # the drop: sub boom + crash on the cut frame
        t = _t(1.6); cr = filt(rng.standard_normal((len(t), 2)), 'highpass', 4000) * np.exp(-t * 3.5)[:, None] * 0.18
        put(drum, pan2(K * 1.0, 0), 0); put(mel, pan2(i_808(nf(26), 1.4, f0=nf(38)) * 0.5, 0), 0); put(drum, cr, 0)
    if kicks:  # light sidechain pump on the melodic bus
        sc = np.ones(N); env = 1 - 0.35 * np.exp(-_t(0.25) * 14)
        for i in (np.array(kicks) * SR).astype(int): j = min(N, i + len(env)); sc[i:j] = np.minimum(sc[i:j], env[:j - i])
        mel *= sc[:, None]
    if A['lp']: mel = filt(mel, 'lowpass', A['lp']); drum = drum * 0.6 + 0.4 * filt(drum, 'lowpass', A['lp'])
    out = drum + mel; w = int(min(L, 8) * SR)
    for _ in range(3):  # tape-style soft clip until crest is about 10 dB
        cr = true_peak(out[:w]) - lufs(out[:w])
        if cr <= 10.5: break
        k = 10 ** ((cr - 9.5) / 20); pk = np.abs(out).max(); out = np.tanh(out / pk * k) / np.tanh(k) * pk
    return out * 10 ** ((MOOD_LVL[mood] - lufs(out[:w])) / 20)

def norm_mood(m):
    m = str(m or 'playful').lower(); m = MOOD_ALIAS.get(m, m); return m if m in MOOD_LVL else 'playful'

def music_plan(spec):
    """Mood sections snapped to the nearest shot cut. spec['music'] = [[frac_or_shot_index, mood], ...]; an int >= 1 is a shot index."""
    T = spec['dur']; cuts = [x['t0'] for x in spec['shots']]; segs = spec.get('music') or [[0, 'playful'], [0.62, 'suspense'], [0.88, 'dark']]
    out = []
    for a, mood in segs:
        t = cuts[a] if isinstance(a, int) and 0 < a < len(cuts) else float(a) * T
        t = 0.0 if t <= 0 else min(cuts, key=lambda c: abs(c - t))
        out = [o for o in out if o[0] < t] + [(t, norm_mood(mood))]
    if not out or out[0][0] > 0: out.insert(0, (0.0, 'playful'))
    secs = [(out[i][0], out[i + 1][0] if i + 1 < len(out) else T, out[i][1]) for i in range(len(out))]
    return [x for x in secs if x[1] > x[0]]

def speech_regions(words, merge=0.6):
    r = []
    for _, a, b in words:
        if r and a - r[-1][1] < merge: r[-1][1] = b
        else: r.append([a, b])
    return r

def holes_plan(spec, secs, words):
    """1-2 hard silences: before light->tension switches and on shots with 'silence': sec."""
    cand = [b0 for (a0, b0, m0), (a1, b1, m1) in zip(secs, secs[1:]) if m0 in LIGHT and m1 not in LIGHT and m1 != 'none']
    cand += [x['t0'] for x in spec['shots'] if x.get('silence')]
    cand = sorted(set(cand)); room = max(0, 2 - sum(m == 'none' for a, b, m in secs if a > 0))
    cand = cand if len(cand) <= room else ([cand[0], cand[-1]][:room] if room else [])
    out = []
    for t in cand:
        sh_ = next((x for x in spec['shots'] if abs(x['t0'] - t) < 1e-6), {})
        want = float(sh_.get('silence') or 0.4) if not isinstance(sh_.get('silence'), bool) else 0.4
        last = max([b for _, a, b in words if b <= t + 0.02] or [0]); a = max(t - want, last + 0.03)
        if t - a >= 0.15: out.append((round(a, 3), t))
    return out

def tapestop(x):
    n = len(x); r = np.clip(1 - np.arange(n) / n, 0, 1) ** 1.3; pos = np.cumsum(r) * (n / max(np.cumsum(r)[-1], 1)) * (r.sum() / n)
    return np.stack([np.interp(pos, np.arange(n), x[:, c]) for c in range(x.shape[1])], 1) * np.linspace(1, 0.2, n)[:, None]

def music_bed(spec, secs, holes=()):
    T = spec['dur']; N = int(round((T + 1) * SR)); m = np.zeros((N, 2))
    for k, (a, b, mood) in enumerate(secs):
        if mood == 'none': continue
        x = section(mood, b - a, seed=k)[:int((b - a + 0.03) * SR)]; f = min(len(x), int(0.03 * SR))
        x[len(x) - f:] *= np.linspace(1, 0, f)[:, None]; put(m, x, a)
    mid, side = (m[:, 0] + m[:, 1]) / 2, (m[:, 0] - m[:, 1]) / 2; side = filt(side, 'highpass', 150) * 2.6  # wide, mono-safe lows
    m = np.stack([mid + side, mid - side], 1)
    for a, b in list(holes) + [(a, b) for a, b, md in secs if md == 'none' and a > 0]:  # tape-stop into silence
        i, j, k = int(a * SR), int(b * SR), int(0.22 * SR); k = min(k, i)
        if k: m[i - k:i] = tapestop(m[i - k:i].copy())
        m[i:j] = 0
    e = int(0.35 * SR); end = int(T * SR); m[end - e:end] *= np.linspace(1, 0, e)[:, None]; m[end:] = 0
    return m


# ================================================================== SFX (all synthesized, no sample files)
def _norm(a): a = as2(a); return a / (np.abs(a).max() + 1e-12)
def _sweep(f, d): return np.sin(2 * np.pi * np.cumsum(f) / SR)
def _thunder(seed=3, d=2.6):
    t = _t(d); r = np.random.default_rng(seed); n = r.standard_normal((len(t), 2))
    brown = np.cumsum(n, 0); brown -= uniform_filter1d(brown, int(0.05 * SR), axis=0)  # red noise, DC removed
    body = filt(brown, 'lowpass', 260, 4)
    env = np.minimum(1, t / 0.04) * np.exp(-t * 1.3)
    for c, w in ((0.35, 0.8), (0.9, 0.6), (1.5, 0.35)):  # rolling swells
        env += w * np.exp(-((t - c) / 0.18) ** 2)
    crack = filt(n, 'highpass', 1200) * np.exp(-t * 30)[:, None] * 0.6
    return _norm(body * env[:, None] + crack)
def _whoosh(d, f0, f1, seed=4):
    t = _t(d); n = np.random.default_rng(seed).standard_normal((len(t), 2)); x = np.zeros_like(n)
    bands = np.geomspace(min(f0, f1), max(f0, f1), 6); fc = np.geomspace(f0, f1, len(t))
    for b in bands:  # crossfade between band-passed copies to move the centre
        w = np.exp(-(np.log(fc / b) / 0.45) ** 2); x += filt(n, 'bandpass', [b / 1.4, min(b * 1.4, SR / 2 - 100)]) * w[:, None]
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return _norm(x * env[:, None])
def _rain(d=6.0, seed=9):
    r = np.random.default_rng(seed); n = len(_t(d)); hiss = filt(r.standard_normal((n, 2)), 'bandpass', [500, 7000])
    drops = (r.random((n, 2)) < 0.0015) * r.uniform(0.3, 1.0, (n, 2))
    drops = filt(drops, 'bandpass', [1800, 6500]) * 6
    flutter = 1 + 0.15 * filt(r.standard_normal((n, 2)), 'lowpass', 3)
    return _norm(hiss * flutter + drops)

def _make(nm, rng):
    if nm == 'step':  # soft footstep: heel thump + scuff
        t = _t(0.16); f = (80 + 40 * rng.random()) * (1 + 0.6 * np.exp(-t * 60))
        th = _sweep(f, 0.16) * np.exp(-t * 38); sc = filt(rng.standard_normal(len(t)), 'bandpass', [300, 2500]) * np.exp(-t * 55) * 0.6
        return pan2(th + sc, 0)
    if nm == 'lightning':  # crack on the bolt frame, re-crack on the 0.14 s flicker, synthetic thunder tail
        t = _t(0.7); n = np.random.default_rng(5).standard_normal((len(t), 2))
        crk = filt(n, 'highpass', 1500) * np.exp(-t * 26)[:, None]
        crackle = (np.random.default_rng(6).random(len(t)) < 0.004) * np.exp(-t * 9) * 3; crk += filt(np.stack([crackle, np.roll(crackle, 37)], 1), 'highpass', 800)
        body = filt(n[:, ::-1], 'lowpass', 220) * np.exp(-t * 7)[:, None] * 3.0
        a = np.zeros((int(3.0 * SR), 2)); put(a, crk + body, 0); put(a, (crk + body) * 0.45, 0.14)
        th = _thunder(5, 2.2); th[-int(0.6 * SR):] *= np.linspace(1, 0, int(0.6 * SR))[:, None]
        put(a, th * 0.35 * np.abs(crk + body).max(), 0.06); return _norm(a)
    if nm == 'flashboom':
        t = _t(0.9); f = 38 + 70 * np.exp(-t * 18); s = _sweep(f, 0.9) * np.exp(-t * 4.5)
        s += filt(np.random.default_rng(7).standard_normal(len(t)), 'lowpass', 400) * np.exp(-t * 12) * 0.5; return pan2(np.tanh(1.5 * s), 0)
    if nm == 'poof':
        t = _t(0.3); nz = np.random.default_rng(8).standard_normal(len(t))
        y = filt(nz, 'bandpass', [500, 2400]) * np.exp(-t * 20) * np.minimum(1, t / 0.006)
        f = 220 * np.exp(-t * 10) + 90; y += 0.8 * _sweep(f, 0.3) * np.exp(-t * 22)
        return np.stack([y, np.roll(y, int(0.0007 * SR))], 1)
    if nm in ('rain', 'drizzle'):
        a = filt(_rain(), 'lowpass', 5000 if nm == 'drizzle' else 9000); return a + 0.25 * (a[:, ::-1] - a)
    if nm == 'thunder': return _thunder()
    if nm == 'whoosh': return _whoosh(0.45, 400, 3000)
    if nm == 'whoosh_up': return _whoosh(0.6, 250, 5000)
    if nm == 'whoosh_down': return _whoosh(0.7, 4000, 200)
    if nm == 'riser':
        t = _t(1.6); x = _whoosh(1.6, 300, 8000) * (t / 1.6)[:, None] ** 2
        return _norm(x + pan2(_sweep(200 + 1000 * (t / 1.6) ** 2, 1.6) * (t / 1.6) ** 2 * 0.3, 0))
    if nm == 'pop':
        t = _t(0.12); f = 300 + 900 * np.exp(-t * 60); return pan2(_sweep(f, 0.12) * np.exp(-t * 40) * np.minimum(1, t / 0.001), 0)
    if nm == 'boing':
        t = _t(0.7); f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 60 * np.exp(-t * 6)
        return pan2((_sweep(f, 0.7) + 0.3 * _sweep(2 * f, 0.7)) * np.exp(-t * 3.5) * np.minimum(1, t / 0.003), 0)
    if nm in ('ding', 'bell'):
        t = _t(1.2); f = 1568 if nm == 'ding' else 880
        s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dk) for r, a, dk in ((1, 1, 3), (2.76, 0.4, 6), (5.4, 0.2, 10)))
        return pan2(s * np.minimum(1, t / 0.001), 0)
    if nm == 'correct':
        a = np.zeros((int(0.8 * SR), 2)); t = _t(0.6)
        for k, f in enumerate((1047, 1568)): put(a, pan2((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 6) * np.minimum(1, t / 0.002), 0), k * 0.11)
        return a
    if nm == 'cash':  # cha-ching: drawer rattle + two bells
        a = np.zeros((int(1.0 * SR), 2)); t = _t(0.08)
        put(a, pan2(filt(rng.standard_normal(len(t)), 'bandpass', [2000, 7000]) * np.exp(-t * 50), 0), 0)
        put(a, _make('ding', rng) * 0.7, 0.09); put(a, pan2(np.sin(2 * np.pi * 2637 * _t(0.8)) * np.exp(-_t(0.8) * 5), 0) * 0.6, 0.16)
        return a
    if nm in ('impact', 'boom'):
        d = 0.9 if nm == 'impact' else 1.8; t = _t(d); f = 35 + 60 * np.exp(-t * 14)
        s = np.tanh(1.8 * _sweep(f, d) * np.exp(-t * (5 if nm == 'impact' else 2.2)))
        nz = filt(np.random.default_rng(12).standard_normal((len(t), 2)), 'lowpass', 900) * np.exp(-t * (14 if nm == 'impact' else 4))[:, None] * 0.5
        return _norm(pan2(s, 0) + nz)
    if nm in ('tick', 'click', 'snap'):
        f, d = {'tick': (2000, 0.03), 'click': (3500, 0.02), 'snap': (1500, 0.06)}[nm]; t = _t(d)
        s = np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + filt(rng.standard_normal(len(t)), 'highpass', 3000) * np.exp(-t * 400) * (1.2 if nm == 'snap' else 0.4)
        return pan2(s, 0)
    if nm == 'heartbeat':
        a = np.zeros((int(0.7 * SR), 2)); t = _t(0.18)
        for k, v in ((0, 1), (0.28, 0.7)): put(a, pan2(_sweep(55 + 30 * np.exp(-t * 30), 0.18) * np.exp(-t * 22) * v, 0), k)
        return a
    if nm == 'glitch':
        t = _t(0.35); s = np.sign(np.sin(2 * np.pi * rng.choice([180, 440, 900, 1500], 8).repeat(len(t) // 8 + 1)[:len(t)] * t))
        return pan2(s * (rng.random(8).repeat(len(t) // 8 + 1)[:len(t)] > 0.3) * 0.5, 0)
    if nm == 'stamp':
        t = _t(0.25); s = _sweep(90 + 120 * np.exp(-t * 40), 0.25) * np.exp(-t * 25) + filt(rng.standard_normal(len(t)), 'bandpass', [600, 3000]) * np.exp(-t * 45) * 0.7
        return pan2(s, 0)
    if nm == 'squeak':
        t = _t(0.22); f = 1800 + 800 * t / 0.22 + 120 * np.sin(2 * np.pi * 30 * t); return pan2(_sweep(f, 0.22) * np.sin(np.pi * t / 0.22), 0)
    if nm == 'scratch':
        t = _t(0.4); f = 250 + 650 * np.abs(np.sin(2 * np.pi * 5 * t)); ph = np.cumsum(f) / SR % 1
        return pan2(filt(2 * ph - 1, 'bandpass', [300, 4000]) * np.sin(np.pi * t / 0.4), 0)
    if nm == 'drop':
        t = _t(1.3); return pan2(np.tanh(2 * _sweep(400 * np.exp(-t * 2.6) + 40, 1.3)) * np.minimum(1, t / 0.005) * np.exp(-t * 1.6), 0)
    raise KeyError(nm)

SFX = {'whoosh', 'whoosh_up', 'whoosh_down', 'pop', 'boing', 'ding', 'impact', 'boom', 'riser', 'scratch', 'bell', 'thunder', 'rain',
       'correct', 'cash', 'heartbeat', 'glitch', 'tick', 'snap', 'squeak', 'drop', 'click', 'stamp'}  # usable in shot 'sfx': ['name@dt']
SFX_GAIN = {'boom': -2, 'impact': -2, 'thunder': -4, 'scratch': -3, 'rain': -14, 'riser': -8}
_C = {}
def sfx_asset(nm, rng):
    if nm == 'step': return trim_on(_make('step', rng), -24) * (0.85 + 0.3 * rng.random())
    if nm not in _C:
        a = as2(_make(nm, np.random.default_rng(len(_C) + 21)))
        _C[nm] = a if nm in ('rain', 'drizzle') else trim_on(a)
    return _C[nm]

def loop_to(a, d, fade_in=0.008, fade_out=0.04):
    n = int(d * SR); x = a; xf = int(0.25 * SR)
    while len(x) < n:
        w = np.linspace(0, 1, xf)[:, None]; x = np.concatenate([x[:-xf], x[-xf:] * (1 - w) + a[:xf] * w, a[xf:]])
    x = x[:n].copy(); fi, fo = min(n, int(fade_in * SR)), min(n, int(fade_out * SR))
    x[:fi] *= np.linspace(0, 1, fi)[:, None]; x[n - fo:] *= np.linspace(1, 0, fo)[:, None]; return x

def fx_items(a):
    for f in a.get('fx', []) or []:
        nm, _, off = str(f).partition('@')
        try: off = float(off) if off else 0.0
        except ValueError: off = 0.0
        yield nm, off

RAIN_LVL = {'drizzle': -34, 'raincloud': -30, 'storm': -28.5, 'bigstorm': -28}
def build_cues(spec):
    """Every cue = effect start (shot t0 + fx @offset). kind: impact | shot | loop."""
    cues = []; pan_of = lambda a: float(np.clip((a.get('at') or [0])[0] / 12.0, -0.25, 0.25))
    for x in spec['shots']:
        t0, t1 = x['t0'], x['t1']; bolts = []
        for a in x.get('actors', []):
            p = pan_of(a)
            for nm, off in fx_items(a):
                t = t0 + off
                if t >= t1: continue
                if nm in RAIN_LVL and off < 0:  # carried over: the loop continues
                    cues.append(dict(nm='drizzle' if nm == 'drizzle' else 'rain', t=t0, kind='loop', pri=5, pan=0, lufs=RAIN_LVL[nm], dur=t1 - t0, cont=True))
                elif off < 0: continue
                elif nm in RAIN_LVL:
                    cues.append(dict(nm='poof', t=t, kind='shot', pri=6, pan=p, rel=-1))
                    if t + 0.25 < t1: cues.append(dict(nm='drizzle' if nm == 'drizzle' else 'rain', t=t + 0.25, kind='loop', pri=5, pan=0, lufs=RAIN_LVL[nm], dur=t1 - t - 0.25))
                elif nm == 'bolt': cues.append(dict(nm='lightning', t=t, kind='impact', pri=10, pan=0, rel=TGT['impact'])); bolts.append(t)
                elif nm == 'smoke': cues.append(dict(nm='whoosh_down', t=t, kind='shot', pri=3, pan=p, rel=-6))
                elif nm.startswith('tag:'): cues.append(dict(nm='pop', t=t, kind='shot', pri=6, pan=0, rel=-1))
                elif nm == 'money': cues.append(dict(nm='cash', t=t, kind='shot', pri=6, pan=p, rel=-2))
                elif nm in ('sparkle', 'glow'): cues.append(dict(nm='ding', t=t, kind='shot', pri=5, pan=p, rel=-4))
            if a.get('walkTo') and a.get('anim') in ('walk', 'run') and a.get('at'):  # foot contacts at cycle phase 0.25 / 0.75
                k = (spec.get('cast') or {}).get(a['who'], {}).get('height', 1.0); dist = math.dist(a['at'][:2], a['walkTo'][:2])
                v = dist / max(t1 - t0, 0.1); run = a['anim'] == 'run'; stride = (4.0 if run else 2.6) * k / (0.6 if run else 1.0)
                if v > 0.05:
                    per = stride / v; c = 0.25
                    while c * per < t1 - t0 - 0.05:
                        cues.append(dict(nm='step', t=t0 + c * per, kind='shot', pri=3, pan=p, rel=-8)); c += 0.5
        if x.get('flash'):
            near = [b for b in bolts if 0 <= b - t0 <= 0.15]
            cues.append(dict(nm='flashboom', t=t0, kind='impact', pri=9, pan=0, rel=TGT['impact'] - (1 if near else 0)))
        if str(x.get('move') or '').startswith('crash'): cues.append(dict(nm='whoosh_up', t=max(0.0, t0 - 0.1), kind='shot', pri=4, pan=0, rel=-5))
        for c in x.get('sfx', []) or []:
            nm, _, dt = str(c).partition('@')
            if nm in SFX:
                big = nm in ('impact', 'boom', 'thunder')
                cues.append(dict(nm=nm, t=t0 + float(dt or 0), kind='impact' if big else 'shot', pri=7, pan=0, rel=TGT['impact'] if big else SFX_GAIN.get(nm, -8) + 6))
    loops = []  # merge a loop with its continuation in the next shot
    for c in sorted([c for c in cues if c['kind'] == 'loop'], key=lambda c: c['t']):
        if loops and loops[-1]['nm'] == c['nm'] and abs(loops[-1]['t'] + loops[-1]['dur'] - c['t']) < 0.03: loops[-1]['dur'] += c['dur']
        elif not c.get('cont'): loops.append(c)
    return [c for c in cues if c['kind'] != 'loop'] + loops

def active_span(a, rel=-15):
    r = rms100(a) if len(a) > SR // 10 else db(np.abs(as2(a)).max(1)); above = np.nonzero(r >= r.max() + rel)[0]
    return (above[-1] + 1) / SR if len(above) else len(a) / SR

def mix(d, spec, words):
    """Stereo mix: VO -16 LUFS, coded bed ducked under speech, SFX on cues, master to TGT['lufs'] / -1 dBTP."""
    T = spec['dur']; N = int(round(T * SR)); vo = np.zeros((N, 2)); vp = os.path.join(d, 'vo.wav'); has_vo = os.path.exists(vp)
    if has_vo:
        v = read_audio(vp)[:N]; vo[:len(v)] = as2(v)
        vo *= 10 ** ((TGT['vo'] - lufs(vo)) / 20); vo = compress(vo, -26, 3.0); vo *= 10 ** ((TGT['vo'] - lufs(vo)) / 20)
    words = words if has_vo else []
    secs = music_plan(spec); holes = holes_plan(spec, secs, words); m = music_bed(spec, secs, holes)[:N]
    if len(m) < N: m = np.concatenate([m, np.zeros((N - len(m), 2))])
    ctl = np.zeros(int(T * 1000) + 2); regs = speech_regions(words)
    for a, b in regs: ctl[max(0, int((a - 0.06) * 1000)):int((b + 0.15) * 1000)] = 1
    ctl = uniform_filter1d(ctl, 60); dd = np.zeros_like(ctl)
    for a, b, mood in secs:
        if MOOD_LVL.get(mood) is not None:
            dd[int(a * 1000):int(b * 1000) + 1] = max(-6.0, TGT['under'] - MOOD_LVL[mood]) if mood == 'hit' else min(0.0, TGT['under'] - MOOD_LVL[mood])
    m *= 10 ** (np.interp(np.arange(N) / SR, np.arange(len(ctl)) / 1000, ctl * dd) / 20)[:, None]
    # SFX bus
    bed = rms100(m); bedq = np.median(bed[bed > -70]) if (bed > -70).any() else -40
    def bed_at(t):
        i, j = int(max(0, t - 1) * SR), int(min(T, t + 1) * SR); w = bed[i:j]; w = w[w > -70]; return float(np.median(w)) if len(w) else bedq
    rng = np.random.default_rng(11); cues = sorted(build_cues(spec), key=lambda c: c['t'])
    for c in cues:
        a = sfx_asset(c['nm'], rng)
        if c['kind'] == 'loop': a = loop_to(trim_on(a, -9), c['dur']); a = a * 10 ** ((c['lufs'] - lufs(a)) / 20)
        else: a = a * 10 ** ((bed_at(c['t']) + c['rel'] - rms100(a).max()) / 20)
        if c.get('pan'): a = a * np.array([np.sqrt(1 - c['pan']) if c['pan'] > 0 else 1, np.sqrt(1 + c['pan']) if c['pan'] < 0 else 1])
        c['a'] = a; c['span'] = (c['t'], c['t'] + (c['dur'] if c['kind'] == 'loop' else active_span(a)))
    keep = []  # stacking guard: max 2 layers alive; lower-priority one-shots yield, loops duck out
    for c in sorted([c for c in cues if c['kind'] != 'loop'], key=lambda c: -c['pri']):
        a0, b0 = c['span']; pts = [a0] + [k['span'][0] for k in keep if a0 <= k['span'][0] < b0]
        if all(1 + sum(k['span'][0] <= p < k['span'][1] for k in keep) <= TGT['stack'] for p in pts): keep.append(c)
    cnt = np.zeros(int(T * 100) + 2)
    for k in keep: cnt[int(k['span'][0] * 100):int(np.ceil(k['span'][1] * 100))] += 1
    for c in [c for c in cues if c['kind'] == 'loop']:
        w = (cnt >= TGT['stack']).astype(float)[int(c['t'] * 100):int(c['t'] * 100) + int(c['dur'] * 100) + 1]
        w = uniform_filter1d(maximum_filter1d(w, 11, mode='nearest'), 4, mode='nearest')
        c['a'] = c['a'] * np.interp(np.arange(len(c['a'])) / SR, np.arange(len(w)) / 100, 1 - np.clip(w, 0, 1) * 0.985)[:, None]; keep.append(c)
    fx = np.zeros((N, 2))
    for c in keep: put(fx, c['a'], c['t'])
    if has_vo:  # SFX bus >= 6 LU under the VO
        over = lufs(fx) - (TGT['vo'] - TGT['sfx_under'])
        if over > 0: fx *= 10 ** (-min(over, TGT['impact'] - 4.5) / 20)
    for a, b in holes: fx[int(a * SR):int(b * SR)] = 0; m[int(a * SR):int(b * SR)] = 0
    pre = vo + m + fx; g = 10 ** ((TGT['lufs'] - lufs(pre)) / 20)
    def master(g): return limit(limit(vo * g, -3.0) + limit(m * g, -4.0) + limit(fx * g, -3.0), TGT['ceil'])
    for _ in range(5):
        out = master(g); err = TGT['lufs'] - lufs(out); g *= 10 ** (err / 20)
        if abs(err) < 0.1: break
    out = master(g); tp = true_peak(out)
    if tp > TGT['tp']: out *= 10 ** ((TGT['tp'] - 0.05 - tp) / 20)
    out = np.concatenate([out, np.zeros((int(round(TAG_S * SR)), 2))])  # silence under the end card
    print(f'mix: {lufs(out):.1f} LUFS, TP {true_peak(out):.2f} dBTP, VO {"yes" if has_vo else "none"}, '
          f'{len(keep)} SFX cues, sections {[(round(a, 2), md) for a, b, md in secs]}', flush=True)
    return out.astype(np.float32)


# ================================================================== picture: captions + brand
# Fallback copies of the brand art (used only when the PNGs are missing from kit/assets/brand).
_WM_B64 = (
    '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')
_MK_B64 = (
    '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')

def _art(name, b64):
    p = os.path.join(BRAND, name)
    try: im = Image.open(p).convert('RGBA'); im.load()
    except Exception: im = Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bb) if bb else im

def _fit(im, w): return im.resize((max(1, int(w)), max(1, round(im.height * w / im.width))), Image.LANCZOS)
def _alpha(im, k): im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * k))); return im

def _badge(art, w, opacity, shadow=0.6, blur=5, off=3):
    """Art scaled to width w, faded to opacity, over a soft dark shadow. Returns RGBA patch + its padding."""
    a = _alpha(_fit(art, w), opacity); pad = blur * 3 + off
    sh = Image.new('RGBA', (a.width + 2 * pad, a.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new('L', sh.size, 0); m.paste(a.getchannel('A'), (pad + off, pad + off))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * shadow))
    sh.putalpha(m); sh.alpha_composite(a, (pad, pad)); return sh, pad

G = {}
def _init(d):
    sp = json.load(open(os.path.join(d, 'timed.json'), encoding='utf8'))
    G['d'] = d; G['keys'] = set(norm(k) for k in sp.get('keys', [])); words = load_words(d); cap = []
    for k, (w, s0, e) in enumerate(words):
        nxt = words[k + 1][1] if k + 1 < len(words) else e + 0.5
        cap.append((re.sub(r"[^\w'$%]", '', w).lower(), s0, min(nxt, s0 + 0.9)))
    G['cap'] = cap; G['wm'] = _art('bv-wordmark-transparent.png', _WM_B64); G['mk'] = _art('bv-mark-transparent.png', _MK_B64)
    G['fonts'] = {}; G['sz'] = None

def _font(size):
    if size not in G['fonts']: G['fonts'][size] = ImageFont.truetype(FONT, size)
    return G['fonts'][size]

def _sized(W, H):
    if G['sz'] != (W, H):
        G['sz'] = (W, H); G['wmp'] = _badge(G['wm'], 0.16 * W, 0.75)
        G['mks'] = {}
    return G['wmp']

def _finish(im):
    """Brand pass on every frame: wordmark top-right, 4 % in from the right edge, just below the Shorts top bar."""
    W, H = im.size; (p, pad) = _sized(W, H)
    x = int(W - 0.04 * W - (p.width - 2 * pad)) - pad; y = int(0.085 * H) - pad
    base = im.convert('RGBA'); base.alpha_composite(p, (x, y)); return base

def comp_frame(i, n):
    d = G['d']; src = os.path.join(d, 'frames', f'{min(i, n - 1):05d}.jpg')
    if not os.path.exists(src):  # hold the nearest rendered frame
        k = next((k for k in list(range(i, -1, -1)) + list(range(i + 1, n)) if os.path.exists(os.path.join(d, 'frames', f'{k:05d}.jpg'))), None)
        src = os.path.join(d, 'frames', f'{k:05d}.jpg')
    im = Image.open(src).convert('RGB'); W, H = im.size; s = W / 1080; t = i / FPS
    im = _finish(im); cur = [c for c in G['cap'] if c[1] <= t < c[2]]
    if cur:
        w, s0, e = cur[-1]; k = (t - s0) * FPS
        sc = 1.0 + 0.28 * max(0.0, 1 - k / 3.0); key = norm(w) in G['keys'] or any(ch.isdigit() for ch in w)
        size = int((118 if key else 96) * sc * s); f = _font(size)
        while f.getlength(w) > 980 * s and size > 50 * s: size -= int(6 * s) or 1; f = _font(size)
        cx, cy = W / 2, 1290 / 1920 * H; dr = ImageDraw.Draw(im)
        dr.text((cx, cy + 6 * s), w, font=f, anchor='mm', fill=(0, 0, 0), stroke_width=int(11 * sc * s), stroke_fill=(0, 0, 0))
        dr.text((cx, cy), w, font=f, anchor='mm', fill=(255, 222, 40) if key else (255, 255, 255), stroke_width=int(10 * sc * s), stroke_fill=(20, 15, 25))
        bb = dr.textbbox((cx, cy), w, font=f, anchor='mm', stroke_width=int(10 * sc * s))  # mark as a corner badge on the caption
        mw = int(0.5 * size)
        if mw not in G['mks']: G['mks'][mw] = _badge(G['mk'], mw, 0.95, shadow=0.7, blur=3, off=2)
        mp, mpad = G['mks'][mw]
        mh = mp.height - 2 * mpad; mx = int(min(W - 0.03 * W - mw, bb[2] - 0.25 * mw)) - mpad; my = int(bb[1] - 0.55 * mh) - mpad
        im.alpha_composite(mp, (mx, my))
    im.convert('RGB').save(os.path.join(d, 'comp', f'{i:05d}.jpg'), quality=94)

def tag_frame(i, n, W, H):
    """End card: navy, wordmark centred, credit line below."""
    im = Image.new('RGBA', (W, H), (11, 16, 38, 255)); s = W / 1080
    wm, pad = _badge(G['wm'], 0.62 * W, 1.0, shadow=0.5, blur=8, off=4)
    im.alpha_composite(wm, (int((W - wm.width) / 2), int(0.45 * H - wm.height / 2)))
    dr = ImageDraw.Draw(im); f = _font(int(46 * s))
    dr.text((W / 2, 0.45 * H + wm.height / 2 + 30 * s), TAG_TEXT, font=f, anchor='mt', fill=(190, 205, 230))
    k = (i - n) / max(1, int(round(TAG_S * FPS)) - 1)  # short fade in from the last frame's black edge
    if k < 0.2: im = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), im, 0.5 + 2.5 * k)
    im.convert('RGB').save(os.path.join(G['d'], 'comp', f'{i:05d}.jpg'), quality=94)

def _work(args):
    i, n, W, H = args
    if i < n: comp_frame(i, n)
    else: tag_frame(i, n, W, H)


# ================================================================== encode
def _has_nvenc():
    try:
        r = subprocess.run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', 'color=s=256x256:d=0.1', '-c:v', 'h264_nvenc', '-f', 'null', '-'], capture_output=True)
        return r.returncode == 0
    except Exception: return False

def encode(d, wav, out):
    v = (['-c:v', 'h264_nvenc', '-preset', 'p7', '-rc', 'vbr', '-cq', '18', '-b:v', '0'] if _has_nvenc() else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18'])
    meta = sum((['-metadata', f'{k}={v_}'] for k, v_ in META.items()), [])
    cmd = [FFMPEG, '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(d, 'comp', '%05d.jpg'), '-i', wav] + v + \
          ['-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-ar', str(SR), '-shortest'] + meta + \
          ['-movflags', '+faststart+use_metadata_tags', out]
    print('encode:', v[1], flush=True); subprocess.run(cmd, check=True)


def post(d):
    d = os.path.abspath(d); t_start = time.time(); name = os.path.basename(d.rstrip('\\/'))
    spec = json.load(open(os.path.join(d, 'timed.json'), encoding='utf8')); words = load_words(d)
    n = int(math.ceil(spec['dur'] * FPS)); ntag = int(round(TAG_S * FPS))
    comp = os.path.join(d, 'comp'); shutil.rmtree(comp, ignore_errors=True); os.makedirs(comp); os.makedirs(os.path.join(d, 'out'), exist_ok=True)
    first = sorted(f for f in os.listdir(os.path.join(d, 'frames')) if f.endswith('.jpg'))
    if not first: sys.exit('no frames/*.jpg in ' + d)
    W, H = Image.open(os.path.join(d, 'frames', first[0])).size
    with Pool(os.cpu_count(), initializer=_init, initargs=(d,)) as pool:  # captions + brand in parallel with the mix
        r = pool.map_async(_work, [(i, n, W, H) for i in range(n + ntag)], chunksize=4)
        audio = mix(d, spec, words); r.get()
    wav = os.path.join(d, 'mix.wav'); wavfile.write(wav, SR, audio)
    out = os.path.join(d, 'out', f'{name}.mp4'); encode(d, wav, out)
    print(f'wrote {out} ({n} frames + {ntag} end card) in {time.time() - t_start:.0f}s', flush=True)
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    post(sys.argv[1])
