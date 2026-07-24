---
name: summary-note
description: 해설을 모아 과목→항목→상세로 종합하고 중복을 정돈한 요약원고(요약노트)를 03 폴더에 HTML(기본)+MD로 만들어야 할 때. 개념 SVG를 적극 삽입하고 출처(회차+번호)를 표기하며 추후 hwpx 변환을 대비한다.
metadata:
  group: 자격시험 파이프라인
  stage: 요약
  produces: 03/summary_*.html(기본) + .md · 03/assets/*.svg
---

# summary-note (요약원고)

## When to use
- 해설을 학습 요약으로 정리할 때. `/exam-summary` 또는 `generate-mockexam`이 호출.

## 입력
- `01/`의 해설(1차) + `02/`의 자사 문항 해설(2차, 있으면).
- 포맷 규약 `${CLAUDE_PLUGIN_ROOT}/references/summary-format.md`, SVG 규약 `svg-conventions.md`,
  개념 순서 `sqld-syllabus.md`.

## 절차
1. **수집.** 과목별로 문항 해설을 모으고 tags/개념으로 군집화.
2. **종합·중복정돈.** 같은 개념이 여러 문항에 흩어져 있으면 한 항목으로 통합하고 출처를 모두 나열.
   상충 설명은 정확한 쪽으로 통일, DBMS 차이는 표/각주로 구분.
3. **구조화.** 과목→대항목→상세. 표로 정리 가능한 것(키·조인·계층함수·윈도우 프레임)은 표로.
   항목 순서는 `sqld-syllabus.md` 흐름.
4. **시각화.** 개념 도형을 `svg-diagram` 스킬로 만들어 `03/assets/*.svg`에 저장하고
   요약에 삽입(HTML은 **인라인** SVG). 요약/이론에 많이 쓴다.
5. **출처 표기.** 각 소절 끝 `> 출처: {id}, {id} ...` (자사 문항 있으면 `· 관련 자사: {id}`).
6. **출력.** `03/summary_{과목}.html`(기본, 자기완결·인라인CSS·인라인SVG) + `.md`(소스).
   마크업은 단순 시맨틱(h1~h4/table/ul/figure)으로 hwpx 변환 친화.

## 산출
- `03/summary_데이터모델링.html` / `.md`
- `03/summary_SQL.html` / `.md`
- `03/assets/*.svg`, (선택) `03/summary_index.html`

## 주의
- HTML이 **기본 산출물**(SVG·표가 가장 잘 담김). hwpx 변환 시 SVG는 PNG 래스터화로 치환(원본 유지).
- 스크립트/외부 리소스 금지(오프라인·변환 친화).
