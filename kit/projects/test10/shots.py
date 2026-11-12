"""10-second test: Sam never gets angry. Writes timed.json next to this file.
Copy this folder to start your own short; kit/template/API.md lists every key."""
import json, os

CAST = {
    'Sam': dict(skin=[0.96, 0.8, 0.6], shirt=[0.9, 0.2, 0.18], pants=[0.15, 0.22, 0.6], shoes=[0.95, 0.95, 0.95],
                hair='cap', hair_color=[0.25, 0.15, 0.08], cap_color=[0.12, 0.3, 0.85], height=1.0),
    'Zoe': dict(skin=[0.85, 0.64, 0.48], shirt=[0.98, 0.84, 0.2], pants=[0.3, 0.3, 0.38], shoes=[0.9, 0.3, 0.35],
                hair='long', hair_color=[0.12, 0.08, 0.06], height=0.95),
}
SAM = [-1.3, -0.4]; ZOE = [2.3, 0.2]


def A(who, at, **kw): return dict(who=who, at=at, **kw)
def S(t0, t1, text, cam, subject, actors, **kw):
    return dict(t0=t0, t1=t1, text=text, set='Street', cam=cam, subject=subject, mood=kw.pop('mood', 'sunny'), actors=actors, **kw)


shots = [
    S(0.0, 2.2, 'This is Sam.', 'ws', 'Sam',
      [A('Sam', [-4.2, -0.4], walkTo=SAM, anim='walk', face='smile', yaw=90),
       A('Zoe', [4.4, 0.2], walkTo=ZOE, anim='walk', face='smile', yaw=-90)], move='creep'),
    S(2.2, 4.4, 'Sam never gets angry.', 'ms', 'Sam',
      [A('Sam', SAM, anim='talk', face='smug', talk=[0, 99], yaw=20)], move='creep'),
    S(4.4, 6.2, 'Then Zoe stepped on his shoe.', 'two', 'Sam',
      [A('Sam', SAM, anim='idle', face='smile', yaw=50, faceAt=[[0.55, 'shock']], animAt=[[0.55, 'shock']]),
       A('Zoe', ZOE, anim='idle', face='grin', yaw=-35, animAt=[[0.3, 'point']])]),
    S(6.2, 8.1, 'Never... ever.', 'cu', 'Sam',
      [A('Sam', SAM, anim='angry', face='angry', yaw=20, fx=['storm@0.1'])], aimUp=True, move='creep'),
    S(8.1, 10.0, 'Okay. Maybe once.', 'ws', 'Sam',
      [A('Sam', SAM, anim='angry', face='angry', yaw=40, fx=['storm@-1', 'bolt@0.35']),
       A('Zoe', ZOE, anim='cheer', face='laugh', yaw=-30)], flash=True, impact=0.35),
]

json.dump(dict(dur=10.0, voice='am_michael', keys=['angry', 'never', 'once'], music=[[0, 'playful'], [0.6, 'suspense'], [0.82, 'playful']],
               cast=CAST, shots=shots),
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timed.json'), 'w', encoding='utf8'), indent=1)
print('timed.json:', len(shots), 'shots, 10.0 s')
