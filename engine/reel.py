#!/usr/bin/env python3
"""Turn a reel spec (JSON) into a finished vertical reel: MP4 with sound, cover, caption file.

    python3 reel.py check                       # are node, ffmpeg and Chromium ready?
    python3 reel.py build reels/my-reel.json    # render (several specs allowed)
    python3 reel.py preview reels/my-reel.json 1.2 6 9.5   # stills at those seconds
    python3 reel.py cover reels/my-reel.json    # only the cover

Only the Python standard library is used. Frames are drawn by engine.html in headless
Chromium (render.mjs), sound effects are synthesised here, ffmpeg encodes the result.
Narration is optional: "voice": "af_heart" in the spec uses Kokoro (see README).
"""
import array, hashlib, json, math, os, random, re, shutil, subprocess, sys, time, wave
from pathlib import Path
from urllib.parse import quote

ENGINE = Path(__file__).resolve().parent
FPS, WPS, PAD = 30, 2.6, 0.15
SR = 48000
CPS = 34            # typing speed in term scenes, characters per second
KOKORO = Path(os.environ.get("REEL_KOKORO_PYTHON", Path.home() / ".venvs" / "kokoro" / "bin" / "python"))
IMG_KEYS = {"img", "cover", "mark", "logo", "logoDark"}
LIST_KEYS = {"imgs", "covers"}


def die(msg):
    sys.exit(f"reel: {msg}")


def run(cmd, quiet=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        die(f"failed: {' '.join(map(str, cmd))}\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def file_url(p):
    return "file://" + quote(str(Path(p).resolve()))


# ---------- spec ----------

def load(spec_path):
    sp = Path(spec_path).resolve()
    spec = json.loads(sp.read_text())
    spec["_dir"] = sp.parent
    spec.setdefault("slug", sp.stem)
    spec["_brand"] = find_brand(spec, sp.parent)
    return spec


def find_brand(spec, base):
    b = spec.get("brand")
    if isinstance(b, str):
        p = (base / b).resolve()
        return dict(json.loads(p.read_text()), _dir=p.parent)
    if isinstance(b, dict):
        return dict(b, _dir=base)
    for d in [base, *base.parents][:4]:
        if (d / "brand.json").exists():
            return dict(json.loads((d / "brand.json").read_text()), _dir=d)
    return {"name": "Your Brand", "handle": "@yourbrand", "accent": "#10b981", "_dir": base}


def brand_for_engine(b):
    out = {k: v for k, v in b.items() if not k.startswith("_")}
    for k in ("logo", "logoDark", "mark"):
        if out.get(k):
            out[k] = file_url((b["_dir"] / out[k]).resolve())
    return out


def resolve(obj, base, cache, key=None):
    """Make image paths absolute file URLs and turn "video" paths into frame folders."""
    if isinstance(obj, dict):
        return {k: resolve(v, base, cache, k) for k, v in obj.items()}
    if isinstance(obj, list):
        if key in LIST_KEYS:
            return [resolve(v, base, cache, "img") if isinstance(v, str) else resolve(v, base, cache) for v in obj]
        return [resolve(v, base, cache) for v in obj]
    if isinstance(obj, str) and key == "video":
        return video_frames((base / obj).resolve(), cache)
    if isinstance(obj, str) and key in IMG_KEYS and not obj.startswith(("file:", "http", "data:")):
        p = (base / obj).resolve()
        if not p.exists():
            die(f"image not found: {p}")
        return file_url(p)
    return obj


def video_frames(src, cache, fps=15, width=540):
    if not src.exists():
        die(f"video not found: {src}")
    h = hashlib.sha1(f"{src}{src.stat().st_mtime}{fps}{width}".encode()).hexdigest()[:12]
    d = cache / f"v-{h}"
    if not (d / "done").exists():
        shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"fps={fps},scale={width}:-2", "-q:v", "3", d / "%05d.jpg"])
        (d / "done").write_text("")
    n = len(list(d.glob("*.jpg")))
    return {"dir": file_url(d), "n": n, "fps": fps}


# ---------- lines and timing ----------

def parse(text):
    """'/' breaks a headline page; *word* or *a few words* is the accent colour (one word is also underlined)."""
    pages, cur, inside, group = [], [], False, []
    for tok in text.split():
        if tok == "/":
            pages.append(cur); cur = []; continue
        start, end = tok.startswith("*"), tok.rstrip(",.:;!?\"'”").endswith("*")
        if start:
            inside, group = True, []
        word = {"w": tok.replace("*", ""), "hl": inside}
        cur.append(word)
        if inside:
            group.append(word)
        if end:
            inside = False
            if len(group) == 1:
                group[0]["u"] = True
    pages.append(cur)
    return [p for p in pages if p]


def split_hold(text):
    m = re.search(r"\[\+(\d+(?:\.\d+)?)\]\s*$", text)
    return (text[:m.start()].rstrip(), float(m.group(1))) if m else (text, 0.0)


def term_need(st):
    typ = min(2.6, max(.7, len(st["cmd"]) / CPS))
    work = len(st.get("work", []))
    show = st.get("show", 2.8 if st.get("result") else .8)
    return typ + .12 + .45 * work + .3 + show


def term_times(st, t0):
    typ = min(2.6, max(.7, len(st["cmd"]) / CPS))
    st["t0"] = round(t0, 4)
    st["t1"] = round(t0 + typ + .12, 4)
    st["w"] = [round(st["t1"] + .45 * (j + 1), 4) for j in range(len(st.get("work", [])))]
    st["tr"] = round((st["w"][-1] if st["w"] else st["t1"]) + .3, 4)


def timeline(spec, clips=None):
    fps, wps = spec.get("fps", FPS), spec.get("wps", WPS)
    lines, scenes, t = [], [], 0.0
    first_theme = spec.get("start", "light")
    for si, sc in enumerate(spec["scenes"]):
        typ, props = sc["type"], dict(sc.get("props", {}))
        texts = sc.get("lines", [])
        if not texts:
            die(f"scene {si} ({typ}) has no lines; every scene needs at least one line to set its timing")
        steps = props.get("steps") if typ == "term" else None
        if steps and len(steps) > len(texts):
            die(f"scene {si}: a term scene needs one line per step ({len(steps)} steps, {len(texts)} lines)")
        s0, idx = t, []
        for k, raw in enumerate(texts):
            text, hold = split_hold(raw)
            pages = parse(text)
            words = [w for pg in pages for w in pg]
            key = f"{si}-{k}"
            if clips and key in clips:
                c = clips[key]
                for w, wt in zip(words, c["word_times"]):
                    w["t"] = round(t + max(0.0, wt - .05), 4)
                dur = c["len"] + .24 + hold
            else:
                for i, w in enumerate(words):
                    w["t"] = round(t + .05 + i / wps, 4)
                if si == 0 and k == 0 and words and spec.get("firstFrame", True):
                    words[0]["t"] = -0.3   # the first word is already on screen at frame one
                dur = len(words) / wps + PAD + hold
            if steps and k < len(steps):
                dur = max(dur, term_need(steps[k]) + .2)
                term_times(steps[k], t + .15)
            if k == len(texts) - 1:
                dur += sc.get("hold", 0)
            dur = round(dur * fps) / fps
            idx.append(len(lines))
            lines.append({"start": round(t, 4), "end": round(t + dur, 4), "scene": si, "key": key,
                          "say": re.sub(r"\s+", " ", text.replace("/", " ").replace("*", "")).strip(), "pages": pages})
            t += dur
        theme = sc.get("theme") or (first_theme if si % 2 == 0 else ("dark" if first_theme == "light" else "light"))
        scenes.append({"id": f"s{si}", "type": typ, "theme": theme, "head": sc.get("head", True),
                       "start": round(s0, 4), "end": round(t, 4), "lines": idx, "props": props})
    return {"fps": fps, "total": round(t, 4), "lines": lines, "scenes": scenes}


# ---------- sound effects (standard library only) ----------

def synth(events, total, seed=7):
    rnd = random.Random(seed)
    n = int(total * SR) + SR
    track = array.array("f", bytes(4 * n))

    def add(t, samples):
        i0 = int(t * SR)
        for i, v in enumerate(samples):
            j = i0 + i
            if 0 <= j < n:
                track[j] += v

    def click(v, decay, body=0.0, bodyf=150.0):
        out, prev = [], 0.0
        L = int(SR * max(decay * 6, .03 if body else 0))
        f = rnd.uniform(2600, 3600)
        for i in range(L):
            x = rnd.uniform(-1, 1); hp = x - prev; prev = x
            e = math.exp(-i / (decay * SR))
            s = (.5 * hp + .25 * math.sin(2 * math.pi * f * i / SR)) * e
            if body:
                s += body * math.sin(2 * math.pi * bodyf * i / SR) * math.exp(-i / (.035 * SR))
            out.append(s * v)
        return out

    def tone(v, freqs, dur, decay, sweep=None, attack=.003):
        out, ph = [], [0.0] * len(freqs)
        L = int(dur * SR)
        for i in range(L):
            tt = i / SR
            env = min(1.0, tt / attack) * math.exp(-tt / decay)
            s = 0.0
            for k, (f, a) in enumerate(freqs):
                ff = f if not sweep else f * (sweep + (1 - sweep) * math.exp(-tt / (dur * .35)))
                ph[k] += 2 * math.pi * ff / SR
                s += a * math.sin(ph[k])
            out.append(s * env * v)
        return out

    def whoosh(v, dur=.38):
        out, lp = [], 0.0
        L = int(dur * SR)
        for i in range(L):
            p = i / L
            a = .02 + .25 * math.sin(math.pi * p)
            lp += a * (rnd.uniform(-1, 1) - lp)
            out.append(lp * math.sin(math.pi * p) ** 2 * v)
        return out

    for e in events:
        k, v, t = e["k"], e.get("v", 1), e["t"]
        if k == "key":
            add(t, click(.2 * v, .0035))
        elif k == "enter":
            add(t, click(.3 * v, .006, body=.35, bodyf=140))
        elif k == "tick":
            add(t, tone(.1 * v, [(2093, 1)], .06, .014))
        elif k == "pop":
            add(t, tone(.3 * v, [(820, 1), (1640, .15)], .12, .045, sweep=.45))
        elif k == "whoosh":
            add(t - .12, whoosh(.55 * v))
        elif k == "ding":
            add(t, tone(.13 * v, [(1567.98, 1), (2349.3, .45), (3135.96, .15)], .7, .22))
        elif k == "thump":
            add(t, tone(.6 * v, [(105, 1), (210, .2)], .3, .09, sweep=.42))
            add(t, click(.18 * v, .004))
        elif k == "sparkle":
            for j in range(3):
                add(t + j * .035, tone(.035 * v, [(rnd.uniform(2600, 4200), 1)], .07, .02))
    peak = max(1e-6, max(abs(x) for x in track))
    g = min(2.5, .9 / peak)
    return [x * g for x in track[:int(total * SR)]]


def write_wav(path, samples, sr=SR):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        buf = array.array("h")
        for x in samples:
            v = int(max(-1.0, min(1.0, x)) * 32000)
            buf.append(v); buf.append(v)
        w.writeframes(buf.tobytes())


# ---------- optional narration (Kokoro) ----------

def narrate(spec, work):
    if not KOKORO.exists():
        die(f"voice needs Kokoro: python not found at {KOKORO} (set REEL_KOKORO_PYTHON, see README)")
    say = spec.get("say", {})
    spoken = lambda w: say.get(w.rstrip(",.:?!"), w.rstrip(",.:?!")) + w[len(w.rstrip(",.:?!")):]
    jobs = []
    for si, sc in enumerate(spec["scenes"]):
        for k, raw in enumerate(sc.get("lines", [])):
            text, _ = split_hold(raw)
            words = [w["w"] for pg in parse(text) for w in pg]
            jobs.append({"key": f"{si}-{k}", "text": " ".join(spoken(w) for w in words), "voice": spec["voice"], "speed": spec.get("speed", 1.08), "words": words})
    (work / "voice").mkdir(parents=True, exist_ok=True)
    (work / "voice" / "jobs.json").write_text(json.dumps(jobs))
    run([KOKORO, ENGINE / "voice.py", work / "voice" / "jobs.json", work / "voice"])
    clips = {}
    for j in jobs:
        m = json.loads((work / "voice" / f"{j['key']}.json").read_text())
        alnum = [tk for tk in m["tokens"] if re.search(r"[A-Za-z0-9]", tk["text"]) and tk["start"] is not None]
        a = max(0.0, alnum[0]["start"] - .06)
        b = min(m["dur"], (alnum[-1]["end"] or m["dur"]) + .14)
        said = [spoken(w).split() for w in j["words"]]
        flat = [i for i, sp in enumerate(said) for _ in sp]
        if len(alnum) == len(flat):
            first = {}
            for tk, i in zip(alnum, flat):
                first.setdefault(i, tk["start"])
            wt = [first[i] - a for i in range(len(j["words"]))]
        else:
            span = (alnum[-1]["end"] or b) - alnum[0]["start"]
            wt = [alnum[0]["start"] - a + span * i / max(1, len(j["words"])) for i in range(len(j["words"]))]
        clips[j["key"]] = {"len": b - a, "word_times": wt, "wav": str(work / "voice" / f"{j['key']}.wav"), "from": a, "to": b}
    return clips


def voice_track(tl, clips, work):
    spec = {"total": tl["total"], "clips": [dict(wav=clips[l["key"]]["wav"], at=l["start"], **{k: clips[l["key"]][k] for k in ("from", "to")}) for l in tl["lines"] if l["key"] in clips]}
    (work / "voice" / "mix.json").write_text(json.dumps(spec))
    run([KOKORO, ENGINE / "voice.py", "--mix", work / "voice" / "mix.json", work / "voice" / "mix.wav"])
    return work / "voice" / "mix.wav"


# ---------- outputs ----------

ts = lambda s: f"{int(s // 60)}:{s % 60:04.1f}"


def caption_md(spec, tl, outs):
    c = spec.get("cta", {})
    rows = "\n".join(f"| {i} | {ts(l['start'])} | {ts(l['end'])} | {l['say']} |" for i, l in enumerate(tl["lines"], 1))
    parts = [f"# {spec.get('title', spec['slug'])}", "",
             f"Video: `{outs['mp4'].name}` (1080x1920, {tl['fps']} fps, {ts(tl['total'])}, {outs['audio']}). Cover: `{outs['cover'].name}`.", ""]
    if spec.get("caption"):
        parts += ["## Caption", "", spec["caption"], ""]
    if spec.get("pinned"):
        parts += ["## Pinned comment", "", spec["pinned"], ""]
    if c.get("keyword"):
        parts += [f"## DM reply when someone comments {c['keyword']}", "", c.get("dm", "") + (f"\n\n{c['url']}" if c.get("url") else ""), ""]
    parts += ["## On-screen lines (also a voiceover script)", "", "| # | Start | End | Line |", "|---|---|---|---|", rows, ""]
    return "\n".join(parts)


def render_one(spec, mode="build", times=()):
    t_start = time.time()
    base, slug = spec["_dir"], spec["slug"]
    out = (base / spec.get("out", "out")).resolve(); out.mkdir(parents=True, exist_ok=True)
    work = base / ".reel-work" / slug
    cache = base / ".reel-work" / "cache"
    work.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    spec = dict(spec, scenes=[dict(sc, props=resolve(sc.get("props", {}), base, cache)) for sc in spec["scenes"]])
    clips = narrate(spec, work) if spec.get("voice") and mode == "build" else None
    tl = timeline(spec, clips)
    tl["brand"] = brand_for_engine(spec["_brand"])
    tlp = work / "timeline.json"
    tlp.write_text(json.dumps(tl))
    node = ["node", ENGINE / "render.mjs", tlp]
    cover = out / f"{slug}-cover.jpg"
    first = tl["scenes"][0]
    cover_t = spec.get("coverAt", max(.5, (first["end"] if first["type"] == "text" else tl["lines"][0]["end"]) - .2))
    if mode == "preview":
        print(run([*node, "preview", out / "previews" / slug, *times]).strip())
        return
    run([*node, "cover", f"{cover_t:.2f}", cover])
    if mode == "cover":
        print(cover); return
    frames = work / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    run([*node, "frames", frames])
    audio = []
    if spec.get("sfx", True):
        run([*node, "sounds", work / "sounds.json"])
        events = json.loads((work / "sounds.json").read_text())
        write_wav(work / "sfx.wav", synth(events, tl["total"]))
        audio.append(("sfx.wav", spec.get("sfxGain", 1.0 if not clips else .45)))
    if clips:
        voice_track(tl, clips, work)
        audio.append(("voice/mix.wav", 1.0))
    mp4 = out / f"{slug}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", tl["fps"], "-i", frames / "%05d.jpg"]
    for a, _ in audio:
        cmd += ["-i", work / a]
    if audio:
        mixf = "".join(f"[{i + 1}:a]volume={g}[a{i}];" for i, (_, g) in enumerate(audio))
        mixf += "".join(f"[a{i}]" for i in range(len(audio))) + f"amix=inputs={len(audio)}:normalize=0,aresample=48000[aout]"
        cmd += ["-filter_complex", mixf, "-map", "0:v", "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", "-ac", "2"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", tl["fps"], "-t", f"{tl['total']:.3f}", "-movflags", "+faststart", mp4]
    run(cmd)
    sheet = out / f"{slug}-sheet.jpg"
    rows_n = max(1, math.ceil(tl["total"] / 6))
    run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", f"fps=1,scale=216:-1,tile=6x{rows_n}:padding=6:color=white", "-frames:v", "1", "-update", "1", sheet])
    kind = ("narration + sound effects" if clips else "sound effects") if audio else "no audio"
    (out / f"{slug}.md").write_text(caption_md(spec, tl, {"mp4": mp4, "cover": cover, "audio": kind}))
    shutil.rmtree(frames, ignore_errors=True)
    secs = time.time() - t_start
    print(f"{mp4}  ({ts(tl['total'])}, {round(tl['total'] * tl['fps'])} frames, rendered in {secs:.0f} s)")
    return {"mp4": str(mp4), "length": tl["total"], "frames": round(tl["total"] * tl["fps"]), "render_s": round(secs, 1)}


def check():
    ok = True
    for name, cmd in [("node", ["node", "--version"]), ("ffmpeg", ["ffmpeg", "-version"])]:
        try:
            v = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()[0]
            print(f"ok   {name}: {v}")
        except Exception:
            ok = False; print(f"MISSING {name}")
    if not (ENGINE / "node_modules" / "playwright").exists():
        ok = False; print(f"MISSING playwright: run  cd '{ENGINE}' && npm install && npx playwright install chromium")
    else:
        r = subprocess.run(["node", "-e", "import('playwright').then(async p=>{const b=await p.chromium.launch();await b.close();console.log('ok')})"],
                           capture_output=True, text=True, cwd=ENGINE)
        if "ok" in r.stdout:
            print("ok   chromium")
        else:
            ok = False; print(f"MISSING chromium: run  cd '{ENGINE}' && npx playwright install chromium\n{r.stderr[-400:]}")
    print("voice: Kokoro found" if KOKORO.exists() else "voice: Kokoro not installed (optional)")
    sys.exit(0 if ok else 1)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    cmd, rest = a[0], a[1:]
    if cmd == "check":
        return check()
    if cmd == "preview":
        return render_one(load(rest[0]), "preview", rest[1:])
    if cmd == "cover":
        for p in rest:
            render_one(load(p), "cover")
        return
    if cmd == "build":
        results = [render_one(load(p)) for p in rest]
        if len(results) > 1:
            print(f"{len(results)} reels, {sum(r['render_s'] for r in results):.0f} s in all")
        return
    die(f"unknown command {cmd}; try --help")


if __name__ == "__main__":
    main()
