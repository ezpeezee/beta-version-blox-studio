"""Voice for a project with Kokoro TTS (free, Apache 2.0, runs on CPU or GPU).

  python kit/blox/voice.py PROJECTDIR

Reads PROJECTDIR/timed.json (written by shots.py), speaks each shot's `text` (words in brackets are skipped),
then fits the shots to the voice: a shot that is shorter than its line (+ a small pause) is lengthened and every
later shot moves along. Writes:
  vo.wav       the voice track, 24 kHz mono
  words.json   [[word, start_s, end_s], ...] from Kokoro's word timestamps (captions + lip-sync follow it)
  timed.json   re-timed shots (shot-local times such as faceAt, animAt and talk stay as they are)
  voice/       one cached wav + json per line, so unchanged lines are not spoken again

Voice: timed.json "voice" (default af_heart), a shot's "voice" overrides it. Speed: timed.json "voice_speed" (1.0).
American voices start with a (af_heart, af_bella, af_nicole, am_michael, am_fenrir, am_puck),
British with b (bf_emma, bf_isabella, bm_george, bm_fable). Full list: huggingface.co/hexgrad/Kokoro-82M (VOICES.md).
"""
import hashlib, json, os, re, sys
import numpy as np

SR = 24000
PAD_IN, PAD_OUT = 0.08, 0.25  # silence before each line inside its shot, and the pause after it


def spoken(text):
    return re.sub(r'\([^)]*\)|\[[^\]]*\]', '', text).strip()


def line_audio(pipes, text, voice, speed, cache):
    key = hashlib.sha1(f'{voice}|{speed}|{text}'.encode('utf8')).hexdigest()[:16]
    wp, jp = os.path.join(cache, key + '.npy'), os.path.join(cache, key + '.json')
    if os.path.exists(wp) and os.path.exists(jp):
        return np.load(wp), json.load(open(jp, encoding='utf8'))
    lang = voice[0] if voice[0] in 'ab' else 'a'
    if lang not in pipes:
        from kokoro import KPipeline
        pipes[lang] = KPipeline(lang_code=lang)
    chunks, words, t = [], [], 0.0
    for r in pipes[lang](text, voice=voice, speed=speed):
        a = r.audio
        if a is None: continue
        a = a.detach().cpu().numpy() if hasattr(a, 'detach') else np.asarray(a)
        a = a.astype(np.float32).reshape(-1)
        toks = getattr(r, 'tokens', None) or []
        got = False
        for tk in toks:
            w = (tk.text or '').strip()
            if not w or not re.search(r'\w', w): continue
            if tk.start_ts is None or tk.end_ts is None: continue
            words.append([w, round(t + tk.start_ts, 3), round(t + tk.end_ts, 3)]); got = True
        if not got:  # no timestamps from this chunk: spread its words across the chunk
            ws = [w for w in (getattr(r, 'graphemes', '') or '').split() if re.search(r'\w', w)]
            d = len(a) / SR
            for i, w in enumerate(ws): words.append([w, round(t + d * i / len(ws), 3), round(t + d * (i + 1) / len(ws), 3)])
        chunks.append(a); t += len(a) / SR
    audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
    # attach trailing punctuation from the text to the caption words ("Sam" -> "Sam.")
    src = text.split()
    if len(src) == len(words):
        for i, w in enumerate(src): words[i][0] = w
    np.save(wp, audio); json.dump(words, open(jp, 'w', encoding='utf8'))
    return audio, words


def main(d):
    tp = os.path.join(d, 'timed.json'); sp = json.load(open(tp, encoding='utf8'))
    base_voice = sp.get('voice', 'af_heart'); speed = float(sp.get('voice_speed', 1.0))
    cache = os.path.join(d, 'voice'); os.makedirs(cache, exist_ok=True)
    pipes, lines = {}, []
    for i, s in enumerate(sp['shots']):
        txt = spoken(s['text'])
        if not txt: lines.append(None); continue
        a, w = line_audio(pipes, txt, s.get('voice', base_voice), speed, cache)
        lines.append((a, w)); print(f'  {i:3d} {len(a) / SR:5.2f} s  {txt[:50]}', flush=True)
    # re-time: each shot at least as long as its line + pauses; later shots move along
    t, moved = 0.0, 0
    for s, ln in zip(sp['shots'], lines):
        dur = s['t1'] - s['t0']
        need = (PAD_IN + len(ln[0]) / SR + PAD_OUT) if ln else 0.0
        nd = max(dur, need)
        if abs(nd - dur) > 1e-3 or abs(s['t0'] - t) > 1e-3: moved += 1
        s['t0'], s['t1'] = round(t, 3), round(t + nd, 3); t += nd
    sp['dur'] = round(max(sp['dur'], t) if moved == 0 else t, 3)
    total = np.zeros(int(np.ceil(sp['dur'] * SR)) + SR, np.float32); words = []
    for s, ln in zip(sp['shots'], lines):
        if not ln: continue
        a, w = ln; o = s['t0'] + PAD_IN; k = int(o * SR)
        total[k:k + len(a)] += a[:len(total) - k]
        words += [[x, round(o + a0, 3), round(o + a1, 3)] for x, a0, a1 in w]
    total = total[:int(np.ceil(sp['dur'] * SR))]
    pk = float(np.abs(total).max() or 1.0); total = total / pk * 0.89  # about -1 dBFS; post levels and mixes it
    from scipy.io import wavfile
    wavfile.write(os.path.join(d, 'vo.wav'), SR, (total * 32767).astype(np.int16))
    json.dump(words, open(os.path.join(d, 'words.json'), 'w', encoding='utf8'))
    json.dump(sp, open(tp, 'w', encoding='utf8'), indent=1)
    open(os.path.join(d, '.voice_kokoro'), 'w').write(base_voice)
    print(f'voice: {len(words)} words, {sp["dur"]:.2f} s, {moved} shots re-timed to fit the voice')


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(os.path.abspath(sys.argv[1]))
