# /reel: a free Claude Code skill that turns one sentence into a finished reel

Type one line in Claude Code:

```
/reel for a bakery: why our sourdough takes 36 hours
```

and get back a 1080x1920 MP4 with sound effects, a cover image, the caption, a pinned comment and
the DM reply for your comment keyword. Every frame is drawn in code (HTML rendered by headless
Chromium): no camera, no editing app, no AI video model. It runs on your own computer.

Made by [Portalcrafter](https://portalcrafter.com). Free and open source (MIT).

## What you get per reel

| file | what it is |
|---|---|
| `reels/out/<name>.mp4` | the reel: 1080x1920, 30 fps, H.264 + AAC, 15 to 30 s |
| `reels/out/<name>-cover.jpg` | the hook as a cover image |
| `reels/out/<name>.md` | caption, pinned comment, DM reply, and the timed lines (a voiceover script) |
| `reels/out/<name>-sheet.jpg` | one frame per second, to check the whole reel at a glance |
| `reels/<name>.json` | the spec Claude wrote; edit a line and render again |

Your brand (name, handle, accent colour, logo) lives in `reels/brand.json`, so every reel comes
out on brand. Claude asks for it the first time.

## Install

You need [Claude Code](https://claude.com/claude-code), Node.js 18+, Python 3.9+ and ffmpeg.

**Easiest:** paste this into Claude Code and let it do the rest:

```
Install the reel skill from https://github.com/PortalCrafterStudio/reel-skill into ~/.claude/skills/reel and run its setup script
```

**Or in a terminal:**

```bash
git clone https://github.com/PortalCrafterStudio/reel-skill.git ~/.claude/skills/reel
bash ~/.claude/skills/reel/scripts/setup.sh
```

Setup installs Playwright and downloads Chromium once (about 150 MB). Then start a new Claude
Code session and type `/reel` followed by your idea.

Missing node or ffmpeg? macOS: `brew install node ffmpeg` · Windows: `winget install OpenJS.NodeJS Gyan.FFmpeg`
· Debian/Ubuntu: `sudo apt install nodejs npm ffmpeg`.

## Try it

```
/reel 3 signs your website is costing you clients, end on comment AUDIT
/reel for a strength coach: you're not lazy, your program is random
/reel 10 trial reels for my newsletter, each with a different hook, keyword READ
```

Or render the bundled examples straight away:

```bash
cd ~/.claude/skills/reel
python3 engine/reel.py build examples/bakery.json examples/coach.json
```

## How it works

1. Claude plans the reel: one idea, a hook of seven words or fewer, 3 to 5 scenes, one keyword ask.
2. It writes a small JSON spec using ready-made animated scenes (steps, comparisons, price cards,
   charts, a terminal demo, a phone playing a video, a comment box, an end card and more; see
   [reference/scenes.md](reference/scenes.md)).
3. `engine/reel.py` times every headline word, `engine/engine.html` draws each frame,
   `engine/render.mjs` captures them in headless Chromium, sound effects are synthesised to
   match, and ffmpeg encodes the MP4.
4. Claude previews stills, checks the contact sheet, fixes anything that overlaps, and hands you
   the files.

A 20-second reel renders in 15 to 60 seconds on a laptop.

## Narration (optional)

By default reels have sound effects only (typing, pops, whooshes), so you can add music in the
app. For a voice, install [Kokoro](https://github.com/hexgrad/kokoro), a small open-source
text-to-speech model that runs locally:

```bash
uv venv ~/.venvs/kokoro --python 3.12 && uv pip install --python ~/.venvs/kokoro/bin/python kokoro soundfile
```

then add `"voice": "af_heart"` (US female) or `"voice": "am_michael"` (US male) to a spec. Headline
words are then timed to the voice. Set `REEL_KOKORO_PYTHON` if your venv lives elsewhere. If you
post a reel with an AI voice, turn on Instagram's AI label.

## Commands

```bash
python3 engine/reel.py check                         # tools ready?
python3 engine/reel.py preview reels/x.json 1 5 9    # stills at those seconds
python3 engine/reel.py build reels/x.json reels/y.json
python3 engine/reel.py cover reels/x.json
```

## The playbook

[reference/playbook.md](reference/playbook.md) has the rules the skill follows: hooks, pacing,
the comment-to-DM loop, testing hooks with Instagram trial reels, safe zones and a checklist.

## License

MIT. Use it for your own brand or your clients'. Credit appreciated, not required.
