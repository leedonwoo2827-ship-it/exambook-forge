---
description: 문제 일괄 — 자사 N회차 재집필 문제 MD(02) + 영상 대본 JSON(04) + 10문항 번들(05)을 생성
argument-hint: "[rounds=3] [book=<ocr-output 경로>] [round=m04] [chunk=10]"
---

# /exam-questions

문제 파트를 한 번에 끝낸다: 재집필(_rounds) → 검증 → 빌드(02 MD + 04 lesson) → 번들(05, 10문항씩).
요약은 만들지 않는다(그건 `/exam-summary`).

## 인자 (선택)
- `rounds` — 회차 수 (기본 3) / `round` — 특정 회차코드만(예 m04)
- `chunk` — 번들 1편당 문항 수 (기본 10; 0이면 회차당 1편)
- `book` — 책 루트(기본 `ocr-output-260723` 자동 탐색)

## 절차
1. 책 루트 확정 + `02/`·`04/`·`05/` 쓰기 **1회 동의**(폴더 없으면 자동 생성).
2. **회차 번호 연속**: `<book>/_rounds/`의 기존 `mNN.json`을 보고 다음 번호부터(예 m01~m03 있으면 m04~).
3. `author-questions` 스킬로 회차별 `<book>/_rounds/mNN.json` 집필. `01/`의 **모든 기출 회차**를 개념 풀로,
   순서 변경·표면 재작성·tags·난이도·derived_from, 개념 시각화는 `svg-diagram`.
4. `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --rounds-dir "<book>/_rounds"` — 오류 0까지 수정.
5. `python "${CLAUDE_PLUGIN_ROOT}/scripts/build.py" --book "<book>"`
   → `02/*.md` + `02/_index.json` + `02/difficulty_stats.json` + `04/lesson_mNN.json` + `04/assets`.
6. `python "${CLAUDE_PLUGIN_ROOT}/scripts/bundle.py" --book "<book>" --chunk 10`
   → 회차당 `05/mNN-1 … mNN-5/`(각 10문항): 일반 deck + 모션 _series + review.json. deck 다듬기는 `build-deck`.
7. 생성 회차·개수·분포·경로 보고. 이어서 요약이 필요하면 `/exam-summary` 안내.

## 참고
- 집필 규칙 `authoring-rules.md`, 개념 풀 `sqld-syllabus.md`, 데이터 스키마 `round-data-schema.md`,
  lesson 규격 `lesson-json-spec.md`, 출력구조 `pipeline-output-structure.md` (모두 `${CLAUDE_PLUGIN_ROOT}/references/`).
