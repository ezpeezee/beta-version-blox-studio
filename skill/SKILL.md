---
name: beta-version-blox-studio
description: Make a short vertical (9:16, 30 fps) animated video with blocky Roblox-style 3D characters in Blender, from an idea or the user's own script, using the Beta Version Blox Studio kit. Use whenever the user asks for a blocky / Roblox-style animation, a "blox" short, or names Blox Studio, even if they only give a one-line idea.
---

# Beta Version Blox Studio

You turn an idea or a script into a finished 9:16 short: blocky characters acting in a code-built 3D street or kitchen,
word-timed captions, a music bed and sound effects. Blender does the 3D; `kit/run.py` runs every step.

## Find the kit
The kit lives in the cloned repo (`<repo>/kit`). If you can't find it, ask the user where they cloned
`beta-version-blox-studio`; if it isn't installed, follow `SETUP.md` in the repo first.

## Steps
1. **Script.** One-line idea: write a 15-40 second script, 4-10 short lines, one clear beat per line, a turn or punchline at the
   end. The user's own script: use it word for word. Show the script and continue (don't wait unless they asked to approve it).
2. **Voice.** By default the `voice` step reads each shot's `text` aloud with Kokoro TTS (free, local) and stretches any
   shot that is shorter than its line, so you can write shot times roughly. Pick the voice with `voice=` in `timed.json`
   (e.g. `am_michael`, `af_heart`, `bm_george`; a shot's own `voice` overrides it, so characters can sound different).
   Give talking characters `talk=[0, 99]` so the mouth moves for the whole line.
   If the user brings a recording instead, save it as `<project>/vo.wav` with `<project>/words.json`
   (`[[word, start_s, end_s], ...]`, e.g. from faster-whisper) and the voice step keeps it. If Kokoro is missing, `run.py`
   installs it into the same Python on the first voice step (about 2 GB). If that fails it prints NO VOICE: fix it with
   `<the kit's python> -m pip install -r kit/requirements-voice.txt` before rendering, never ship a short without a voice.
3. **Shots.** Copy `kit/projects/test10` to `kit/projects/<name>` and rewrite its `shots.py`: the cast, then one `S(...)` per
   caption line. Every key is in `kit/API.md`. Rules that keep it watchable:
   - Cut every 1-2.5 s. Vary the camera (`ews` to open, `mcu`/`cu` for lines, `two` for exchanges, `ws` for payoffs).
   - Each shot's `text` is the caption shown; with a voice, shots follow the word times.
   - Keep characters 2.5+ apart; `walkTo` for entrances; face the camera side (`yaw` -60..60) when they talk.
   - Act reactions with `faceAt`/`animAt`. Use `fx` (rain cloud, storm, bolt, smoke) only when the story itself has
     that moment (bad luck, a shock, a burn); never by default, and never in a story that doesn't mention it.
4. **Look first.** `python kit/run.py kit/projects/<name>` runs shots, voice, compile and stills. Open `stills_sheet.jpg` and check
   every shot: subject in frame, faces visible, nobody blocking, nothing inside a wall. `compile.log` prints `clash frames`;
   0 is the goal (characters overlapping). Fix `shots.py` and rerun until it is clean.
5. **Render and finish.** `python kit/run.py kit/projects/<name> render post` -> `kit/projects/<name>/out/<name>.mp4`.
   Watch the start, middle and end, then give the user the path and a one-line caption for posting.

## Speed
The render uses several Blender processes at once (picked from free RAM). About 1 s per frame per process on an NVIDIA GPU:
a 30 s short (900 frames) takes about 5-8 minutes on 3 processes. Tell the user the estimate before the full render.

## Don't
- Don't edit files in `kit/blox/` for one video; put story choices in `shots.py`.
- Don't remove or cover the Beta Version branding (prints, signs, watermark, end tag): it is part of the kit's look.
