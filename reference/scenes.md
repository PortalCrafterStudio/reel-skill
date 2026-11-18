# Scene types

Every scene is `{"type": ..., "lines": [...], "props": {...}}` with optional `"theme": "light" | "dark"`,
`"head": false` (hide the headline) and `"hold": 1.2` (extra seconds at the end of the scene).

A **cue** is a word from the scene's own lines, written in lower case without punctuation
(`"fold"`, `"18"`, `"don't"`). `"three#2"` is the second time *three* is said in that scene.
A number instead of a word means "this many seconds after the scene starts".

Icons for chips: `file receipt bell mail check x key palette db user lock clock send warn play film type`.

Paths (`img`, `cover`, `video`, `imgs`, `covers`) are relative to the spec file. `video` takes an
MP4/MOV; the engine samples it at 15 fps and plays it inside the card.

---

## text
Headline only, centred in the middle of the frame. Each new line appears under the last and the
earlier ones dim. Best for the hook and for a one-line turn ("So don't post one. / Post ten.").
```json
{"type": "text", "lines": ["You're not *lazy.*", "Your program / is *random.*"]}
```

## flow
Numbered steps down a line; each lights up on its cue. 3 or 4 items read best (5 max).
```json
{"type": "flow", "lines": ["Day one, 7pm: / we *feed the starter.*", "Next morning: / *fold four times.*", "Then *18 hours* / cold.", "Day three: / *into the oven.*"],
 "props": {"title": "One loaf, start to finish", "items": [
   {"n": "7pm", "b": "Feed the starter", "sub": "Day one", "cue": "feed"},
   {"n": "9am", "b": "Mix and fold", "sub": "Four folds by 1pm", "cue": "fold"},
   {"n": "18h", "b": "Cold proof", "sub": "Overnight in the fridge", "cue": "18"},
   {"n": "7am", "b": "Bake", "sub": "Day three", "cue": "oven"}]}}
```
`n` is the circle label (keep it to 3 characters).

## compare
Two columns: left gets red X rows, right gets check rows. 2 or 3 rows.
```json
{"type": "compare", "lines": ["Random workouts? / *Same weights* / for months.", "A real program: / *small jumps* / every week."],
 "props": {"left": "Random workouts", "right": "A real program",
           "rows": [{"l": "Same weights for months", "r": "Small jumps every week", "lc": "same", "rc": "small"}]}}
```

## tiers
Up to three price cards sliding in; the current one is outlined.
```json
{"type": "tiers", "lines": ["Starter: / *$49* a month.", "Pro: / *$99,* / with coaching calls."],
 "props": {"tiers": [{"name": "Starter", "price": "$49", "meta": "App + weekly plan", "cue": "starter"},
                     {"name": "Pro", "price": "$99", "meta": "Plus two calls a month", "cue": "pro"}]}}
```
`"price": "from $900"` shows a small "from".

## quote
A document with rows ticking off, then a stamp.
```json
{"type": "quote", "lines": ["Your price is *fixed* / before we start."],
 "props": {"title": "Quote · kitchen refit", "sub": "sent in 24 h",
           "rows": [{"l": "Price", "r": "Fixed", "cue": "price"}, {"l": "Start date", "r": "Booked", "cue": "fixed"}],
           "stamp": {"text": "FIXED", "cue": "start"}}}
```

## bars
A bar chart. `h` is the bar height from 0 to 1. Optional `dimBars` (cue to grey them out) and
`line` (a flat line with a label).
```json
{"type": "bars", "lines": ["Cheap at *10 clients.*", "At *200,* / it's your biggest bill."],
 "props": {"title": "Monthly cost", "xlabel": "clients",
           "bars": [{"label": "10", "h": 0.12, "cue": "10"}, {"label": "50", "h": 0.3}, {"label": "100", "h": 0.55}, {"label": "200", "h": 0.92, "cue": "biggest"}],
           "line": {"label": "Flat fee", "h": 0.2, "cue": "200"}}}
```

## note
A messy spreadsheet on top and up to three numbered "signs" flying in below.
```json
{"type": "note", "lines": ["Three signs / you've *outgrown* / your spreadsheet.", "One: / it's called *v3 FINAL.*", "Two: / everyone sees *every row.*", "Three: / only one person / *gets the formulas.*"],
 "props": {"title": "tracker_v3_FINAL (2).xlsx",
           "items": [{"text": "It's called v3 FINAL", "cue": "one"}, {"text": "Everyone sees every row", "cue": "two"}, {"text": "One person knows the formulas", "cue": "three#2"}],
           "sheet": [["Client", "Status", "Owner", "Total"], ["Harbor", "??", "me", "#REF!"]]}}
```

## progress
A big percentage counting up, then a red "stalled" badge and error rows.
```json
{"type": "progress", "lines": ["You built *60%* / with an AI builder. / Then it *stalled.*"],
 "props": {"label": "client-portal-v1", "value": 60, "fill": "built", "stall": "stalled", "errors": ["Permission denied", "Webhook failed"]}}
```

## mail
Inbox rows dropping in (up to 5), finishing on `dropEnd`.
```json
{"type": "mail", "lines": ["Every *any update?* email / is a question / you could answer once."],
 "props": {"rows": [["Dana W.", "Any update on this?", "9:12"], ["Marcus Lee", "Re: any update?", "8:47"]], "dropEnd": "question"}}
```

## tracker
A chat bubble, then a 4-step status tracker filling in.
```json
{"type": "tracker", "lines": ["Your clients aren't impatient. / They just *can't see* / where things stand."],
 "props": {"bubble": {"text": "Hey, any update?", "cue": "your"}, "title": "Order #2041", "sub": "Shared with your client",
           "steps": ["Ordered", "Made", "Shipped", "Delivered"], "done": ["see", "where"], "current": "stand",
           "msg": "Arrives Friday", "trackCue": "can't"}}
```

## portal
A browser card with a screenshot; `swaps` change the screenshot on cues with a label chip;
`chips` fly in under the card; `badge` is an inbox count that drops to a check.
```json
{"type": "portal", "lines": ["Each client gets / *their own dashboard.*"],
 "props": {"img": "shots/dashboard.jpg", "tag": "Sample data",
           "swaps": [{"img": "shots/files.jpg", "label": "Files", "cue": "own"}],
           "chips": [{"label": "Status", "icon": "check", "cue": "client"}]}}
```

## assemble
Grey skeleton blocks snap into a layout, then the real screenshot fades in on `ready`.
```json
{"type": "assemble", "lines": ["Then we put / *a portal* on top."],
 "props": {"img": "shots/app.jpg", "ready": "portal", "chips": [{"label": "Your data", "icon": "db", "cue": "then"}, {"label": "Portal", "icon": "user", "cue": "top"}]}}
```

## base
A database table card with an owner badge and rows that glow.
```json
{"type": "base", "lines": ["Your data / *in a base you own.*"],
 "props": {"title": "Your Airtable base", "ownerLabel": "Owner: you", "owner": "own", "glow": "data",
           "tabs": ["Clients", "Projects"], "cols": ["Client", "Stage", "Next step"],
           "rows": [["Harbor Dance", "a", "Active", "Review designs"], ["Northvale", "b", "Onboarding", "Sign"]]}}
```
Row pill colours: `a` accent, `b` amber, `c` indigo.

## split
One shared sheet with a warning, then a private card for each of two people.
```json
{"type": "split", "lines": ["In a shared sheet / it's *all or nothing.*", "In a portal / each sees *only theirs.*"],
 "props": {"clients": ["Harbor Dance", "Northvale"], "all": "all", "split": "portal"}}
```
Optional: `file`, `cols`, `rows`, `warn`, `minis` (two lists of `[label, value]`).

## phone
A finished reel or video playing in a phone. Optional prompt card above and label below.
```json
{"type": "phone", "lines": ["You type / *one sentence.*", "It hands you / *the reel.* [+1.4]"],
 "props": {"video": "out/bakery.mp4", "cue": "hands", "w": 390, "y": 790,
           "prompt": "/reel for a bakery: why our sourdough takes 36 hours", "promptY": 590}}
```
Use `cover` (an image) instead of `video` for a still. `from` skips seconds into the video.
With a prompt, keep `w` around 390 so the phone ends above y=1480.

## term
A Claude Code terminal: a command types itself, work lines tick, then the result (a playing
reel plus the files it made). **One line per step**; the line stays up while its step runs and
the engine stretches it to fit.
```json
{"type": "term", "theme": "dark", "lines": ["One skill. / Three *sentences.*", "A *coach.*"],
 "props": {"title": "~/reels · claude", "steps": [
   {"cmd": "/reel for a strength coach: you're not lazy, your program is random",
    "work": [["Writing the script", "6 lines"], ["Rendering 595 frames", "14 s"]],
    "result": {"video": "out/coach.mp4", "file": "coach.mp4", "dur": "0:19", "meta": "1080×1920 · 30 fps · sound",
               "outs": ["coach-cover.jpg", "caption + DM reply"], "stat": "0:19 reel", "statSub": "rendered in 14 s"}},
   {"cmd": "...", "work": [], "result": {}}]}}
```
`show` (seconds the result stays, default 2.8). A result with no `video` or `cover` shows only the
file list. `height` / `top` resize the terminal. Only show numbers you measured.

## code
A code card typing line by line, then a phone with the frame it draws.
```json
{"type": "code", "lines": ["Every frame / is *drawn by code.* [+1.8]"],
 "props": {"file": "reel.json", "frameCue": "code", "video": "out/bakery.mp4",
           "lines": ["{", "  \"type\": \"flow\",", "  \"title\": \"One loaf\"", "}"]}}
```
Keep code lines under 34 characters. Without `img`/`video` the card is full width.

## grid
Covers popping into a grid one by one.
```json
{"type": "grid", "lines": ["Ten hooks. / *One sentence* each. [+1.6]"],
 "props": {"imgs": ["out/a-cover.jpg", "out/b-cover.jpg"], "cols": 5, "numbers": true, "cue": "ten", "stagger": 0.1}}
```

## logo
The brand mark on a pedestal with up to two chips and a plus sign.
```json
{"type": "logo", "lines": ["Built on *Softr* / and Airtable."],
 "props": {"logoCue": "built", "chips": [{"label": "Softr", "icon": "palette", "cue": "softr"}, {"label": "Airtable", "icon": "db", "cue": "airtable"}], "plus": "and"}}
```

## cta
The default ending: a comment box where the keyword is typed and posted, then a DM reply bubble.
The line must contain the keyword (and the word "DM" if `dm` is set, or set `dmCue`).
```json
{"type": "cta", "lines": ["Comment *BREAD* / and I'll DM you / *tomorrow's bake list.* [+1.6]"],
 "props": {"keyword": "BREAD", "dm": "Here's tomorrow's bake list", "url": "kettleandcrumb.com/menu",
           "comments": [["AL", "#ec4899", "ana.loves.food", "Do you deliver?"], ["TW", "#14b8a6", "tom.wu", "Worth the wait"]]}}
```
Comment rows are made-up placeholders: keep them neutral (questions, "need this"), never fake praise.

## endcard
A poster ending: "Comment", the keyword huge, a line under it, up to three fanned covers and
three small lines. Set `"head": false` so the headline does not compete.
```json
{"type": "endcard", "theme": "dark", "head": false, "lines": ["Comment GUIDE and I'll DM you the guide. [+2.2]"],
 "props": {"keyword": "GUIDE", "cue": "guide", "after": "and I'll DM you the guide",
           "covers": [{"img": "out/a-cover.jpg", "label": "Part 1"}],
           "l1": "Free, no email needed.", "l2": "Follow first so the DM can reach you.", "l3": ""}}
```
