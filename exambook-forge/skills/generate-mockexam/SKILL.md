---
name: generate-mockexam
description: 기출 문제집(ocr-output */01의 01-*, 02-*, … 여러 회차)으로 자사 N회차 모의고사 문제(02)·영상 대본 JSON(04)·10문항 번들(05)·요약원고(03)까지 한 번에 만들어야 할 때 쓰는 오케스트레이터. "모의고사 만들어줘 / N회차 생성 / 문제집 집필"류 요청의 진입점.
metadata:
  group: 자격시험 파이프라인
  stage: 오케스트레이션
  produces: 02 문제 MD · 04 영상 대본 JSON · 05 번들(일반 deck+모션 _series) · 03 요약원고
  chains: [author-questions, svg-diagram, build-video-json, build-deck, summary-note]
---

# generate-mockexam (오케스트레이터)

기출 문제집을 재료로 자사 모의고사 전체 산출물을 정렬된 순서로 생성한다.

## When to use
- "SQLD 모의고사 N회차 만들어줘", "기출로 자사 문제집 집필", "문제+영상+요약 한 번에".
- 단계별로만 하고 싶으면 `/exam-questions`(문제+영상+번들) → `/exam-summary`(요약)로 나눠 실행.

## 입력
- 책 루트: `ocr-output-*` (기본: 이 작업공간 상위의 `ocr-output-260723`). `01/`에 기출 문항 MD.
- 회차 수 `rounds`(기본 3), 과목/테마(기본 SQLD/sqld — 빅분기 필기면 4과목·`theme=teal`), 번들 분할 `chunk`(기본 10문항/편).
- **웹-only 품목(예: 빅분기 필기 `bdae-w`)**: 04/05(영상)는 선택이다. `exam-web-contract.md` §3대로 문제(02)·요약(03)만
  만들어도 웹의 문제풀이·성적표·이론·게시판이 동작한다. 영상까지 원하면 6~8단계도 그대로 실행.

## 절차
1. **책 루트 확인 + 권한 1회 확인.** 경로 확정 후 `02/`·`03/`·`04/`·`05/`에 쓸 것임을 **한 번** 알리고
   동의받는다(없으면 자동 생성). 이후 단계에서 다시 묻지 않는다.
2. **입력 분석.** `01/`의 **모든 기출 회차(01-*, 02-*, …)** 문항 전체를 개념 풀로 삼고
   **대상 시험의 syllabus**와 대조해 개념·난이도·과목 배분을 정한다
   (SQLD → `sqld-syllabus.md` 2과목 10:40 · 빅데이터분석기사 필기 → `bdae-written-syllabus.md` 4과목 20씩).
   웹 품목이면 `${CLAUDE_PLUGIN_ROOT}/references/exam-web-contract.md`를 반드시 지킨다(subject_no·question_no 연속).
3. **회차 번호 결정(연속).** `<book>/_rounds/`의 기존 `mNN.json`을 확인해 **다음 번호부터** 이어서
   `rounds`개를 만든다(예: m01~m03 있으면 → m04~m06). 기존 회차는 덮어쓰지 않는다.
4. **문제 집필** → `author-questions` 스킬. 회차별 `<book>/_rounds/mNN.json` 집필
   (순서 변경·표면 재작성·tags·난이도·derived_from). 그림/개념 시각화는 `svg-diagram`로 SVG.
5. **검증** → `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --rounds-dir "<book>/_rounds"` (오류 0까지).
6. **빌드(문제+영상)** → `python "${CLAUDE_PLUGIN_ROOT}/scripts/build.py" --book "<book>"`
   → `02/*.md`, `04/lesson_mNN.json`, `02/_index.json`, `02/difficulty_stats.json`, `02/assets`, `04/assets`.
7. **번들(일반/모션, 10문항씩)** → `python "${CLAUDE_PLUGIN_ROOT}/scripts/bundle.py" --book "<book>" --chunk 10`
   → 회차당 `05/mNN-1 … mNN-5/`(각 10문항): `source/deck.html`+`_deck.*`+부분 lesson, `script/…_script.json`, `review.json`.
   deck.html 다듬기는 `build-deck` 스킬.
8. **요약원고(백업+병합)** → `summary-note` 스킬. 기존 `03/`을 백업하고 **기출 전 회차 + 자사 전 회차** 해설을
   과목→항목→상세로 종합·중복정돈해 재생성.
9. **README 단계 등록.** 책 루트 `README.md`에 `04/`·`05/` 행이 없으면 추가.
10. **보고.** 생성 회차·개수·난이도/정답 분포·산출 경로·다음 단계(#3 render / 리모션)를 알린다.

## 산출
- `02/mNN-01.md ~ mNN-50.md` + `_index.json` + `difficulty_stats.json` + `assets/*.svg`
- `04/lesson_mNN.json` (+ `04/assets/*.svg`)
- `05/mNN-1 … mNN-5/` 번들(일반 deck + 모션 _series + review.json)
- `03/summary_*.html` + `.md` (+ `assets/*.svg`), 기존은 `03/_backup_<날짜>/`로 백업

## 참고
- 집필 규칙: `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`
- 개념 풀(시험별): `sqld-syllabus.md`(SQLD) · `bdae-written-syllabus.md`(빅분기 필기)
- **웹 소비 계약: `${CLAUDE_PLUGIN_ROOT}/references/exam-web-contract.md`** (02/·03/ 필수 규약)
- 데이터 스키마: `${CLAUDE_PLUGIN_ROOT}/references/round-data-schema.md`
- MD/lesson/요약/SVG 포맷: 각 `references/*.md`
