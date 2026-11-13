"""Big hand-built places, ported from the In This Town series (code-only: every piece is built here or in props.py).

Each builder is (b, coll, O) -> anchors, like Street and Kitchen in sets.py. Actors stand near the origin.
    Gym       school gym: wood court, hoops at x +-40, bleachers along the back wall, high windows
    MusicRow  shopping street: music shop (display windows, striped awning), road in front, houses across it
    TownPool  swimming pool behind the actors (y 8..32), ladder, diving board, lifeguard chair, pool house
"""
import math

from mathutils import Vector

import props
import sets as S
from places import CATALOG, _FOOT, _m, fence, house, tree
from props import Prop


def bleachers(coll, name, loc, rotz=0.0, w=20.0, rows=5):
    """Stepped wooden bleachers; front (lowest row) faces -y before yaw."""
    p = Prop(coll, name, loc, rotz, bev=0.04)
    seat = S.pbr('bleachwood', 'wood_table_001', 3.0, sat=0.8, val=1.15, grime=0.1)
    frame = _m('bleachframe', '#4a5a6a', rough=0.45, metal=0.5)
    for i in range(rows):
        y0, z = i * 2.2, 1.0 + i * 1.6
        p.boxr(seat, -w / 2, w / 2, y0, y0 + 1.3, z, z + 0.35)
        p.boxr(seat, -w / 2, w / 2, y0 + 1.2, y0 + 2.2, z - 1.0, z - 0.8)
        for x in range(int(-w / 2), int(w / 2) + 1, 5):
            p.box(frame, (0.25, 0.25, z), (x, y0 + 0.65, z / 2))
    p.boxr(frame, -w / 2, w / 2, rows * 2.2 - 0.3, rows * 2.2, 0, 1.0 + rows * 1.6 + 2.5)
    return p.finish()


def hoop(coll, name, loc, rotz=0.0):
    """Basketball hoop on a pole; the board faces -y before yaw."""
    P = S.P
    p = Prop(coll, name, loc, rotz, bev=0.03)
    pole = _m('hooppole', '#2b3a4a', rough=0.4, metal=0.6)
    p.boxr(pole, -0.4, 0.4, 2.0, 2.8, 0, 13.0)
    p.boxr(pole, -0.3, 0.3, 0.0, 2.8, 12.0, 12.6)
    p.boxr(P['white'], -3.6, 3.6, -0.2, 0.0, 11.0, 15.4)
    p.boxr(_m('hoopred', '#c8433a', rough=0.5), -1.2, 1.2, -0.24, -0.2, 12.2, 12.3)
    p.boxr(_m('hoopred', '#c8433a', rough=0.5), -1.2, 1.2, -0.24, -0.2, 13.9, 14.0)
    rim = _m('hooprim', '#e0602c', rough=0.4, metal=0.4)
    for a in range(16):
        r = a / 16 * 6.283
        p.box(rim, (0.5, 0.12, 0.12), (math.cos(r) * 1.1, -1.3 + math.sin(r) * 1.1, 12.0), rot=(0, 0, r + 1.57))
    net = _m('hoopnet', '#f2f0ea', rough=0.9)
    for a in range(8):
        r = a / 8 * 6.283
        p.box(net, (0.06, 0.06, 1.5), (math.cos(r) * 0.85, -1.3 + math.sin(r) * 0.85, 11.2))
    return p.finish()


def umbrella(coll, name, loc, rotz=0.0, color='#c8433a'):
    p = Prop(coll, name, loc, rotz, bev=0.0)
    p.cyl(S.P['white'], 0.12, 8.5, (0, 0, 4.25), seg=8)
    for i in range(8):
        r = i / 8 * 6.283
        c = color if i % 2 == 0 else '#f2f0ea'
        p.box(_m('umb' + c, c, rough=0.7), (2.4, 1.9, 0.12), (math.cos(r) * 2.0, math.sin(r) * 2.0, 8.2), rot=(0, 0.28, r))
    return p.finish()


CATALOG.update(bleachers=bleachers, hoop=hoop, umbrella=umbrella)
_FOOT.update(bleachers=(10.0, 5.5), hoop=(3.6, 3.0))


def _ext_lights(coll, name, O):
    S._light(coll, name, 'fill', 'AREA', O, (11, -18, 7), (0, 0, 3.5), 'ext_fill', 1400, colch='fill_col', size=10,
             cutoff=60, volume=0.0)
    S._light(coll, name, 'rim', 'AREA', O, (6, 11, 11), (0, 0, 4.2), 'ext_rim', 2600, colch='rim_col', size=4,
             cutoff=45, volume=0.2)
    S._light(coll, name, 'key', 'AREA', O, (-9, -10, 9), (0, 0, 4), 'ext_key', 1800, colch='key_col', size=5,
             cutoff=45, volume=0.2)
    S._fog(coll, name, O, (-120, -60, -1), (120, 110, 70), 1.0)


def gym(b, coll, O):
    name = 'Gym'; P = S.P; W = Vector(O)
    floor = S.pbr('gymfloor', 'wood_table_001', 5.0, tint='#f0c890', sat=0.7, val=1.6, grime=0.0, floor=True)
    wall = S.pbr('gymwall', 'painted_plaster_wall', 6.0, paint='#b9c8d8', paint_keep=0.2, grime=0.1)
    low = S.pbr('gymlow', 'painted_plaster_wall', 6.0, paint='#3d5f8f', paint_keep=0.2, grime=0.1)
    b.boxr('ground', P['grass'], -150, 150, -150, 150, -1.3, -0.65, bev=False)
    b.boxr('floor', floor, -45, 45, -35, 32, -0.6, 0.0, bev=False)
    b.boxr('wall', wall, -45, 45, 31.0, 32.0, 0.0, 30.0, bev=False)
    b.boxr('wainscot', low, -44, 44, 30.8, 31.0, 0.0, 5.0, bev=False)
    for sx in (-1, 1):
        x0, x1 = (44.0, 45.0) if sx > 0 else (-45.0, -44.0)
        b.boxr('wall', wall, x0, x1, -35, 32, 0.0, 30.0, bev=False)
        b.boxr('wainscot', low, x0 - 0.2 if sx > 0 else x1, x0 if sx > 0 else x1 + 0.2, -35, 31, 0.0, 5.0, bev=False)
        for wy in (-18.0, 0.0, 18.0):
            xi = 43.9 if sx > 0 else -43.9
            b.boxr('gymwin', P['win'], min(xi, xi - sx * 0.12), max(xi, xi - sx * 0.12), wy - 4.0, wy + 4.0, 18.0, 26.0,
                   bev=False)
    lm = P['white']
    b.boxr('line', lm, -0.15, 0.15, -35, 31, 0.0, 0.03, bev=False)
    for a in range(48):
        r = a / 48 * 6.283
        b.box('line', lm, (0.85, 0.3, 0.03), (math.cos(r) * 6.0, math.sin(r) * 6.0, 0.015), bev=False, rot=r + 1.57)
    for sx in (-1, 1):
        b.boxr('key', _m('gymkey', '#c8433a', rough=0.6), min(sx * 40, sx * 30), max(sx * 40, sx * 30), -6, 6, 0.0, 0.02,
               bev=False)
    b.boxr('ceiling', wall, -45, 45, -35, 32, 30.0, 30.6, bev=False)
    for x in (-11.0, 11.0):
        bleachers(coll, f'{name}.bleachers{int(x)}', W + Vector((x, 17.0, 0)), 0, w=20.0)
    for sx in (-1, 1):
        hoop(coll, f'{name}.hoop{sx}', W + Vector((sx * 40.0, 0.0, 0.0)), 90.0 * sx)
    for x in (-24.0, 0.0, 24.0):
        for y in (-14.0, 10.0):
            props.pendant_lamp(coll, f'{name}.lamp{int(x)}_{int(y)}', W + Vector((x, y, 25.0)), h=5.0)
    props.atlas_decal(coll, f'{name}.banner', 'AD', W + Vector((0, 30.7, 20.0)), (0, 0, 0), 9.0)
    S._room_lights(coll, name, O,
                   wins=[((sx * 42.5, wy, 22.0), (0, wy, 2.0), 7.0, 7.0) for sx in (-1, 1) for wy in (-18.0, 0.0, 18.0)],
                   ceil_lights=[((x, y, 24.0), 'AREA', 1400) for x in (-24.0, 0.0, 24.0) for y in (-14.0, 10.0)])
    return {'bleachers': (0.0, 17.0, 3.0), 'hoop': (40.0, 0.0, 12.0), 'court': (0.0, 0.0, 0.0)}


def musicrow(b, coll, O):
    name = 'MusicRow'; P = S.P; W = Vector(O); A = S.ARCH
    walk = S.pbr('mrwalk', 'square_concrete_pavers', 6.0, sat=0.55, val=1.0, grime=0.1, floor=True)
    front = S.pbr('mrfront', 'painted_plaster_wall', 6.0, paint='#2f6f73', paint_keep=0.25, grime=0.12)
    inner = S.flat('mrinner', '#5a3a28', rough=0.8)
    stage = S.pbr('mrstage', 'wood_table_001', 3.0, sat=0.8, val=0.9, grime=0.0, floor=True)
    red = S.flat('mrawn', '#c8433a', rough=0.6)
    b.boxr('ground', P['grass'], -200, 200, -200, 200, -1.3, -0.4, bev=False)
    b.boxr('walk', walk, -120, 120, -8.0, 40.0, -0.6, 0.0, bev=False)
    b.boxr('curb', P['curb'], -120, 120, -8.6, -8.0, -0.6, 0.12, bev=A)
    b.boxr('road', P['road'], -120, 120, -34.0, -8.6, -0.8, -0.2, bev=False)
    b.boxr('curb', P['curb'], -120, 120, -34.6, -34.0, -0.6, 0.12, bev=A)
    b.boxr('walk', walk, -120, 120, -42.0, -34.6, -0.6, 0.0, bev=False)
    for x in range(-117, 120, 9):
        b.box('lines', P['yellow'], (4.5, 0.35, 0.04), (x, -21.3, -0.18), bev=False)
    fy0, fy1 = 10.0, 10.8
    for (a0, a1) in ((-18, -15), (-2, 3), (8, 10), (16, 18)):
        b.boxr('mfront', front, a0, a1, fy0, fy1, -0.3, 22.0, bev=False)
    for (a0, a1, z0, z1) in ((-15, -2, -0.3, 1.8), (-15, -2, 11.0, 22.0), (3, 8, 9.5, 22.0), (10, 16, -0.3, 1.8),
                             (10, 16, 11.0, 22.0)):
        b.boxr('mfront', front, a0, a1, fy0, fy1, z0, z1, bev=False)
    b.boxr('mbody', front, -18, 18, 16.4, 34.0, -0.3, 22.0, bev=False)
    b.boxr('mtrim', P['trim'], -18.4, 18.4, 9.6, 10.0, 21.4, 22.6, bev=A)
    b.boxr('mtrim', P['trim'], -15.3, -1.7, 9.5, 10.2, 1.4, 1.9, bev=A)
    b.boxr('mtrim', P['trim'], 9.7, 16.3, 9.5, 10.2, 1.4, 1.9, bev=A)
    b.boxr('mglass', P['shopglass'], -15, -2, 10.3, 10.45, 1.8, 11.0, bev=False)
    b.boxr('mglass', P['shopglass'], 10, 16, 10.3, 10.45, 1.8, 11.0, bev=False)
    b.boxr('mdoor', P['trimdark'], 3.0, 8.0, 10.25, 10.6, 0.0, 9.5, bev=A)
    b.boxr('mglass', P['shopglass'], 3.8, 7.2, 10.15, 10.25, 3.5, 8.6, bev=False)
    b.ball('knob', P['brushed'], 0.22, (7.3, 10.05, 4.6))
    b.boxr('mstage', stage, -15, -2, 10.5, 16.0, 0.0, 1.8, bev=False)
    b.boxr('mstage', stage, 10, 16, 10.5, 16.0, 0.0, 1.8, bev=False)
    b.boxr('minner', inner, -18, 18, 16.0, 16.4, -0.3, 22.0, bev=False)
    b.boxr('minner', inner, -15, 16, 10.8, 16.0, 10.9, 11.0, bev=False)
    b.boxr('minner', inner, -2, 10, 10.8, 16.0, -0.3, 22.0, bev=False)
    gcol = S.flat('guitar', '#b0612c', rough=0.4, coat=0.5)          # instruments in the display window
    b.ball('guitar', gcol, 1.1, (-11.0, 13.5, 3.6), scale=(1, 0.3, 1.1))
    b.ball('guitar', gcol, 0.8, (-11.0, 13.5, 5.2), scale=(1, 0.3, 1.0))
    b.box('guitar', P['dark'], (0.3, 0.2, 4.0), (-11.0, 13.3, 7.6))
    b.cyl('drum', S.flat('drum', '#2f5d8a', rough=0.4, coat=0.4), 1.3, 1.4, (-5.5, 13.5, 2.5), seg=24)
    b.cyl('drum', P['white'], 1.32, 0.1, (-5.5, 13.5, 3.25), seg=24)
    for i in range(10):
        x0 = -16.5 + i * 3.4
        m_ = red if i % 2 == 0 else P['white']
        b.boxr('mawning', m_, x0, x0 + 3.4, 6.6, 10.0, 11.6, 11.8, bev=False)
        b.boxr('mawning', m_, x0, x0 + 3.4, 6.5, 6.6, 10.8, 11.8, bev=False)
    props.shop_sign(coll, f'{name}.shopsign', W + Vector((0.0, 9.55, 15.5)), width=9.0, height=2.2)
    S._building(b, -62, -18, 10.0, 24, 26, P['brick'], facing=-1, shop=True, k=1)
    S._building(b, 18, 62, 10.0, 24, 20, P['stucco'], facing=-1, shop=True, k=2)
    S._building(b, -106, -62, 10.0, 24, 30, P['wbrick'], facing=-1, shop=True, k=3)
    S._building(b, 62, 106, 10.0, 24, 24, P['brick'], facing=-1, shop=True, k=4)
    cols = ['#c9b79c', '#9fb0b3', '#b3bb9f', '#c8a48e', '#d6cebd']
    for i, x in enumerate(range(-64, 65, 16)):                        # houses across the road (reverse angle)
        house(coll, f'{name}.house{i}', W + Vector((x, -44.0, 0.0)), 180, color=cols[i % 5],
              roof=['#7d4a42', '#4c6170', '#5f6f4c'][i % 3])
    for x in (-26.0, 26.0):
        props.lamp_post(coll, f'{name}.lamp{int(x)}', W + Vector((x, -6.4, 0.0)))
        S._light(coll, name, f'lamp{int(x)}', 'SPOT', O, (x, -7.2, 12.4), (x, -4.0, 0), 'lamp', 3800,
                 color=(1.0, 0.76, 0.5), spot=110, blend=0.6, size=0.4, cutoff=45)
    props.bench(coll, f'{name}.bench', W + Vector((32.0, 7.0, 0.0)))
    props.trash_can(coll, f'{name}.trashcan', W + Vector((-24.0, 7.5, 0.0)))
    for x in (-46.0, 46.0):
        tree(coll, f'{name}.tree{int(x)}', W + Vector((x, -5.0, 0.0)), 0, s=1.1)
    for (lx, e) in ((-8.5, 650.0), (13.0, 400.0)):                    # warm display lights behind the glass
        S._light(coll, name, f'disp{int(lx)}', 'AREA', O, (lx, 13.0, 10.6), (lx, 13.0, 0), 'prac_int', e,
                 color=(1.0, 0.85, 0.65), size=5.0, cutoff=30)
    _ext_lights(coll, name, O)
    return {'shop': (0.0, 10.0, 6.0), 'door': (5.5, 9.6, 4.0), 'window': (-8.5, 10.3, 5.0)}


TP_DY = 20.0   # the pool sits behind the actors' clear zone (In This Town had it at the origin)


def _water_mat():
    m, new = S._new_mat('pool_water')
    if new:
        nt = m.node_tree; bs = S._bsdf(m)
        bs.inputs['Base Color'].default_value = S._col('#3aa9cf'); bs.inputs['Roughness'].default_value = 0.08
        tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise')
        ns.inputs['Scale'].default_value = 0.5; ns.inputs['Detail'].default_value = 5.0
        nt.links.new(tc.outputs['Object'], ns.inputs['Vector'])
        bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.2
        nt.links.new(ns.outputs['Fac'], bu.inputs['Height']); nt.links.new(bu.outputs[0], bs.inputs['Normal'])
    return m


def townpool(b, coll, O):
    name = 'TownPool'; P = S.P; W = Vector(O); dy = TP_DY; A = S.ARCH
    deck = S.pbr('tpdeck', 'long_white_tiles', 4.0, tint='#f0ece4', sat=0.35, val=1.1, grime=0.05, floor=True)
    tile = S.flat('tptile', '#5cb8d6', rough=0.35, var=0.15)
    rim = S.flat('tprim', '#f2f0ea', rough=0.5)
    red = S.flat('tpred', '#c8433a', rough=0.5)
    X0, X1, Y0, Y1 = -30.0, 30.0, -12.0 + dy, 12.0 + dy
    for (a0, a1, c0, c1) in ((-200, 200, -150, -50), (-200, 200, 50 + dy, 150), (-200, -70, -50, 50 + dy),
                             (70, 200, -50, 50 + dy)):
        b.boxr('ground', P['grass'], a0, a1, c0, c1, -1.3, -0.05, bev=False)
    for (a0, a1, c0, c1) in ((-70, 70, -50, Y0), (-70, 70, Y1, 50 + dy), (-70, X0, Y0, Y1), (X1, 70, Y0, Y1)):
        b.boxr('deck', deck, a0, a1, c0, c1, -0.6, 0.0, bev=False)
    b.boxr('pwall', tile, X0, X1, Y0, Y0 + 0.4, -9.0, -0.05, bev=False)
    b.boxr('pwall', tile, X0, X1, Y1 - 0.4, Y1, -9.0, -0.05, bev=False)
    b.boxr('pwall', tile, X0, X0 + 0.4, Y0, Y1, -9.0, -0.05, bev=False)
    b.boxr('pwall', tile, X1 - 0.4, X1, Y0, Y1, -9.0, -0.05, bev=False)
    b.boxr('pwall', tile, X0, X1, Y0, Y1, -9.5, -9.0, bev=False)
    for k in (-8, -4, 0, 4, 8):                                         # lane lines on the pool floor
        b.boxr('pline', S.flat('tplane', '#2c5f7a', rough=0.4), X0 + 2, X1 - 2, dy + k - 0.2, dy + k + 0.2,
               -8.98, -8.95, bev=False)
    for (a0, a1, c0, c1) in ((X0 - 1, X1 + 1, Y0 - 1, Y0), (X0 - 1, X1 + 1, Y1, Y1 + 1), (X0 - 1, X0, Y0, Y1),
                             (X1, X1 + 1, Y0, Y1)):
        b.boxr('rim', rim, a0, a1, c0, c1, -0.1, 0.22, bev=A)
    b.boxr('water', _water_mat(), X0 + 0.4, X1 - 0.4, Y0 + 0.4, Y1 - 0.4, -0.85, -0.8, bev=False)
    lx, ly = -20.0, Y0                                                  # ladder on the near wall (actors' side)
    for sx in (-1.1, 1.1):
        b.cyl('ladder', P['metal'], 0.14, 9.5, (lx + sx, ly + 0.6, -2.25), seg=10)
        b.cyl('ladder', P['metal'], 0.14, 1.6, (lx + sx, ly - 0.2, 2.5), axis='Y', seg=10)
        b.cyl('ladder', P['metal'], 0.14, 0.9, (lx + sx, ly - 1.0, 2.05), seg=10)
    for z in (-5.0, -3.4, -1.8, -0.2):
        b.cyl('ladder', P['metal'], 0.1, 2.2, (lx, ly + 0.6, z), axis='X', seg=8)
    b.boxr('dstand', S.flat('tpstand', '#2f6fa0', rough=0.5), 33.0, 37.0, dy - 2.0, dy + 2.0, 0.0, 2.4, bev=A)
    b.boxr('dboard', rim, 22.0, 37.0, dy - 1.1, dy + 1.1, 2.4, 2.75, bev=A)
    cx, cy = -40.0, 18.0 + dy
    for ox in (-1.4, 1.4):
        for oy in (-1.4, 1.4):
            b.boxr('lgchair', rim, cx + ox - 0.2, cx + ox + 0.2, cy + oy - 0.2, cy + oy + 0.2, 0.0, 7.0, bev=A)
    b.boxr('lgseat', red, cx - 1.8, cx + 1.8, cy - 1.8, cy + 1.8, 7.0, 7.4, bev=A)
    b.boxr('lgseat', red, cx - 1.8, cx + 1.8, cy + 1.4, cy + 1.8, 7.4, 10.0, bev=A)
    for z in (2.0, 4.0, 6.0):
        b.boxr('lgchair', rim, cx - 1.6, cx + 1.6, cy - 1.6, cy - 1.3, z, z + 0.25, bev=A)
    S._building(b, -44, 44, 52.0 + dy, 18, 14, P['stucco'], facing=-1, shop=False, k=5)
    props.atlas_decal(coll, f'{name}.poster', 'AD', W + Vector((12.0, 51.7 + dy, 4.0)), (0, 0, 0), 4.0)
    for x in range(-66, 67, 12):
        fence(coll, f'{name}.fence{x}', W + Vector((x, -50.0, 0.0)), 0, w=12.0)
    for sx in (-70.0, 70.0):
        for y in range(-44, 50 + int(dy), 12):
            fence(coll, f'{name}.fence{int(sx)}_{y}', W + Vector((sx, y, 0.0)), 90, w=12.0)
    for (tx, ty, s_) in ((-60.0, 40.0, 1.2), (60.0, 42.0, 1.3), (-85.0, -20.0, 1.4), (85.0, 0.0, 1.3),
                         (-30.0, -70.0, 1.2), (40.0, -72.0, 1.3)):
        tree(coll, f'{name}.tree{int(tx)}_{int(ty)}', W + Vector((tx, ty + dy, 0.0)), 0, s=s_)
    for (x, y, r, c) in ((-14.0, -8.0, 20.0, '#c8433a'), (52.0, 28.0 + dy, -30.0, '#2f6fa0'),
                         (-52.0, -24.0, 0.0, '#e0b43c')):
        umbrella(coll, f'{name}.umbrella{int(x)}', W + Vector((x, y, 0.0)), r, color=c)
    _ext_lights(coll, name, O)
    return {'pool': (0.0, dy, -0.8), 'ladder': (lx, ly, 0.0), 'board': (30.0, dy, 2.75), 'lifeguard': (cx, cy, 7.4)}


BUILT = {'Gym': gym, 'MusicRow': musicrow, 'TownPool': townpool}
