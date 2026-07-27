/* 공유 덱 컨트롤러 — 좌우 내비 · 풀스크린 · 페이지카운터 · 푸터 자동주입.
   슬라이드는 1920×1080 고정폭. 캡처(#3)는 각 .slide 를 개별 스크린샷하므로
   이 스크립트 없이도 렌더된다(내비 UI 는 캡처 시 숨겨짐). */
(function () {
  const deck = document.getElementById('deck');
  if (!deck) return;
  const slides = [...deck.querySelectorAll('.slide')];
  const prev = document.getElementById('prev');
  const next = document.getElementById('next');
  const fs = document.getElementById('fs');
  const title = deck.dataset.title || document.title || '';

  // 본문(.content) 슬라이드에 푸터 자동 주입 (없을 때만)
  slides.forEach((s) => {
    if (s.classList.contains('content') && !s.querySelector('.s-foot')) {
      const f = document.createElement('div');
      f.className = 's-foot';
      f.innerHTML = `<span class="fl"><b>${title}</b> · EXAM BOOK</span><span class="pg"></span>`;
      s.appendChild(f);
    }
  });

  const pgs = [...deck.querySelectorAll('.pg')];
  const slideW = () => (slides[0] ? slides[0].getBoundingClientRect().width : deck.clientWidth) || 1;
  const idx = () => Math.round(deck.scrollLeft / slideW());

  function go(i) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    slides[i].scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
  }
  function sync() {
    const i = idx();
    if (prev) prev.toggleAttribute('disabled', i === 0);
    if (next) next.toggleAttribute('disabled', i === slides.length - 1);
    pgs.forEach((p) => {
      const s = p.closest('.slide');
      p.textContent = (slides.indexOf(s) + 1) + ' / ' + slides.length;
    });
  }
  deck.addEventListener('scroll', sync);
  if (prev) prev.onclick = () => go(idx() - 1);
  if (next) next.onclick = () => go(idx() + 1);

  addEventListener('keydown', (e) => {
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(idx() + 1); }
    if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); go(idx() - 1); }
    if (e.key === 'f' || e.key === 'F') toggleFs();
  });
  deck.addEventListener('wheel', (e) => {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { e.preventDefault(); deck.scrollLeft += e.deltaY; }
  }, { passive: false });

  function toggleFs() {
    const el = document.documentElement;
    if (!document.fullscreenElement) {
      (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
    } else {
      document.exitFullscreen();
    }
  }
  if (fs) {
    fs.onclick = toggleFs;
    document.addEventListener('fullscreenchange', () => {
      fs.textContent = document.fullscreenElement ? '⛶ 나가기' : '⛶ 전체화면';
    });
  }

  sync();
  const jump = parseInt(location.hash.slice(1), 10);
  if (jump) { deck.scrollLeft = (jump - 1) * slideW(); setTimeout(sync, 60); }
})();
