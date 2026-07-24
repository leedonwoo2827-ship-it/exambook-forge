---
name: svg-diagram
description: 문제·지문·해설·요약·이론에 넣을 개념 도형을 인라인 SVG로 그려야 할 때. ERD·계층 트리·집합 벤다이어그램·조인 매칭도·정규화 흐름·윈도우 프레임·실행순서 흐름도 등. PNG 대신 SVG를 많이 쓴다.
metadata:
  group: 자격시험 파이프라인
  stage: 시각화
  produces: 02/assets/*.svg · 03/assets/*.svg (인라인 SVG 문자열)
---

# svg-diagram (SVG 도형화)

## When to use
- 구조·관계·흐름을 시각화하면 이해가 좋아지는 모든 곳. **그림 의존 문항 전용이 아니다** —
  해설·요약·이론에서도 적극 사용(나중에 요약/이론에서 재사용 예정).

## 입력
- 규약: `${CLAUDE_PLUGIN_ROOT}/references/svg-conventions.md` (viewBox·텍스트는 `<text>`·대비·마커 규칙).

## 절차
1. 시각화 대상을 고른다(예: UNION/MINUS 벤다이어그램, CONNECT BY 계층 트리, INNER/OUTER 조인 매칭,
   1→2→3정규형 흐름, ROWS/RANGE 프레임 구간, FROM→WHERE→...→ORDER BY 흐름).
2. `svg-conventions.md`의 템플릿을 바탕으로 **인라인 SVG 문자열**을 만든다.
   - `viewBox` 사용, 텍스트는 `<text>`(이미지로 굽지 않기), 한글 포함, 진회색 대비.
3. 배치:
   - 문항용: 회차 데이터 문항의 `assets: [{"name":"m01-09-erd","svg":"<svg ...>"}]`에 넣고
     본문(`question`/`passage`/`explanation`)에서 `![설명](assets/m01-09-erd.svg)`로 참조.
   - 요약/이론용: `03/assets/{slug}.svg`로 저장하고 요약 HTML엔 **인라인**으로 삽입.
4. 한 문항/항목에 여러 개 넣어도 된다.

## 산출
- 문항: `02/assets/*.svg` (build.py가 assets[]에서 기록)
- 요약/이론: `03/assets/*.svg` + HTML 인라인

## 주의
- 영상 툴이 SVG를 직접 못 받으면 `build.py --rasterize-svg`(또는 hwpx 내보내기 시)로 PNG 치환.
  원본 SVG는 유지.
