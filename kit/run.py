"""Beta Version Blox Studio: one command from a shot list to a finished video.

  python kit/run.py projects/<name>                 # shots -> voice -> compile -> stills (look first)
  python kit/run.py projects/<name> render post     # full render (parallel) -> captions, music, mp4
  python kit/run.py projects/<name> all             # everything in one go

Stages: shots voice compile stills render post
  shots    runs <project>/shots.py, which writes timed.json (and placeholder word times)
  voice    Kokoro TTS reads each shot's text -> vo.wav + words.json, and stretches shots to fit the voice
           (skipped when you brought your own vo.wav + words.json, or Kokoro isn't installed)
  compile  Blender builds the scene, keys every frame and checks that no two characters overlap
  stills   one draft frame per shot -> <project>/stills_sheet.jpg (check the look before the full render)
  render   all frames, on several Blender processes at once (count picked from free RAM)
  post     captions, coded music and sound effects, branding -> <project>/out/<name>.mp4

Blender: set BLENDER to blender.exe, or put the path in kit/config.json {"blender": "..."}, or have it on PATH.
"""
import json, math, os, shutil, subprocess, sys, time

KIT = os.path.dirname(os.path.abspath(__file__))
BLOX = os.path.join(KIT, 'blox')
FPS = 30
PER_PROC_GB, MAX_PROCS = 4.0, 3


def blender():
    cfg = os.path.join(KIT, 'config.json')
    for p in (os.environ.get('BLENDER'), json.load(open(cfg)).get('blender') if os.path.exists(cfg) else None,
              shutil.which('blender'), r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'):
        if p and os.path.exists(p): return p
    sys.exit('Blender not found: set BLENDER or kit/config.json {"blender": "C:/.../blender.exe"}')


def sh(cmd, log=None, **kw):
    print('>>', ' '.join(map(str, cmd))[:150], flush=True); t = time.time()
    if log:
        with open(log, 'w', encoding='utf8') as f: r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, **kw)
    else: r = subprocess.run(cmd, **kw)
    if r.returncode: sys.exit(f'failed ({r.returncode}) {log or ""}')
    print(f'   {time.time() - t:.0f} s', flush=True)


def free_gb():
    try:
        import ctypes
        class M(ctypes.Structure):
            _fields_ = [('l', ctypes.c_ulong), ('m', ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in ('t', 'a', 'tp', 'ap', 'tv', 'av', 'x')]
        m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)); return m.a / 2 ** 30
    except Exception: return 8.0


def procs(): return max(1, min(MAX_PROCS, int((free_gb() - 2) // PER_PROC_GB), os.cpu_count() // 2))


def placeholder_words(spec):
    """No voice yet: spread each shot's caption words evenly across the shot."""
    out = []
    for s in spec['shots']:
        ws = [w for w in s['text'].split() if not w.startswith('(')]
        if not ws: continue
        d = (s['t1'] - s['t0']) * 0.9 / len(ws)
        for i, w in enumerate(ws): out.append([w, round(s['t0'] + i * d, 3), round(s['t0'] + (i + 1) * d, 3)])
    return out


class Project:
    def __init__(s, d): s.d = os.path.abspath(d); s.name = os.path.basename(s.d)
    def p(s, *a): return os.path.join(s.d, *a)
    def spec(s): return json.load(open(s.p('timed.json'), encoding='utf8'))
    def cuts(s):
        sp = s.spec(); return [round(x['t0'] * FPS) for x in sp['shots']] + [math.ceil(sp['dur'] * FPS)]

    def own_voice(s):  # the user's own recording (not one Kokoro made)
        return os.path.exists(s.p('vo.wav')) and os.path.exists(s.p('words.json')) and not os.path.exists(s.p('.voice_kokoro'))

    def shots(s):
        sh([sys.executable, s.p('shots.py')], cwd=s.d)
        if not s.own_voice():
            json.dump(placeholder_words(s.spec()), open(s.p('words.json'), 'w', encoding='utf8'))
            print('   words.json: placeholder timings (the voice step replaces them)')

    def voice(s):
        if s.own_voice(): print('   your own vo.wav + words.json: kept'); return
        try:
            import importlib.util
            ok = importlib.util.find_spec('kokoro') is not None
        except Exception: ok = False
        if not ok:
            for f in ('vo.wav', '.voice_kokoro'):
                if os.path.exists(s.p(f)): os.remove(s.p(f))
            print('   Kokoro not installed: no voice (pip install -r kit/requirements-voice.txt)'); return
        sh([sys.executable, os.path.join(BLOX, 'voice.py'), s.d], log=s.p('voice.log'))
        print('  ', open(s.p('voice.log'), encoding='utf8').read().strip().splitlines()[-1])

    def compile(s):
        sh([blender(), '-b', '--factory-startup', '-P', os.path.join(BLOX, 'compile.py'), '--', s.d], log=s.p('compile.log'))
        n = len([x for x in open(s.p('clash.txt')).read().split('\n') if x.strip()])
        print('   clash frames', n, '(characters overlapping; 0 is the goal; see clash.txt)')

    def stills(s):
        c = s.cuts(); fr = [min(a + max(1, int((b - a) * 0.4)), b - 1) for a, b in zip(c, c[1:])]
        if os.path.isdir(s.p('stills')): shutil.rmtree(s.p('stills'))
        sh([sys.executable, os.path.join(BLOX, 'render_par.py'), s.d, str(procs()), '--frames', ','.join(map(str, fr)), '--out', 'stills'])
        from PIL import Image, ImageDraw
        W, H, cols = 216, 384, 6; rows = -(-len(fr) // cols); S = Image.new('RGB', (W * cols, H * rows), (12, 14, 20))
        sp = s.spec()
        for i, f in enumerate(fr):
            p = s.p('stills', f'{f:05d}.jpg')
            if not os.path.exists(p): continue
            im = Image.open(p).convert('RGB').resize((W, H)); d = ImageDraw.Draw(im)
            d.rectangle((0, 0, W, 16), fill=(0, 0, 0)); d.text((3, 2), f'{i} {sp["shots"][i]["text"][:28]}', fill=(255, 220, 0))
            S.paste(im, ((i % cols) * W, (i // cols) * H))
        S.save(s.p('stills_sheet.jpg')); print('   ->', s.p('stills_sheet.jpg'))

    def render(s):
        if os.path.isdir(s.p('frames')): shutil.rmtree(s.p('frames'))
        sh([sys.executable, os.path.join(BLOX, 'render_par.py'), s.d, str(procs())], log=s.p('render.log'))
        print('  ', open(s.p('render.log')).read().strip().split('\n')[-1])

    def post(s):
        sh([sys.executable, os.path.join(BLOX, 'post.py'), s.d], log=s.p('post.log'))
        print('   ->', s.p('out', s.name + '.mp4'))


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    pr = Project(sys.argv[1]); st = sys.argv[2:] or ['shots', 'voice', 'compile', 'stills']
    if st == ['all']: st = ['shots', 'voice', 'compile', 'stills', 'render', 'post']
    os.environ.setdefault('BLENDER', blender())
    t0 = time.time()
    for x in st: print(f'== {x}', flush=True); getattr(pr, x)()
    print(f'== done in {time.time() - t0:.0f} s')
