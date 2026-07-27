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
1. 책 루트 확정 + `03/` 쓰기 **1회 동의**.
2. **백업**: 기존 `03/summary_*`·`03/assets/`가 있으면 `03/_backup_<YYYYMMDD-HHMM>/`로 **이동**(덮어쓰기 아님).
3. `summary-note` 스킬로 **전 회차 병합**:
   - `01/`의 **모든 기출 회차** + `02/`의 **모든 자사 회차** 해설 수집 → 군집화 → 종합·중복정돈(한 개념=한 항목, 출처 모두 표기).
   - 과목→대항목→상세 구조화, 표로 정리, 개념 SVG(`svg-diagram`)를 `03/assets`에 넣어 삽입.
   - `03/summary_{과목}.html`(기본, 자기완결·인라인 SVG) + `.md`(소스). hwpx 변환 친화 마크업.
4. 생성 파일·항목 수·출처 커버리지·백업 위치 보고.

## 참고
- 포맷 `summary-format.md`, SVG `svg-conventions.md`, 개념 순서 `sqld-syllabus.md`
  (`${CLAUDE_PLUGIN_ROOT}/references/`).
