"""Narration for the reels with Kokoro (local, Apache-2.0 model hexgrad/Kokoro-82M).

Run with the Kokoro venv, not system python:
    $REEL_KOKORO_PYTHON voice.py jobs.json outdir  (default ~/.venvs/kokoro/bin/python)

jobs.json: [{"key": "01-3", "text": "...", "voice": "af_heart", "speed": 1.08}, ...]
    ~/.venvs/kokoro/bin/python voice.py --mix mix.json out.wav

Writes outdir/<key>.wav (24 kHz mono) and outdir/<key>.json with the clip
length and per-token start/end times, which build.py uses to time each
headline word to the narration.
"""
import json, sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

SR = 24000


def mix(spec_path, out_path):
    """Lay the trimmed line clips onto one track at their timeline positions."""
    spec = json.loads(Path(spec_path).read_text())
    track = np.zeros(int(spec["total"] * SR) + SR, dtype=np.float32)
    for c in spec["clips"]:
        a, _ = sf.read(c["wav"], dtype="float32")
        seg = a[int(c["from"] * SR):int(c["to"] * SR)].copy()
        f = min(len(seg) // 4, int(.012 * SR))
        if f:
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        i = int(c["at"] * SR)
        track[i:i + len(seg)] += seg
    sf.write(out_path, track[:int(spec["total"] * SR)], SR)


def main():
    if sys.argv[1] == "--mix":
        return mix(sys.argv[2], sys.argv[3])
    jobs = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    for j in jobs:
        wav, meta = out / f"{j['key']}.wav", out / f"{j['key']}.json"
        if wav.exists() and meta.exists() and json.loads(meta.read_text()).get("text") == j["text"] and json.loads(meta.read_text()).get("voice") == j["voice"]:
            continue
        audio, tokens, offset = [], [], 0.0
        for r in pipe(j["text"], voice=j["voice"], speed=j.get("speed", 1.0), split_pattern=None):
            a = r.audio.detach().cpu().numpy() if hasattr(r.audio, "detach") else np.asarray(r.audio)
            for tk in (r.tokens or []):
                tokens.append({"text": tk.text, "ws": tk.whitespace,
                               "start": None if tk.start_ts is None else round(offset + tk.start_ts, 3),
                               "end": None if tk.end_ts is None else round(offset + tk.end_ts, 3)})
            audio.append(a)
            offset += len(a) / SR
        a = np.concatenate(audio).astype(np.float32)
        sf.write(wav, a, SR)
        meta.write_text(json.dumps({"text": j["text"], "voice": j["voice"], "dur": round(len(a) / SR, 3), "tokens": tokens}))
        print(j["key"], round(len(a) / SR, 2), "s", flush=True)


if __name__ == "__main__":
    main()
