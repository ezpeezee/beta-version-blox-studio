"""Story places for Blox Studio: build any room or outdoor place from a small spec, plus ready presets.

A place spec (a dict, written in shots.py under the top-level key `places`, or one of PRESETS below):

    kind     'room' (default) or 'outdoor'
  room:
    wall     wall paint hex, e.g. '#9fb3c8'
    lower    optional lower-wall (wainscot) paint hex
    floor    'wood' | 'tiles' | 'carpet' | 'concrete' | 'checker'   (+ floor_color for carpet/checker)
    windows  x positions of windows on the back wall, e.g. [-6, 6]
    side_window  true: a window on the right wall too
    light    'warm' (bulb) | 'panel' (office/school ceiling panels)
  outdoor:
    ground   'grass' | 'pavers' | 'asphalt' | 'sand' | 'dirt'
    backdrop 'houses' | 'trees' | 'city' | 'fence' | 'none'   (what stands behind, far back)
  both:
    props    list of [type, x, y, yaw] or [type, x, y, yaw, {options}] (catalogue in CATALOG, docs in API.md)
             yaw 0 = the prop's front faces the camera side (-y); 90 faces +x; -90 faces -x; 180 faces +y
             option 'name' sets the anchor name (camera `focus`); default = type, type2, type3 ...

Floor plan (studs, camera on the -y side): back wall at y 8, side walls at x -14 / 14, room open towards the camera.
Characters stand in the clear zone |x| < 7, -4 < y < 3: put furniture along the back wall (y 4..7.5) and the side
walls (|x| 9..13), never in the clear zone unless the actors use it (a table they stand behind).
"""
import math
import random

from mathutils import Vector

import props
import sets as S
from props import Prop

H = S.H_ROOM


def _m(name, hexcol, **kw):
    return S.flat(name, hexcol, **kw)


def _hex(c, default):
    if not c:
        return default
    if isinstance(c, (list, tuple)):
        return '#%02x%02x%02x' % tuple(int(max(0, min(1, v)) * 255) for v in c[:3])
    return c


# ------------------------------------------------------------------ prop catalogue (front faces -y before yaw)
def bed(coll, name, loc, rotz=0.0, color='#5b7fb8', bunk=False):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.06)
    W = P['wood']; sheet = _m('sheet', '#e9e6df', rough=0.9); blanket = _m('blk' + color, color, rough=0.9)
    # headboard against the wall (+y), bed runs towards the camera
    p.boxr(W, -2.6, 2.6, -4.2, 4.2, 0.4, 1.4)
    for sx in (-2.4, 2.4):
        for sy in (-4.0, 4.0):
            p.box(W, (0.4, 0.4, 1.0), (sx, sy, 0.5))
    p.boxr(W, -2.7, 2.7, 3.9, 4.4, 0, 4.0)
    p.boxr(W, -2.7, 2.7, -4.4, -4.0, 0, 2.2)
    p.boxr(sheet, -2.4, 2.4, -3.9, 3.9, 1.4, 2.1)
    p.boxr(blanket, -2.5, 2.5, -3.95, 1.8, 2.0, 2.35)
    p.box(sheet, (3.6, 1.2, 0.6), (0, 3.0, 2.45))
    if bunk:
        for sx in (-2.5, 2.5):
            for sy in (-4.1, 4.1):
                p.box(W, (0.35, 0.35, 8.0), (sx, sy, 4.0))
        p.boxr(W, -2.6, 2.6, -4.2, 4.2, 5.2, 5.9)
        p.boxr(sheet, -2.4, 2.4, -3.9, 3.9, 5.9, 6.4)
        p.boxr(_m('blk2' + color, '#c98a3a', rough=0.9), -2.5, 2.5, -3.95, 1.8, 6.35, 6.65)
        p.boxr(W, -2.6, 2.6, -4.2, -3.9, 6.4, 7.4)
        for z in (1.8, 3.0, 4.2):
            p.box(W, (0.2, 1.4, 0.2), (2.75, -2.5, z))
    return p.finish()


def nightstand(coll, name, loc, rotz=0.0, lamp=True):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(P['wood'], -0.9, 0.9, -0.8, 0.8, 0, 2.2)
    p.box(P['trimdark'], (1.4, 0.05, 0.6), (0, -0.82, 1.5))
    if lamp:
        p.cyl(P['dark'], 0.3, 0.2, (0, 0, 2.3), seg=14)
        p.cyl(P['dark'], 0.06, 1.0, (0, 0, 2.8), seg=6)
        p.cyl(_m('lampshade', '#efe2c4', rough=0.8, emit_col='#ffe2b0', drv=('0.3+prac*3', ['prac'])), 0.55, 0.8,
              (0, 0, 3.5), seg=16, r2=0.35)
    return p.finish()


def desk(coll, name, loc, rotz=0.0, computer=True, color=None):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    top = _m('desk' + color, color) if color else P['wood']
    p.boxr(top, -2.6, 2.6, -1.2, 1.2, 2.6, 2.85)
    for sx in (-2.4, 2.4):
        p.boxr(top, sx - 0.15, sx + 0.15, -1.1, 1.1, 0, 2.6)
    p.boxr(top, 1.0, 2.3, -1.1, 1.1, 1.0, 2.6)
    p.box(P['metal'], (0.6, 0.06, 0.1), (1.65, -1.12, 2.1))
    if computer:
        p.boxr(P['black'], -1.3, 1.3, 0.3, 0.45, 3.4, 4.9)
        p.boxr(_m('screen', '#3a6fa8', rough=0.3, emit_col='#6fb7ff', drv=('0.6+prac*2', ['prac'])),
               -1.15, 1.15, 0.27, 0.3, 3.55, 4.75)
        p.box(P['black'], (0.2, 0.2, 0.6), (0, 0.4, 3.1))
        p.box(P['black'], (1.0, 0.6, 0.06), (0, 0.4, 2.88))
        p.box(P['dark'], (1.8, 0.6, 0.08), (0, -0.4, 2.9))
    return p.finish()


def office_chair(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.05)
    seat = _m('chairfabric', '#3a3f48', rough=0.9)
    for a in range(5):
        r = math.radians(a * 72)
        p.box(P['dark'], (0.15, 1.0, 0.12), (math.sin(r) * 0.45, math.cos(r) * 0.45, 0.25), rot=(0, 0, -r))
    p.cyl(P['metal'], 0.1, 1.2, (0, 0, 0.9), seg=8)
    p.boxr(seat, -0.9, 0.9, -0.9, 0.9, 1.5, 1.85)
    p.boxr(seat, -0.85, 0.85, 0.7, 0.95, 1.9, 3.8)
    return p.finish()


def wardrobe(coll, name, loc, rotz=0.0, color=None):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.05)
    m = _m('wardrobe' + color, color) if color else P['wood']
    p.boxr(m, -2.4, 2.4, -1.2, 1.2, 0, 9.0)
    p.box(P['trimdark'], (0.06, 0.05, 8.2), (0, -1.22, 4.6))
    for sx in (-0.35, 0.35):
        p.box(P['metal'], (0.12, 0.15, 1.0), (sx, -1.28, 4.8))
    return p.finish()


def bookshelf(coll, name, loc, rotz=0.0, w=4.4, h=8.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    for sx in (-1, 1):
        p.boxr(P['wood'], sx * w / 2 - 0.15, sx * w / 2 + 0.15, -0.8, 0.8, 0, h)
    p.boxr(P['wood'], -w / 2, w / 2, 0.65, 0.8, 0, h)
    rnd = random.Random(name)
    z = 0.2
    while z < h - 0.5:
        p.boxr(P['wood'], -w / 2, w / 2, -0.8, 0.8, z - 0.1, z + 0.1)
        x = -w / 2 + 0.25
        while z + 1.6 < h and x < w / 2 - 0.4:
            bw = rnd.uniform(0.2, 0.35); bh = rnd.uniform(1.0, 1.45)
            p.boxr(P['books'], x, x + bw, -0.5, 0.55, z + 0.1, z + 0.1 + bh, rnd=rnd.random())
            x += bw + 0.03
        z += 1.9
    p.boxr(P['wood'], -w / 2, w / 2, -0.8, 0.8, h - 0.2, h)
    return p.finish()


def sofa(coll, name, loc, rotz=0.0, color='#7a5a8c', w=7.0):
    p = Prop(coll, name, loc, rotz, bev=0.15)
    c = _m('sofa' + color, color, rough=0.9, var=0.08)
    c2 = _m('cushion' + color, color, rough=0.95, var=0.14)
    p.boxr(c, -w / 2, w / 2, -1.4, 1.4, 0.3, 1.6)
    p.boxr(c, -w / 2, w / 2, 0.6, 1.5, 1.6, 3.8)
    for sx in (-1, 1):
        p.boxr(c, sx * w / 2 - 0.5 * (sx > 0) - 0.0, sx * w / 2 + 0.5 * (sx < 0), -1.4, 1.5, 1.6, 2.6)
    n = 3 if w > 5 else 2
    cw = (w - 1.2) / n
    for i in range(n):
        x0 = -w / 2 + 0.6 + i * cw
        p.boxr(c2, x0 + 0.05, x0 + cw - 0.05, -1.3, 0.6, 1.6, 2.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(S.P['dark'], (0.25, 0.25, 0.3), (sx * (w / 2 - 0.4), sy * 1.1, 0.15))
    return p.finish()


def armchair(coll, name, loc, rotz=0.0, color='#a0623c'):
    return sofa(coll, name, loc, rotz, color=color, w=3.4)


def coffee_table(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(P['wood'], -2.0, 2.0, -1.0, 1.0, 1.2, 1.45)
    for sx in (-1.8, 1.8):
        for sy in (-0.8, 0.8):
            p.box(P['wood'], (0.25, 0.25, 1.2), (sx, sy, 0.6))
    p.cyl(props._m()['ceramic'], 0.3, 0.5, (0.8, 0.2, 1.7), seg=14)
    return p.finish()


def tv(coll, name, loc, rotz=0.0, w=6.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(P['wood'], -w / 2 - 0.5, w / 2 + 0.5, -1.0, 1.0, 0, 2.2)
    p.box(P['trimdark'], (w * 0.45, 0.05, 0.9), (-w * 0.24, -1.02, 1.1))
    p.box(P['trimdark'], (w * 0.45, 0.05, 0.9), (w * 0.24, -1.02, 1.1))
    p.box(P['black'], (0.6, 0.6, 0.6), (0, 0.2, 2.5))
    h = w * 0.56
    p.boxr(P['black'], -w / 2, w / 2, 0.0, 0.25, 2.8, 2.8 + h)
    p.boxr(_m('tvscreen', '#2b4f78', rough=0.2, emit_col='#7fb4e8', drv=('0.5+prac*2.5', ['prac'])),
           -w / 2 + 0.15, w / 2 - 0.15, -0.03, 0.0, 2.95, 2.65 + h)
    return p.finish()


def floor_lamp(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.02)
    p.cyl(P['dark'], 0.6, 0.15, (0, 0, 0.08), seg=16)
    p.cyl(P['dark'], 0.07, 6.5, (0, 0, 3.3), seg=8)
    p.cyl(_m('lampshade', '#efe2c4', rough=0.8, emit_col='#ffe2b0', drv=('0.3+prac*3', ['prac'])), 0.9, 1.2,
          (0, 0, 7.0), seg=18, r2=0.55)
    return p.finish()


def rug(coll, name, loc, rotz=0.0, color='#8a5a50', w=8.0, d=5.0):
    p = Prop(coll, name, loc, rotz, bev=0.0)
    p.boxr(_m('rug' + color, color, rough=0.97, var=0.18), -w / 2, w / 2, -d / 2, d / 2, 0.0, 0.05)
    p.boxr(_m('rugedge', '#e2d6bd', rough=0.97), -w / 2 + 0.4, w / 2 - 0.4, -d / 2 + 0.4, d / 2 - 0.4, 0.05, 0.07)
    p.boxr(_m('rug' + color, color, rough=0.97, var=0.18), -w / 2 + 0.6, w / 2 - 0.6, -d / 2 + 0.6, d / 2 - 0.6,
           0.07, 0.09)
    return p.finish()


def poster(coll, name, loc, rotz=0.0, color='#c8643c', brand=None, w=2.4, z=7.0):
    """Wall poster at height z (loc = the wall point, front faces -y). brand='P1'|'P2'|'P3'|'AD' prints brand art."""
    x, y, z0 = loc
    if brand:
        return props.atlas_decal(coll, name, brand, (x, y, z0 + z), (0, 0, math.radians(rotz)), w)
    p = Prop(coll, name, (x, y, z0 + z), rotz, bev=0.0)
    h = w * 1.35
    p.boxr(_m('poster' + color, color, rough=0.8, var=0.25), -w / 2, w / 2, -0.04, 0.0, -h / 2, h / 2)
    p.boxr(_m('posterink', '#f1ead8', rough=0.8), -w / 2 + 0.3, w / 2 - 0.3, -0.06, -0.04, -h / 2 + 0.3, -h / 2 + 0.9)
    p.ball(_m('posterink', '#f1ead8', rough=0.8), w * 0.22, (0, -0.05, h * 0.12), scale=(1, 0.1, 1), sub=2)
    return p.finish()


def picture(coll, name, loc, rotz=0.0, color='#a88f6a', w=3.0, z=7.5):
    x, y, z0 = loc
    P = S.P
    p = Prop(coll, name, (x, y, z0 + z), rotz, bev=0.03)
    h = w * 0.75
    p.boxr(P['wood'], -w / 2, w / 2, -0.15, 0.0, -h / 2, h / 2)
    p.boxr(_m('pic' + color, color, rough=0.8, var=0.3), -w / 2 + 0.3, w / 2 - 0.3, -0.2, -0.15, -h / 2 + 0.3,
           h / 2 - 0.3)
    return p.finish()


def door(coll, name, loc, rotz=0.0, color='#8a6a4c', open=False, beyond='#2a2422', sign=None):
    """A standing door in a frame (put it against a wall). open=True: the door is swung in and you see `beyond`
    (a glow colour, e.g. a bedroom's warm light '#ffcf8a', a dark void '#0a0a10', a sky '#9cc8f0')."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    leaf = _m('door' + color, color, rough=0.55, var=0.1)
    p.boxr(P['trim'], -2.3, -1.9, -0.3, 0.3, 0, 8.0)
    p.boxr(P['trim'], 1.9, 2.3, -0.3, 0.3, 0, 8.0)
    p.boxr(P['trim'], -2.3, 2.3, -0.3, 0.3, 7.6, 8.3)
    if open:
        p.boxr(_m('beyond' + beyond, beyond, rough=1.0, emit_col=beyond, drv=('1.2', [])), -1.9, 1.9, 0.25, 0.3,
               0, 7.6)
        p.box(leaf, (0.18, 3.7, 7.5), (-1.85, 1.8, 3.8))
    else:
        p.boxr(leaf, -1.9, 1.9, -0.12, 0.12, 0.02, 7.58)
        for z0, z1 in ((4.3, 7.0), (0.6, 3.7)):
            p.boxr(leaf, -1.5, 1.5, -0.2, -0.12, z0, z1)
        p.cyl(P['metal'], 0.16, 0.35, (1.3, -0.3, 3.7), axis='Y', seg=12)
    if sign:
        p.boxr(_m('doorsign' + sign, sign, rough=0.6), -0.7, 0.7, -0.35, -0.3, 6.0, 6.8)
    return p.finish()


def school_desk(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    top = _m('schooldesk', '#c9a46a', rough=0.6)
    p.boxr(top, -1.6, 1.6, -1.0, 1.0, 2.3, 2.5)
    for sx in (-1.4, 1.4):
        for sy in (-0.8, 0.8):
            p.box(P['metal'], (0.15, 0.15, 2.3), (sx, sy, 1.15))
    p.boxr(P['metal'], -1.4, 1.4, -0.7, 0.8, 1.5, 1.6)
    p.boxr(P['white'], -0.6, 0.4, -0.5, 0.3, 2.5, 2.55)
    return p.finish()


def whiteboard(coll, name, loc, rotz=0.0, w=12.0, board='#eef1ef', z=4.0):
    P = S.P
    x, y, z0 = loc
    p = Prop(coll, name, (x, y, z0 + z), rotz, bev=0.03)
    h = w * 0.36
    p.boxr(P['metal'], -w / 2, w / 2, -0.25, 0.0, 0, h)
    p.boxr(_m('board' + board, board, rough=0.25 if board.startswith('#e') else 0.9), -w / 2 + 0.25, w / 2 - 0.25,
           -0.3, -0.25, 0.25, h - 0.25)
    p.boxr(P['metal'], -w / 2, w / 2, -0.7, 0.0, -0.1, 0.05)
    rnd = random.Random(name)
    ink = _m('marker', '#3a5a8c', rough=0.5)
    for i in range(4):
        L = rnd.uniform(w * 0.2, w * 0.45)
        x0 = -w / 2 + 1.0 + rnd.uniform(0, w * 0.2)
        p.boxr(ink, x0, x0 + L, -0.33, -0.3, h - 1.0 - i * 0.8, h - 0.85 - i * 0.8)
    return p.finish()


def lockers(coll, name, loc, rotz=0.0, n=5, color='#4f6f9a'):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    c = _m('locker' + color, color, rough=0.45, metal=0.4, var=0.06)
    w = 1.6
    for i in range(n):
        x = (i - (n - 1) / 2) * w
        p.boxr(c, x - w / 2 + 0.04, x + w / 2 - 0.04, -0.8, 0.8, 0, 8.0)
        for z in (6.8, 6.95, 7.1):
            p.box(P['dark'], (0.9, 0.05, 0.06), (x, -0.82, z))
        p.box(P['metal'], (0.12, 0.12, 0.5), (x + 0.5, -0.86, 4.2))
    return p.finish()


def counter(coll, name, loc, rotz=0.0, w=8.0, register=True, color='#5d6f62'):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(_m('counterfront' + color, color, rough=0.6), -w / 2, w / 2, -1.3, 1.3, 0, 3.4)
    p.boxr(_m('countertop', '#3c3f44', rough=0.38, var=0.15), -w / 2 - 0.2, w / 2 + 0.2, -1.5, 1.5, 3.4, 3.7)
    if register:
        p.boxr(P['dark'], 0.8, 2.6, -0.6, 0.8, 3.7, 4.4)
        p.boxr(P['dark'], 1.1, 2.3, 0.4, 0.6, 4.4, 5.3)
        p.boxr(_m('screen', '#3a6fa8', rough=0.3, emit_col='#6fb7ff', drv=('0.6+prac*2', ['prac'])),
               1.2, 2.2, 0.37, 0.4, 4.5, 5.2)
    return p.finish()


GOODS = ['#c8463c', '#e0b43c', '#3c7ab4', '#4c9a5a', '#e07a3c', '#8a5aa8', '#e8e2d2']


def store_shelf(coll, name, loc, rotz=0.0, w=8.0, h=7.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    sh = _m('storeshelf', '#d9dcdf', rough=0.45, metal=0.3)
    p.boxr(sh, -w / 2, w / 2, 0.6, 0.8, 0, h)
    for sx in (-1, 1):
        p.boxr(sh, sx * w / 2 - 0.1, sx * w / 2 + 0.1, -0.9, 0.8, 0, h)
    rnd = random.Random(name)
    for z in (0.3, 2.0, 3.7, 5.4):
        p.boxr(sh, -w / 2, w / 2, -0.9, 0.8, z - 0.08, z + 0.08)
        x = -w / 2 + 0.3
        while x < w / 2 - 0.6:
            kind = rnd.random()
            bw = rnd.uniform(0.4, 0.7); bh = rnd.uniform(0.8, 1.4)
            col = rnd.choice(GOODS)
            m = _m('goods' + col, col, rough=0.5, var=0.1)
            if kind < 0.35:
                p.cyl(m, bw / 2, bh, (x + bw / 2, -0.1, z + 0.08 + bh / 2), seg=12)
            else:
                p.boxr(m, x, x + bw, -0.6, 0.5, z + 0.08, z + 0.08 + bh)
            x += bw + 0.08
    return p.finish()


def cooler(coll, name, loc, rotz=0.0, w=6.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    p.boxr(P['white'], -w / 2, w / 2, -1.2, 1.2, 0, 8.5)
    glass = S.P['shopglass']
    p.boxr(_m('coolerglow', '#dfefff', rough=0.3, emit_col='#e8f4ff', drv=('0.8+prac*2', ['prac'])),
           -w / 2 + 0.3, w / 2 - 0.3, 1.0, 1.1, 0.6, 7.8)
    rnd = random.Random(name)
    for z in (0.8, 2.8, 4.8):
        x = -w / 2 + 0.5
        while x < w / 2 - 0.6:
            col = rnd.choice(GOODS)
            p.cyl(_m('goods' + col, col, rough=0.4), 0.22, 1.2, (x + 0.25, 0.2, z + 0.6), seg=10)
            x += 0.6
    p.boxr(_m('coolerglass', '#cfe3ee', rough=0.05, spec=0.8, alpha=0.25, var=0.0), -w / 2 + 0.2, w / 2 - 0.2,
           -1.25, -1.2, 0.4, 8.1)
    for sx in (-w / 2 + 0.2, 0, w / 2 - 0.2):
        p.box(P['metal'], (0.2, 0.15, 7.8), (sx, -1.25, 4.2))
    return p.finish()


def table(coll, name, loc, rotz=0.0, w=3.0, d=2.0, color=None):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    m = _m('table' + color, color) if color else P['wood']
    p.boxr(m, -w / 2, w / 2, -d / 2, d / 2, 2.35, 2.6)
    for lx in (-w / 2 + 0.25, w / 2 - 0.25):
        for ly in (-d / 2 + 0.25, d / 2 - 0.25):
            p.box(m, (0.28, 0.28, 2.35), (lx, ly, 1.175))
    return p.finish()


def plant(coll, name, loc, rotz=0.0, h=1.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.02)
    p.cyl(props.flat_pot(), 0.8 * h, 1.6 * h, (0, 0, 0.8 * h), seg=14, r2=0.6 * h)
    rnd = random.Random(name)
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        p.ball(P['leaf' if i % 2 else 'leaf2'], rnd.uniform(0.6, 0.9) * h,
               (math.cos(a) * 0.5 * h, math.sin(a) * 0.5 * h, rnd.uniform(2.0, 3.0) * h), sub=2)
    return p.finish()


def tree(coll, name, loc, rotz=0.0, s=1.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.0)
    p.cyl(P['trunk'], 0.4 * s, 5.0 * s, (0, 0, 2.5 * s), seg=10, r2=0.3 * s)
    rnd = random.Random(name)
    for i in range(7):
        a = rnd.uniform(0, 6.28); r = rnd.uniform(0.6, 1.6) * s
        p.ball(P['leaf' if i % 2 else 'leaf2'], rnd.uniform(1.3, 2.0) * s,
               (math.cos(a) * r, math.sin(a) * r * 0.7, rnd.uniform(5.4, 7.8) * s), sub=2)
    return p.finish()


def bush(coll, name, loc, rotz=0.0, s=1.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.0)
    rnd = random.Random(name)
    for i in range(4):
        p.ball(P['leaf' if i % 2 else 'leaf2'], rnd.uniform(0.9, 1.3) * s,
               (rnd.uniform(-1, 1) * s, rnd.uniform(-0.4, 0.4) * s, 0.9 * s), sub=2)
    return p.finish()


def fence(coll, name, loc, rotz=0.0, w=12.0, color='#e8e2d6'):
    p = Prop(coll, name, loc, rotz, bev=0.03)
    c = _m('fence' + color, color, rough=0.7, grime=0.2)
    x = -w / 2
    while x <= w / 2 + 0.01:
        p.boxr(c, x - 0.25, x + 0.25, -0.12, 0.12, 0, 4.0)
        p.boxr(c, x - 0.25, x + 0.25, -0.12, 0.12, 4.0, 4.3)
        x += 0.9
    for z in (1.2, 3.0):
        p.boxr(c, -w / 2, w / 2, 0.12, 0.3, z, z + 0.35)
    return p.finish()


def swing(coll, name, loc, rotz=0.0):
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.04)
    frame = _m('playred', '#c8463c', rough=0.5)
    for sx in (-3.2, 3.2):
        for sy in (-1.2, 1.2):
            p.box(frame, (0.3, 0.3, 9.4), (sx, sy * 0.6, 4.6), rot=(sy * 0.12, 0, 0))
    p.cyl(frame, 0.22, 6.8, (0, 0, 9.0), axis='X', seg=10)
    for sx in (-1.4, 1.4):
        for dx in (-0.6, 0.6):
            p.cyl(P['metal'], 0.04, 6.6, (sx + dx, 0, 5.6), seg=6)
        p.boxr(_m('playyellow', '#e0b43c', rough=0.5), sx - 0.8, sx + 0.8, -0.4, 0.4, 2.2, 2.4)
    return p.finish()


def slide(coll, name, loc, rotz=0.0):
    p = Prop(coll, name, loc, rotz, bev=0.05)
    blue = _m('playblue', '#3c7ab4', rough=0.5); yel = _m('playyellow', '#e0b43c', rough=0.5)
    for sx in (-1.0, 1.0):
        p.box(yel, (0.2, 0.2, 6.5), (sx, 3.0, 3.25))
        for z in range(1, 6):
            p.box(yel, (2.0, 0.18, 0.18), (0, 3.0, z * 1.1))
    p.boxr(yel, -1.2, 1.2, 1.8, 3.2, 6.3, 6.6)
    a = math.atan2(6.3, 5.5)
    p.box(blue, (2.0, 7.4, 0.2), (0, -1.0, 3.3), rot=(-a, 0, 0))
    for sx in (-1.05, 1.05):
        p.box(blue, (0.15, 7.4, 0.6), (sx, -1.0, 3.6), rot=(-a, 0, 0))
    return p.finish()


def house(coll, name, loc, rotz=0.0, color='#c9b79c', roof='#7d4a42', w=14.0):
    """A simple house facade + roof for outdoor backdrops (front faces -y)."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.05)
    wall = _m('house' + color, color, rough=0.8, var=0.08, grime=0.2)
    rf = _m('roof' + roof, roof, rough=0.8, var=0.12)
    d = 10.0
    p.boxr(wall, -w / 2, w / 2, 0, d, 0, 9.0)
    for i, z in enumerate(range(9, 15)):
        k = (z - 9) / 6.0
        p.boxr(rf, -w / 2 - 0.6 + k * (w / 2), w / 2 + 0.6 - k * (w / 2), -0.8, d + 0.8, z, z + 1.0)
    p.boxr(_m('door' + '#6a4a3a', '#6a4a3a'), -1.2, 1.2, -0.1, 0.1, 0, 5.2)
    for sx in (-w / 4 - 0.5, w / 4 + 0.5):
        p.boxr(P['trim'], sx - 1.4, sx + 1.4, -0.15, 0.0, 3.0, 6.4)
        p.boxr(P['win'], sx - 1.1, sx + 1.1, -0.2, -0.15, 3.3, 6.1)
    p.boxr(P['curb'], -1.8, 1.8, -1.6, 0, 0, 0.35)
    return p.finish()


def rock(coll, name, loc, rotz=0.0, s=1.0):
    p = Prop(coll, name, loc, rotz, bev=0.0)
    p.ball(_m('rock', '#8a8a84', rough=0.9, var=0.2), 1.0 * s, (0, 0, 0.5 * s), scale=(1.4, 1.0, 0.7), sub=1)
    return p.finish()


def toilet(coll, name, loc, rotz=0.0):
    c = props._m()['ceramic']
    p = Prop(coll, name, loc, rotz, bev=0.06)
    p.cyl(c, 0.7, 1.6, (0, -0.2, 0.8), seg=16, r2=0.55)
    p.ball(c, 1.0, (0, -0.4, 1.7), scale=(0.9, 1.2, 0.25), sub=2)
    p.boxr(c, -1.1, 1.1, 0.4, 1.0, 1.6, 3.6)
    return p.finish()


def bathtub(coll, name, loc, rotz=0.0):
    c = props._m()['ceramic']
    p = Prop(coll, name, loc, rotz, bev=0.15)
    p.boxr(c, -4.0, 4.0, -1.8, 1.8, 0, 2.6)
    p.boxr(_m('water', '#9cc8e0', rough=0.05, spec=0.8), -3.6, 3.6, -1.4, 1.4, 2.4, 2.65)
    return p.finish()


def mirror(coll, name, loc, rotz=0.0, w=3.0, z=5.0):
    x, y, z0 = loc
    p = Prop(coll, name, (x, y, z0 + z), rotz, bev=0.03)
    p.boxr(S.P['trim'], -w / 2, w / 2, -0.15, 0, 0, w * 1.2)
    p.boxr(S.flat('mirror', '#c9d3d8', rough=0.02, metal=1.0, var=0.0), -w / 2 + 0.2, w / 2 - 0.2, -0.2, -0.15,
           0.2, w * 1.2 - 0.2)
    return p.finish()


def _wrap(fn, **fixed):
    return lambda coll, name, loc, rotz=0.0, **kw: fn(coll, name, loc, rotz, **{**fixed, **kw})


CATALOG = {
    # bedroom / home
    'bed': bed, 'bunk_bed': _wrap(bed, bunk=True), 'nightstand': nightstand, 'wardrobe': wardrobe,
    'desk': desk, 'office_chair': office_chair, 'bookshelf': bookshelf, 'sofa': sofa, 'armchair': armchair,
    'coffee_table': coffee_table, 'tv': tv, 'floor_lamp': floor_lamp, 'rug': rug, 'poster': poster,
    'picture': picture, 'door': door, 'table': table, 'chair': props.chair, 'plant': plant,
    'toilet': toilet, 'bathtub': bathtub, 'mirror': mirror,
    'clock': lambda coll, name, loc, rotz=0.0, z=9.0, **kw: props.wall_clock(coll, name, (loc[0], loc[1], loc[2] + z), rotz),
    'shelves': props.shelves, 'fridge': props.fridge, 'stove': props.stove, 'sink_unit': props.sink_unit,
    # school / office / store
    'school_desk': school_desk, 'whiteboard': whiteboard,
    'chalkboard': _wrap(whiteboard, board='#2f4a3c'), 'lockers': lockers, 'counter': counter,
    'store_shelf': store_shelf, 'cooler': cooler,
    # outdoor
    'tree': tree, 'bush': bush, 'fence': fence, 'swing': swing, 'slide': slide, 'house': house, 'rock': rock,
    'bench': props.bench, 'car': props.car, 'lamp_post': props.lamp_post, 'trash_can': props.trash_can,
    'wheelie_bin': props.wheelie_bin, 'hydrant': props.hydrant, 'box': props.cardboard_box, 'crate': props.crate,
}

# ------------------------------------------------------------------ the story's own things (blocky, from parts)
_TOPS = {}
SIZES = {}   # (place, anchor) -> height of a story thing, for 'ins' framing


def _thing(parts):
    """A story object made only of chunky parts: block, tube, cone, ball. Coarse on purpose (Roblox parts, not models).
    part = [shape, colour, size..., [x, y, z]] (+ optional {options}); x/y/z is the part's centre, the prop's front is -y.
      ['block', '#c83c3c', [w, d, h], [x, y, z]]
      ['tube',  '#d8d8d8', r, h, [x, y, z]]          upright; {'axis': 'X'} or 'Y' lays it down
      ['cone',  '#e8e2d6', r, h, [x, y, z]]          point up; {'r2': 0.3} for a cut cone; {'flip': True} points down
      ['ball',  '#5f9a3c', r, [x, y, z]]             {'scale': [1, 1, 0.6]} to squash it
    options on any part: 'glow': 0..5 (lights up), 'metal': true, 'tilt': [rx, ry, rz] degrees,
    'main': true (a prop's {'color': ...} option recolours this part)."""
    def build(coll, name, loc, rotz=0.0, s=1.0, color=None):
        p = Prop(coll, name, loc, rotz, bev=0.06 * s)
        for it in parts:
            it = list(it)
            o = it.pop() if isinstance(it[-1], dict) else {}
            shape, col = it[0], (color if color and o.get('main') else _hex(it[1], '#a0a0a0'))
            c = Vector(it[-1]) * s
            gl = float(o.get('glow', 0)); mt = bool(o.get('metal'))
            m = _m(f'thing{col}{gl}{mt}', col, rough=0.35 if mt else 0.8, metal=0.8 if mt else 0.0,
                   emit=gl, emit_col=col if gl else None, var=0.1)
            rot = tuple(math.radians(a) for a in o['tilt']) if o.get('tilt') else None
            if shape == 'block':
                p.box(m, tuple(v * s for v in it[2]), c, rot=rot or (0, 0, 0))
            elif shape in ('tube', 'cone'):
                r, h = it[2] * s, it[3] * s
                r2 = o['r2'] * s if 'r2' in o else (r if shape == 'tube' else 0.0)
                if o.get('flip'): r, r2 = r2, r
                p.cyl(m, r, h, c, axis=o.get('axis', 'Z'), seg=10, r2=r2, rot=rot)
            elif shape == 'ball':
                p.ball(m, it[2] * s, c, scale=tuple(o.get('scale', (1, 1, 1))), sub=1)
            else:
                print(f'[things] {name}: unknown part {shape!r} (block, tube, cone, ball)')
        return p.finish()
    return build


def register_things(things):
    """Add the story's own things (timed.json 'things': {name: [parts]}) to the prop catalogue."""
    for nm, parts in (things or {}).items():
        CATALOG[nm] = _thing(parts)
        tops = [pt[-2][2] if isinstance(pt[-1], dict) else pt[-1][2] for pt in parts if len(pt) >= 3]
        _TOPS[nm] = (max(tops) if tops else 2.0) + 0.5


# rough footprints (half width x, half depth y) before yaw, for the clear-zone warning
_FOOT = {'bed': (2.7, 4.4), 'bunk_bed': (2.7, 4.4), 'desk': (2.6, 1.2), 'sofa': (3.5, 1.5), 'armchair': (1.7, 1.5),
         'wardrobe': (2.4, 1.2), 'bookshelf': (2.2, 0.8), 'tv': (3.5, 1.0), 'counter': (4.0, 1.5),
         'store_shelf': (4.0, 0.9), 'cooler': (3.0, 1.2), 'lockers': (4.0, 0.8), 'coffee_table': (2.0, 1.0),
         'table': (1.5, 1.0), 'school_desk': (1.6, 1.0), 'car': (6.8, 2.6), 'swing': (3.4, 1.0), 'slide': (1.2, 4.5),
         'house': (7.0, 10.0), 'fence': (6.0, 0.3), 'bathtub': (4.0, 1.8)}
_FLAT = {'rug', 'poster', 'picture', 'whiteboard', 'chalkboard', 'mirror', 'clock'}


# ------------------------------------------------------------------ floors / grounds
def _floor_mat(kind, color):
    if kind == 'tiles':
        return S.pbr('pl_tiles', 'floor_tiles_06', 5.0, tint='#e8e2d6', sat=0.35, val=1.25, grime=0.2, floor=True,
                     nstr=0.6)
    if kind == 'concrete':
        return S.pbr('pl_concrete', 'concrete_wall_008', 8.0, tint='#c8c6c0', sat=0.3, val=1.05, grime=0.3, floor=True)
    if kind == 'carpet':
        return S.flat('carpet' + color, color, rough=0.98, var=0.1)
    if kind == 'checker':
        return S.flat('checker' + color, '#e6e1d6', rough=0.4, ramp=['#e6e1d6', color], var=0.03)
    return S.pbr('pl_woodfloor', 'wood_table_001', 4.0, sat=0.8, val=1.05, grime=0.15, floor=True)


def _checker(b, m, x0, x1, y0, y1, s=2.5):
    i = 0
    y = y0
    while y < y1:
        x = x0; j = 0
        while x < x1:
            b.boxr('floor', m, x, min(x + s, x1), y, min(y + s, y1), -0.6, 0.0, bev=False, rnd=0.0 if (i + j) % 2 else 1.0)
            x += s; j += 1
        y += s; i += 1


def _ground_mat(kind):
    P = S.P
    if kind == 'pavers':
        return P['walk']
    if kind == 'asphalt':
        return P['road']
    if kind == 'sand':
        return S.flat('sand', '#d8c49a', rough=0.95, var=0.12)
    if kind == 'dirt':
        return S.flat('dirt', '#8a6c4e', rough=0.95, var=0.18)
    return S.pbr('pl_grass', 'leafy_grass', 8.0, paint='#5f9a3c', paint_keep=0.5, grime=0.0, floor=True, nstr=0.6)


# ------------------------------------------------------------------ builders
def _props(coll, name, O, spec, A):
    W = Vector(O)
    count = {}
    for it in spec.get('props', []):
        typ, x, y = it[0], float(it[1]), float(it[2])
        yaw = float(it[3]) if len(it) > 3 else 0.0
        opts = dict(it[4]) if len(it) > 4 else {}
        if typ not in CATALOG:
            print(f'[places] {name}: unknown prop {typ!r}; known: {", ".join(sorted(CATALOG))}')
            continue
        count[typ] = count.get(typ, 0) + 1
        an = opts.pop('name', typ if count[typ] == 1 else f'{typ}{count[typ]}')
        fx, fy = _FOOT.get(typ, (1.0, 1.0))
        if round(abs(yaw) / 90) % 2 == 1: fx, fy = fy, fx   # turned sideways
        if typ not in _FLAT and abs(x) - fx < 7 and -4 < y + fy and y - fy < 3 and not opts.pop('in_clear', False):
            print(f'[places] {name}: {typ} at ({x}, {y}) is in the actors\' clear zone (|x|<7, -4<y<3); '
                  f'move it, or add {{"in_clear": true}} if actors use it')
        opts.pop('in_clear', None)
        try:
            CATALOG[typ](coll, f'{name}.{an}', W + Vector((x, y, 0)), yaw, **opts)
        except TypeError as e:
            print(f'[places] {name}: {typ} options {opts}: {e}')
            CATALOG[typ](coll, f'{name}.{an}', W + Vector((x, y, 0)), yaw)
        top = {'door': 4.0, 'bed': 2.4, 'desk': 3.4, 'whiteboard': 6.0, 'chalkboard': 6.0, 'poster': 7.0,
               'picture': 7.5, 'tv': 4.5, 'counter': 3.8, 'swing': 3.0, 'slide': 4.0}.get(typ, _TOPS.get(typ, 2.6))
        if typ in _TOPS:   # the story's own things: aim at the middle, and let an 'ins' shot frame all of it
            A[an] = (x, y, top / 2); SIZES[(name, an)] = top
        else:
            A[an] = (x, y, top)


def room(b, coll, O, name, spec):
    P = S.P
    wall = _hex(spec.get('wall'), '#c9c2b2')
    wm = S.pbr('pl_wall' + wall, 'painted_plaster_wall', 6.0, paint=wall, paint_keep=0.25, grime=0.2)
    lower = spec.get('lower')
    lm = S.pbr('pl_lower' + lower, 'plywood', 3.0, paint=lower, paint_keep=0.2, grime=0.15) if lower else None
    fk = spec.get('floor', 'wood'); fc = _hex(spec.get('floor_color'), '#7d8a99' if fk == 'carpet' else '#3b3d40')
    fm = _floor_mat(fk, fc)
    S._shell(b, wm, fm if fk != 'checker' else P['trimdark'], P['trim'], P['plaster'], lower=lm)
    if fk == 'checker':
        _checker(b, fm, -14, 14, -32, 8)
    card = S._exterior_card()
    wins = []
    for wx in spec.get('windows', []):
        S._window(b, wx, 7.0, 5.0, 5.0, 7.85, card)
        wins.append(((wx, 7.3, 7.0), (wx, 0, 2.5), 4.8, 4.6))
    if spec.get('side_window'):
        S._window(b, -8.0, 7.0, 6.0, 5.0, 13.85, card, axis='X')
        wins.append(((13.3, -8.0, 7.0), (0, -8, 2.5), 5.6, 4.6))
    if not wins:   # windowless rooms still need a soft daylight source from the camera side
        wins.append(((0, -20, 9.0), (0, 0, 3.0), 10.0, 6.0))
    if spec.get('light', 'warm') == 'panel':
        ceil = [((-5.0, -2.0, H - 0.4), 'AREA', 520), ((5.0, -2.0, H - 0.4), 'AREA', 520), ((0, 4.0, H - 0.4), 'AREA', 420)]
        for cx, cy, _ in (c[0] for c in ceil):
            b.boxr('ceilfix', P['panel'], cx - 2.0, cx + 2.0, cy - 1.0, cy + 1.0, H - 0.15, H, bev=False)
    else:
        ceil = [((0.0, 0.0, H - 0.4), 'SPOT', 560), ((-4.0, -8.0, H - 0.4), 'AREA', 420)]
        b.cyl('ceilfix', P['bulb'], 1.3, 0.25, (0.0, 0.0, H - 0.12), seg=24, bev=False)
    S._room_lights(coll, name, O, wins=wins, ceil_lights=ceil)
    S._fog(coll, name, O, (-14, -32, 0), (14, 8, H), 0.5, col='#d6d2cc')
    A = {}
    _props(coll, name, O, spec, A)
    return A


def outdoor(b, coll, O, name, spec):
    P = S.P
    gm = _ground_mat(spec.get('ground', 'grass'))
    b.boxr('ground', P['grass'], -150, 150, -150, 150, -1.3, -0.3, bev=False)
    b.boxr('ground', gm, -40, 40, -30, 26, -0.6, 0.0, bev=False)
    W = Vector(O)
    bd = spec.get('backdrop', 'trees')
    rnd = random.Random(name)
    if bd == 'houses':
        cols = ['#c9b79c', '#9fb0b3', '#b3bb9f', '#c8a48e', '#d6cebd']
        for i, hx in enumerate(range(-60, 61, 17)):
            house(coll, f'{name}.house{i}', W + Vector((hx, 34 + (i % 2) * 3, 0)), 0, color=cols[i % len(cols)],
                  roof=['#7d4a42', '#4c6170', '#5f6f4c'][i % 3])
        for i, hx in enumerate(range(-52, 53, 17)):
            tree(coll, f'{name}.btree{i}', W + Vector((hx, 30, 0)), 0, s=rnd.uniform(0.9, 1.2))
    elif bd == 'city':
        x = -90; k = 0
        while x < 90:
            w = [14, 12, 16, 13][k % 4]
            S._building(b, x, x + w, 34.0, 14, [22, 17, 28, 19, 25][k % 5],
                        [P['brick'], P['stucco'], P['wbrick'], P['stucco']][k % 4], -1, True, k)
            x += w + 0.6; k += 1
    elif bd == 'fence':
        for i, fx in enumerate(range(-36, 37, 12)):
            fence(coll, f'{name}.bfence{i}', W + Vector((fx, 20, 0)), 0, w=12.0)
        for i, hx in enumerate(range(-50, 51, 20)):
            tree(coll, f'{name}.btree{i}', W + Vector((hx, 32, 0)), 0, s=rnd.uniform(1.0, 1.3))
    if bd in ('trees', 'houses', 'fence'):
        for i in range(26):
            a = rnd.uniform(-0.6, 0.6) * math.pi
            r = rnd.uniform(48, 80)
            tree(coll, f'{name}.ftree{i}', W + Vector((math.sin(a) * r, 40 + abs(math.cos(a)) * r * 0.5, 0)), 0,
                 s=rnd.uniform(1.1, 1.6))
        for i in range(8):
            side = -1 if i % 2 else 1
            tree(coll, f'{name}.stree{i}', W + Vector((side * rnd.uniform(22, 36), rnd.uniform(-26, 12), 0)), 0,
                 s=rnd.uniform(0.9, 1.3))
    S._light(coll, name, 'fill', 'AREA', O, (11, -18, 7), (0, 0, 3.5), 'ext_fill', 1400, colch='fill_col', size=10,
             cutoff=60, volume=0.0)
    S._light(coll, name, 'rim', 'AREA', O, (6, 11, 11), (0, 0, 4.2), 'ext_rim', 2600, colch='rim_col', size=4,
             cutoff=45, volume=0.2)
    S._light(coll, name, 'key', 'AREA', O, (-9, -10, 9), (0, 0, 4), 'ext_key', 1800, colch='key_col', size=5,
             cutoff=45, volume=0.2)
    S._fog(coll, name, O, (-120, -60, -1), (120, 110, 70), 1.0)
    A = {}
    _props(coll, name, O, spec, A)
    return A


def build(b, coll, O, name, spec):
    return (outdoor if spec.get('kind') == 'outdoor' else room)(b, coll, O, name, spec)


# ------------------------------------------------------------------ presets (also examples of the spec)
PRESETS = {
    'Bedroom': dict(wall='#8fa6c4', lower='#e6e0d2', floor='wood', windows=[5.5], props=[
        ['bed', -10.0, 3.4, 0], ['nightstand', -4.8, 6.6, 0], ['wardrobe', 10.5, 6.3, 0], ['desk', 11.0, -2.0, 90],
        ['office_chair', 8.8, -2.0, -90], ['rug', 0, -1.0, 0, {'color': '#c47a5a'}],
        ['poster', -1.0, 7.95, 0, {'brand': 'P1'}], ['poster', 3.0, 7.95, 0, {'color': '#3c7ab4', 'w': 1.8}],
        ['bookshelf', -13.0, -6.0, 90], ['door', -13.85, -14.0, 90]]),
    'Hallway': dict(wall='#c9b79c', lower='#7d5a44', floor='checker', floor_color='#5d4a3e', light='warm', props=[
        ['door', -9.0, 7.7, 0, {'color': '#7a4a3c'}], ['door', -3.0, 7.7, 0, {'color': '#3c5a7a', 'name': 'door2'}],
        ['door', 3.0, 7.7, 0, {'color': '#4c6a48', 'name': 'door3'}],
        ['door', 9.0, 7.7, 0, {'color': '#8a6a3c', 'name': 'door4'}],
        ['door', -13.85, -6.0, 90, {'color': '#6a4a6a', 'name': 'door5'}],
        ['door', 13.85, -6.0, -90, {'color': '#7a3c3c', 'name': 'door6'}],
        ['picture', 0, 7.9, 0, {'z': 9.5, 'w': 2.4}], ['plant', 12.5, 4.0, 0], ['rug', 0, -1.0, 0,
                                                                                 {'color': '#8a3c3c', 'w': 6, 'd': 12}],
        ['clock', -6.0, 7.9, 0, {'z': 10.5}]]),
    'Classroom': dict(wall='#d9d2b0', lower='#7f9c8f', floor='tiles', windows=[], side_window=True, light='panel',
                      props=[['chalkboard', 0, 7.85, 0, {'w': 14.0, 'z': 3.2}], ['desk', 10.2, 3.8, 0,
                                                                                 {'computer': False, 'name': 'teacher_desk'}],
                             ['school_desk', -10.0, 1.5, 0], ['school_desk', -10.0, -4.5, 0],
                             ['school_desk', 10.0, -2.0, 0], ['school_desk', 10.0, -8.0, 0],
                             ['school_desk', -10.0, -10.5, 0], ['clock', -9.0, 7.9, 0, {'z': 10.5}],
                             ['bookshelf', -12.8, 6.3, 0, {'w': 3.0, 'h': 5.0}], ['poster', 12.0, 7.95, 0, {'brand': 'P2'}],
                             ['lockers', -13.0, -18.0, 90]]),
    'LivingRoom': dict(wall='#b8a48c', floor='wood', windows=[-6.0, 6.0], props=[
        ['sofa', -10.0, -1.0, 90, {'color': '#5a6f8c'}], ['tv', 10.8, -1.0, -90], ['coffee_table', -5.5, -4.0, 90,
                                                                                   {'in_clear': True}],
        ['rug', -1.0, -1.5, 0, {'color': '#8a5a50', 'w': 10, 'd': 7}], ['floor_lamp', -12.5, 5.5, 0],
        ['bookshelf', 0, 6.9, 0, {'w': 5.0, 'h': 6.0}], ['plant', 12.5, 6.0, 0], ['armchair', 11.0, 4.8, 0],
        ['picture', -13.9, -6.0, 90, {'z': 7.0}], ['poster', 13.9, -8.0, -90, {'brand': 'P3'}]]),
    'Store': dict(wall='#e0e4e2', floor='tiles', light='panel', props=[
        ['store_shelf', -9.0, 6.6, 0], ['store_shelf', 0.5, 6.6, 0, {'name': 'shelf2'}], ['cooler', 10.5, 6.6, 0],
        ['counter', 10.5, -4.0, 90, {'name': 'checkout'}], ['store_shelf', -12.8, -6.0, 90, {'name': 'shelf3'}],
        ['poster', -4.5, 7.95, 0, {'brand': 'AD', 'w': 3.4, 'z': 9.5}], ['box', -11.0, -16.0, 20],
        ['crate', -12.0, -12.0, 0, {'h': 2.0}]]),
    'Office': dict(wall='#c8ccd0', lower='#5d6f80', floor='carpet', floor_color='#5f6a78', windows=[-6.0, 6.0],
                   light='panel', props=[
                       ['desk', -10.5, 4.5, 0], ['office_chair', -10.5, 2.2, 180], ['desk', 10.5, 4.5, 0, {'name': 'desk2'}],
                       ['office_chair', 10.5, 2.2, 180], ['desk', 11.0, -6.0, -90, {'name': 'desk3'}],
                       ['whiteboard', 0, 7.85, 0, {'w': 8.0, 'z': 4.5}], ['plant', 12.8, 6.8, 0], ['plant', -12.8, -12.0, 0],
                       ['bookshelf', -13.0, -4.0, 90, {'h': 6.0}], ['clock', 5.5, 7.9, 0, {'z': 11.0}]]),
    'Bathroom': dict(wall='#cfe0e4', lower='#e8e6e0', floor='checker', floor_color='#3c5a6a', windows=[0], props=[
        ['bathtub', -9.5, 5.5, 0], ['toilet', 10.0, 6.4, 0], ['mirror', 4.5, 7.85, 0], ['plant', 12.8, -4.0, 0],
        ['door', 13.85, -12.0, -90]]),
    'Park': dict(kind='outdoor', ground='grass', backdrop='trees', props=[
        ['bench', -10.0, 4.0, 0], ['tree', 12.0, 6.0, 0], ['tree', -16.0, 10.0, 0, {'s': 1.2}], ['swing', 16.0, 14.0, 0],
        ['slide', -16.0, 16.0, 30], ['trash_can', -6.5, 6.0, 0], ['lamp_post', 9.0, 3.5, 0], ['bush', -12.0, -6.0, 0],
        ['rock', 10.0, -8.0, 0]]),
    'Backyard': dict(kind='outdoor', ground='grass', backdrop='fence', props=[
        ['house', 0, 30.0, 0, {'color': '#d6cebd'}], ['table', 10.0, 3.0, 0], ['chair', 10.0, 5.0, 0],
        ['tree', -12.0, 8.0, 0], ['bush', 13.0, 10.0, 0], ['wheelie_bin', -10.0, 14.0, 0], ['box', 12.0, -4.0, 30]]),
    'Playground': dict(kind='outdoor', ground='sand', backdrop='houses', props=[
        ['swing', -12.0, 8.0, 0], ['slide', 12.0, 9.0, 0], ['bench', -10.0, -6.0, 90], ['tree', 16.0, -2.0, 0],
        ['fence', 0, 18.0, 0, {'w': 40.0}], ['trash_can', 9.0, 3.5, 0]]),
}
