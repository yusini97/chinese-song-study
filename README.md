# youtube-study

Chrome에서 들은 중국어 노래를 매일 모아 HSK 5~6급 **문장 공부** 자료로 만드는 개인 프로젝트.

- 시작 페이지: `index.html` (곡 목록, 다음에 만들 곡, 건너뛴 곡)
- 곡 페이지: `videos/<영상ID>/index.html` — 문형·예문, 뉘앙스 비교, 글말↔구어, 작문 연습, 내 문장 카드(설명란 가사를 붙여 넣으면 줄별 카드), 설명란 오류, 참고 단어

## 자동 생성

예약 작업 「【매일】중국어 노래 문장 공부 자료 만들기」가 매일 22:30쯤 `TASK.md`를 따라 돈다.
Claude 앱이 꺼져 있으면 다음에 켤 때 실행된다.

1. `tools/track_chrome.py` — 모든 Chrome 프로필의 방문 기록에서, 제목에 한자가 2자 이상이고 60초 이상 연(또는 지금 열려 있는) YouTube 영상을 `state/queue.json`에 넣는다
2. 하루 최대 5곡(들은 시간이 긴 순)에 대해 `tools/fetch_video.py --description`으로 정보를 받고, 중국어 노래인지 판단해 `videos/<ID>/data.js`를 쓴다
3. `tools/build_index.py`로 목록 갱신

손으로 쓸 때:
```
python tools/track_chrome.py --now                 # 지금 듣는 곡 보기
python tools/track_chrome.py                       # 새 곡을 대기열에
python tools/track_chrome.py --mark ID skipped 이유  # 대기열에서 빼기
python tools/build_index.py
```

## 구조

- `assets/study.css`, `assets/study.js` — 곡 페이지 공통 틀. `data.js`의 `window.STUDY`를 그린다
- `template/song.html` — 곡 페이지 껍데기 (`videos/<ID>/index.html`로 복사)
- `tools/fetch_video.py` — 영상 정보·자막·설명란 저장, 자막이 없으면 `--whisper`로 받아쓰기
- `state/` — 대기열과 마지막 확인 시각 (Git 제외)

## 한계와 주의

- 방문 기록 기준이라 끝까지 들었는지는 모른다. 들은 시간은 탭이 열려 있던 시간이다.
- 제목에 한자가 없는 중국어 노래는 놓친다. 제목에 한자만 있는 한국어 곡은 생성 단계에서 건너뛴다.
- 노래 가사는 저작권이 있어 페이지에 옮기지 않는다. 받은 설명란·자막은 개인 공부용이며 Git에서 제외한다.
- 문장·병음·해석은 AI가 작성했고 원어민 검수 전이다.
