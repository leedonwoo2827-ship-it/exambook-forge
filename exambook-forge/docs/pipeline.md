# 파이프라인 규약 (ocr-output 폴더 단계)

책 루트(`ocr-output-*`)는 단계별 폴더로 앱 간 연결을 맞춘다. exambook-forge는 `01/`을 읽고 `02/03/04/`를 쓴다.

| 폴더 | 단계 | 내용 | 담당 |
|---|---|---|---|
| `00/` | (선택) 원본 | 렌더 이미지/원시 OCR | ocr 툴 |
| `01/` | OCR → 문제 MD | 문항별 구조화 MD (입력) | `260723-ocr` |
| `02/` | 집필 | **자사 모의고사 문제 MD** + `_index.json` + `difficulty_stats.json` + `assets/*.svg` | **exambook-forge** |
| `03/` | 요약 | **요약원고** `summary_*.html`(기본)+`.md` + `assets/*.svg` | **exambook-forge** |
| `04/` | 영상 대본 | **문제 영상 대본** `lesson_*.json` + `04/assets/*.svg`(도형 동반) (chodangi-mp4 입력) | **exambook-forge** |
| `05/` | 번들/영상 | per-회차 번들 `05/<회차>/{source,images,audio,subtitles,script,draft} + review.json` (밝은 deck.html 슬라이드 + 리모션 _series + 일반/리모션 영상) | **exambook-forge**(골격) → **chodangi-mp4**(일반영상) → 리모션(모션) |
| `_rounds/` | (작업) | 회차 데이터 `mNN.json` (build 입력, 단일 진실 원천) | **exambook-forge** |

> `04/`·`05/`는 원래 파이프라인 README(00~03)에 없던 새 단계다. 스킬이 처음 만들 때
> 책 루트 `README.md`에 해당 행을 추가한다.
> **05 번들 구조/파일명/review.json/_series 규약은 [`../references/pipeline-output-structure.md`](../references/pipeline-output-structure.md)가 단일 진실 원천이다.**

## 책 루트 & 권한
- 기본 책 루트: 작업공간 상위의 `ocr-output-260723` 자동 탐색(없으면 사용자에게 경로 질의).
- Claude Desktop 코웍에서 **책 루트 폴더에 읽기/쓰기 권한**을 부여해야 한다.
- 파일 생성 직전 **한 번** "02/03/04에 씁니다" 동의를 받는다(이후 단계에서 반복 질문하지 않음).
- `02/03/04/_rounds`는 없으면 헬퍼/스킬이 자동 생성(미리 만들 필요 없음).

## 파이프라인 #3(영상 렌더) 연동 규약
- lesson JSON 텍스트 필드는 **순수 텍스트**(마크다운 금지), `choices`는 **원문자 없이 내용만**.
- **보이는 텍스트**(`question`/`explanation`, 원문 표기) ↔ **들리는 텍스트**(`explanation_speech`, 발음 표기) 분리.
- 참조 SVG는 `04/assets/`에 동반 복사(도형이 04만 봐도 따라오게). deck.html의 `figure>svg`로 인라인.
- **유튜브 업로드 글은 #3가 렌더 후 생성**(챕터 타임스탬프는 렌더 후 확정) — #2는 JSON에 넣지 않음.

## 05 번들 / 슬라이드 / 리모션 연동 규약
- `build-deck` 스킬 + `scripts/bundle.py`가 `04/lesson_mNN.json`으로 `05/mNN/` 번들을 만든다:
  밝은 `source/deck.html`(슬라이드 원본) + `script/mNN_script.json`(리모션 _series) + `review.json` 스켈레톤.
- **슬라이드 = deck.html**(1920×1080 고정). #3(chodangi-mp4)가 각 `.slide`를 캡처 → `images/slide_%02d.png`.
- **일반영상**(리모션 전): #3가 deck 캡처 + Supertonic3(자막/음성 **최종 OK**) + ffmpeg → `draft/mNN.static.mp4` + `mNN.ko.vtt`.
- **리모션영상**(키네틱): 클로드 데스크탑이 `script/mNN_script.json`으로 `draft/mNN.motion.mp4` 생성. 무거운 스크래치는 책 루트 밖.
- 씬 순서 = deck 캡처 슬라이드 순서 = `slide_%02d.png` = `scene_%02d.wav` = `review.json.slides[]` **1:1 일치**.
- 단일 진실 원천: [`../references/pipeline-output-structure.md`](../references/pipeline-output-structure.md), 슬라이드 규약: [`../references/deck-conventions.md`](../references/deck-conventions.md).

## 파일명 규약
- 문제 MD: `02/mNN-01.md` ~ `mNN-50.md` (자사 회차는 `m` 접두, 원본 기출은 `01-`~`07-`)
- 영상 대본: `04/lesson_mNN.json`
- 요약: `03/summary_{과목}.html` / `.md`
- 회차 데이터: `_rounds/mNN.json`
- 05 번들: `05/mNN/source/deck.html` · `script/mNN_script.json` · `review.json` · `images/slide_%02d.png` · `audio/scene_%02d.wav` · `subtitles/subtitles.srt` · `draft/mNN.{static,motion}.mp4` · `draft/mNN.ko.vtt`
