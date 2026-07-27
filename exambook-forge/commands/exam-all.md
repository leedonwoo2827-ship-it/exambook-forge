---
description: 기출 문제집으로 자사 N회차 모의고사 문제(02)+영상 JSON(04)+10문항 번들(05)+요약원고(03)를 한 번에 생성
argument-hint: "[rounds=3] [book=<ocr-output 경로>] [chunk=10] [subject=SQLD]"
---

# /exam-all

`generate-mockexam` 스킬을 실행해 **한 번에** 전체 파이프라인을 돌린다.

## 인자 (선택)
- `rounds` — 추가할 자사 회차 수 (기본 3; 기존 `_rounds` 다음 번호부터 이어서)
- `chunk` — 번들 1편당 문항 수 (기본 10; 0=회차당 1편)
- `book` — 책 루트(`ocr-output-*`) 경로 (기본: `ocr-output-260723` 자동 탐색)
- `subject` / `theme` — 과목/테마 (기본 SQLD / sqld)

## 절차
1. 책 루트 확정 + `02/`·`03/`·`04/`·`05/` 쓰기 **1회 동의**(폴더 없으면 자동 생성).
2. `generate-mockexam` 스킬 절차대로:
   회차 번호 연속 결정(m04~) → 집필(_rounds/mNN.json, `01/` 전 기출 회차 개념풀) → validate →
   `build.py`(02 MD + 04 lesson) → `bundle.py --chunk 10`(05 회차당 5편, 일반+모션) →
   `summary-note`(기존 03 백업 후 **기출+자사 전체 병합** 재생성).
3. 완료 후 생성 회차·개수·분포·산출 경로·다음 단계(#3 render / 리모션)를 보고한다.

## 참고
- 한 번에 처리가 무거우면 `/exam-questions`(문제+영상) 다음 `/exam-summary`(요약) 2단계로 나눠 실행.
- 규칙/포맷: `${CLAUDE_PLUGIN_ROOT}/references/` 전체.
