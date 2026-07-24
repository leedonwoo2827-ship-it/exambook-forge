# SVG 도형화 규약

그림은 PNG 대신 **인라인 SVG**로 만든다. 확대·편집이 쉽고 텍스트 렌더에 친화적이며, 영상 슬라이드에서 선명하다.

> **SVG는 그림 의존 문항 전용이 아니다 — 많이 쓸수록 좋다.**
> 문제·지문뿐 아니라 **해설의 개념 시각화**에 적극 사용한다. 좋은 후보:
> ERD/관계도, 계층 트리(CONNECT BY 전개), 집합연산 벤다이어그램(UNION/MINUS/교집합),
> 조인 결과 매칭도, 정규화 단계 흐름, 윈도우 프레임(ROWS/RANGE) 구간, SQL 논리적 실행순서 흐름도,
> 3층 스키마 계층, 슈퍼/서브타입 구조.
> 한 문항에 여러 개 넣어도 된다(`assets[]`).

## 저장/참조
- 문항용: `02/assets/{문항id}.svg` (예: `02/assets/m01-09.svg`)
- **요약노트/이론용**: `03/assets/{개념slug}.svg` (예: `03/assets/join-types.svg`). 요약원고·이론 설명에서
  `![조인 종류](assets/join-types.svg)`로 참조한다. 문항용 SVG를 요약에서 재사용하려면 03/assets로 복사/링크.
- 이 규약은 문항·해설·**요약·이론** 모두에 동일하게 적용한다(용도가 늘어날 것을 전제로 설계).
- MD 참조: `## 지문` 안에서 `![ERD](assets/m01-09.svg)`
- 회차 데이터에서는 `"svg": "m01-09.svg"`(파일명) 또는 `"svg": "<svg ...>...</svg>"`(인라인 문자열).
  - 파일명이면 스킬이 SVG 파일을 함께 만들고 build가 `02/assets/`로 복사.
  - 인라인이면 build가 `02/assets/{id}.svg`로 저장하고 참조를 건다.

## 작성 원칙
- `viewBox` 사용, 고정 px 대신 상대 좌표. 배경 투명 또는 흰색.
- 글꼴은 시스템 기본(`font-family="sans-serif"`), 한글 포함. 글자 크기 14~20.
- 선/박스는 얇은 스트로크(1~2px), 명도 대비 확보(다크/라이트 모두 읽히게 진회색 계열).
- **텍스트를 이미지로 굽지 말 것** — `<text>`로 넣어 검색/수정 가능하게.
- 관계선에 카디널리티/식별 표기(까마귀발, 1:N, 실선/점선)를 텍스트/마커로 표현.

## 유형별 템플릿

### ERD (엔터티-관계)
```svg
<svg viewBox="0 0 480 220" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="14">
  <rect x="20" y="40" width="150" height="90" fill="none" stroke="#333"/>
  <text x="95" y="60" text-anchor="middle" font-weight="bold">회원</text>
  <line x1="20" y1="70" x2="170" y2="70" stroke="#333"/>
  <text x="30" y="90">PK 회원ID</text>
  <text x="30" y="112">이름</text>

  <rect x="310" y="40" width="150" height="90" fill="none" stroke="#333"/>
  <text x="385" y="60" text-anchor="middle" font-weight="bold">주문</text>
  <line x1="310" y1="70" x2="460" y2="70" stroke="#333"/>
  <text x="320" y="90">PK 주문번호</text>
  <text x="320" y="112">FK 회원ID</text>

  <!-- 1:N 관계선 -->
  <line x1="170" y1="85" x2="310" y2="85" stroke="#333"/>
  <text x="240" y="78" text-anchor="middle">1 : N</text>
</svg>
```

### 계층 트리 (CONNECT BY 결과 시각화)
```svg
<svg viewBox="0 0 420 220" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="14">
  <rect x="170" y="10" width="80" height="34" fill="none" stroke="#333"/>
  <text x="210" y="32" text-anchor="middle">1000 조조</text>
  <line x1="210" y1="44" x2="110" y2="80" stroke="#333"/>
  <line x1="210" y1="44" x2="310" y2="80" stroke="#333"/>
  <rect x="70" y="80" width="80" height="34" fill="none" stroke="#333"/>
  <text x="110" y="102" text-anchor="middle">1001 유비</text>
  <rect x="270" y="80" width="80" height="34" fill="none" stroke="#333"/>
  <text x="310" y="102" text-anchor="middle">1002 관우</text>
</svg>
```

### 집합 다이어그램(UNION/MINUS/교집합)
- 두 원(벤 다이어그램)과 음영으로 결과 영역 표시. `<circle>` + `<path>`/투명도.

## 영상 슬라이드용 래스터화(선택)
- 영상 툴이 SVG를 직접 못 받으면 `build.py --rasterize-svg`로 `02/assets/{id}.png` 생성 후
  lesson JSON은 PNG를 참조. 래스터화는 표준 라이브러리 밖 의존이 필요할 수 있어 기본은 off,
  실패 시 SVG 원본을 그대로 두고 경고만 남긴다(파이프라인 중단 없음).
