---
description: 기출 1권으로 자사 N회차 모의고사 문제(02)+영상 대본 JSON(04)+요약원고(03)를 한 번에 생성
argument-hint: "[rounds=3] [book=<ocr-output 경로>] [subject=SQLD]"
---

# /exam-all

`generate-mockexam` 스킬을 실행해 **한 번에** 전체 파이프라인을 돌린다.

## 인자 (선택)
- `rounds` — 만들 자사 회차 수 (기본 3)
- `book` — 책 루트(`ocr-output-*`) 경로 (기본: 작업공간 상위의 `ocr-output-260723` 자동 탐색)
- `subject` / `theme` — 과목/테마 (기본 SQLD / sqld)

## 절차
1. 책 루트를 확정하고 `02/`·`03/`·`04/`에 쓸 것임을 **한 번** 알리고 동의를 받는다(폴더 없으면 자동 생성).
2. `generate-mockexam` 스킬의 절차대로:
   문제 집필(_rounds/mNN.json) → validate → build.py(02 MD + 04 lesson JSON) → 요약원고(03 HTML+MD).
3. 완료 후 생성 개수·난이도/정답 분포·산출 경로·다음 단계(영상 툴에 04 JSON 로드)를 보고한다.

## 참고
- 한 번에 처리가 무거우면 `/exam-questions`(문제+영상) 다음 `/exam-summary`(요약) 2단계로 나눠 실행.
- 규칙/포맷: `${CLAUDE_PLUGIN_ROOT}/references/` 전체.
