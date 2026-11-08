// 곡별 공부 페이지 렌더러. 같은 폴더의 data.js가 window.STUDY를 정의한다.
// STUDY = {id, title, artist, channel, duration, intro,
//   patterns:[[문형, 설명, [[중국어, 병음, 한국어], ...], 포인트]],
//   nuance:[[비교 제목, 설명, 예문]], spoken:[[글말, 구어]],
//   notes:[[낱말, 정확한 뜻, 설명란과 다른 점]], ref:[[단어, 병음, 뜻]]}
(function () {
  const D = window.STUDY;
  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const say1 = z => `<button class="ghost mini" data-say="${esc(z)}">🔊</button>`;
  const sent = ([z, p, k]) => `<div class="sent"><div class="zh">${esc(z)} ${say1(z)}</div><div class="py">${esc(p || "")}</div><div class="ko">${esc(k || "")}</div></div>`;
  const has = k => D[k] && D[k].length;

  document.title = `${D.title} 문장 공부`;
  const sections = [
    ["how", "공부 순서", true], ["pattern", `문형 ${(D.patterns || []).length}개`, has("patterns")],
    ["nuance", "뉘앙스 비교", has("nuance")], ["spoken", "글말 ↔ 구어", has("spoken")],
    ["write", "작문 연습", has("patterns")], ["mine", "내 문장 카드", true],
    ["notes", "설명란 주의", has("notes")], ["ref", "참고 단어", has("ref")]];
  $("#app").innerHTML = `
<p><a href="../../index.html">← 곡 목록</a></p>
<h1><span class="zh">${esc(D.title)}</span> 문장 공부 <span class="muted">HSK 5~6</span></h1>
<p class="muted">${esc([D.artist, D.channel && "채널 " + D.channel, D.duration].filter(Boolean).join(" · "))}</p>
<p class="muted">${esc(D.intro || "")} 가사 전문은 저작권 때문에 싣지 않는다. 가사는 영상 설명란에서 보고, 설명란 가사를 <a href="#mine">내 문장 카드</a>에 붙여 넣으면 줄마다 카드로 만든다.</p>
<nav>${sections.filter(s => s[2]).map(([id, t]) => `<a href="#${id}">${t}</a>`).join("")}</nav>
<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/${esc(D.id)}" title="영상" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>
<div class="tools"><a href="https://www.youtube.com/watch?v=${esc(D.id)}" target="_blank" rel="noopener" class="muted">YouTube에서 열기</a>
<button class="ghost" id="tpy">병음 가리기</button><button class="ghost" id="tko">해석 가리기</button><span class="muted" id="ttsinfo"></span></div>
<h2 id="how">공부 순서</h2>
<ol>
<li>설명란 가사를 <b>내 문장 카드</b>에 붙여 넣고, 노래를 들으며 해석을 가린 채 줄마다 뜻을 먼저 말해 본다.</li>
<li><b>문형</b>에서 가사에 쓰인 구조를 확인하고 예문을 소리 내 읽는다(🔊).</li>
<li><b>뉘앙스 비교</b>와 <b>글말 ↔ 구어</b>로 비슷한 표현의 차이와 쓰임을 정리한다.</li>
<li><b>작문 연습</b>: 한국어를 보고 중국어로 먼저 말하거나 쓴 뒤 답을 연다. 틀린 문장만 다시 돈다.</li>
</ol>
${has("patterns") ? `<h2 id="pattern">문형 ${D.patterns.length}개</h2><p class="muted">가사에 나오는 구조를 바탕으로 새로 만든 문장.</p>` +
      D.patterns.map(([t, d, ss, pt], i) => `<div class="box"><h3>${i + 1}. <span class="zh s">${esc(t)}</span></h3><p class="muted">${esc(d)}</p>${ss.map(sent).join("")}${pt ? `<div class="note">포인트: ${esc(pt)}</div>` : ""}</div>`).join("") : ""}
${has("nuance") ? `<h2 id="nuance">뉘앙스 비교</h2>` + D.nuance.map(([t, d, ex]) => `<div class="box"><h3 class="zh s">${esc(t)}</h3><p>${esc(d)}</p>${ex ? `<p class="zh s">${esc(ex)} ${say1(ex)}</p>` : ""}</div>`).join("") : ""}
${has("spoken") ? `<h2 id="spoken">글말 ↔ 구어</h2><p class="muted">왼쪽(직접 지은 글말 문장)을 보고 오른쪽 구어를 먼저 말해 본다.</p><table><thead><tr><th>글말·시적</th><th>구어</th></tr></thead><tbody>` +
      D.spoken.map(([a, b]) => `<tr><td class="zh s">${esc(a)}</td><td class="zh s ko">${esc(b)} ${say1(b)}</td></tr>`).join("") + `</tbody></table>` : ""}
${has("patterns") ? `<h2 id="write">작문 연습</h2>
<div class="tools"><button id="wnew">섞어서 시작</button><button class="ghost" id="wshow">답 보기</button><button class="ghost" id="wok">맞음</button><button class="ghost" id="wbad">다시</button><span class="muted" id="wpos"></span></div>
<div class="card"><div class="q ko" id="wq"></div><div id="wa" hidden><p class="zh" id="wz"></p><p class="py" id="wp"></p><button class="ghost mini" id="wsay">🔊</button></div></div>` : ""}
<h2 id="mine">내 문장 카드</h2>
<p class="muted">설명란 가사(또는 아무 중국어 문장)를 붙여 넣는다. 빈 줄로 나뉜 묶음마다 한자 줄·병음 줄·한자 뒤 한국어 줄(해석)을 찾아 카드로 만든다. 한자 앞의 한글 발음 줄은 건너뛴다. 붙여 넣은 내용은 이 브라우저에만 저장된다.</p>
<textarea id="paste" placeholder="여기에 붙여 넣기"></textarea>
<div class="tools"><button id="mk">카드 만들기</button><button class="ghost" id="clr">지우기</button><span class="muted" id="mcount"></span></div>
<div id="ml"></div>
${has("notes") ? `<h2 id="notes">설명란 번역·표기 주의</h2><table><thead><tr><th>낱말</th><th>정확한 뜻·소리</th><th>설명란과 다른 점</th></tr></thead><tbody>` +
      D.notes.map(([w, r, x]) => `<tr><td class="zh s">${esc(w)}</td><td>${esc(r)}</td><td>${esc(x)}</td></tr>`).join("") + `</tbody></table>` : ""}
${has("ref") ? `<details id="ref"><summary>참고 단어 (HSK 5~6급 이상·문어 표현)</summary><table><thead><tr><th>단어</th><th>뜻</th></tr></thead><tbody>` +
      D.ref.map(([w, p, k]) => `<tr><td><span class="zh s">${esc(w)}</span> <span class="py">${esc(p)}</span></td><td class="ko">${esc(k)}</td></tr>`).join("") + `</tbody></table></details>` : ""}
<p class="muted" style="margin-top:40px">문장·병음·해석은 Claude가 작성했고 원어민 검수 전이다${D.generated ? ` (${esc(D.generated)} 생성)` : ""}. 🔊는 브라우저 중국어 음성을 쓴다.</p>`;

  // 음성
  let zhVoice = null;
  function loadVoice() {
    const vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
    zhVoice = vs.find(v => /^zh(-|_)?CN/i.test(v.lang)) || vs.find(v => /^zh/i.test(v.lang)) || null;
    $("#ttsinfo").textContent = window.speechSynthesis ? (zhVoice ? "🔊 " + zhVoice.name : "이 브라우저에 중국어 음성이 없어 🔊가 소리 나지 않을 수 있음") : "";
  }
  if (window.speechSynthesis) { loadVoice(); speechSynthesis.onvoiceschanged = loadVoice; }
  function say(t) {
    if (!window.speechSynthesis) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(t); u.lang = "zh-CN"; if (zhVoice) u.voice = zhVoice; u.rate = 0.85;
    speechSynthesis.speak(u);
  }
  document.addEventListener("click", e => { const b = e.target.closest("[data-say]"); if (b) say(b.dataset.say); });
  $("#tpy").onclick = () => document.body.classList.toggle("hide-py");
  $("#tko").onclick = () => document.body.classList.toggle("hide-ko");

  // 작문 연습: 문형 예문 전체에서 출제, '다시'는 뒤로 보내 다시 나온다
  const shuf = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  if (has("patterns")) {
    const W = D.patterns.flatMap(p => p[2]); let wq = [], right = 0;
    const show = () => {
      if (!wq.length) { $("#wq").textContent = "모두 맞혔다! 섞어서 다시 시작할 수 있다."; $("#wa").hidden = true; $("#wpos").textContent = `맞힘 ${right}`; return; }
      const [z, p, k] = W[wq[0]];
      $("#wq").textContent = k; $("#wz").textContent = z; $("#wp").textContent = p; $("#wsay").dataset.say = z;
      $("#wa").hidden = true; $("#wpos").textContent = `남은 문장 ${wq.length} · 맞힘 ${right}`;
    };
    $("#wnew").onclick = () => { wq = shuf(W.map((_, i) => i)); right = 0; show(); };
    $("#wshow").onclick = () => { $("#wa").hidden = false; };
    $("#wok").onclick = () => { if (wq.length) { wq.shift(); right++; show(); } };
    $("#wbad").onclick = () => { if (wq.length) { wq.push(wq.shift()); show(); } };
    $("#wnew").click();
  }

  // 내 문장 카드 (곡마다 따로 이 브라우저 localStorage에만 저장)
  const HAN = /[一-鿿]/, HANGUL = /[가-힣]/, TONE = /[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]/i;
  const KEY = "mine:" + D.id;
  function parse(text) {
    const out = [];
    for (const blk of text.split(/\n\s*\n/)) {
      const ls = blk.split("\n").map(s => s.trim()).filter(Boolean);
      const zi = ls.findIndex(l => HAN.test(l) && !HANGUL.test(l));
      if (zi < 0) continue;
      const py = ls.find(l => !HAN.test(l) && !HANGUL.test(l) && TONE.test(l)) || "";
      const ko = ls.slice(zi + 1).reverse().find(l => HANGUL.test(l)) || "";
      out.push([ls[zi], py, ko]);
    }
    return out;
  }
  function render(text) { const cs = parse(text); $("#ml").innerHTML = cs.map(sent).join(""); $("#mcount").textContent = cs.length ? `${cs.length}개 카드` : ""; }
  $("#mk").onclick = () => { const t = $("#paste").value; render(t); try { localStorage.setItem(KEY, t); } catch (e) {} };
  $("#clr").onclick = () => { $("#paste").value = ""; render(""); try { localStorage.removeItem(KEY); } catch (e) {} };
  try { const t = localStorage.getItem(KEY); if (t) { $("#paste").value = t; render(t); } } catch (e) {}
})();
