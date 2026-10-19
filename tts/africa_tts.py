#!/usr/bin/env python3
"""Voice Petrarch's *Africa* (ElevenLabs recitation text) section by section.

Needs only Python 3.8+ (no extra packages). ffmpeg is optional: with it the sections
are also joined into one MP3 with a short pause between them.

  python3 africa_tts.py voices                                   list the voices in your account
  python3 africa_tts.py estimate Africa_09_Liber_IX.txt          sections and characters, no API call
  python3 africa_tts.py run Africa_09_Liber_IX.txt --voice ID --only 1   test the first section
  python3 africa_tts.py run Africa_09_Liber_IX.txt --voice ID    voice the whole book (resumable)
  python3 africa_tts.py merge Africa_09_Liber_IX_audio           join the section MP3s again

The API key is read from the environment variable ELEVENLABS_API_KEY, else from a file
elevenlabs_key.txt next to this script, else the script asks for it (input is hidden).
The script never prints or saves the key.
"""
import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")
SEP = re.compile(r"^=====\s*Africa\s+([IVX]+)\.(\d+)[–-](\d+)\s*\|\s*(.*?)\s*\|.*=====\s*$")


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elevenlabs_key.txt")
    if not k and os.path.exists(kf):
        with open(kf, encoding="utf-8") as f:
            k = f.read().strip()
    if not k and not sys.stdin.isatty():
        sys.exit("No API key: set ELEVENLABS_API_KEY or put it in elevenlabs_key.txt next to this script.")
    if not k:
        k = getpass.getpass("ElevenLabs API key (hidden): ").strip()
    if not k:
        sys.exit("No API key given.")
    return k


def request(method, path, key, body=None, accept="application/json", timeout=300):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("xi-api-key", key)
    req.add_header("Accept", accept)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_sections(path):
    sections, cur = [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            m = SEP.match(line)
            if m:
                cur = {"book": m.group(1), "start": int(m.group(2)), "end": int(m.group(3)),
                       "title": m.group(4), "lines": []}
                sections.append(cur)
            elif cur is not None:
                cur["lines"].append(line)
    for i, s in enumerate(sections, 1):
        s["index"] = i
        s["text"] = "\n".join(s["lines"]).strip()
        s["name"] = f"{s['book']}_{i:02d}_{s['start']:03d}-{s['end']:03d}.mp3"
    if not sections:
        sys.exit(f"No sections found in {path} (expected lines starting with '===== Africa ...').")
    return sections


def cmd_voices(a):
    key = api_key()
    data = json.loads(request("GET", "/v1/voices", key))
    voices = data.get("voices", [])
    for v in sorted(voices, key=lambda v: v.get("name", "")):
        labels = v.get("labels") or {}
        lab = ", ".join(f"{k}: {x}" for k, x in labels.items() if x)
        print(f"{v.get('voice_id')}  {v.get('name')}  [{v.get('category', '')}]  {lab}")
    print(f"\n{len(voices)} voices. Use the first column with --voice.")


def cmd_estimate(a):
    secs = parse_sections(a.textfile)
    total = 0
    for s in secs:
        total += len(s["text"])
        print(f"{s['index']:2d}  {s['book']}.{s['start']}–{s['end']}  {len(s['text']):5d} chars  {s['title']}")
    print(f"\n{len(secs)} sections, {total:,} characters in total (= the text sent to ElevenLabs).")


def out_dir_for(textfile, given):
    if given:
        return given
    base = os.path.splitext(os.path.basename(textfile))[0]
    return os.path.join(os.path.dirname(os.path.abspath(textfile)), base + "_audio")


def cmd_run(a):
    secs = parse_sections(a.textfile)
    if a.only:
        wanted = set()
        for part in a.only.split(","):
            if "-" in part:
                x, y = part.split("-")
                wanted.update(range(int(x), int(y) + 1))
            else:
                wanted.add(int(part))
        secs = [s for s in secs if s["index"] in wanted]
    out = out_dir_for(a.textfile, a.out)
    os.makedirs(out, exist_ok=True)
    key = api_key()
    body_base = {"model_id": a.model, "language_code": a.language}
    if a.stability is not None:
        body_base["voice_settings"] = {"stability": a.stability}
    if a.seed is not None:
        body_base["seed"] = a.seed
    path = f"/v1/text-to-speech/{a.voice}?output_format={a.format}"
    done = 0
    for s in secs:
        target = os.path.join(out, s["name"])
        if os.path.exists(target) and os.path.getsize(target) > 0 and not a.force:
            print(f"skip  {s['name']} (already there)")
            continue
        body = dict(body_base, text=s["text"])
        for attempt in range(1, 6):
            try:
                t0 = time.time()
                audio = request("POST", path, key, body, accept="audio/mpeg")
                tmp = target + ".part"
                with open(tmp, "wb") as f:
                    f.write(audio)
                os.replace(tmp, target)
                print(f"ok    {s['name']}  {len(s['text'])} chars  {len(audio)/1e6:.1f} MB  {time.time()-t0:.0f}s")
                done += 1
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "replace")[:500]
                if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                    wait = 10 * attempt
                    print(f"wait  {s['name']}: HTTP {e.code}, retrying in {wait}s")
                    time.sleep(wait)
                    continue
                sys.exit(f"error {s['name']}: HTTP {e.code}\n{msg}\n(Finished sections are kept; run the same command again to resume.)")
            except urllib.error.URLError as e:
                if attempt < 5:
                    print(f"wait  {s['name']}: {e.reason}, retrying")
                    time.sleep(10 * attempt)
                    continue
                sys.exit(f"error {s['name']}: {e.reason}")
        if a.pause:
            time.sleep(a.pause)
    print(f"\n{done} section(s) generated in {out}")
    if not a.only and not a.no_merge:
        merge(out, a.gap)


def merge(out, gap):
    files = sorted(f for f in os.listdir(out) if re.match(r"^[IVX]+_\d\d_\d{3}-\d{3}\.mp3$", f))
    if not files:
        print("Nothing to merge.")
        return
    book = files[0].split("_")[0]
    target = os.path.join(out, f"Africa_{book}_complete.mp3")
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg not found: the section MP3s are complete; install ffmpeg and run "
              f"'python3 africa_tts.py merge {out}' to join them into one file.")
        return
    silence = os.path.join(out, "_gap.mp3")
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(gap), "-c:a", "libmp3lame", "-b:a", "128k", silence], check=True)
    lst = os.path.join(out, "_list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for i, name in enumerate(files):
            if i:
                f.write("file '_gap.mp3'\n")
            f.write(f"file '{name}'\n")
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-b:a", "128k", target], check=True)
    os.remove(lst)
    os.remove(silence)
    print(f"joined {len(files)} sections -> {target}")


def cmd_merge(a):
    merge(a.folder, a.gap)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices").set_defaults(fn=cmd_voices)
    e = sub.add_parser("estimate")
    e.add_argument("textfile")
    e.set_defaults(fn=cmd_estimate)
    r = sub.add_parser("run")
    r.add_argument("textfile")
    r.add_argument("--voice", required=True, help="voice_id (see: voices)")
    r.add_argument("--model", default="eleven_v3", help="eleven_v3 (default) or eleven_v4")
    r.add_argument("--language", default="it", help="language code sent to ElevenLabs (default it = Italian)")
    r.add_argument("--stability", type=float, default=None,
                   help="eleven_v3: 0.0 Creative, 0.5 Natural, 1.0 Robust (default: the voice's own setting)")
    r.add_argument("--seed", type=int, default=None, help="optional fixed seed for more repeatable takes")
    r.add_argument("--format", default="mp3_44100_128", help="output_format (default mp3_44100_128)")
    r.add_argument("--only", default="", help="sections to (re)do, e.g. 1 or 3,7 or 5-9")
    r.add_argument("--force", action="store_true", help="redo sections that already have an MP3")
    r.add_argument("--out", default="", help="output folder (default: <textfile>_audio next to the text)")
    r.add_argument("--pause", type=float, default=1.0, help="seconds to wait between requests")
    r.add_argument("--gap", type=float, default=1.5, help="silence between sections in the joined MP3")
    r.add_argument("--no-merge", action="store_true")
    r.set_defaults(fn=cmd_run)
    m = sub.add_parser("merge")
    m.add_argument("folder")
    m.add_argument("--gap", type=float, default=1.5)
    m.set_defaults(fn=cmd_merge)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
