"""곡 목록 페이지(index.html)를 videos/*/data.js와 대기열로 다시 만든다."""
import html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")


def study(path):
    t = path.read_text(encoding="utf-8")
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def main():
    queue = {}
    q = ROOT / "state" / "queue.json"
    if q.exists():
        queue = json.loads(q.read_text(encoding="utf-8"))

    songs = []
    for d in (ROOT / "videos").glob("*/data.js"):
        s = study(d)
        n = sum(len(p[2]) for p in s.get("patterns", []))
        songs.append(dict(id=s["id"], title=s["title"], artist=s.get("artist", ""), generated=s.get("generated", ""),
                          intro=s.get("intro", ""), patterns=len(s.get("patterns", [])), sentences=n,
                          first_seen=(queue.get(s["id"]) or {}).get("first_seen") or ""))
    songs.sort(key=lambda s: (s["generated"], s["first_seen"]), reverse=True)
    waiting = [(k, v) for k, v in queue.items() if v.get("status") == "new"]
    skipped = [(k, v) for k, v in queue.items() if v.get("status") == "skipped"]

    e = html.escape
    rows = "\n".join(
        f'<a class="song" href="videos/{e(s["id"])}/index.html"><span class="zh s">{e(s["title"])}</span>'
        f'<span class="tag">{e(s["generated"])}</span><span class="tag">문형 {s["patterns"]} · 예문 {s["sentences"]}</span>'
        f'<div class="muted">{e(s["artist"])}</div><div class="muted">{e(s["intro"])}</div></a>' for s in songs)
    wait = "".join(f"<li>{e(v.get('title') or k)}</li>" for k, v in waiting)
    skip = "".join(f"<li>{e(v.get('title') or k)} <span class='muted'>— {e(v.get('reason') or '')}</span></li>" for k, v in skipped)

    def page(title, body):
        return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="assets/study.css">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""
    # index.html은 GitHub Pages에 공개된다: 만든 곡만 싣는다
    (ROOT / "index.html").write_text(page("중국어 노래 문장 공부", f"""<h1>중국어 노래 문장 공부</h1>
<p class="muted">들은 중국어 노래로 만든 HSK 5~6급 문장 자료. 곡 {len(songs)}개. 가사 전문은 싣지 않는다.</p>
{rows or '<p class="muted">아직 만든 곡이 없다.</p>'}"""), encoding="utf-8")
    # queue.html은 이 PC에서만 보는 대기열 (청취 기록이라 Git 제외)
    (ROOT / "queue.html").write_text(page("대기열", f"""<p><a href="index.html">← 곡 목록</a></p><h1>대기열</h1>
<h2>다음에 만들 곡 ({len(waiting)})</h2><ul>{wait}</ul>
<h2>건너뛴 곡 ({len(skipped)})</h2><ul>{skip}</ul>"""), encoding="utf-8")
    print(f"index.html: 곡 {len(songs)} · queue.html: 대기 {len(waiting)} · 건너뜀 {len(skipped)}")


if __name__ == "__main__":
    main()
