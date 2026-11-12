# Setup

The easy way: open Claude Code and paste

```text
Set up github.com/ezpeezee/beta-version-blox-studio on my PC, and run its test.
```

Claude Code follows the steps below. With the tools already installed it takes about three minutes.

## 1. Tools

| Tool | Check | Install (Windows) |
|---|---|---|
| Python 3.11+ | `python --version` | `winget install Python.Python.3.12` |
| ffmpeg | `ffmpeg -version` | `winget install Gyan.FFmpeg` |
| Blender 5.2 | `blender --version` or the path to `blender.exe` | `winget install BlenderFoundation.Blender` |
| Claude Code | `claude --version` | see claude.com/claude-code |

An NVIDIA GPU renders fastest; any GPU or a CPU also works, more slowly. About 4 GB of free RAM per render process.

## 2. Clone

```bash
git clone https://github.com/ezpeezee/beta-version-blox-studio
cd beta-version-blox-studio
```

## 3. Python packages

```bash
python -m venv .venv
.venv\Scripts\pip install -r kit\requirements.txt
```

Voice (Kokoro TTS, reads the script aloud; about 2 GB with PyTorch, works on CPU):

```bash
.venv\Scripts\pip install -r kit\requirements-voice.txt
```

Optional: install [eSpeak NG](https://github.com/espeak-ng/espeak-ng/releases) so unusual words and names are pronounced
better. Skip the voice packages and videos still render, with captions and music only.

Run the kit with `.venv\Scripts\python` (or activate the venv first).

## 4. Tell the kit where Blender is

If `blender` isn't on PATH, write `kit/config.json`:

```json
{"blender": "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"}
```

(or set the `BLENDER` environment variable).

## 5. Install the skill

Copy `skill/` to `%USERPROFILE%\.claude\skills\beta-version-blox-studio\`.

## 6. Run the test

```bash
.venv\Scripts\python kit\run.py kit\projects\test10 all
```

It builds the street, two characters and five shots, reads the lines aloud, renders about 300 frames and writes
`kit/projects/test10/out/test10.mp4` (10 s, 1080x1920, 30 fps). About 3-5 minutes with an NVIDIA GPU.

Then, in Claude Code inside the repo folder:

```text
/beta-version-blox-studio a short video about a kid who can't stop sneezing
```
