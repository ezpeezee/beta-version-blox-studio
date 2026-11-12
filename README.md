<div align="center">

<img src="docs/banner.png" alt="Beta Version Blox Studio" width="100%">

# Beta Version Blox Studio

**Turn an idea, or your own script, into a vertical blocky-3D animated short with Claude Code.**

[![License: MIT](https://img.shields.io/badge/license-MIT-3ad6f0?style=for-the-badge)](LICENSE.md)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-d97757?style=for-the-badge)](skill/SKILL.md)
[![Blender 5.2](https://img.shields.io/badge/Blender-5.2-e87d0d?style=for-the-badge&logo=blender&logoColor=white)](https://www.blender.org/download/)
[![Instagram](https://img.shields.io/badge/Follow-@beta__versionhq-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/beta_versionhq/)
[![YouTube](https://img.shields.io/badge/Subscribe-@BetaVersion__HQ-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@BetaVersion_HQ)

### **📣 Like it? Follow [@beta_versionhq on Instagram](https://www.instagram.com/beta_versionhq/) and subscribe on [YouTube @BetaVersion_HQ](https://www.youtube.com/@BetaVersion_HQ) for new tools, updates and behind-the-scenes.**

</div>

---

## 🎬 See it in action

https://github.com/user-attachments/assets/b8a61620-e614-4b59-8725-f3aa0fce79f1

<div align="center"><sub>Every clip above was made with the Blender pipeline this kit comes from.</sub></div>

---

## ✨ What you get

<table>
<tr>
<td width="50%" valign="top">

### 📝 Script help
Give it one line and it writes a short script, or paste yours and it uses it word for word.

</td>
<td width="50%" valign="top">

### 🧱 Blocky 3D characters
Built entirely in code: walk, talk, point, cheer, panic, with 12 faces and lip-sync. No downloads, no rigs to buy.

</td>
</tr>
<tr>
<td valign="top">

### 🏙️ Ready-made sets
A city street and a kitchen, built from code with free CC0 textures, plus sunny, storm and night lighting.

</td>
<td valign="top">

### 🗣️ Voice and captions
Free Kokoro text-to-speech reads your script, or bring your own recording. Every caption and mouth movement lands on its word.

</td>
</tr>
<tr>
<td valign="top">

### 🎥 Camera and effects
16 camera framings, pushes and crash-ins, rain clouds over heads, lightning, smoke.

</td>
<td valign="top">

### 📱 Ready to post
A 9:16 video at 30 fps, with sound effects and a music bed made in code.

</td>
</tr>
</table>

---

## 🚀 Quick start

**The easy way:** install [Claude Code](https://claude.com/claude-code), then paste this into it:

```text
Set up github.com/ezpeezee/beta-version-blox-studio on my PC, and run its test.
```

It clones the repo, follows [SETUP.md](SETUP.md), checks your tools (and gives you the install command for anything missing),
makes the Python environment and renders the 10-second test clip.

**By hand:**

```text
1. Install Blender 5.2, Python 3.11+, ffmpeg and Claude Code
2. pip install -r kit/requirements.txt -r kit/requirements-voice.txt
3. Copy skill/ to ~/.claude/skills/beta-version-blox-studio/
4. python kit/run.py kit/projects/test10 all
5. Open Claude Code in the repo and type:

   /beta-version-blox-studio a short video about a kid who can't stop sneezing
```

## 🛠️ How it works

| Step | What happens |
|---|---|
| **1. Script** | It writes one from your idea, or uses yours. |
| **2. Voice** | Kokoro TTS reads each line (or your recording is used), and shots stretch to fit the voice. |
| **3. Shots** | Claude writes `shots.py`: the cast and one line per shot ([API](kit/API.md)). |
| **4. Look** | One still per shot comes first, and a check makes sure no two characters overlap. |
| **5. Render** | Blender renders frames on several processes at once. |
| **6. Finish** | Captions, music and sound effects are added, and the mp4 is written. |

```text
python kit/run.py kit/projects/<name>               # shots, compile, stills
python kit/run.py kit/projects/<name> render post   # full render and the mp4
```

## 💻 Requirements

| | |
|---|---|
| **OS** | Windows 10/11 (Linux and macOS work with the Blender path set) |
| **Software** | Blender 5.2, Python 3.11+, ffmpeg, Claude Code |
| **Hardware** | An NVIDIA GPU is best; a CPU also works, more slowly. About 4 GB RAM per render process |

---

<div align="center">

Made by **Beta Version** · [Instagram](https://www.instagram.com/beta_versionhq/) · [YouTube](https://www.youtube.com/@BetaVersion_HQ)

Stuck, or something broke? DM me on Instagram.

<sub>Not affiliated with Roblox Corporation. The characters are original, code-built blocky figures.</sub>

</div>
