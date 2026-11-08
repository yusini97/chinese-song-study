"""Chrome 방문 기록에서 새로 들은 중국어 노래(YouTube)를 찾아 대기열에 넣는다.

사용법:
  python tools/track_chrome.py                 # 지난 확인 이후 새 곡을 대기열에 추가, 대기 중인 곡 출력
  python tools/track_chrome.py --since-hours 48  # 처음 실행이거나 다시 훑을 때 범위 지정
  python tools/track_chrome.py --now           # 지금 열려 있는(듣는 중인) YouTube만 보기, 저장 안 함
  python tools/track_chrome.py --mark ID done            # 공부 페이지를 만든 곡
  python tools/track_chrome.py --mark ID skipped "이유"  # 중국어 노래가 아니라 건너뛴 곡

Chrome은 History 파일을 잠그므로 복사본을 읽는다. 대기열(state/queue.json)에는 후보 YouTube 곡만 남기고
다른 방문 기록은 저장하지 않는다.
"""
import argparse, datetime as dt, json, os, re, shutil, sqlite3, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
QUEUE = STATE / "queue.json"
TRACK = STATE / "tracker.json"
CHROME = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
EPOCH = dt.datetime(1601, 1, 1)
HAN = re.compile(r"[一-鿿]")
MIN_LISTEN = 60  # 초. 이보다 짧게 연 영상은 건너뛴다 (지금 열려 있어 0초로 기록된 영상은 포함)

sys.stdout.reconfigure(encoding="utf-8")


def chrome_time(t):
    return EPOCH + dt.timedelta(microseconds=t)


def to_chrome(d):
    return int((d - EPOCH).total_seconds() * 1e6)


def load(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save(p, data):
    STATE.mkdir(exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def visits(since):
    """모든 Chrome 프로필에서 since(UTC) 이후 YouTube 영상 방문을 읽는다."""
    out = []
    tmp = Path(tempfile.mkdtemp())
    for hist in CHROME.glob("*/History"):
        copy = tmp / (hist.parent.name.replace(" ", "") + ".db")
        try:
            shutil.copy2(hist, copy)
            con = sqlite3.connect(copy)
            rows = con.execute(
                "select u.url, u.title, v.visit_time, v.visit_duration from visits v join urls u on u.id = v.url "
                "where u.url like '%youtube.com/watch%' and v.visit_time > ?", (to_chrome(since),)).fetchall()
            con.close()
        except (OSError, sqlite3.Error) as e:
            print(f"[경고] {hist.parent.name} 기록을 읽지 못함: {e}")
            continue
        for url, title, vt, dur in rows:
            m = re.search(r"[?&]v=([\w-]{11})", url)
            if m:
                out.append(dict(id=m.group(1), title=re.sub(r" - YouTube$", "", title or ""),
                                at=chrome_time(vt), sec=dur / 1e6, profile=hist.parent.name))
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def is_candidate(title):
    return len(HAN.findall(title)) >= 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since-hours", type=float, help="이 시간만큼 거슬러 훑기 (기본: 지난 확인 이후, 처음이면 24시간)")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--mark", nargs="+", metavar=("ID", "STATUS"))
    a = ap.parse_args()
    queue = load(QUEUE, {})

    if a.mark:
        vid, status, *why = a.mark
        if vid not in queue:
            queue[vid] = dict(title="", first_seen=None, listened_sec=0)
        queue[vid]["status"] = status
        queue[vid]["reason"] = " ".join(why) or None
        queue[vid]["updated"] = dt.datetime.now().isoformat(timespec="minutes")
        save(QUEUE, queue)
        print(f"{vid} → {status}")
        return

    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    if a.now:
        for v in sorted(visits(now - dt.timedelta(hours=3)), key=lambda v: v["at"], reverse=True)[:5]:
            local = v["at"] + dt.timedelta(hours=9)
            state = "듣는 중" if v["sec"] == 0 else f"{v['sec']:.0f}초"
            print(f"{local:%H:%M} [{state}] {v['title']} ({v['id']})")
        return

    track = load(TRACK, {})
    if a.since_hours:
        since = now - dt.timedelta(hours=a.since_hours)
    elif track.get("last_check"):
        since = dt.datetime.fromisoformat(track["last_check"]) - dt.timedelta(minutes=10)
    else:
        since = now - dt.timedelta(hours=24)

    agg = {}
    for v in visits(since):
        g = agg.setdefault(v["id"], dict(title=v["title"], sec=0.0, open=False, last=v["at"]))
        g["sec"] += v["sec"]
        g["open"] |= v["sec"] == 0
        g["last"] = max(g["last"], v["at"])
        if v["title"]:
            g["title"] = v["title"]

    added = []
    for vid, g in agg.items():
        if not is_candidate(g["title"]) or (g["sec"] < MIN_LISTEN and not g["open"]):
            continue
        q = queue.get(vid)
        if q:
            q["listened_sec"] = round(q.get("listened_sec", 0) + g["sec"])
            q["last_seen"] = (g["last"] + dt.timedelta(hours=9)).isoformat(timespec="minutes")
            continue
        status = "done" if (ROOT / "videos" / vid / "data.js").exists() else "new"
        queue[vid] = dict(title=g["title"], status=status, listened_sec=round(g["sec"]),
                          first_seen=(g["last"] + dt.timedelta(hours=9)).isoformat(timespec="minutes"))
        if status == "new":
            added.append(vid)

    save(QUEUE, queue)
    save(TRACK, dict(last_check=now.isoformat(timespec="seconds")))
    print(f"확인 범위: {since + dt.timedelta(hours=9):%m-%d %H:%M} 이후 (한국 시각)")
    print(f"새로 추가: {len(added)}곡")
    pending = [(vid, q) for vid, q in queue.items() if q.get("status") == "new"]
    print(f"만들 차례(new): {len(pending)}곡")
    for vid, q in sorted(pending, key=lambda x: x[1].get("first_seen") or ""):
        print(f"  {vid}  {q['listened_sec']:>4}초  {q['title']}")


if __name__ == "__main__":
    main()
