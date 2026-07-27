# 파이프라인 출력구조 규약 (세 툴 공통)

> 이 문서는 기출 문제집 → 해설영상 파이프라인의 **단일 진실 원천**이다.
> 세 툴(#1 OCR · #2 exambook-forge · #3 chodangi-mp4)과 리모션(클로드 데스크탑)이 모두
> 이 규약을 따른다. 각 단계의 **출력 = 다음 단계의 입력**이다.
> (pressplay `docs/파이프라인-아웃풋-구조.md`의 per-항목 번들 구조를 기출 파이프라인에 이식한 것.)

## 툴 & 단계 개요

| # | 레포 | 읽기 | 쓰기 | 역할 |
|---|---|---|---|---|
| #1 | `260723-ocr` | 원본 이미지 `00/` | `01/` | OCR → 문항별 구조화 MD |
| #2 | `260724-munje-sumary` / **exambook-forge** | `01/` | `02/ 03/ 04/` + `05/<회차>/source·script·review.json` | 집필: 문제·요약·영상대본·**deck.html 슬라이드**·리모션 대본 |
| #3 | `260724-chodangi-mp4` / **chodangi-mp4-forge** | `04/` + `05/<회차>/source` | `05/<회차>/images·audio·subtitles·draft` + review.json 갱신 | 렌더: deck 캡처 + Supertonic3 자막/음성 + ffmpeg → **일반영상** |
| — | 리모션 (클로드 데스크탑) | `05/<회차>/script·source·audio` | `05/<회차>/draft/*.motion.mp4` + review.json 갱신 | 키네틱(모션) 영상 |

## 책 루트 스테이지 폴더

```
ocr-output-*/
  00/  (선택) 원본 이미지 / 원시 OCR            ← #1
  01/  문항별 구조화 MD                          ← #1
  02/  문제 MD + _index.json + difficulty_stats.json + assets/*.svg   ← #2
  03/  요약 summary_{과목}.html/.md + assets/*.svg                     ← #2
  04/  lesson_{회차}.json (영상 대본) + assets/*.svg                   ← #2  (#3 입력)
  05/  <회차>/ per-회차 번들 (아래)             ← #2 골격 → #3 채움 → 리모션 보강
```

## 05/ per-회차 번들 (핵심 규약)

`<회차>` = 회차코드 `mNN`(번호 접두 없음 — 기존 회차코드와 일치). 하위폴더 규율로 복잡도를 구획한다.

```
05/mNN/
  source/       deck.html          ← 슬라이드 원본(HTML, 편집 가능)          [#2]
                lesson_mNN.json    ← 04 lesson JSON 복사(추적용)            [#2]
                _deck.css _deck.js ← 공유 덱 자산                            [#2]
                slides.json        ← 덱 슬라이드 구조/캡처 매니페스트         [#3]
                mNN.timing.json    ← 씬별 오디오 길이/큐(전역)               [#3]
  images/       slide_00.png …     ← deck.html 캡처(1920×1080, 씬 순서)      [#3]
  audio/        scene_00.wav …     ← Supertonic3 TTS(씬별)                   [#3]
  subtitles/    subtitles.srt      ← 병합 자막(전역)                         [#3]
  script/       mNN_script.json    ← 리모션 _series 입력                     [#2]
  draft/        mNN.static.mp4     ← 일반영상                                [#3]
                mNN.ko.vtt         ← 일반영상 자막(웹 <track>용, 하드번인 X) [#3]
                mNN.motion.mp4     ← 리모션(키네틱) 영상                     [리모션]
  review.json   ← 매니페스트(아래). #2가 스켈레톤 → #3가 시간/일반영상 → 리모션이 motion 채움
```

### 파일명 규칙 (엄수)
- 슬라이드 이미지: `slide_%02d.png` (0-base, 씬 순서).
- 오디오: `scene_%02d.wav` (0-base, 씬 순서 — 이미지와 인덱스 대응).
- 자막: 전역 `subtitles/subtitles.srt` + 일반영상용 `draft/mNN.ko.vtt`.
- 최종 영상: `draft/mNN.static.mp4`(일반) · `draft/mNN.motion.mp4`(리모션).
- 리모션 입력: `script/mNN_script.json` (_series 포맷).
- 타이밍: `source/mNN.timing.json`.

> **리모션 스크래치 금지:** 리모션의 무거운 작업파일(React 번들·프레임 캐시 등)은 책 루트에
> **넣지 않는다.** 번들에는 입력(`script/mNN_script.json`)과 결과(`draft/mNN.motion.mp4`)만 둔다.

## review.json 스키마

pressplay `output/assets/js/media-tabs.js`가 소비하던 형태 그대로. 모든 미디어 참조는 **파일명만**(번들 기준 상대 경로).

```jsonc
{
  "title": "자사 모의고사 01회 — 문제 풀이",
  "totalSeconds": 0,                     // #3가 합성 후 확정
  "slides": [
    {
      "index": 0,
      "heading": "1과목 · 데이터 모델링의 이해",
      "narration": "화면/자막 원문 표기",   // 자막
      "narration_text": "소리나는 대로 발음", // 발음(있으면 TTS가 읽음, 없으면 narration)
      "image": "slide_00.png",             // images/ 기준 파일명
      "audio": "scene_00.wav",             // audio/ 기준 파일명
      "durSec": 0,                         // #3가 ffprobe로 확정
      "startSec": 0,                       // #3가 확정
      "cues": []                           // 문장 단위 [{start,end}] (#3)
    }
  ],
  "staticVideo": null,                     // "mNN.static.mp4" (#3)
  "staticSubtitles": null,                 // "mNN.ko.vtt"     (#3)
  "motionVideo": null                      // "mNN.motion.mp4" (리모션)
}
```

- **#2**: `title`·`slides[].{index,heading,narration,narration_text,image,audio}`를 채운 스켈레톤 생성(시간·비디오 필드는 `0`/`null`).
- **#3**: `totalSeconds`·`slides[].{durSec,startSec,cues}`·`staticVideo`·`staticSubtitles` 채움.
- **리모션**: `motionVideo` 채움.

## 리모션 _series 스크립트 (`script/mNN_script.json`)

리모션이 키네틱 영상을 만들 때 읽는 씬 배열. #2가 lesson JSON에서 생성한다.

```jsonc
{
  "version": "1.0",
  "kind": "series",
  "round": "자사 모의고사 01회",
  "subject": "SQLD",
  "theme": "sqld",
  "voice": "F2",
  "speed": 1.05,
  "scenes": [
    {
      "scene": 0,
      "kind": "section",                  // section | problem | answer | countdown | gap
      "heading": "1과목 · 데이터 모델링의 이해",
      "narration": "자막 원문 표기",
      "narration_text": "발음 표기",       // 없으면 narration을 읽음
      "image": "slide_00.png",            // images/ 기준(캡처 후 #3가 생성)
      "audio": "scene_00.wav",            // audio/ 기준(#3가 생성)
      "durSec": 0,                        // #3가 확정(리모션은 이 값으로 타임라인)
      "startSec": 0
    }
  ]
}
```

## 자막(보이는 텍스트) vs 발음(들리는 텍스트)

세부 규약은 [`lesson-json-spec.md`](./lesson-json-spec.md) "보이는 텍스트 ↔ 들리는 텍스트"를 따른다.
- **자막/화면용**(`narration`, deck 텍스트, `question`/`explanation`/`choices`): 원문 표기 그대로(`시각`, `1.2%`, `3,000원`).
- **낭독용**(`narration_text`, lesson `explanation_speech`/`narration_*`): 소리나는 대로(`시깍`, `일 점 이 퍼센트`).
- 낭독 필드의 괄호 `(…)` 부가설명은 읽지 않는다(자막엔 유지). `build.py`의 `to_speech`가 처리.
- #3는 "정답은 N번" 자동 삽입 안 함 → 정답 안내는 낭독본을 `"정답은 N번입니다. …"`로 시작하게 집필.

## end-to-end 흐름 (일반영상 → 리모션)

1. **#1** OCR → `01/`.
2. **#2** `build.py` → `02/ 03/ 04/`. `bundle.py` → `05/mNN/source/{deck.html, lesson 복사, _deck.*}` + `script/mNN_script.json` + `review.json` 스켈레톤. (deck.html 집필은 `build-deck` 스킬.)
3. **#3** `render.bat mNN` → deck.html 캡처(`images/slide_*.png`) + Supertonic3(`audio/scene_*.wav`, `subtitles/subtitles.srt`) + ffmpeg → `draft/mNN.static.mp4` + `mNN.ko.vtt`; `review.json`·`slides.json`·`mNN.timing.json` 갱신. **여기서 자막/음성 최종 OK.**
4. **리모션(클로드 데스크탑)** `script/mNN_script.json` + `source/`·`images/`·`audio/` → `draft/mNN.motion.mp4`; `review.json.motionVideo` 갱신.
