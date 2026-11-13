# Shot list API (`shots.py` -> `timed.json`)

`shots.py` writes `timed.json` next to it. Copy `projects/test10` to start a new short. All times are seconds.

## Top level
| Key | Meaning |
|---|---|
| `dur` | length of the video (s) |
| `cast` | `{name: look}` (below) |
| `shots` | list of shots, back to back (`t0` of one = `t1` of the one before) |
| `music` | `[[fraction_of_video, mood], ...]`: `playful`, `suspense`, `dark`, ... the coded music bed changes there |
| `keys` | words that get a stronger caption pop |
| `places` | `{name: spec}`: your own places, built from the story (see **Places**) |
| `things` | `{name: parts}`: objects the story needs that the catalogue lacks (see **Things**) |

## Cast look
`skin`, `shirt`, `pants`, `shoes`, `hair_color`, `cap_color`, `tie_color`, `apron_color`: RGB 0-1.
`hair`: short, curly, spiky, cap, long, pigtails, bald, bun, grey_old. `height`: 1.0 adult, about 0.8 kid.
`extras`: glasses, collar, tie, pocket, apron, cardigan. `sleeves`: short or long.

## Shot
| Key | Meaning |
|---|---|
| `t0`, `t1` | start and end in the video |
| `text` | caption line for this shot (words in brackets are not captioned) |
| `set` | the place the shot happens in: a ready place, a preset, or your own place from `places` (see **Places**) |
| `cam` | `ews` `ws` `mls` `ms` `two` `mcu` `cu` `ecu` `ots` `low` `worm` `ground` `high` `top` `pov` `ins` |
| `subject` | who the camera frames |
| `mood` | `sunny`, `storm`, `night` (light, sky, fog) |
| `move` | `creep` (slow push), `push`, `reveal_push`, `crash_in`, `drift`, `lock` |
| `side` | 1 or -1: which side of the subject the camera stands |
| `aimUp` | true: frame higher (clouds above heads) |
| `flash`, `impact` | lightning flash and camera kick at `impact` s into the shot |
| `focus` | an anchor or prop name; with `cam='ins'` the shot is on that object (a story thing is framed whole) |

## Actor (inside `actors`)
| Key | Meaning |
|---|---|
| `who` | a cast name |
| `at` | `[x, y]` on the set floor; the camera side is -y. Keep people 2.5+ apart |
| `walkTo` | `[x, y]`: walks there during the shot (feet locked to the floor, no sliding) |
| `yaw` | facing in degrees: 0 faces the camera side (-y), 90 faces +x, -90 faces -x |
| `anim` | idle, talk, walk, run, point, shrug, shock, scared, cheer, eat, cross_arms, think, sad, angry, wave, sit, facepalm |
| `animAt` | `[[t, anim], ...]` switch the animation at shot time t |
| `face` | neutral, smile, grin, laugh, shock, scared, sad, worried, angry, smug, think, blink |
| `faceAt` | `[[t, face], ...]` |
| `talk` | `[t_start, t_end]` mouth moves (follows the words in `words.json`) |
| `look` | `[x, y]` eye direction, -1..1 |
| `fx` | `['name@t', ...]`: `drizzle`, `raincloud`, `storm`, `bigstorm` (a cloud above the head that rains), `bolt`, `smoke`, `crumbs`. `@-1` = already there when the shot starts |

## Places (the world comes from the story)
Every location in the script gets its own place. A shot's `set` names one of:
- **Ready places** (full sets): `Street`, `Kitchen`, `Gym` (basketball court, bleachers, hoops), `MusicRow`
  (music shop on a street, houses across the road), `TownPool` (pool, diving board, lifeguard chair, pool house).
- **Presets** (built from the spec below, good starting points): `Bedroom`, `Hallway`, `Classroom`, `LivingRoom`,
  `Store`, `Office`, `Bathroom`, `Park`, `Backyard`, `Playground`.
- **Your own place**: any name defined under top-level `places` in `timed.json`. Only the places the shots use are built.

A spec is a small dict:
```python
PLACES = {
  'DoorHall': dict(wall='#6a4a7a', lower='#2f2a3a', floor='carpet', floor_color='#8a2f3a', light='warm', props=[
      ['door', -9, 7.7, 0, {'open': True, 'beyond': '#ffcf8a'}],
      ['door',  3, 7.7, 0, {'open': True, 'beyond': '#9cc8f0', 'name': 'blue_door'}],
      ['bed', 11, -8, -90, {'color': '#c84a6a'}]]),
  'Beach': dict(kind='outdoor', ground='sand', backdrop='none', props=[['umbrella', 9, 4, 0], ['rock', -10, 6, 0]]),
}
json.dump(dict(..., places=PLACES, shots=...), ...)
```
| Key | Meaning |
|---|---|
| `kind` | `room` (default) or `outdoor` |
| `wall`, `lower` | room: wall colour and the lower wall band (hex) |
| `floor`, `floor_color` | room: `wood`, `tiles`, `carpet`, `concrete`, `checker` (+ colour for carpet/checker) |
| `windows` | room: x positions of back-wall windows, e.g. `[-6, 6]`; `side_window: true` adds one on the left wall |
| `light` | room: `warm` (lamps) or `panel` (ceiling panels, school/office/store) |
| `ground` | outdoor: `grass`, `pavers`, `asphalt`, `sand`, `dirt` |
| `backdrop` | outdoor: what stands far behind: `houses`, `trees`, `city`, `fence`, `none` |
| `props` | `[type, x, y, yaw]` or `[type, x, y, yaw, {options}]` |
| `base` | build a ready place or preset and add this spec's `props` to it: `dict(base='Street', props=[['rocket', 11, 6, 0]])` |

Floor plan: camera on the -y side, back wall at y 8, side walls at x -14 / 14. Actors stand in the clear zone
`|x| < 7, -4 < y < 3`, so put furniture along the back wall (y 4..7.5) and the side walls (|x| 9..13). Compile prints a
`[places]` line for anything in the clear zone; add `{'in_clear': True}` if the actors use it (a table they stand at).
Yaw 0 = the prop faces the camera side, 90 faces +x, -90 faces -x.

Props and options (`name` on any prop sets its anchor, else the type, `type2`, ...):
`bed` (color, bunk), `bunk_bed`, `nightstand` (lamp), `desk` (computer, color), `office_chair`, `chair`, `wardrobe` (color),
`bookshelf` (w, h), `shelves`, `sofa` (color, w), `armchair` (color), `coffee_table`, `table` (w, d, color), `tv` (w),
`floor_lamp`, `lamp`, `rug` (color, w, d), `poster` (color or brand `P1`/`P2`/`P3`/`AD`, w, z), `picture` (color, w, z),
`clock` (z), `mirror` (w, z), `door` (color, open, beyond = glow colour seen through an open door, sign),
`school_desk`, `whiteboard` / `chalkboard` (w, board, z), `lockers` (n, color), `counter` (w, register, color),
`store_shelf` (w, h), `cooler` (w), `fridge`, `stove`, `sink_unit`, `toilet`, `bathtub`, `plant` (h), `tree` (s),
`bush` (s), `rock` (s), `fence` (w, color), `swing`, `slide`, `house` (color, roof, w), `bench`, `car`, `lamp_post`,
`trash_can`, `wheelie_bin`, `hydrant`, `box`, `crate`, `bleachers` (w, rows), `hoop`, `umbrella` (color).

Anchors for a shot's `focus`: every prop's name; `Gym`: bleachers, hoop, court; `MusicRow`: shop, door, window;
`TownPool`: pool, ladder, board, lifeguard.

## Things (anything the story names)
If the script names an object the catalogue doesn't have (a rocket, a dog, a giant tissue box, a vending machine), build
it under top-level `things` from chunky parts and use its name like any prop. Keep it Roblox-blocky: 3-12 parts,
bright flat colours, no fine detail; a dog is a box body, a box head and four tubes, not a sculpted dog.
```python
THINGS = {
  'rocket': [['tube', '#e8e8e8', 1.2, 7.0, [0, 0, 4.0]], ['cone', '#d0392b', 1.2, 2.4, [0, 0, 8.7]],
             ['block', '#d0392b', [0.3, 2.2, 2.0], [1.3, 0, 1.4]], ['block', '#d0392b', [0.3, 2.2, 2.0], [-1.3, 0, 1.4]],
             ['cone', '#ffb02e', 0.9, 1.2, [0, 0, 0.1], {'flip': True, 'glow': 4}]],
  'dog': [['block', '#c8873c', [1.2, 2.4, 1.1], [0, 0, 1.6]], ['block', '#c8873c', [1.0, 1.0, 1.0], [0, -1.4, 2.4]],
          ['tube', '#c8873c', 0.22, 1.0, [0.4, -0.9, 0.5]], ['tube', '#c8873c', 0.22, 1.0, [-0.4, -0.9, 0.5]],
          ['tube', '#c8873c', 0.22, 1.0, [0.4, 0.9, 0.5]], ['tube', '#c8873c', 0.22, 1.0, [-0.4, 0.9, 0.5]]],
}
PLACES = {'LaunchStreet': dict(base='Street', props=[['rocket', 11, 6, 0], ['dog', -5, 1, 30, {'in_clear': True}]])}
json.dump(dict(..., things=THINGS, places=PLACES, shots=...), ...)
```
Parts (x, y, z = the part's centre in studs; the floor is z 0, the front faces -y; a person is about 5 tall):
| Part | Form |
|---|---|
| `block` | `['block', colour, [w, d, h], [x, y, z]]` |
| `tube` | `['tube', colour, r, h, [x, y, z]]` upright; `{'axis': 'X'}` or `'Y'` lays it down |
| `cone` | `['cone', colour, r, h, [x, y, z]]` point up; `{'r2': r}` cut cone; `{'flip': True}` point down |
| `ball` | `['ball', colour, r, [x, y, z]]`; `{'scale': [1, 1, 0.6]}` squashes it |

Part options: `glow` 0-5 (lights up), `metal`, `tilt` `[rx, ry, rz]` degrees, `main` (the prop option `color` recolours
it). Prop options for a thing: `s` (scale), `color`, `name`, `in_clear`. Things don't move: a creature that has to act
is a cast member with a costume, not a thing.

## Voice
The `voice` step (Kokoro TTS) speaks each shot's `text` and writes `vo.wav` + `words.json`. A shot shorter than its line
is stretched and later shots move along, so shot times can be rough.

| Key | Where | Meaning |
|---|---|---|
| `voice` | top level | Kokoro voice, default `af_heart`. American: af_heart af_bella af_nicole am_michael am_fenrir am_puck. British: bf_emma bf_isabella bm_george bm_fable |
| `voice` | shot | a different voice for this line (one per character, for dialogue) |
| `voice_speed` | top level | 1.0 normal, 1.1 a bit faster |

Use `talk=[0, 99]` on the speaking actor so the mouth moves for the whole line.
Your own recording: put `vo.wav` and `words.json` (`[[word, start, end], ...]`) in the project; the voice step keeps them.
Without Kokoro installed, the video has captions, music and sound effects only.
