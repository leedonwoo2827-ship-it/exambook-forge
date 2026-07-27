---
name: build-deck
description: 회차의 lesson JSON을 pressplay식 밝은 deck.html 슬라이드 + 05/<회차>/ 번들(리모션 _series 대본 + review.json 스켈레톤)로 만들어야 할 때. 일반영상(#3 chodangi-mp4 캡처)과 리모션영상(클로드 데스크탑)의 공통 슬라이드 원본을 집필한다.
metadata:
  group: 자격시험 파이프라인
  stage: 슬라이드/번들
  produces: 05/<회차>/source/deck.html · script/<회차>_script.json · review.json
---

# build-deck (deck.html 슬라이드 + 05 번들)

## When to use
- 회차 영상을 만들기 직전, `04/lesson_mNN.json`으로부터 편집 가능한 밝은 HTML 슬라이드와
  per-회차 번들을 만들 때. 산출물은 #3(일반영상 캡처)와 리모션(키네틱)의 공통 입력.

## 입력
- `04/lesson_mNN.json` (build-video-json 산출) + 회차 데이터 `<book>/_rounds/mNN.json`.
- 규약: `${CLAUDE_PLUGIN_ROOT}/references/deck-conventions.md`,
  `${CLAUDE_PLUGIN_ROOT}/references/pipeline-output-structure.md`.

## 절차
1. **번들 골격 생성**:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/bundle.py" --book "<book>" --round m01`
   → `05/m01/{source,images,audio,subtitles,script,draft}` 생성,
     `source/`에 `lesson_m01.json` 복사 + `_deck.css`/`_deck.js` 복사,
     `script/m01_script.json`(리모션 _series) + `review.json` 스켈레톤 생성,
     `source/deck.html` **스텁**(표지/섹션/문제/해설 슬롯) 생성.
2. **deck.html 집필**: 스텁을 열어 `deck-conventions.md`에 따라 슬라이드를 채운다.
   - 슬라이드 1장 = 씬 1개, 순서 = `review.json.slides[]` 순서(= `slide_%02d.png`/`scene_%02d.wav` 인덱스).
   - 문제 씬(`.qcard`: `.qnum`·`.qtext`·`passage`/`pre.sql`/`table`/`figure`·`.choices`) →
     해설 씬(`.answer-badge`·`.choice.correct`·`.explain`) 순. 과목 바뀌면 섹션 슬라이드.
   - **밝은 배경 유지**, 원문자 직접입력 금지(`.choice .marker` 숫자), SVG는 `svg-diagram` 산출을 `figure>svg`로 인라인.
   - deck 텍스트 = **자막 원문 표기**. 발음(낭독)은 `review.json.slides[].narration_text`/lesson `explanation_speech`가 담당(deck엔 안 넣음).
3. **review.json 확인**: 슬라이드 수 = 씬 수 = deck 슬라이드 수가 일치하는지, `heading`/`narration`/`narration_text`가 채워졌는지 확인(시간·비디오 필드는 #3가 채움).
4. **핸드오프 안내**:
   - 일반영상: #3에서 `render.bat m01` → deck 캡처 + Supertonic3 + ffmpeg → `05/m01/draft/m01.static.mp4`.
   - 리모션: 클로드 데스크탑에서 `05/m01/script/m01_script.json`으로 `draft/m01.motion.mp4` 생성.

## 산출
- `05/m01/source/deck.html` (+ `_deck.css`/`_deck.js`, `lesson_m01.json` 복사)
- `05/m01/script/m01_script.json` (리모션 _series)
- `05/m01/review.json` (스켈레톤 — #3/리모션이 나머지 채움)

## 주의
- 캡처/TTS/자막/ffmpeg(일반영상)와 리모션 렌더는 이 스킬 범위 밖. 여기선 deck.html + 번들 골격까지.
- 슬라이드 수와 씬 수가 어긋나면 캡처-오디오 인덱스가 밀린다 — 반드시 1:1 유지.
- `04/lesson_mNN.json`은 계속 #3의 대본/음성 컴파일 입력으로 유지된다(deck은 화면, lesson은 텍스트/음성).
