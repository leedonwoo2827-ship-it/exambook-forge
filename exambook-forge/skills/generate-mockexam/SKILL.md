---
name: generate-mockexam
description: 기출 1권(ocr-output */01) 하나로 자사 N회차 모의고사 문제(02)·문제 영상 대본 JSON(04)·요약원고(03)까지 한 번에 만들어야 할 때 쓰는 오케스트레이터. "모의고사 만들어줘 / N회차 생성 / 문제집 집필"류 요청의 진입점.
metadata:
  group: 자격시험 파이프라인
  stage: 오케스트레이션
  produces: 02 문제 MD · 04 영상 대본 JSON · 03 요약원고(HTML 기본+MD)
  chains: [author-questions, svg-diagram, build-video-json, summary-note]
---

# generate-mockexam (오케스트레이터)

기출 1권을 재료로 자사 모의고사 전체 산출물을 정렬된 순서로 생성한다.

## When to use
- "SQLD 모의고사 N회차 만들어줘", "기출 1회분으로 자사 문제집 집필", "문제+영상+요약 한 번에".
- 단계별로만 하고 싶으면 `/exam-questions`(문제+영상) → `/exam-summary`(요약)로 나눠 실행.

## 입력
- 책 루트: `ocr-output-*` (기본: 이 작업공간 상위의 `ocr-output-260723`). `01/`에 원본 문항 MD가 있어야 함.
- 회차 수 `rounds`(기본 3), 과목/테마(기본 SQLD/sqld).

## 절차
1. **책 루트 확인 + 권한 1회 확인.** 책 루트 경로를 확정하고, `02/`·`03/`·`04/`에 파일을 쓸 것임을
   사용자에게 **한 번** 알리고 동의를 받는다(없으면 폴더는 자동 생성). 이후 단계에서 다시 묻지 않는다.
2. **입력 분석.** `01/`의 문항과 `${CLAUDE_PLUGIN_ROOT}/references/sqld-syllabus.md`(개념 풀)를 대조해
   커버할 개념·난이도·과목 비율(10:40)을 정한다.
3. **문제 집필** → `author-questions` 스킬. 회차별 `<book>/_rounds/mNN.json`을 집필
   (순서 변경·표면 재작성·tags·난이도·derived_from). 그림/개념 시각화는 `svg-diagram` 스킬로 SVG 생성.
4. **검증** → `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --rounds-dir "<book>/_rounds"`.
   오류 0이 될 때까지 데이터 수정.
5. **빌드(문제+영상)** → `build-video-json` 스킬 = `python "${CLAUDE_PLUGIN_ROOT}/scripts/build.py" --book "<book>"`.
   → `02/*.md`, `04/lesson_mNN.json`(include_lecture:false), `02/_index.json`, `02/difficulty_stats.json`.
6. **요약원고** → `summary-note` 스킬. `01/`(+`02/`) 해설을 과목→항목→상세로 종합·중복정돈 →
   `03/summary_*.html`(기본)+`.md`, 개념 SVG 포함.
7. **04 단계 등록.** 책 루트 `README.md`에 `04/ | 영상 대본 | 문제 영상 lesson JSON` 행이 없으면 추가.
8. **요약 보고.** 생성 개수, 난이도/정답 분포, 산출 경로, 다음 단계(영상 툴에 04 JSON 로드)를 알린다.

## 산출
- `02/mNN-01.md ~ mNN-50.md` + `_index.json` + `difficulty_stats.json` + `assets/*.svg`
- `04/lesson_mNN.json` (문제 전용 영상 대본)
- `03/summary_*.html` + `.md` (+ `assets/*.svg`)

## 참고
- 집필 규칙: `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`
- 개념 풀: `${CLAUDE_PLUGIN_ROOT}/references/sqld-syllabus.md`
- 데이터 스키마: `${CLAUDE_PLUGIN_ROOT}/references/round-data-schema.md`
- MD/lesson/요약/SVG 포맷: 각 `references/*.md`
