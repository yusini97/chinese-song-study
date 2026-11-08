"""유튜브 영상의 정보와 자막(대사)을 공부용 폴더에 저장한다.

사용법:
  python tools/fetch_video.py URL                 # 정보 + 자막(있으면)
  python tools/fetch_video.py URL --lang zh,ko    # 자막 언어 우선순위
  python tools/fetch_video.py URL --whisper       # 자막이 없으면 음성을 받아 Whisper로 받아쓰기
  python tools/fetch_video.py URL --description   # 설명란도 저장 (가사가 설명란에만 있는 영상)

결과: videos/<영상ID>/
  meta.json        제목·채널·길이·자막 언어 목록
  transcript.srt   시각이 붙은 대사
  transcript.txt   [mm:ss] 대사 한 줄씩 (공부 노트에 붙여 넣기 좋게)
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YTDLP = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--quiet", "--no-warnings"]


def run(args, **kw):
    return subprocess.run(YTDLP + args, capture_output=True, text=True, encoding="utf-8", **kw)


def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    if not m:
        sys.exit(f"영상 ID를 찾지 못했습니다: {url}")
    return m.group(1)


def srt_from_vtt(vtt):
    """yt-dlp의 VTT(자동 자막 포함)를 겹침 없는 SRT 블록 목록으로 바꾼다."""
    cues, last = [], None
    for block in re.split(r"\n\s*\n", vtt):
        m = re.search(r"(\d+:\d\d:\d\d\.\d+) --> (\d+:\d\d:\d\d\.\d+)", block)
        if not m:
            continue
        text = block[m.end():].split("\n", 1)[-1] if "\n" in block[m.end():] else ""
        text = re.sub(r"<[^>]+>", "", text).strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        # 자동 자막은 앞 줄을 반복해서 보여 주므로 새로 나온 줄만 남긴다
        lines = [l for l in lines if l != last]
        if not lines:
            continue
        last = lines[-1]
        cues.append((m.group(1), m.group(2), " ".join(lines)))
    return cues


def to_sec(ts):
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def write_transcript(out, cues):
    srt = []
    for i, (a, b, t) in enumerate(cues, 1):
        srt.append(f"{i}\n{a.replace('.', ',')} --> {b.replace('.', ',')}\n{t}\n")
    (out / "transcript.srt").write_text("\n".join(srt), encoding="utf-8")
    txt = [f"[{int(to_sec(a)) // 60:02d}:{int(to_sec(a)) % 60:02d}] {t}" for a, _, t in cues]
    (out / "transcript.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    return len(cues)


def fetch_captions(url, out, langs):
    for auto in (False, True):
        flag = "--write-auto-subs" if auto else "--write-subs"
        for lang in langs:
            for f in out.glob("cap.*.vtt"):
                f.unlink()
            run(["--skip-download", flag, "--sub-langs", lang, "--sub-format", "vtt",
                 "-o", str(out / "cap.%(ext)s"), url])
            got = sorted(out.glob("cap.*.vtt"))
            if got:
                cues = srt_from_vtt(got[0].read_text(encoding="utf-8"))
                got[0].unlink()
                if cues:
                    return lang, ("자동 자막" if auto else "업로드 자막"), cues
    return None


def whisper(url, out, lang):
    audio = out / "audio.m4a"
    r = run(["-f", "bestaudio[ext=m4a]/bestaudio", "-o", str(audio), url])
    if not audio.exists():
        sys.exit("음성을 받지 못했습니다: " + r.stderr[-300:])
    from faster_whisper import WhisperModel
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(audio), language=lang, beam_size=5, condition_on_previous_text=False)
    fmt = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}"
    cues = [(fmt(s.start), fmt(s.end), s.text.strip()) for s in segs if s.text.strip()]
    audio.unlink()
    return cues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--lang", default="ko,zh-Hans,zh,zh-Hant,en,ja", help="자막 언어 우선순위(쉼표)")
    ap.add_argument("--whisper", action="store_true", help="자막이 없으면 음성 받아쓰기")
    ap.add_argument("--whisper-lang", default=None, help="받아쓰기 언어 (예: zh, ko). 비우면 자동 감지")
    ap.add_argument("--description", action="store_true", help="설명란을 description.txt로 저장")
    a = ap.parse_args()

    vid = video_id(a.url)
    url = f"https://www.youtube.com/watch?v={vid}"
    out = ROOT / "videos" / vid
    out.mkdir(parents=True, exist_ok=True)

    r = run(["--skip-download", "--dump-json", url])
    if r.returncode:
        sys.exit("영상 정보를 가져오지 못했습니다: " + r.stderr[-300:])
    info = json.loads(r.stdout)
    meta = dict(id=vid, url=url, title=info.get("title"), channel=info.get("channel"),
                duration=info.get("duration_string"), upload_date=info.get("upload_date"),
                subtitles=sorted(info.get("subtitles") or {}),
                auto_caption_langs=len(info.get("automatic_captions") or {}))
    if a.description:
        (out / "description.txt").write_text(info.get("description") or "", encoding="utf-8")

    langs = [l.strip() for l in a.lang.split(",") if l.strip()]
    got = fetch_captions(url, out, langs) if (meta["subtitles"] or meta["auto_caption_langs"]) else None
    if got:
        lang, kind, cues = got
        meta["transcript"] = dict(source=kind, lang=lang, lines=write_transcript(out, cues))
    elif a.whisper:
        cues = whisper(url, out, a.whisper_lang)
        meta["transcript"] = dict(source="Whisper medium 받아쓰기", lang=a.whisper_lang or "auto",
                                  lines=write_transcript(out, cues))
    else:
        meta["transcript"] = None

    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{meta['title']} ({meta['duration']})")
    print(f"저장 위치: {out}")
    t = meta["transcript"]
    if t:
        print(f"대사 {t['lines']}줄 ({t['source']}, {t['lang']})")
    else:
        print("자막이 없습니다. --whisper로 받아쓰거나, 가사가 설명란에 있으면 --description을 쓰세요.")


if __name__ == "__main__":
    main()
