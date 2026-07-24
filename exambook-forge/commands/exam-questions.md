---
description: 문제 일괄 — 자사 N회차 재집필 문제 MD(02)와 문제 전용 영상 대본 JSON(04)을 생성
argument-hint: "[rounds=3] [book=<ocr-output 경로>] [round=m01]"
---

# /exam-questions

문제 파트를 한 번에 끝낸다: 재집필(_rounds) → 검증 → 빌드(02 문제 MD + 04 영상 대본 JSON).
요약은 만들지 않는다(그건 `/exam-summary`).

## 인자 (선택)
- `rounds` — 회차 수 (기본 3) / `round` — 특정 회차코드만(예 m01)
- `book` — 책 루트(기본 `ocr-output-260723` 자동 탐색)

## 절차
1. 책 루트 확정 + `02/`·`04/` 쓰기 **1회 동의**(폴더 없으면 자동 생성).
2. `author-questions` 스킬로 회차별 `<book>/_rounds/mNN.json` 집필
   (순서 변경·표면 재작성·tags·난이도·derived_from, 개념 시각화는 `svg-diagram`).
3. `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --rounds-dir "<book>/_rounds"` — 오류 0까지 수정.
4. `build-video-json` 스킬 = `python "${CLAUDE_PLUGIN_ROOT}/scripts/build.py" --book "<book>"`
   → `02/*.md` + `02/_index.json` + `02/difficulty_stats.json` + `04/lesson_mNN.json`(include_lecture:false).
5. 생성 개수·분포·경로 보고. 이어서 요약이 필요하면 `/exam-summary` 안내.

## 참고
- 집필 규칙 `authoring-rules.md`, 개념 풀 `sqld-syllabus.md`, 데이터 스키마 `round-data-schema.md`,
  lesson 규격 `lesson-json-spec.md` (모두 `${CLAUDE_PLUGIN_ROOT}/references/`).
