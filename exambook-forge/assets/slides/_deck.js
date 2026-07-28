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
      f.innerHTML = `<span class="fl"><b>${title}</b></span><span class="pg"></span>`;
      s.appendChild(f);
    }
  });

  const pgs = [...deck.querySelectorAll('.pg')];

  // 화면 미리보기 전용: 창이 1920 보다 좁으면 통째로 축소해 가로형 한 장이 다 보이게 한다.
  // 캡처(#3)는 뷰포트가 정확히 1920×1080 이라 배율 1 — 캡처 결과에는 영향이 없다.
  function fit() {
    const z = Math.min(1, window.innerWidth / 1920);
    document.body.style.zoom = z >= 1 ? '' : z;
  }
  addEventListener('resize', fit);
  fit();

  // zoom 이 걸리면 getBoundingClientRect 와 scrollLeft 의 단위가 어긋난다 →
  // 둘 다 레이아웃 좌표인 offsetLeft 로 현재 슬라이드를 찾는다.
  const idx = () => {
    let best = 0, min = Infinity;
    slides.forEach((s, i) => {
      const d = Math.abs(s.offsetLeft - deck.scrollLeft);
      if (d < min) { min = d; best = i; }
    });
    return best;
  };

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
  if (jump && slides[jump - 1]) { deck.scrollLeft = slides[jump - 1].offsetLeft; setTimeout(sync, 60); }
})();
