# 매일 자동 생성 작업 지침

예약 작업(매일)이 이 파일을 그대로 따른다. 작업 폴더: `C:\Users\kim yu shin\Desktop\youtube-study`.
학습자: 한국어 화자, 중국어 HSK 5급 상위~6급 하위. 단어보다 **문장 단위** 공부를 원한다.

## 순서

1. 새로 들은 곡 찾기
   ```
   python tools/track_chrome.py
   ```
   `만들 차례(new)` 목록이 나온다. 없으면 7단계로 가서 "새 곡 없음"으로 보고하고 끝낸다.

2. 하루 최대 **5곡**만 만든다. `state/queue.json`에서 status가 `new`인 곡 중 `listened_sec`가 큰 순서로 고른다. 나머지는 다음 날로 남긴다.

3. 곡마다 정보와 설명란을 받는다 (설명란은 이 PC에만 저장되고 Git에서 제외된다).
   ```
   python tools/fetch_video.py "https://www.youtube.com/watch?v=<ID>" --description
   ```
   `videos/<ID>/meta.json`, `videos/<ID>/description.txt`(가사·병음·해석이 있는 경우가 많음)를 읽는다.

4. 중국어(표준어·광둥어)로 부르는 노래인지 판단한다. 아니면(한국어 곡, 연주곡, 가사 없는 DJ 리믹스 등) 건너뛴다.
   ```
   python tools/track_chrome.py --mark <ID> skipped "한국어 커버" 
   ```

5. 중국어 노래면 `videos/<ID>/data.js`를 쓴다. 형식은 `videos/DZimlVK9Ybs/data.js`와 똑같이 맞춘다 (`window.STUDY = { ...JSON... };`, 안쪽은 반드시 유효한 JSON). 그다음 `template/song.html`을 `videos/<ID>/index.html`로 복사하고 `python tools/track_chrome.py --mark <ID> done`.

   | 키 | 내용 |
   |---|---|
   | id, title, artist, channel, duration | meta.json 기준. title은 중국어 곡명만 |
   | generated | 오늘 날짜 YYYY-MM-DD |
   | intro | 곡 분위기와 이 곡에서 배울 문형 요약 1~2문장 |
   | patterns | 가사에 쓰인 문형 **8~12개**. 각 `[문형, 설명, [[중국어, 병음, 한국어] 1~2개], 포인트]` |
   | nuance | 이 곡 표현과 관련된 비슷한 말 비교 3~6개 `[제목, 설명, 예문]` |
   | spoken | 직접 지은 글말·시적 문장 ↔ 구어 짝 3~5개 |
   | notes | 설명란 번역·병음·한글 표기 오류 `[낱말, 정확한 뜻·소리, 다른 점]`. 없으면 빈 배열 |
   | ref | HSK 5급 이상·문어 단어 8~15개 `[단어, 병음, 뜻]` |

   지킬 것:
   - **가사 줄을 옮겨 적지 않는다.** 예문·글말 문장은 모두 새로 지은 문장이어야 한다. 가사와 겹쳐도 되는 건 단어·짧은 어구(4자 이하 성어 포함)뿐이다. notes의 낱말 칸도 낱말·짧은 어구만.
   - 수준: HSK 5~6급. 복문, 서면어, 성어, 보어를 섞은 15~30자 문장. 기초 단어 뜻풀이는 하지 않는다.
   - 병음은 성조 변화를 적용해 실제 읽는 대로 (不再 búzài, 一个 yí ge, 找不到 zhǎo bu dào), 경성 표기.
   - 번체 가사여도 예문은 간체로 쓴다.
   - 한국어 해석은 자연스러운 구어체.

6. 목록 페이지를 다시 만든다.
   ```
   python tools/build_index.py
   ```

7. 보고: 만든 곡(제목·문형 수), 건너뛴 곡(이유), 남은 대기 곡 수를 3~6줄로 정리한다. 실패한 곡이 있으면 이유를 적고 status는 `new`로 둔다.

## 하지 않는 것
- Git 커밋·푸시, 파일 삭제, 대기열 외 방문 기록 저장.
- `description.txt` 내용을 data.js나 보고에 옮겨 적기.
