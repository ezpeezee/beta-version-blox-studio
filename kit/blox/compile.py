"""Compile an episode (timed.json) into a keyframed .blend.
blender -b --factory-startup -P compile.py -- EPDIR [--frames a,b,c --still OUT_DIR]
Writes EPDIR/scene.blend (render with render_par.py) and EPDIR/clash.txt (body/prop overlap gate).
"""
import bpy, sys, os, json, math, random, re
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sets, chars

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
EP = os.path.abspath(argv[0])
SPEC = json.load(open(os.path.join(EP, 'timed.json'), encoding='utf8'))
WORDS = json.load(open(os.path.join(EP, 'words.json'), encoding='utf8'))
FPS = 30; N = int(math.ceil(SPEC['dur'] * FPS))
import places as _places
_places.register_things(SPEC.get('things', {}))   # the story's own blocky objects
PLACES = SPEC.get('places', {})   # the story's own places (specs, see places.py); built-in names need none
_used = []
for _s in SPEC['shots']:
    if _s['set'] not in _used: _used.append(_s['set'])
ORIG = {nm: Vector((i * 400, 0, 0)) for i, nm in enumerate(_used)}   # only the places this story uses
OFF = Vector((0, 0, -2000))  # parked actors
H = chars.HEAD_C[2] if hasattr(chars, 'HEAD_C') else 4.5  # real R6 head centre at scale 1

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, x): return a + (b - a) * x
def yawdir(yaw):  # yaw 0 = facing -Y, + = counter-clockwise
    r = math.radians(yaw); return Vector((math.sin(r), -math.cos(r), 0))

# ---------- scene ----------
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
sets.setup_render(sc)
sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = N - 1
for nm, o in ORIG.items(): sets.build_set(nm, origin=tuple(o), spec=PLACES.get(nm))

# ---------- cast ----------
CAST = {}
for nm, spec in SPEC['cast'].items():
    spec = dict(spec); spec['skin'] = tuple(spec['skin']); spec['shirt'] = tuple(spec['shirt']); spec['pants'] = tuple(spec['pants'])
    spec['shoes'] = tuple(spec.get('shoes', (0.9, 0.9, 0.9))); spec['hair_color'] = tuple(spec.get('hair_color', (0.2, 0.1, 0.05)))
    CAST[nm] = chars.make_char(nm, spec)

# ---------- materials / fx objects ----------
def mat(name, col, emit=0.0, alpha=1.0, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m

FXC = bpy.data.collections.new('FX'); sc.collection.children.link(FXC)
def link(o): FXC.objects.link(o); return o
def sphere(name, r, m, loc=(0, 0, 0), parent=None):
    me = bpy.data.meshes.new(name); import bmesh; bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m); o.location = loc
    if parent: o.parent = parent
    return o

def make_cloud(name, col):
    root = link(bpy.data.objects.new(name, None)); m = mat(name + '_m', col, rough=0.9)
    rnd = random.Random(name)
    for i, (x, y, z, r) in enumerate([(0, 0, 0, 1.0), (-1.1, 0, -0.15, 0.8), (1.1, 0, -0.1, 0.85), (-0.5, 0.35, 0.45, 0.75), (0.55, -0.2, 0.4, 0.7),
                                      (-1.8, 0.1, -0.35, 0.55), (1.85, 0.05, -0.3, 0.55), (0, -0.55, -0.2, 0.75), (0.1, 0.6, -0.1, 0.7)]):
        sphere(f'{name}_p{i}', r, m, (x, y, z), root)
    root.location = OFF
    return root

def make_rain(name, n):
    m = mat('rain_m', (0.6, 0.8, 1.0), emit=0.6, alpha=0.75)
    out = []
    for i in range(n):
        me = bpy.data.meshes.new(f'{name}{i}'); import bmesh; bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.035, radius2=0.035, depth=0.55); bm.to_mesh(me); bm.free()
        o = link(bpy.data.objects.new(f'{name}{i}', me)); o.data.materials.append(m); o.location = OFF; out.append(o)
    return out

def make_bolt(name):
    rnd = random.Random(7); pts = [Vector((0, 0, 0))]
    for i in range(9): pts.append(pts[-1] + Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.2, 0.2), -1.3)))
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.11; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts): p.co = (*v, 1)
    o = link(bpy.data.objects.new(name, cu)); o.data.materials.append(mat('bolt_m', (1.0, 0.95, 0.55), emit=40)); o.location = OFF
    return o, (pts[0] - pts[-1]).length

CLOUD_W = make_cloud('cloud_white', (0.92, 0.94, 1.0))
CLOUD_G = make_cloud('cloud_grey', (0.45, 0.48, 0.56))
CLOUD_D = make_cloud('cloud_dark', (0.12, 0.13, 0.17))
RAIN = make_rain('rain', 46)
BOLT, BOLT_LEN = make_bolt('bolt')
fl = bpy.data.lights.new('flash', 'POINT'); fl.energy = 0; fl.shadow_soft_size = 3; fl.color = (0.85, 0.9, 1.0)
FLASH = link(bpy.data.objects.new('flash', fl)); FLASH.location = OFF
SMOKE = [sphere(f'smoke{i}', 0.5, mat('smoke_m', (0.3, 0.3, 0.32), alpha=0.6, rough=1)) for i in range(6)]
for s in SMOKE: s.location = OFF
CRUMB = [sphere(f'crumb{i}', 0.028, mat('crumb_m', (0.62, 0.4, 0.18), rough=0.9)) for i in range(3)]
for c in CRUMB: c.location = OFF; c.visible_shadow = False

cam_data = bpy.data.cameras.new('cam'); cam_data.sensor_fit = 'VERTICAL'; cam_data.clip_start = 0.1; cam_data.clip_end = 900
CAM = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(CAM); sc.camera = CAM

# ---------- helpers ----------
VOW = {'a': 'A', 'e': 'E', 'i': 'E', 'o': 'O', 'u': 'O', 'y': 'E'}
# mouth: one shape per syllable group, each held >= 4 frames (acting.md 3.4)
MOUTH = []  # (t0, t1, shape)
for w, a, b in WORDS:
    ww = re.sub(r'[^a-z]', '', w.lower()) or 'm'
    syl = re.findall(r'[^aeiouy]*[aeiouy]+', ww) or [ww]
    n = max(1, min(len(syl), int((b - a) * FPS // 4)))
    groups = [syl[i * len(syl) // n:(i + 1) * len(syl) // n] for i in range(n)]
    for i, g in enumerate(groups):
        s_ = ''.join(g); v = re.search(r'[aeiouy]', s_)
        shp = 'M' if s_[:1] in ('m', 'b', 'p') and i == 0 and len(groups) > 1 else VOW.get(v.group(0) if v else 'a', 'A')
        MOUTH.append((a + (b - a) * i / n, a + (b - a) * (i + 1) / n, shp))
def viseme(t):
    for a, b, shp in MOUTH:
        if a <= t < b: return shp
    return None
def at_list(base, lst, tl):
    cur = base
    for tt, v in (lst or []):
        if tl >= tt: cur = v
    return cur
def at_list2(base, lst, tl):  # (current, previous, switch time) for pose blends
    cur, prev, ts = base, None, None
    for tt, v in (lst or []):
        if tl >= tt and v != cur: prev, cur, ts = cur, v, tt
    return cur, prev, ts
def fx_list(a):
    out = []
    for f in a.get('fx', []):
        nm, _, t = f.partition('@'); out.append((nm, float(t) if t else 0.0))
    return out

def shot_at(t):
    for s in SPEC['shots']:
        if s['t0'] <= t < s['t1']: return s
    return SPEC['shots'][-1]

def actor_pos(s, a, tl):
    o = ORIG[s['set']]; p0 = Vector((a['at'][0], a['at'][1], 0))
    yaw = a.get('yaw', 0)
    if a.get('walkTo'):
        p1 = Vector((a['walkTo'][0], a['walkTo'][1], 0)); x = tl / max(s['t1'] - s['t0'], 0.1)
        p = p0.lerp(p1, x); d = p1 - p0
        if d.length > 0.05: yaw = math.degrees(math.atan2(d.x, -d.y))
        return o + p, yaw, d.length / max(s['t1'] - s['t0'], 0.1)
    return o + p0, yaw, 0

# camera.md 4.2: kind -> frame width (studs), side angle off the facing axis, eye height vs head ('ground:z' / 'obj'),
# eye line position from the frame top, lens mm, f-stop, default move
CAMS = {
    'ecu': (1.5, 30, -0.3, 0.42, 50, 0.7, 'lock'), 'cu': (2.4, 30, -0.6, 0.38, 35, 0.9, 'lock'),
    'mcu': (3.2, 30, -1.2, 0.36, 30, 1.2, 'creep'), 'ms': (4.6, 35, -1.6, 0.33, 26, 1.8, 'creep'),
    'mls': (6.0, 40, -2.4, 0.30, 22, 2.8, 'lock'), 'ws': (12.0, 25, 1.0, 0.45, 18, 4.0, 'lock'),
    'ews': (16.0, 20, 'ground:0.6', 0.55, 16, 5.6, 'creep'), 'ots': (3.6, 150, -0.8, 0.36, 30, 1.2, 'lock'),
    'low': (4.2, 30, -3.0, 0.30, 24, 1.6, 'lock'), 'worm': (3.4, 10, 'ground:0.5', 0.30, 18, 1.4, 'lock'),
    'ground': (5.0, 30, 'ground:0.4', 0.50, 18, 1.4, 'lock'), 'high': (8.0, 20, 4.0, 0.40, 20, 3.5, 'lock'),
    'top': (10.0, 0, 9.0, 0.50, 18, 4.0, 'lock'), 'ins': (1.2, 20, 'obj', 0.50, 50, 0.6, 'lock'),
    'pov': (3.4, 180, 0.0, 0.40, 24, 1.6, 'drift'), 'two': (5.2, 35, -1.2, 0.34, 24, 2.0, 'creep')}
SET_FRONT = {'ws', 'ews', 'top', 'high'}  # framed from the set's open side (-Y), not the actor's facing
CLOUDY = ('raincloud', 'drizzle', 'storm', 'bigstorm')
def bell(x): return (1 - math.cos(math.pi * max(0, min(1, x)))) / 2

def solve_cam(s, tl, heads):
    """returns eye, target, lens, focus point, fstop"""
    dur = s['t1'] - s['t0']; kind = s.get('cam', 'ms'); kind = kind if kind in CAMS else 'ms'
    fw, sdeg, edz, eyy, lens, fst, mv0 = CAMS[kind]; side = s.get('side', 1); o = ORIG[s['set']]
    if kind == 'ins' or not heads:
        anc = sets.ANCHORS.get(s['set'], {}).get(s.get('focus', ''), (0, 0, 2.6))
        foc = o + Vector(anc); F = Vector((0, -1, 0)); hp = foc
        k = max(1.0, _places.SIZES.get((s['set'], s.get('focus', '')), 0) * 1.4 / fw)   # whole story thing in frame
    elif kind == 'two':
        pts = [h[0] for h in heads.values()]; foc = sum(pts, Vector()) / len(pts)
        spread = max((p - foc).length for p in pts) if len(pts) > 1 else 1
        hp = foc; k = max(h[2] for h in heads.values()); F = Vector((0, -1, 0)); fw = max(fw * k, spread * 2.2 + 2.5) / k
        sub = s.get('subject');
        if sub in heads: foc = heads[sub][0]
    else:
        sub = s.get('subject') if s.get('subject') in heads else next(iter(heads)); hp, yaw, k = heads[sub]; foc = hp
        F = Vector((0, -1, 0)) if kind in SET_FRONT else yawdir(yaw)
    fw *= k; fh = fw * 16 / 9
    d = (fw / 2) / (12 / lens * 9 / 16)
    cloud = s.get('aimUp') or any(f.split('@')[0] in CLOUDY for a in s['actors'] for f in a.get('fx', []))
    r = math.radians(sdeg * side); dirv = Vector((F.x * math.cos(r) - F.y * math.sin(r), F.x * math.sin(r) + F.y * math.cos(r), 0))
    tgt = hp - Vector((0, 0, (0.5 - eyy) * fh))
    if cloud and kind != 'ins': tgt = tgt + Vector((0, 0, 1.6 * k)); d *= 1.3
    eye = tgt + dirv * d
    if isinstance(edz, str) and edz.startswith('ground'): eye.z = o.z + float(edz.split(':')[1])
    elif edz == 'obj': eye.z = foc.z + d * 0.55
    else: eye.z = hp.z + edz * k
    # keep scenery out of the lens: pull the eye in front of the first set surface between subject and camera
    def blocked(e):
        d = e - tgt; dn = d.normalized(); o = tgt.copy(); left = d.length
        for _ in range(8):
            ok, loc, nrm, idx, ob, mtx = sc.ray_cast(DG, o, dn, distance=left)
            if not ok: return None
            if ob.name.split('_')[0] in CAST or ob.users_collection[0].name == 'FX' or (
                    s.get('focus') and ob.name.split('.')[:2] == [s['set'], s['focus']]):   # the thing being filmed
                st = (loc - o).length + 0.05; o = o + dn * st; left -= st; continue
            return (loc - tgt).length
        return None
    if blocked(eye) is not None:
        for up in (0.8, 1.6, 2.4, 3.2):
            e2 = eye + Vector((0, 0, up)); e2 = tgt + (e2 - tgt).normalized() * (eye - tgt).length
            if blocked(e2) is None: eye = e2; break
        else:
            h = blocked(eye); eye = tgt + (eye - tgt).normalized() * max(1.2 if kind == 'ins' else 3.0, h - 0.7)
    # moves (camera.md 4.3): scale = image scale, done by dolly along the view axis
    mv = s.get('move', mv0); x = tl / max(dur, 0.1); sc_ = 1.0
    if mv == 'creep': sc_ = 1 + 0.05 * x
    elif mv == 'push': sc_ = 1 + 0.15 * min(1, tl / min(1.2, dur))
    elif mv == 'reveal_push': sc_ = 1 + 0.5 * bell(x)
    elif mv == 'crash_in':
        ti = s.get('impact', 0.0) + 1 / FPS; u = max(0, min(1, (tl - ti) / (4 / FPS))); sc_ = 1 + 0.15 * (1 - (1 - u) ** 2)
    elif mv == 'drift':
        tgt = tgt + Vector((math.sin(tl * 3.1) * 0.006 * fw, 0, math.sin(tl * 2.3 + 1) * 0.006 * fw))
    eye = tgt + (eye - tgt) / sc_
    if s.get('flash') or mv == 'crash_in':  # kick on impact frames (impact = given, else the first bolt)
        bolts = [float(f.split('@')[1]) for a in s['actors'] for f in a.get('fx', []) if f.startswith('bolt@')]
        ti = s.get('impact', min(bolts) if bolts else 0.0) + 1 / FPS; fi = int(round((tl - ti) * FPS))
        if 0 <= fi < 4:
            off = [0.016, -0.009, 0.004, 0][fi] * fw; Rv = Vector((dirv.y, -dirv.x, 0)); eye = eye + Rv * off; tgt = tgt + Rv * off
    return eye, tgt, lens, foc, s.get('fstop', fst)

def key_obj(o, f, loc=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if scale is not None: o.scale = (scale, scale, scale); o.keyframe_insert('scale', frame=f)

# ---------- acting schedulers (acting.md 3) ----------
SHOTS = SPEC['shots']; CUTF = [int(round(s_['t0'] * FPS)) for s_ in SHOTS] + [N]
BLINK = {nm: set() for nm in CAST}
for si, s_ in enumerate(SHOTS):  # event blinks: every face swap happens behind a 3-frame blink
    for a in s_['actors']:
        for tt, _ in a.get('faceAt', []):
            f0 = int(round((s_['t0'] + tt) * FPS)) - 1
            BLINK[a['who']].update(range(f0, f0 + 3))
for nm in CAST:  # ambient blinks every 2.5-5 s, none within 6 frames of a cut
    r = random.Random('blink' + nm); tb = r.uniform(0.6, 2.5)
    while tb < SPEC['dur']:
        f0 = int(tb * FPS)
        if all(abs(f0 - c) > 6 and abs(f0 + 2 - c) > 6 for c in CUTF): BLINK[nm].update(range(f0, f0 + 3))
        tb += r.uniform(2.5, 5.0)
DART_FACES = {'scared', 'worried', 'think', 'shock'}
def dart(nm, si, fl):  # eye darts every 4-13 frames for nervous faces, snapped
    r = random.Random(f'dart{nm}{si}'); acc = r.randint(4, 13); dx = dy = 0.0
    while acc <= fl: dx, dy = r.uniform(-0.35, 0.35), r.uniform(-0.12, 0.15); acc += r.randint(4, 13)
    return dx, dy
BLEND_W = [0.3, 0.62, 0.86, 1.06, 1.0]  # 4 f ease-out in with a 1 f overshoot
def safe_pose(arm, f, anim, phase, amt=1.0):
    try: chars.pose(arm, f, anim, phase, amt)
    except Exception: chars.pose(arm, f, 'idle', phase, amt); MISSING.add(anim)
MISSING = set()
ONE_SHOT = {'nod', 'headshake', 'flinch', 'slump', 'jump_joy', 'shock', 'surrender', 'head_tilt', 'what', 'facepalm', 'clap'}
cam_data.dof.use_dof = True
try: sc.render.motion_blur_position = 'START'  # never sample the previous shot across a cut
except Exception: pass

# ---------- per-frame keying ----------
DG = bpy.context.evaluated_depsgraph_get()
CLASH = []
for f in range(N):
    t = f / FPS; s = shot_at(t); tl = t - s['t0']; dur = s['t1'] - s['t0']; si = SHOTS.index(s); lf = f - CUTF[si]
    inshot = {a['who']: a for a in s['actors']}
    heads = {}
    for nm, arm in CAST.items():
        a = inshot.get(nm)
        if not a:
            chars.place(arm, f, tuple(OFF), 0); continue
        p, yaw, v = actor_pos(s, a, tl)
        k = SPEC['cast'][nm].get('height', 1.0)
        chars.place(arm, f, tuple(p), yaw)
        def eff(x):
            an = at_list(a.get('anim', 'idle'), a.get('animAt'), x)
            if an == 'idle' and a.get('talk') and a['talk'][0] <= x <= a['talk'][1]: an = 'talk'
            return an
        anim = eff(tl); talking = a.get('talk') and a['talk'][0] <= tl <= a['talk'][1]
        if anim in ('walk', 'run'): phase = (v * tl) / ((2.6 if anim == 'walk' else 4.0) * k) * (1.0 if anim == 'walk' else 0.6)  # cycles from distance walked, in cycle-seconds: no foot slide
        else: phase = t + (sum(map(ord, nm)) % 7) * 0.31
        if anim in ONE_SHOT:  # gestures play once from when they start, not looped on absolute time
            st = 0.0
            for tt, an in (a.get('animAt') or []):
                if tt <= tl and an == anim: st = tt
            phase = tl - st
        prev = None
        for j in range(1, len(BLEND_W) + 1):  # pose blend after a switch inside the shot (never across a cut)
            if lf - j < 0: break
            if eff(tl - j / FPS) != anim: prev = eff(tl - j / FPS); w = BLEND_W[j - 1]; break
        if prev and hasattr(chars, 'pose_mix'):
            try: chars.pose_mix(arm, f, prev, phase, anim, phase, w)
            except Exception: safe_pose(arm, f, anim, phase); MISSING.add('mix:' + prev + '>' + anim)
        else: safe_pose(arm, f, anim, phase)
        expr = at_list(a.get('face', 'neutral'), a.get('faceAt'), tl)
        vis = viseme(t) if talking else None
        lk = tuple(a.get('look', (0, 0)))
        if expr in DART_FACES: dx, dy = dart(nm, si, lf); lk = (max(-1, min(1, lk[0] + dx)), max(-1, min(1, lk[1] + dy)))
        chars.face(arm, f, expr, viseme=vis, blink=1.0 if f in BLINK[nm] else 0.0, look=lk)
        heads[nm] = (p + Vector((0, 0, H * k)), yaw, k)
    # fx (one of each kind active)
    cloud_on = {}; rain_on = None; bolt_on = None; smoke_on = None; crumbs_on = None
    for a in s['actors']:
        if a['who'] not in heads: continue
        hp, yaw, k = heads[a['who']]
        for nm, t0 in fx_list(a):
            if tl < t0: continue
            age = tl - t0
            if nm in ('raincloud', 'drizzle', 'storm', 'bigstorm'):
                big = {'drizzle': 0.55, 'raincloud': 0.8, 'storm': 1.15, 'bigstorm': 2.6}[nm]
                pop = min(1.0, age / 0.22); pop = pop * (1 + 0.18 * math.sin(pop * math.pi))
                obj = {'drizzle': CLOUD_W, 'raincloud': CLOUD_G, 'storm': CLOUD_D, 'bigstorm': CLOUD_D}[nm]
                zc = hp.z + (2.6 if nm != 'bigstorm' else 4.2) * max(k, 0.8)
                c = Vector((hp.x + 0.15 * math.sin(t * 1.7), hp.y + 0.1 * math.cos(t * 1.3), zc))
                cloud_on[obj] = (c, big * max(pop, 0.01))
                if age > 0.25: rain_on = (c, big, {'drizzle': 0.35, 'raincloud': 0.7, 'storm': 1.0, 'bigstorm': 1.0}[nm], hp.z - 4.9 * k)
            elif nm == 'bolt' and age < 0.32:
                bolt_on = (hp, age)
            elif nm == 'smoke':
                smoke_on = (hp, age)
            elif nm == 'crumbs':
                crumbs_on = (hp, yaw, k)
    for obj in (CLOUD_W, CLOUD_G, CLOUD_D):
        if obj in cloud_on: key_obj(obj, f, cloud_on[obj][0], cloud_on[obj][1])
        else: key_obj(obj, f, OFF, 0.01)
    rnd = random.Random(3)
    for i, r in enumerate(RAIN):
        sx, sy, sp = rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1)
        if rain_on and i < int(len(RAIN) * rain_on[2]):
            c, big, dens, floor = rain_on; fall = c.z - 0.6 - floor
            z = c.z - 0.6 - ((t * 11 + sp * fall) % max(fall, 0.5))
            key_obj(r, f, Vector((c.x + sx * 1.5 * big, c.y + sy * 0.9 * big, z)))
        else: key_obj(r, f, OFF)
    if bolt_on:
        hp, age = bolt_on; on = age < 0.08 or 0.14 < age < 0.22
        key_obj(BOLT, f, hp + Vector((0.1, 0, BOLT_LEN + 0.2)) if on else OFF)
        FLASH.location = hp + Vector((1.5, -3, 3)); fl.energy = 2500 if on else 0
    else:
        key_obj(BOLT, f, OFF); FLASH.location = OFF; fl.energy = 0
    FLASH.keyframe_insert('location', frame=f); fl.keyframe_insert('energy', frame=f)
    for i, sm in enumerate(SMOKE):
        if smoke_on:
            hp, age = smoke_on; a2 = (age + i * 0.12) % 1.2
            key_obj(sm, f, hp + Vector((math.sin(i * 2.1) * 0.6, math.cos(i * 1.7) * 0.4, 0.9 + a2 * 2.2)), 0.4 + a2 * 0.7)
        else: key_obj(sm, f, OFF, 0.4)
    for i, cb in enumerate(CRUMB):
        if crumbs_on:
            hp, yaw, k = crumbs_on; F = yawdir(yaw); R = Vector((F.y, -F.x, 0))
            ox, oz = [(-0.17, -0.24), (0.15, -0.3), (0.03, -0.36)][i]
            key_obj(cb, f, hp + F * 0.64 * k + R * ox * k + Vector((0, 0, oz * k)))
        else: key_obj(cb, f, OFF)
    # mood
    mx = s.get('moodx', [1.0, 1.0]); sets.set_mood(s.get('mood', 'sunny'), lerp(mx[0], mx[1], ease(tl / max(dur, 0.1))))
    try:
        w = sc.world; w.keyframe_insert('color', frame=f)
        if w.use_nodes:
            for nd in w.node_tree.nodes:
                for inp in nd.inputs:
                    if hasattr(inp, 'default_value') and not inp.is_linked:
                        try: inp.keyframe_insert('default_value', frame=f)
                        except Exception: pass
        for lo in bpy.data.objects:  # every mood-driven light (sun, key, rim, practicals), not the bolt flash
            if lo.type == 'LIGHT' and lo is not FLASH:
                lo.data.keyframe_insert('energy', frame=f); lo.data.keyframe_insert('color', frame=f); lo.keyframe_insert('rotation_euler', frame=f)
    except Exception as e: pass
    # camera
    eye, tgt, lens, foc, fst = solve_cam(s, tl, heads)
    CAM.location = eye; CAM.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    CAM.keyframe_insert('location', frame=f); CAM.keyframe_insert('rotation_euler', frame=f)
    cam_data.lens = lens; cam_data.keyframe_insert('lens', frame=f)
    cam_data.dof.focus_distance = (foc - eye).length; cam_data.dof.aperture_fstop = fst
    cam_data.dof.keyframe_insert('focus_distance', frame=f); cam_data.dof.keyframe_insert('aperture_fstop', frame=f)

# every frame is keyed: LINEAR inside shots (smooth motion blur), CONSTANT on each shot's last frame so cuts never blend
LASTF = set(c - 1 for c in CUTF[1:])
def all_fcurves(ad):
    act = ad.action
    if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
    out = []  # Blender 5 layered actions
    for ly in getattr(act, 'layers', []):
        for st in ly.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
ids = list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.cameras) + list(bpy.data.worlds) + list(bpy.data.materials) + list(bpy.data.node_groups)
ids += [w.node_tree for w in bpy.data.worlds if w.node_tree]
for o in ids:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        try:
            for fc in all_fcurves(ad):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if int(round(kp.co.x)) in LASTF else 'LINEAR'
        except Exception as e: print('interp', o.name, e)
print('MISSING anims', sorted(MISSING))

# ---------- clash gate: actor vs actor, actor vs set solids (world AABB of body parts, 10 % tolerance) ----------
def aabb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))); hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
    m = (hi - lo) * 0.1; return lo + m, hi - m
def hit(a, b): return all(a[0][i] < b[1][i] and b[0][i] < a[1][i] for i in range(3))
step = 2
for f in range(0, N, step):
    sc.frame_set(f); s = shot_at(f / FPS); names = [a['who'] for a in s['actors']]
    boxes = {nm: [(o, aabb(o)) for o in chars.body_parts(CAST[nm]) if o.type == 'MESH' and max(o.dimensions) > 0.3] for nm in names}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs = [(x, y) for x in boxes[names[i]] for y in boxes[names[j]] if hit(x[1], y[1])]
            if pairs:
                dg = bpy.context.evaluated_depsgraph_get()
                for x, y in pairs:
                    if BVHTree.FromObject(x[0], dg).overlap(BVHTree.FromObject(y[0], dg)):
                        CLASH.append(f'{f}:{x[0].name}/{y[0].name}'); break
open(os.path.join(EP, 'clash.txt'), 'w').write('\n'.join(CLASH))
print('CLASH frames', len(CLASH))

sc.render.filepath = os.path.join(EP, 'frames', '#####')
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(EP, 'scene.blend'))
print('saved', os.path.join(EP, 'scene.blend'), 'frames', N)
