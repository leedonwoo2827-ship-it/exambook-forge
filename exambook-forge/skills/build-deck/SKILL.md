---
name: build-deck
description: 회차의 lesson JSON을 pressplay식 밝은 deck.html 슬라이드 + 05/<회차>/ 번들(리모션 _series 대본 + review.json 스켈레톤)로 만들어야 할 때. bundle.py 가 헤드리스 크로미움으로 높이를 재서 페이지를 나눠 주므로 잘림 없는 슬라이드가 바로 나온다. 일반영상(#3 chodangi-mp4 캡처)과 리모션영상(클로드 데스크탑)의 공통 슬라이드 원본.
metadata:
  group: 자격시험 파이프라인
  stage: 슬라이드/번들
  produces: 05/<회차>/source/deck.html · script/<회차>_script.json · review.json
---

# build-deck (deck.html 슬라이드 + 05 번들)

## When to use
- 회차 영상을 만들기 직전, `04/lesson_mNN.json`으로부터 밝은 HTML 슬라이드와
  per-회차 번들을 만들 때. 산출물은 #3(일반영상 캡처)와 리모션(키네틱)의 공통 입력.

## 입력
- `04/lesson_mNN.json` (build-video-json 산출) + 회차 데이터 `<book>/_rounds/mNN.json`.
- 규약: `${CLAUDE_PLUGIN_ROOT}/references/deck-conventions.md`,
  `${CLAUDE_PLUGIN_ROOT}/references/pipeline-output-structure.md`.

## 절차
1. **번들 생성** (이 한 줄이 전부 — deck.html 을 손으로 집필하지 않는다):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/bundle.py" --book "<book>" --round m01 --chunk 10`
   → `05/m01-1..m01-5/{source,images,audio,subtitles,script,draft}` 생성,
     `source/`에 **페이지 분할이 끝난 `deck.html`** + `lesson_*.json` 복사 + `_deck.css`/`_deck.js`,
     `script/<회차>_script.json`(리모션 _series) + `review.json`.
   - **첫 실행 전 1회 필수**: `pip install playwright && python -m playwright install chromium`
     없으면 `bundle.py` 가 **멈춘다**(경고가 아니라 중단). 예전에는 분할을 건너뛰고
     경고만 남겼는데, 그러면 한 슬라이드에 내용을 전부 밀어 넣어 **보기 박스가 붙고
     아래가 잘린 채로** deck·PNG·영상까지 나갔다. 경고는 로그에 묻히고, 잘린 것은
     영상을 보고 나서야 알게 되어 그 회차를 다시 만들어야 했다.
     분할·캡처를 정말 건너뛰려면 `--no-paginate` / `--no-capture` 로 명시한다.
   - 슬라이드 PNG 는 **2배 해상도(3840×2160)로 찍어** 1080p 로 내려보낸다.
     1배로 찍으면 h.264 압축에서 글자가 뭉갠다.
2. **결과 확인**: `05/<회차>/source/deck.html` 을 브라우저로 열어 넘겨 본다.
   실행 로그의 `[warn]` 이 없으면 잘린 슬라이드가 없다는 뜻.
   `[warn] 슬라이드 N 이 …px 넘칩니다` 가 뜨면 **lesson 의 해당 지문/해설을 줄여야 한다**
   (분할·축소로도 안 들어가는 분량).
3. **핸드오프**:
   - 일반영상: **XAM LOCAL(#4) 의 `#/video` 화면**에서 렌더 → `05/m01-1/draft/m01-1.static.mp4`.
     (2026-08-03 부터 #3 렌더 엔진이 XAM LOCAL 안 `vendor/chodangi/` 로 들어왔다.
      `render.bat` 은 쓰지 않는다 — BOOK 경로가 하드코딩돼 있고 별도 저장소도 없어졌다.
      자막 시간축 수정 4건도 그 소스에 반영돼 있다.)
   - 리모션: 클로드 데스크탑에서 `05/m01-1/script/m01-1_script.json`으로 `draft/*.motion.mp4`.

## bundle.py 가 자동으로 하는 것
- **페이지 분할**: 헤드리스 크로미움으로 블록별 실제 높이를 재서 안전영역(1080 − 패딩 − 푸터)에
  맞게 페이지를 나눈다. 발문/정답 배지는 페이지마다 상단 반복, **보기 4개는 절대 쪼개지 않는다**.
  그래도 넘치면 `.dense` → `.dense2` 축소, 마지막 수단으로만 잘라내고 안내문을 남긴다.
- **마크다운 렌더**: question/passage/explanation 안의 `**볼드**`·`` `코드` ``·불릿·번호목록·
  표(`| a | b |`)·코드펜스(```sql)를 HTML 로. 구조화 `table`/`sql` 필드도 `<table>`/`<pre class="sql">`.
- **씬 생성**: `script.json`/`review.json` 의 씬을 **분할된 슬라이드에서 파생**시킨다
  (→ `.slide` 수 == capture 씬 수가 항상 성립). 카운트다운은 그 문항의 마지막 문제 페이지 뒤.
- **페이지별 낭독 분배**: 발문 낭독은 1페이지에 통째로, 이후 페이지는 그 페이지에 보이는
  지문·보기를 읽는다. 표/SQL 뿐인 페이지는 짧은 안내문("표를 확인해 보세요.").
  해설은 손으로 다듬은 `explanation_speech` 를 표시 분량 비율로 문장 단위 분배.
- **브랜딩 제거**: 표지 eyebrow·푸터의 "EXAM BOOK", `round` 의 "자사 " 접두를 뺀다.

## 주의
- 캡처/TTS/자막/ffmpeg(일반영상)와 리모션 렌더는 이 스킬 범위 밖.
- `deck.html` 을 손으로 고쳤다면 `bundle.py` 를 다시 돌릴 때 덮어써진다(항상 재생성).
  내용을 바꾸려면 `04/lesson_mNN.json` 을 고치고 다시 생성하는 게 원칙.
- 슬라이드 수와 씬 수가 어긋나면 #3 `render.bat` 이 **중단**한다(이미지-음성이 밀린 영상 방지).
  bundle.py 가 항상 둘을 같이 만들므로, 어긋났다면 deck.html 만 따로 손댄 경우다.
- `04/lesson_mNN.json`은 계속 #3의 대본/음성 컴파일 입력으로 유지된다(deck은 화면, lesson은 텍스트/음성).
