"""Code-built Roblox-style props + Beta Version brand placements for sets.py.

Every prop is one mesh object (several materials, bevelled), built in studs with its origin at the bottom centre,
front facing -Y before `rotz`. Decals / labels / brand plates are child objects of their prop.

Brand
    brand_plate(coll, name, loc, rot, width, plate=True, emissive=False)   wordmark quad (aspect kept) on a dark plate
    atlas_decal(coll, name, slot, loc, rot, width, emissive=False)          poster art from brand_posters_atlas.png
    Brand objects carry the custom property 'brand' = 1 (list them with brand_objects()).
The wordmark PNGs live in kit/assets/brand; if a file is missing the embedded copy (WORDMARK_B64) is used.
"""
import base64
import math
import os
import random
import tempfile

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

import sets as S

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'assets')
BRAND_DIR = os.path.normpath(os.path.join(ASSETS, 'brand'))
ATLAS = os.path.normpath(os.path.join(ASSETS, 'textures', 'brand_posters_atlas.png'))
PLATE_HEX = '#101522'
WM_ASPECT = 680 / 1600

# poster atlas slots in pixels (x0, y0, x1, y1), top-left origin, atlas 2048 x 2560 (see _dev make_brand_atlas.py)
ATLAS_SIZE = (2048, 2560)
SLOTS = dict(BILL=(0, 0, 2048, 864), P1=(0, 864, 512, 1632), P2=(512, 864, 1024, 1632), P3=(1024, 864, 1536, 1632),
             CEREAL=(1536, 864, 2048, 1632), COLA=(0, 1632, 1024, 2048), MUG=(1024, 1632, 2048, 2048),
             AD=(0, 2048, 1024, 2560), TOWEL=(1024, 2048, 1408, 2560), CRATE=(1408, 2048, 1920, 2560))

# fallback wordmark (400 px, 64 colours) used when kit/assets/brand/*.png is missing
WORDMARK_B64 = (
    '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'
)


# ------------------------------------------------------------------ images + materials
def _image(kind):
    """kind: 'wm' (transparent wordmark), 'mark', 'atlas'. Returns a bpy image or None (atlas missing)."""
    name = 'bv_' + kind
    img = bpy.data.images.get(name)
    if img is not None:
        return img
    fn = {'wm': 'bv-wordmark-transparent.png', 'mark': 'bv-mark-transparent.png'}.get(kind)
    path = os.path.join(BRAND_DIR, fn) if fn else ATLAS
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=False)
    elif kind == 'atlas':
        return None
    else:
        fd, tmp = tempfile.mkstemp(suffix='.png')
        with os.fdopen(fd, 'wb') as f:
            f.write(base64.b64decode(''.join(WORDMARK_B64)))
        img = bpy.data.images.load(tmp, check_existing=False)
        img.pack()
        try:
            os.remove(tmp)
        except OSError:
            pass
    img.name = name
    return img


def _uv_rect(slot):
    if slot is None or _image('atlas') is None:
        return (0.0, 0.0, 1.0, 1.0)
    x0, y0, x1, y1 = SLOTS[slot]
    W, H = ATLAS_SIZE
    return (x0 / W, 1 - y1 / H, x1 / W, 1 - y0 / H)


def _img_mat(key, kind, emit=None, rough=0.55, alpha_mul=1.0, over_plate=False):
    """Image material on UVs. emit=(expr, keys) drives emission (follows the mood ctl nodes).
    over_plate: composite the image's alpha over the dark plate colour (atlas fallback)."""
    m, new = S._new_mat(key)
    if not new:
        return m
    nt = m.node_tree
    b = S._bsdf(m)
    img = _image(kind)
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    tx.interpolation = 'Cubic'
    tx.extension = 'CLIP'
    col, alpha = tx.outputs['Color'], tx.outputs['Alpha']
    if over_plate:
        col = S._mix(nt, S._col(PLATE_HEX), col, alpha)
        alpha = None
    nt.links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.35
    if alpha is not None and kind in ('wm', 'mark'):
        nt.links.new(S._math(nt, 'MULTIPLY', alpha, alpha_mul, clamp=True), b.inputs['Alpha'])
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            pass
    if emit:
        nt.links.new(col, b.inputs['Emission Color'])
        v = S._drv_value(nt, 'drv_emit', emit[0], emit[1])
        nt.links.new(v.outputs[0], b.inputs['Emission Strength'])
    m.diffuse_color = S._col(PLATE_HEX)
    return m


def _atlas_mat(emissive=False):
    fb = _image('atlas') is None
    kind = 'wm' if fb else 'atlas'
    if emissive:
        return _img_mat('brand_atlas_lit', kind, emit=('0.12+win*1.6', ['win']), rough=0.4, over_plate=fb)
    return _img_mat('brand_atlas', kind, rough=0.6, over_plate=fb)


def _wm_mat(emissive=False, kind='wm', alpha_mul=1.0, rough=0.5):
    key = f'brand_{kind}' + ('_lit' if emissive else '') + ('' if alpha_mul == 1.0 else f'_{int(alpha_mul * 100)}')
    return _img_mat(key, kind, emit=('0.3+neon*3.5', ['neon']) if emissive else None, rough=rough, alpha_mul=alpha_mul)


def _plate_mat():
    return S.flat('brandplate', PLATE_HEX, rough=0.45, var=0.03)


# ------------------------------------------------------------------ raw geometry
def _quad(coll, name, mat, w, h, M, uv=(0, 0, 1, 1)):
    """Plane w x h in local XZ, normal -Y, placed by world matrix M."""
    me = bpy.data.meshes.new(name)
    v = [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]
    me.from_pydata(v, [], [(0, 1, 2, 3)])
    u0, v0, u1, v1 = uv
    lay = me.uv_layers.new(name='UVMap')
    for li, (uu, vv) in zip(range(4), ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        lay.data[li].uv = (uu, vv)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = M
    coll.objects.link(ob)
    return ob


def _band(coll, name, mat, r, z0, z1, M, uv=(0, 0, 1, 1), seg=40):
    """Open cylinder side (label wrap) around local Z; u runs counter-clockwise, u=0.25 faces -Y."""
    me = bpy.data.meshes.new(name)
    u0, v0, u1, v1 = uv
    verts, faces = [], []
    for i in range(seg + 1):
        a = -math.pi + 2 * math.pi * i / seg
        verts += [(r * math.cos(a), r * math.sin(a), z0), (r * math.cos(a), r * math.sin(a), z1)]
    for i in range(seg):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me.from_pydata(verts, [], faces)
    lay = me.uv_layers.new(name='UVMap')
    for fi, p in enumerate(me.polygons):
        p.use_smooth = True
        for li, vi in zip(p.loop_indices, p.vertices):
            k = vi // 2
            lay.data[li].uv = (u0 + (u1 - u0) * k / seg, v1 if vi % 2 else v0)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = M
    coll.objects.link(ob)
    return ob


def _mtx(loc, rot=(0, 0, 0)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()


def _brand_at(coll, name, M, width, plate=True, emissive=False, kind='wm', alpha_mul=1.0):
    h = width * (WM_ASPECT if kind == 'wm' else 1.0)
    q = _quad(coll, name, _wm_mat(emissive, kind, alpha_mul), width, h, M @ Matrix.Translation((0, -0.012, 0)))
    q['brand'] = 1
    if plate:
        pad = width * 0.08
        me = bpy.data.meshes.new(name + '.plate')
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0.025, 0)) @
                              Matrix.Diagonal((width + 2 * pad, 0.05, h + 2 * pad, 1)))
        bm.to_mesh(me); bm.free()
        me.materials.append(_plate_mat())
        p = bpy.data.objects.new(name + '.plate', me)
        p.matrix_world = M
        md = p.modifiers.new('bevel', 'BEVEL'); md.width = min(0.02, pad * 0.4); md.segments = 2
        coll.objects.link(p)
        p.parent = q
        p.matrix_parent_inverse = q.matrix_world.inverted()
    return q


def brand_plate(coll, name, loc, rot, width, plate=True, emissive=False, kind='wm', alpha_mul=1.0):
    """Beta Version wordmark (aspect kept, never recoloured) facing -Y before rot (Euler radians), centred at the
    world point loc. plate=True puts it on a dark #101522 plate (use on light surfaces). emissive: lit at night.
    kind='mark' uses the square mark instead."""
    return _brand_at(coll, name, _mtx(loc, rot), width, plate, emissive, kind, alpha_mul)


def atlas_decal(coll, name, slot, loc, rot, width, emissive=False):
    """A poster / print from the brand atlas (wordmark baked into the art), facing -Y before rot."""
    x0, y0, x1, y1 = SLOTS[slot]
    q = _quad(coll, name, _atlas_mat(emissive), width, width * (y1 - y0) / (x1 - x0), _mtx(loc, rot), _uv_rect(slot))
    q['brand'] = 1
    return q


def brand_objects():
    return [o for o in bpy.data.objects if o.get('brand')]


# ------------------------------------------------------------------ prop builder
class Prop:
    """One bevelled mesh object built from boxes / cylinders / balls in prop-local studs."""

    def __init__(self, coll, name, loc, rotz=0.0, bev=0.05):
        self.coll, self.name, self.bev = coll, name, bev
        self.M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rotz), 4, 'Z')
        self.bm = bmesh.new()
        self.lay = self.bm.faces.layers.float.new('rnd')
        self.mats, self.kids = [], []
        self.rng = random.Random(name)

    def _add(self, m, verts, smooth=False, rnd=None):
        if m not in self.mats:
            self.mats.append(m)
        i = self.mats.index(m)
        r = self.rng.random() if rnd is None else rnd
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i
            f[self.lay] = r
            f.smooth = smooth and len(f.verts) == 4

    def box(self, m, size, c, rot=(0, 0, 0), rnd=None):
        M = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        self._add(m, bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)['verts'], rnd=rnd)

    def boxr(self, m, x0, x1, y0, y1, z0, z1, rnd=None):
        self.box(m, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), rnd=rnd)

    def cyl(self, m, r, depth, c, axis='Z', seg=16, r2=None, rot=None, rnd=None):
        R = {'Z': Matrix(), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
        if rot:
            R = Euler(rot).to_matrix().to_4x4() @ R
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2,
                                    depth=depth, matrix=Matrix.Translation(c) @ R)
        self._add(m, res['verts'], smooth=True, rnd=rnd)

    def ball(self, m, r, c, scale=(1, 1, 1), sub=2, rnd=None):
        M = Matrix.Translation(c) @ Matrix.Diagonal((*scale, 1))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=M)
        self._add(m, res['verts'], rnd=rnd)
        for f in {f for v in res['verts'] for f in v.link_faces}:
            f.smooth = True

    # children (world matrix = prop matrix @ local)
    def decal(self, name, slot, w, c, rot=(0, 0, 0), emissive=False):
        x0, y0, x1, y1 = SLOTS[slot]
        q = _quad(self.coll, name, _atlas_mat(emissive), w, w * (y1 - y0) / (x1 - x0), self.M @ _mtx(c, rot),
                  _uv_rect(slot))
        q['brand'] = 1
        self.kids.append(q)
        return q

    def band(self, name, slot, r, z0, z1, c=(0, 0, 0)):
        q = _band(self.coll, name, _atlas_mat(), r, z0, z1, self.M @ Matrix.Translation(c), _uv_rect(slot))
        q['brand'] = 1
        self.kids.append(q)
        return q

    def brand(self, name, c, rot, width, plate=True, emissive=False, kind='wm', alpha_mul=1.0):
        q = _brand_at(self.coll, name, self.M @ _mtx(c, rot), width, plate, emissive, kind, alpha_mul)
        self.kids.append(q)
        return q

    def finish(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        ob.matrix_world = self.M
        self.coll.objects.link(ob)
        if self.bev:
            md = ob.modifiers.new('bevel', 'BEVEL')
            md.width = self.bev
            md.segments = 2
            md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(40)
            md.harden_normals = False
        for k in self.kids:
            k.parent = ob
            k.matrix_parent_inverse = self.M.inverted()
        return ob


# ------------------------------------------------------------------ prop materials
M = {}


def _m():
    if M:
        return M
    P = S.P
    f = S.flat
    M.update(
        carpaint=f('carpaint', '#2f7fd0', rough=0.32, coat=0.6, var=0.05),
        carglass=f('carglass', '#1b232b', rough=0.06, spec=0.8, var=0.0),
        chrome=f('chrome', '#c9ced3', rough=0.18, metal=1.0, var=0.03),
        taillight=f('taillight', '#b3202a', rough=0.3, emit_col='#ff3030', drv=('0.4+lamp*8', ['lamp'])),
        headlight=f('headlight', '#f4f1e6', rough=0.15, emit_col='#fff2d6', drv=('0.2+lamp*12', ['lamp'])),
        lamppost=f('lamppost', '#1f2b28', rough=0.45, metal=0.5, var=0.06),
        hydrant=f('hydrant', '#c23a2e', rough=0.45, grime=0.25),
        hydcap=f('hydcap', '#d9b443', rough=0.45),
        binmetal=f('binmetal', '#40524a', rough=0.45, metal=0.6, var=0.08),
        wheelie=f('wheelie', '#3e6d4a', rough=0.55, var=0.06),
        cardboard=f('cardboard', '#b58a5b', rough=0.85, var=0.15),
        tape=f('tape', '#d4b98e', rough=0.35, var=0.05),
        ceramic=f('ceramic', '#f1efe9', rough=0.22, coat=0.4, var=0.03),
        brass=f('brass', '#b98d3f', rough=0.3, metal=0.9, var=0.05),
        bottle=f('bottleglass', '#4a2414', rough=0.08, spec=0.8, coat=0.6, var=0.0),
        capred=f('capred', '#c42d2d', rough=0.35, metal=0.5),
        burner=f('burner', '#2a2a2d', rough=0.6),
        shelfpaint=f('shelfpaint', '#7f9c8f', rough=0.6, grime=0.1),
        jar=f('jarglass', '#c9d6d2', rough=0.1, spec=0.7, var=0.0),
        calgrid=f('calgrid', '#8f8a80', rough=0.8, var=0.0),
        cyanled=f('cyanled', '#3de4fd', rough=0.3, emit_col='#3de4fd', drv=('0.5+neon*8', ['neon'])),
        shade=f('shade', '#2f4a3f', rough=0.35, metal=0.4),
        cereal=f('cerealside', '#f5c93a', rough=0.6, var=0.05),
        towel=f('towelcloth', '#e9e6dd', rough=0.95),
        brick_red=f('brickred', '#8e4a3a', rough=0.8, var=0.2),
    )
    return M


def _wheel(p, x, y, z, r=1.25, w=0.9):
    m = _m()
    p.cyl(S.P['tire'], r, w, (x, y, z), axis='Y', seg=24)
    side = -1 if y < 0 else 1
    p.cyl(m['chrome'], r * 0.55, 0.08, (x, y + side * w / 2, z), axis='Y', seg=20)
    p.cyl(S.P['dark'], r * 0.22, 0.12, (x, y + side * (w / 2 + 0.03), z), axis='Y', seg=12)


# ------------------------------------------------------------------ STREET props
def lamp_post(coll, name, loc, rotz=0.0, banner=None, side=1):
    """Victorian-style gas lamp, 13.5 studs. banner=atlas slot -> a lamp-post ad banner hung on the +X/-X side."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    L = m['lamppost']
    p.cyl(L, 0.62, 0.35, (0, 0, 0.175), seg=8)
    p.cyl(L, 0.48, 1.3, (0, 0, 1.0), seg=8, r2=0.36)
    p.cyl(L, 0.42, 0.18, (0, 0, 1.75), seg=8)
    p.cyl(L, 0.2, 9.4, (0, 0, 6.5), seg=12, r2=0.16)
    for z in (4.0, 8.0, 11.2):
        p.cyl(L, 0.27, 0.16, (0, 0, z), seg=12)
    p.box(L, (2.0, 0.14, 0.14), (0, 0, 10.4))              # ladder arm
    for sx in (-0.9, 0.9):
        p.ball(L, 0.1, (sx, 0, 10.4), sub=1)
    p.cyl(L, 0.18, 0.4, (0, 0, 11.45), seg=4, r2=0.5, rot=(0, 0, math.pi / 4))
    p.cyl(P['lampglass'], 0.5, 1.2, (0, 0, 12.25), seg=4, rot=(0, 0, math.pi / 4))
    for a in range(4):
        aa = math.pi / 4 + a * math.pi / 2
        p.box(L, (0.08, 0.08, 1.25), (0.5 * math.cos(aa), 0.5 * math.sin(aa), 12.25))
    p.cyl(L, 0.78, 0.45, (0, 0, 13.05), seg=4, r2=0.12, rot=(0, 0, math.pi / 4))
    p.ball(L, 0.13, (0, 0, 13.38), sub=1)
    if banner:
        bx = side * 1.35
        p.box(L, (2.6, 0.1, 0.1), (side * 1.2, 0, 9.75))
        p.box(L, (2.6, 0.1, 0.1), (side * 1.2, 0, 6.4))
        for k in (-1, 1):
            p.decal(f'{name}.banner{"F" if k < 0 else "B"}', banner, 2.2, (bx, k * 0.03, 8.07),
                    (0, 0, 0 if k < 0 else math.pi))
    return p.finish()


def hydrant(coll, name, loc, rotz=0.0):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.03)
    R, C = m['hydrant'], m['hydcap']
    p.cyl(R, 0.6, 0.2, (0, 0, 0.1), seg=10)
    p.cyl(R, 0.42, 1.75, (0, 0, 1.07), seg=18)
    p.cyl(R, 0.52, 0.2, (0, 0, 1.95), seg=18)
    p.ball(R, 0.44, (0, 0, 2.05), scale=(1, 1, 0.75))
    p.cyl(C, 0.13, 0.3, (0, 0, 2.45), seg=5)
    p.cyl(R, 0.17, 1.3, (0, 0, 1.45), axis='X', seg=12)
    for sx in (-0.67, 0.67):
        p.cyl(C, 0.21, 0.12, (sx, 0, 1.45), axis='X', seg=6)
    p.cyl(R, 0.24, 0.35, (0, -0.48, 1.2), axis='Y', seg=12)
    p.cyl(C, 0.28, 0.12, (0, -0.68, 1.2), axis='Y', seg=6)
    return p.finish()


def trash_can(coll, name, loc, rotz=0.0):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.03)
    B = m['binmetal']
    p.cyl(B, 0.78, 2.5, (0, 0, 1.3), seg=20, r2=0.85)
    for z in (0.5, 1.3, 2.1):
        p.cyl(S.P['dark'], 0.84, 0.12, (0, 0, z), seg=20)
    p.cyl(B, 0.95, 0.18, (0, 0, 2.6), seg=20)
    p.ball(B, 0.85, (0, 0, 2.65), scale=(1, 1, 0.35))
    p.cyl(S.P['black'], 0.42, 0.06, (0, -0.0, 2.95), seg=16)
    p.cyl(S.P['dark'], 0.7, 0.12, (0, 0, 0.06), seg=12)
    return p.finish()


def wheelie_bin(coll, name, loc, rotz=0.0):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.06)
    G = m['wheelie']
    p.boxr(G, -0.85, 0.85, -0.95, 0.95, 0.35, 2.7)
    p.boxr(G, -0.95, 0.95, -1.08, 1.05, 2.7, 2.92)
    p.boxr(S.P['dark'], -0.6, 0.6, -1.05, -0.95, 2.4, 2.65)
    p.cyl(S.P['dark'], 0.06, 1.7, (0, 1.12, 2.65), axis='X', seg=8)
    for sx in (-0.7, 0.7):
        p.cyl(S.P['tire'], 0.36, 0.3, (sx, 0.85, 0.36), axis='X', seg=16)
    return p.finish()


def bench(coll, name, loc, rotz=0.0):
    """Park bench: 3 seat planks, 2 back planks, cast-iron ends with armrests; back on +Y."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    for i in range(3):
        p.box(P['plank'], (4.4, 0.36, 0.14), (0, -0.42 + i * 0.4, 1.38))
    for z in (2.0, 2.55):
        p.box(P['plank'], (4.4, 0.13, 0.36), (0, 0.62 + (z - 2.0) * 0.12, z), rot=(-0.2, 0, 0))
    for k in (-1.85, 1.85):
        p.box(P['dark'], (0.16, 0.16, 1.32), (k, -0.55, 0.66))
        p.box(P['dark'], (0.16, 0.16, 2.9), (k, 0.6, 1.45), rot=(-0.12, 0, 0))
        p.box(P['dark'], (0.16, 1.3, 0.16), (k, 0.0, 1.25))
        p.box(P['dark'], (0.2, 1.2, 0.12), (k, -0.05, 2.05))
        p.box(P['dark'], (0.16, 0.16, 0.7), (k, -0.6, 1.7))
    return p.finish()


def cardboard_box(coll, name, loc, rotz=0.0, h=1.25, stamp=False):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.03)
    w, d = h * 1.3, h * 1.05
    p.boxr(m['cardboard'], -w / 2, w / 2, -d / 2, d / 2, 0, h)
    p.boxr(m['tape'], -0.18 * h, 0.18 * h, -d / 2 - 0.01, d / 2 + 0.01, h - 0.01, h + 0.01)
    p.boxr(m['tape'], -0.18 * h, 0.18 * h, -d / 2 - 0.01, -d / 2 + 0.01, h * 0.75, h)
    if stamp:
        p.decal(name + '.stamp', 'CRATE', h * 0.55, (w * 0.18, -d / 2 - 0.015, h * 0.45))
    return p.finish()


def crate(coll, name, loc, rotz=0.0, h=2.4, stamp=True):
    """Wooden slat crate; stamp=True prints the brand crate stamp on the -Y and +X faces."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    s = h
    p.boxr(P['plank'], -s / 2 + 0.08, s / 2 - 0.08, -s / 2 + 0.08, s / 2 - 0.08, 0.05, s - 0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(P['wood'], (0.26, 0.26, s), (sx * (s / 2 - 0.13), sy * (s / 2 - 0.13), s / 2))
    for z in (0.13, s - 0.13):
        for sy in (-1, 1):
            p.box(P['wood'], (s, 0.26, 0.26), (0, sy * (s / 2 - 0.13), z))
            p.box(P['wood'], (0.26, s, 0.26), (sy * (s / 2 - 0.13), 0, z))
    for sy in (-1, 1):
        p.box(P['wood'], (s * 1.05, 0.12, 0.26), (0, sy * (s / 2 - 0.02), s / 2), rot=(0, 0.78, 0))
    if stamp:
        p.decal(name + '.stamp', 'CRATE', s * 0.42, (0, -s / 2 - 0.09, s * 0.68))
        p.decal(name + '.stampX', 'CRATE', s * 0.42, (s / 2 + 0.09, 0, s * 0.68), (0, 0, math.pi / 2))
    return p.finish()


def pallet(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.02)
    for i in range(7):
        p.box(P['plank'], (0.42, 3.0, 0.1), (-1.6 + i * 0.533, 0, 0.6))
    for i in range(3):
        p.box(P['plank'], (3.6, 0.42, 0.1), (0, -1.25 + i * 1.25, 0.05))
        for j in range(3):
            p.box(P['wood'], (0.45, 0.42, 0.42), (-1.5 + j * 1.5, -1.25 + i * 1.25, 0.31))
    p.box(P['plank'], (3.6, 0.42, 0.08), (0, -1.25, 0.69))
    return p.finish()


def shrub(coll, name, loc, rotz=0.0, length=5.2):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0)
    rnd = random.Random(name)
    n = 6
    for i in range(n):
        x = -length / 2 + 0.7 + i * (length - 1.4) / (n - 1)
        r = rnd.uniform(0.75, 1.05)
        p.ball(P['leaf' if i % 2 else 'leaf2'], r, (x, rnd.uniform(-0.2, 0.2), r * 0.7 + rnd.uniform(0, 0.25)),
               scale=(1.1, 0.85, 0.9), sub=2)
    for i in range(3):
        p.ball(P['leaf2'], 0.7, (rnd.uniform(-1.5, 1.5), rnd.uniform(-0.1, 0.1), 1.6), scale=(1, 0.8, 0.8))
    return p.finish()


def car(coll, name, loc, rotz=0.0, length=13.5):
    """Chunky boxy hatchback (front +X), branded doors on both sides."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.12)
    L = length / 2
    C, G = m['carpaint'], m['carglass']
    p.boxr(C, -L, L, -3.0, 3.0, 0.95, 3.25)                     # body tub
    p.boxr(C, -L + 0.9, 2.4, -2.75, 2.75, 3.25, 5.35)           # cabin
    p.boxr(C, 2.0, L - 0.2, -2.9, 2.9, 3.2, 3.45)               # bonnet lip
    # glass: windscreen / rear / side windows (split by pillars)
    p.boxr(G, 2.38, 2.48, -2.45, 2.45, 3.6, 5.1)
    p.boxr(G, -L + 0.82, -L + 0.92, -2.4, 2.4, 3.7, 5.1)
    for sy in (-1, 1):
        y = sy * 2.77
        p.boxr(G, -L + 1.3, -1.75, y - 0.04, y + 0.04, 3.65, 5.05)
        p.boxr(G, -1.45, 2.05, y - 0.04, y + 0.04, 3.65, 5.05)
        p.boxr(P['black'], -1.7 + 0.0, -1.5, y - 0.06, y + 0.06, 3.3, 5.2)   # B pillar seam
        p.boxr(P['black'], -1.66, -1.62, sy * 3.0 - 0.03, sy * 3.0 + 0.03, 1.1, 3.2)  # door seams
        p.boxr(P['black'], 2.2, 2.24, sy * 3.0 - 0.03, sy * 3.0 + 0.03, 1.1, 3.2)
        p.box(m['chrome'], (0.6, 0.12, 0.14), (1.4, sy * 3.05, 2.9))           # handle
        p.box(C, (0.5, 0.5, 0.35), (2.0, sy * 3.05, 4.0))                     # mirror
        for x in (-4.4, 4.4):
            _wheel(p, x, sy * 2.75, 1.25)
            p.boxr(P['black'], x - 1.55, x + 1.55, sy * 3.0 - 0.05, sy * 3.0 + 0.05, 2.45, 2.7)  # arch trim
    # bumpers, lights, grille, plates
    for sx in (-1, 1):
        p.boxr(P['dark'], sx * L - 0.25, sx * L + 0.25, -3.05, 3.05, 0.85, 1.65)
        p.boxr(P['white'], sx * (L + 0.24) - 0.03, sx * (L + 0.24) + 0.03, -0.7, 0.7, 1.0, 1.5)
    for sy in (-1, 1):
        p.boxr(m['headlight'], L - 0.02, L + 0.06, sy * 2.1 - 0.6, sy * 2.1 + 0.6, 2.3, 2.95)
        p.boxr(m['taillight'], -L - 0.06, -L + 0.02, sy * 2.3 - 0.45, sy * 2.3 + 0.45, 2.1, 3.0)
    p.boxr(P['black'], L - 0.02, L + 0.05, -1.3, 1.3, 2.0, 2.85)
    for z in (2.2, 2.45, 2.7):
        p.boxr(m['chrome'], L + 0.03, L + 0.07, -1.25, 1.25, z - 0.04, z + 0.04)
    p.boxr(P['dark'], -L + 1.0, 2.2, -2.5, 2.5, 5.35, 5.5)       # roof rails
    # brand on both front doors
    p.brand(name + '.doorL', (0.3, -3.08, 2.15), (0, 0, 0), 2.6, plate=True)
    p.brand(name + '.doorR', (0.3, 3.08, 2.15), (0, 0, math.pi), 2.6, plate=True)
    return p.finish()


def billboard(coll, name, loc, rotz=0.0, width=12.0):
    """Rooftop billboard on two legs with a catwalk and three lamp heads; lit art from the atlas (BILL)."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.05)
    h = width * 864 / 2048
    z0 = 2.2
    D = P['dark']
    for sx in (-width * 0.3, width * 0.3):
        p.box(D, (0.45, 0.45, z0 + h), (sx, 0.5, (z0 + h) / 2))
        p.box(D, (0.25, 2.2, 0.25), (sx, 0.3, z0 * 0.5), rot=(0.6, 0, 0))
    p.boxr(D, -width / 2 - 0.3, width / 2 + 0.3, -0.05, 0.35, z0 - 0.3, z0 + h + 0.3)
    p.boxr(D, -width / 2, width / 2, -1.3, 0.0, z0 - 0.45, z0 - 0.3)                  # catwalk
    p.boxr(D, -width / 2, width / 2, -1.32, -1.22, z0 - 0.3, z0 + 0.6)
    for i in range(3):
        x = -width / 3 + i * width / 3
        p.box(D, (0.12, 1.6, 0.12), (x, -0.8, z0 + h + 0.55))
        p.box(D, (0.6, 0.45, 0.25), (x, -1.55, z0 + h + 0.5))
        p.box(P['lampglass'], (0.5, 0.35, 0.06), (x, -1.55, z0 + h + 0.36))
    p.decal(name + '.art', 'BILL', width, (0, -0.07, z0 + h / 2), emissive=True)
    return p.finish()


def shop_sign(coll, name, loc, rotz=0.0, width=4.2, height=1.35):
    """Fascia sign: dark board with a lit wordmark and a cyan LED strip (faces -Y)."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(P['black'], -width / 2, width / 2, -0.25, 0.0, 0, height)
    p.boxr(P['trim'], -width / 2 - 0.08, width / 2 + 0.08, -0.32, 0.0, height - 0.05, height + 0.08)
    p.boxr(m['cyanled'], -width / 2 + 0.1, width / 2 - 0.1, -0.29, -0.24, 0.06, 0.14)
    p.brand(name + '.wordmark', (0, -0.27, height / 2 + 0.05), (0, 0, 0), min(width * 0.72, (height - 0.3) / WM_ASPECT),
            plate=False, emissive=True)
    return p.finish()


# ------------------------------------------------------------------ KITCHEN props
def fridge(coll, name, loc, rotz=0.0, w=8.3, d=4.65, h=8.0):
    """Two-door commercial fridge, front face at local y=-d/2; brand magnet on the right door."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.06)
    B = P['brushed']
    p.boxr(B, -w / 2, w / 2, -d / 2 + 0.1, d / 2, 0.75, h)
    p.boxr(P['dark'], -w / 2 + 0.1, w / 2 - 0.1, -d / 2 + 0.15, d / 2, 0.0, 0.75)
    for i in range(8):
        p.boxr(P['black'], -w / 2 + 0.6 + i * (w - 1.2) / 8, -w / 2 + 0.6 + i * (w - 1.2) / 8 + 0.5,
               -d / 2 + 0.12, -d / 2 + 0.16, 0.2, 0.6)
    for sx in (-1, 1):
        x0, x1 = (-w / 2 + 0.08, -0.05) if sx < 0 else (0.05, w / 2 - 0.08)
        p.boxr(B, x0, x1, -d / 2, -d / 2 + 0.12, 0.85, h - 0.55)
        p.cyl(P['metal'], 0.09, 2.8, (sx * 0.45, -d / 2 - 0.25, 4.6), seg=10)
        for z in (3.3, 5.9):
            p.box(P['metal'], (0.12, 0.3, 0.12), (sx * 0.45, -d / 2 - 0.12, z))
    p.boxr(P['dark'], -w / 2 + 0.1, w / 2 - 0.1, -d / 2 + 0.05, -d / 2 + 0.12, h - 0.5, h - 0.08)
    p.boxr(m['cyanled'], -0.6, 0.6, -d / 2 + 0.02, -d / 2 + 0.06, h - 0.38, h - 0.2)
    p.brand(name + '.magnet', (2.9, -d / 2 - 0.03, 7.0), (0, 0, 0), 1.2, plate=True)
    return p.finish()


def stove(coll, name, loc, rotz=0.0, w=4.0, d=3.9, h=3.4):
    """Enamel range: black cooktop, 4 burners, oven door with window + bar handle, brand badge on the door."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.05)
    E, K = P['enamel'], P['black']
    fy = -d / 2
    p.boxr(E, -w / 2, w / 2, fy, d / 2, 0.25, h - 0.2)
    p.boxr(K, -w / 2, w / 2, fy, d / 2, h - 0.2, h)
    p.boxr(P['dark'], -w / 2 + 0.15, w / 2 - 0.15, fy + 0.1, d / 2, 0.0, 0.25)
    for (bx, by) in ((-1.0, -0.05), (1.0, -0.05), (-1.0, 0.95), (1.0, 0.95)):
        p.cyl(m['burner'], 0.55, 0.06, (bx, by, h + 0.03), seg=20)
        p.box(P['dark'], (1.2, 0.08, 0.08), (bx, by, h + 0.1))
        p.box(P['dark'], (0.08, 1.2, 0.08), (bx, by, h + 0.1))
    p.boxr(E, -w / 2, w / 2, d / 2 - 0.35, d / 2, h, h + 1.0)                     # backguard
    p.boxr(K, -w / 2 + 0.15, w / 2 - 0.15, fy - 0.08, fy, 0.55, 2.65)              # oven door
    p.boxr(m['carglass'], -1.1, 1.1, fy - 0.1, fy - 0.07, 0.9, 1.85)
    p.cyl(P['metal'], 0.08, w - 0.8, (0, fy - 0.32, 2.78), axis='X', seg=10)
    for sx in (-1.4, 1.4):
        p.box(P['metal'], (0.12, 0.3, 0.12), (sx, fy - 0.17, 2.78))
    p.boxr(K, -w / 2, w / 2, fy - 0.05, fy, 2.92, h - 0.2)                        # knob panel
    for i in range(5):
        p.cyl(P['metal'], 0.13, 0.15, (-1.5 + i * 0.75, fy - 0.12, 3.06), axis='Y', seg=12)
    p.brand(name + '.badge', (-0.55, fy - 0.1, 2.33), (0, 0, 0), 1.15, plate=False)
    # tea towel over the handle (brand atlas TOWEL)
    tw = 1.0
    th = tw * 512 / 384
    p.decal(name + '.towel', 'TOWEL', tw, (0.95, fy - 0.42, 2.82 - th / 2))
    p.cyl(m['towel'], 0.1, tw, (0.95, fy - 0.33, 2.86), axis='X', seg=10)
    return p.finish()


def sink_unit(coll, name, loc, rotz=0.0, w=8.0, d=3.44, h=3.35):
    """Steel sink run: cabinet, two basins, gooseneck faucet; right deck kept free (cereal box goes there)."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    B = P['brushed']
    fy = -d / 2
    p.boxr(B, -w / 2, w / 2, fy + 0.1, d / 2, 0.3, h - 0.3)
    p.boxr(P['dark'], -w / 2 + 0.1, w / 2 - 0.1, fy + 0.2, d / 2, 0.0, 0.3)
    p.boxr(B, -w / 2, w / 2, fy, d / 2, h - 0.3, h)
    for i in range(4):
        x0 = -w / 2 + 0.1 + i * (w - 0.2) / 4
        p.boxr(B, x0 + 0.05, x0 + (w - 0.2) / 4 - 0.05, fy + 0.02, fy + 0.12, 0.45, h - 0.45)
        p.box(P['metal'], (0.8, 0.14, 0.12), (x0 + (w - 0.2) / 8, fy - 0.02, h - 0.75))
    for cx in (-2.0, 1.0):
        p.boxr(P['dark'], cx - 1.2, cx + 1.2, fy + 0.45, d / 2 - 0.6, h - 0.02, h + 0.005)
        p.boxr(B, cx - 1.3, cx + 1.3, fy + 0.35, fy + 0.45, h, h + 0.08)
    fx, fyb = -0.5, d / 2 - 0.4
    p.cyl(P['metal'], 0.14, 1.7, (fx, fyb, h + 0.85), seg=12)
    p.cyl(P['metal'], 0.11, 1.1, (fx, fyb - 0.5, h + 1.7), axis='Y', seg=12)
    p.cyl(P['metal'], 0.1, 0.4, (fx, fyb - 1.0, h + 1.5), seg=12)
    for sx in (-0.5, 0.5):
        p.cyl(P['metal'], 0.1, 0.4, (fx + sx, fyb, h + 0.2), seg=10)
        p.box(P['metal'], (0.35, 0.1, 0.08), (fx + sx, fyb, h + 0.42))
    return p.finish()


def cereal_box(coll, name, loc, rotz=0.0, w=1.1):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.015)
    h, d = w * 1.5, w * 0.4
    p.boxr(m['cereal'], -w / 2, w / 2, -d / 2, d / 2, 0, h)
    p.decal(name + '.front', 'CEREAL', w * 0.995, (0, -d / 2 - 0.006, h / 2))
    p.decal(name + '.back', 'CEREAL', w * 0.995, (0, d / 2 + 0.006, h / 2), (0, 0, math.pi))
    return p.finish()


def cola_bottle(coll, name, loc, rotz=0.0, h=0.9):
    """Generic glass cola bottle with a wrap-around brand label (atlas COLA)."""
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0)
    k = h / 0.9
    p.cyl(m['bottle'], 0.16 * k, 0.55 * k, (0, 0, 0.275 * k), seg=20)
    p.cyl(m['bottle'], 0.16 * k, 0.17 * k, (0, 0, 0.635 * k), seg=20, r2=0.065 * k)
    p.cyl(m['bottle'], 0.065 * k, 0.15 * k, (0, 0, 0.795 * k), seg=14)
    p.cyl(m['capred'], 0.078 * k, 0.05 * k, (0, 0, 0.875 * k), seg=14)
    p.band(name + '.label', 'COLA', 0.166 * k, 0.12 * k, 0.46 * k)
    return p.finish()


def mug(coll, name, loc, rotz=0.0, h=0.5):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.01)
    r = h * 0.48
    p.cyl(m['ceramic'], r, h, (0, 0, h / 2), seg=24)
    p.cyl(S.P['dark'], r * 0.85, 0.02, (0, 0, h - 0.005), seg=24)
    p.box(m['ceramic'], (0.07, 0.06, h * 0.55), (r + 0.13, 0, h / 2))
    p.box(m['ceramic'], (0.16, 0.06, 0.06), (r + 0.06, 0, h * 0.78))
    p.box(m['ceramic'], (0.16, 0.06, 0.06), (r + 0.06, 0, h * 0.22))
    p.band(name + '.print', 'MUG', r + 0.004, h * 0.12, h * 0.85)
    return p.finish()


def brass_pan(coll, name, loc, rotz=0.0):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0.01)
    p.cyl(m['brass'], 0.72, 0.3, (0, 0, 0.17), seg=24, r2=0.8)
    p.cyl(S.P['dark'], 0.7, 0.02, (0, 0, 0.3), seg=24)
    p.box(m['brass'], (1.3, 0.14, 0.08), (1.4, 0, 0.3), rot=(0, -0.12, 0))
    return p.finish()


def wall_clock(coll, name, loc, rotz=0.0, d=2.6):
    """Round wall clock, bottom at loc (centre at loc.z + d/2), face towards -Y."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.02)
    r = d / 2
    c = r
    p.cyl(P['black'], r, 0.3, (0, 0, c), axis='Y', seg=32)
    p.cyl(P['white'], r * 0.86, 0.06, (0, -0.15, c), axis='Y', seg=32)
    for i in range(12):
        a = i * math.pi / 6
        L = 0.22 if i % 3 == 0 else 0.12
        p.box(P['black'], (0.06, 0.04, L), (math.sin(a) * r * 0.72, -0.19, c + math.cos(a) * r * 0.72), rot=(0, a, 0))
    p.box(P['black'], (0.08, 0.04, r * 0.45), (math.sin(-0.9) * r * 0.2, -0.22, c + math.cos(-0.9) * r * 0.2),
          rot=(0, -0.9, 0))
    p.box(P['black'], (0.06, 0.04, r * 0.7), (math.sin(2.1) * r * 0.32, -0.24, c + math.cos(2.1) * r * 0.32),
          rot=(0, 2.1, 0))
    p.box(P['red'], (0.03, 0.04, r * 0.75), (math.sin(4.0) * r * 0.33, -0.26, c + math.cos(4.0) * r * 0.33),
          rot=(0, 4.0, 0))
    p.cyl(P['black'], 0.08, 0.1, (0, -0.25, c), axis='Y', seg=10)
    return p.finish()


def calendar(coll, name, loc, rotz=0.0, h=2.6):
    """Plain paper wall calendar (no year): red header, 5 x 7 day grid, one day ringed."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.0)
    w = h * 0.7
    p.boxr(P['white'], -w / 2, w / 2, -0.02, 0.02, 0, h)
    p.boxr(P['white'], -w / 2 + 0.05, w / 2 - 0.05, -0.04, -0.02, h * 0.02, h * 0.52)   # page curl hint
    p.boxr(P['red'], -w / 2, w / 2, -0.035, -0.02, h * 0.8, h * 0.97)
    p.boxr(P['white'], -w * 0.3, w * 0.3, -0.045, -0.03, h * 0.86, h * 0.91)
    gw, gh = (w - 0.3) / 7, (h * 0.5) / 5
    for r in range(5):
        for c in range(7):
            x = -w / 2 + 0.15 + (c + 0.5) * gw
            z = h * 0.08 + (r + 0.5) * gh
            mat = P['red'] if (r, c) == (2, 4) else m['calgrid']
            p.box(mat, (gw * 0.72, 0.012, gh * 0.72), (x, -0.03, z))
    p.box(P['white'], (w - 0.3, 0.012, h * 0.08), (0, -0.03, h * 0.66))
    p.cyl(P['dark'], 0.06, 0.12, (0, -0.05, h * 0.985), axis='Y', seg=8)
    return p.finish()


def chair(coll, name, loc, rotz=0.0, h=3.4):
    """Dining chair, seat 1.75, back towards +Y."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    W = P['wood']
    p.boxr(W, -0.8, 0.8, -0.75, 0.75, 1.55, 1.8)
    for sx in (-0.65, 0.65):
        p.box(W, (0.2, 0.2, 1.55), (sx, -0.6, 0.775))
        p.box(W, (0.2, 0.2, h), (sx, 0.65, h / 2))
    p.boxr(W, -0.65, 0.65, 0.58, 0.72, h - 0.65, h - 0.1)
    p.boxr(W, -0.65, 0.65, 0.6, 0.7, 2.35, 2.55)
    for sx in (-0.25, 0.25):
        p.boxr(W, sx - 0.06, sx + 0.06, 0.6, 0.7, 2.55, h - 0.65)
    p.boxr(W, -0.6, 0.6, -0.08, 0.08, 0.5, 0.65)
    return p.finish()


def pendant_lamp(coll, name, loc, rotz=0.0, h=4.6):
    """Ceiling pendant: canopy, cord, green enamel shade, emissive bulb; loc = shade bottom."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.01)
    p.cyl(m['shade'], 1.0, 1.0, (0, 0, 0.5), seg=24, r2=0.28)
    p.cyl(m['shade'], 0.28, 0.25, (0, 0, 1.1), seg=16)
    p.cyl(P['black'], 0.04, h - 1.2, (0, 0, 1.2 + (h - 1.2) / 2), seg=6)
    p.cyl(m['shade'], 0.4, 0.12, (0, 0, h - 0.06), seg=16)
    p.ball(P['bulb'], 0.28, (0, 0, 0.3), sub=2)
    return p.finish()


def plate_set(coll, name, loc, rotz=0.0):
    m = _m()
    p = Prop(coll, name, loc, rotz, bev=0)
    p.cyl(m['ceramic'], 0.45, 0.04, (0, 0, 0.02), seg=24, r2=0.5)
    p.cyl(m['ceramic'], 0.33, 0.05, (0, 0, 0.06), seg=24, r2=0.36)
    return p.finish()


def cutlery(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0)
    for dx in (-0.12, 0.12):
        p.box(P['metal'], (0.06, 0.75, 0.025), (dx, 0, 0.015))
        p.box(P['metal'], (0.1, 0.22, 0.025), (dx, 0.42, 0.015))
    return p.finish()


def shelves(coll, name, loc, rotz=0.0, h=7.0, w=4.4, d=1.4):
    """Painted kitchen shelf unit (front -Y before rotz) with jars, books and a plant."""
    m = _m(); P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    Sp = m['shelfpaint']
    for sx in (-1, 1):
        p.boxr(Sp, sx * w / 2 - 0.12, sx * w / 2 + 0.12, -d / 2, d / 2, 0, h)
    p.boxr(Sp, -w / 2, w / 2, d / 2 - 0.08, d / 2, 0, h)
    zs = [0.2, 1.9, 3.6, 5.3, h - 0.1]
    for z in zs:
        p.boxr(Sp, -w / 2, w / 2, -d / 2, d / 2, z - 0.1, z + 0.1)
    rnd = random.Random(name)
    x = -w / 2 + 0.35
    while x < w / 2 - 0.5:
        bw = rnd.uniform(0.18, 0.3); bh = rnd.uniform(1.0, 1.4)
        p.boxr(P['books'], x, x + bw, -0.4, 0.45, 5.4, 5.4 + bh, rnd=rnd.random())
        x += bw + 0.02
    for i, jx in enumerate((-1.4, -0.5, 0.4, 1.3)):
        p.cyl(m['jar'], 0.3, 0.9 - 0.1 * (i % 2), (jx, 0, 3.7 + 0.45 - 0.05 * (i % 2)), seg=16)
        p.cyl(P['wood'], 0.32, 0.12, (jx, 0, 4.18 - 0.1 * (i % 2)), seg=16)
    p.cyl(flat_pot(), 0.4, 0.7, (1.2, 0, 2.35), seg=14, r2=0.32)
    p.ball(P['leaf'], 0.55, (1.2, 0, 3.0), sub=2)
    for i, bx in enumerate((-1.5, -0.8)):
        p.boxr(P['white'], bx - 0.25, bx + 0.25, -0.4, 0.4, 2.0, 2.0 + 0.12 * (i + 1))
    return p.finish()


def flat_pot():
    return S.flat('pot', '#9a6a4a', rough=0.8)


def framed_print(coll, name, loc, rotz=0.0, slot='P2', w=2.0):
    """Wooden frame with a brand atlas print (portrait slots) on a wall; faces -Y before rotz."""
    P = S.P
    x0, y0, x1, y1 = SLOTS[slot]
    h = w * (y1 - y0) / (x1 - x0)
    p = Prop(coll, name, loc, rotz, bev=0.03)
    fw = 0.22
    p.boxr(P['wood'], -w / 2 - fw, w / 2 + fw, 0.0, 0.18, -h / 2 - fw, h / 2 + fw)
    p.decal(name + '.art', slot, w, (0, -0.01, 0))
    return p.finish()
