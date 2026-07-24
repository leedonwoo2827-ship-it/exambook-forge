---
description: 요약 일괄 — 해설을 과목→항목→상세로 종합·중복정돈한 요약원고를 03에 HTML(기본)+MD로 생성
argument-hint: "[book=<ocr-output 경로>] [subject=all]"
---

# /exam-summary

요약 파트를 한 번에 끝낸다: `summary-note` 스킬로 요약원고 생성.

## 인자 (선택)
- `book` — 책 루트(기본 `ocr-output-260723` 자동 탐색)
- `subject` — `all`(기본) / `데이터 모델링의 이해` / `SQL 기본 및 활용`

## 절차
1. 책 루트 확정 + `03/` 쓰기 **1회 동의**(폴더 없으면 자동 생성).
2. `summary-note` 스킬로:
   - `01/`(+`02/`) 해설 수집 → tags/개념 군집화 → 종합·중복정돈(한 개념=한 항목, 출처 모두 표기).
   - 과목→대항목→상세 구조화, 표로 정리, 개념 SVG(`svg-diagram`)를 `03/assets`에 넣어 삽입.
   - `03/summary_{과목}.html`(기본, 자기완결·인라인 SVG) + `.md`(소스) 출력. hwpx 변환 친화 마크업.
3. 생성 파일·항목 수·출처 커버리지 보고.

## 참고
- 포맷 `summary-format.md`, SVG `svg-conventions.md`, 개념 순서 `sqld-syllabus.md`
  (`${CLAUDE_PLUGIN_ROOT}/references/`).
