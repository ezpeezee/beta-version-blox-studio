"""Render EPDIR/scene.blend in K parallel Blender processes (interleaved chunks so all finish together).
python render_par.py EPDIR [K=4] [--frames 0,30,60|10..40] [--out frames]  (frames -> only those, into EPDIR/stills or EPDIR/<out>)"""
import sys, os, subprocess, time, glob
BL = os.environ.get('BLENDER') or 'blender'  # kit/run.py sets BLENDER
ep = os.path.abspath(sys.argv[1]); K = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 4
blend = os.path.join(ep, 'scene.blend'); t = time.time()
if '--frames' in sys.argv:
    fr = []
    for x in sys.argv[sys.argv.index('--frames') + 1].split(','):
        a, _, b = x.partition('..'); fr += [str(i) for i in range(int(a), int(b or a) + 1)]
    sub = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'stills'
    out = os.path.join(ep, sub, '#####'); groups = [fr[i::K] for i in range(K)]
    cmds = [[BL, '-b', blend, '-o', out, '-F', 'JPEG', '-f', ','.join(g)] for g in groups if g]
else:
    import json, math
    n = int(math.ceil(json.load(open(os.path.join(ep, 'timed.json')))['dur'] * 30))
    os.makedirs(os.path.join(ep, 'frames'), exist_ok=True)
    CH = -(-n // K); chunks = [(a, min(a + CH, n) - 1) for a in range(0, n, CH)]
    groups = [chunks[i::K] for i in range(K)]
    cmds = []
    for g in groups:
        args = [BL, '-b', blend]
        for a, b in g: args += ['-s', str(a), '-e', str(b), '-a']
        cmds.append(args)
ps = [subprocess.Popen(c, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) for c in cmds]
for p in ps: p.wait()
print('rendered with', len(ps), 'procs in', round(time.time() - t, 1), 's; frames on disk', len(glob.glob(os.path.join(ep, 'frames', '*.jpg'))))
