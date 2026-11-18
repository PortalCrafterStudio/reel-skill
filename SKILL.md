---
name: reel
description: Turn one sentence into a finished vertical reel (1080x1920 MP4 with sound effects, cover image, caption, pinned comment and DM reply) for Instagram Reels, TikTok or YouTube Shorts. Every frame is drawn in code (HTML rendered by headless Chromium), so there is no camera, no editing app and no AI video model. Use when the user types /reel, asks for a reel, short, TikTok, trial reels, a batch of reels, faceless video, or an animated explainer for their brand, product or offer.
---

# /reel: one sentence in, one finished reel out

The user gives an idea in a sentence ("/reel for a bakery: why our sourdough takes 36 hours").
You write a reel spec (JSON), the engine in this skill renders it, and you hand back the files.

The skill's folder is the base directory shown when this skill loads. Below, `ENGINE` means
`<that folder>/engine` and `REF` means `<that folder>/reference`.

## 1. First run only: check the tools

```bash
python3 "ENGINE/reel.py" check
```

If Playwright or Chromium is missing, run `bash "<skill folder>/scripts/setup.sh"` (installs the
Node packages into ENGINE and downloads Chromium, about 150 MB, once). It needs Node.js 18+,
Python 3.9+ and ffmpeg; if node or ffmpeg is missing, tell the user the one command for their OS
(macOS `brew install node ffmpeg`, Windows `winget install OpenJS.NodeJS Gyan.FFmpeg`,
Debian/Ubuntu `sudo apt install nodejs npm ffmpeg`) and stop until it is installed.

## 2. Brand (once per project)

Reels live in `reels/` in the user's current project. Look for `reels/brand.json`. If it is not
there, ask the user in one message for: brand name, Instagram handle, accent colour (hex, or
pick one from their logo or site), and optionally a logo file. Then write it:

```json
{ "name": "Kettle & Crumb", "handle": "@kettleandcrumb", "accent": "#d97706",
  "logo": "logo.png", "logoDark": "logo-white.png", "mark": "icon.png" }
```

`logo` shows on light scenes, `logoDark` on dark scenes, `mark` is a square icon (round crop).
All are optional; without them the engine draws a coloured initial and the name in text.
Paths are relative to brand.json.

## 3. Plan the reel before writing anything

Read `REF/playbook.md` once per session. Then decide, from the user's sentence:

- **One idea.** A reel makes one point. If the sentence holds three, make three reels.
- **The hook:** the first line, seven words or fewer, readable in the first second. It should be
  a claim, a question or a number the viewer cares about, never the brand name.
- **3 to 5 scenes, 15 to 30 seconds.** Something new appears every two or three seconds.
- **Proof the viewer can see.** Each line names what is on screen right then.
- **One ask at the end:** a single comment keyword in capitals (PLAN, BREAD, GUIDE) and what they
  get by DM. Use the user's keyword if they gave one.

**Facts:** use only what the user told you or what is in their files or site. Never invent
prices, results, client names, review scores or statistics. If the reel needs a fact you do not
have, ask once, or rewrite the line so it does not need it. Screenshots with fake data get a
`"tag": "Sample data"` label.

## 4. Write the spec: `reels/<slug>.json`

```json
{
  "title": "Why our sourdough takes 36 hours",
  "caption": "Why our sourdough takes 36 hours: ... Comment BREAD and I'll DM you tomorrow's bake list.",
  "pinned": "Comment BREAD and I'll send tomorrow's list.",
  "cta": {"keyword": "BREAD", "dm": "Here's tomorrow's bake list", "url": "kettleandcrumb.com/menu"},
  "start": "dark",
  "scenes": [
    {"type": "text", "lines": ["Why our sourdough / takes *36 hours.*"]},
    {"type": "flow", "lines": ["Day one, 7pm: / we *feed the starter.*", "..."], "props": {"title": "One loaf", "items": [...]}},
    {"type": "cta", "lines": ["Comment *BREAD* / and I'll DM you / *tomorrow's bake list.* [+1.6]"], "props": {"keyword": "BREAD", "dm": "Here's tomorrow's bake list"}}
  ]
}
```

How lines work (every scene needs at least one; they set its timing):

- Each line is shown as a big headline, a few words at a time, at about 2.6 words a second.
- `/` starts a new headline page. Keep pages to five words or fewer.
- `*word*` is the accent colour; a single starred word is also underlined.
- `[+1.5]` at the end of a line holds it 1.5 s longer (use it when a scene needs time to play).
- Props point at moments with **cue words**: `"cue": "fold"` means "when the word *fold* is said".
  `"18"` works for numbers; `"three#2"` is the second time *three* is said.

Scene types (full props and examples in `REF/scenes.md`):

| type | what it shows | good for |
|---|---|---|
| `text` | headline lines only, centred, earlier lines dim | the hook, a turn, a punchline |
| `flow` | numbered steps lighting up down a line | process, timeline, recipe, "how it works" |
| `compare` | two columns, X vs check, row by row | before/after, us vs them, myth vs fact |
| `tiers` | stacked price cards | pricing, packages, menu |
| `quote` | a document with rows ticking and a stamp | a promise, guarantee, quote, checklist |
| `bars` | a bar chart with an optional line | growth, cost over time |
| `note` | a messy spreadsheet plus numbered signs | "3 signs you...", problems |
| `progress` | a big percentage that stalls, errors below | "stuck at 60%" stories |
| `mail` | inbox rows dropping in | "every email you get about..." |
| `tracker` | a chat bubble then a status tracker | updates, order status |
| `portal` / `assemble` | a browser card with screenshots | product or app tours (needs images) |
| `base` / `split` | a database table / private views per person | data, permissions |
| `phone` | a finished reel or video playing in a phone | showing an output, a product video |
| `term` | a Claude Code session typing a command and showing the result | demos of a command or tool |
| `code` | a code card typing, then the frame it draws | "made with code" angles |
| `grid` | covers popping into a grid | batches, portfolios |
| `logo` | the brand mark on a pedestal with chips | "built on X and Y" |
| `cta` | a comment box: keyword typed, posted, DM reply | the ending (default) |
| `endcard` | big "Comment KEYWORD", fanned covers | the ending, poster style (`"head": false`) |

Scenes alternate light and dark automatically; set `"theme"` on a scene to override, or
`"start": "dark"` on the spec. Images and videos are paths relative to the spec file.

## 5. Preview, look, fix

```bash
python3 "ENGINE/reel.py" preview reels/<slug>.json 1 4 9 14
```

Open the PNGs it prints (Read them) and check: the headline never collides with a card, text fits,
nothing important sits below y=1480 or within 120 px of the sides (Instagram's buttons and caption
cover those), every cue fires at the right word. Fix the spec and preview again. A failing cue
stops the render with the scene and the words it has, so fix the cue word.

## 6. Render and hand over

```bash
python3 "ENGINE/reel.py" build reels/<slug>.json      # several specs at once is fine
```

Takes 15 to 60 seconds per reel. It writes to `reels/out/`:

- `<slug>.mp4`: 1080x1920, 30 fps, H.264 + AAC, sound effects synced to the animation
- `<slug>-cover.jpg`: the hook as a cover image
- `<slug>.md`: caption, pinned comment, DM reply and the timed lines (also a voiceover script)
- `<slug>-sheet.jpg`: one frame per second; Read it to check the whole reel at a glance

Read the contact sheet before you report. Then tell the user the file paths, the length, and the
caption, and say what to do on Instagram (post, pin the comment, reply by DM to the keyword).

Sound: the default track is sound effects only (typing, pops, whooshes), which works with or
without music added in the app. Narration is optional: `"voice": "af_heart"` (US female) or
`"am_michael"` (US male) uses Kokoro, a local open-source voice model, if the user has it set up
(see README). Never clone a real person's voice.

## 7. Batches and trial reels

When the user wants several reels ("10 trial reels", "a week of reels"), write one spec per reel,
each with a different hook and a different first scene type, the same keyword, and build them in
one command. Suggest posting them as Instagram trial reels (shown to non-followers first) and
comparing them after 48 hours: see the testing section of `REF/playbook.md`.

## Rules

- Never invent facts, numbers or testimonials. Label sample data.
- Keep every line short enough to read: 7 words max per page, one idea per line.
- Don't use another brand's logo, characters or music.
- The keyword ask appears once, at the end, plainly; no "comment to unlock" or "share or else".
