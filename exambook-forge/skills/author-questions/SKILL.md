---
name: author-questions
description: 기출 문항(01)을 근거로 자사 모의고사 회차 데이터(_rounds/mNN.json)를 저작권 안전하게 재집필해야 할 때. 개념·난이도·키워드는 유지하되 표면(문제문·테이블·값·SQL·보기·오답)을 전면 재작성하고 출제 순서를 바꾼다.
metadata:
  group: 자격시험 파이프라인
  stage: 집필
  produces: <book>/_rounds/mNN.json (build.py 입력)
---

# author-questions (문제 재집필)

## When to use
- 회차별 문제 데이터를 "집필"할 때. `generate-mockexam` 또는 `/exam-questions`가 호출.

## 입력
- `01/`의 원본 문항 MD, 개념 풀 `${CLAUDE_PLUGIN_ROOT}/references/sqld-syllabus.md`,
  집필 규칙 `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`,
  데이터 스키마 `${CLAUDE_PLUGIN_ROOT}/references/round-data-schema.md`.

## 절차
0. **회차 번호 결정.** `<book>/_rounds/`의 기존 `mNN.json`을 확인해 **다음 번호부터** 이어서 집필
   (예: m01~m03 있으면 m04부터). 기존 회차 덮어쓰지 않음.
1. **개념 매핑.** `01/`의 **모든 기출 회차(01-*, 02-*, …)** 문항 전체 + 개념 풀(`sqld-syllabus.md`)에서
   회차가 커버할 개념을 고른다. 과목 비율 1과목 10 : 2과목 40 유지. 회차가 늘수록 회차 간 소재가 겹치지
   않게 기출 다회분에서 폭넓게 뽑는다.
2. **순서 설계(필수).** 원본 문항 순서를 그대로 쓰지 말 것. 개념을 **섞어** 배치하되
   과목 경계(1~10=1과목, 11~50=2과목)는 유지. 3개 회차는 서로 다른 흐름/하위주제 강조.
3. **문항 재작성(저작권 안전).** 개념·유형·난이도만 취하고 아래는 전부 새로:
   문제 지시문, 지문의 테이블명/컬럼/값/행수, SQL 값·별칭·조건, 보기 4개와 오답 구성, 소재/인물.
   단순 패러프레이즈·값 몇 개 교체 금지 → 시나리오 자체를 새로 구성.
4. **정답 확정(검산).** 계산·실행결과 문항은 실제로 검산해 `answer_index`를 확정
   (행 수, 집계값, 정렬결과, 조인건수, NULL 경계, 계층 전개 등). SQL은 문법적으로 유효하게.
5. **시각화(SVG).** 구조 이해가 필요한 문제/지문/**해설**은 `svg-diagram` 스킬로 SVG를 만들어
   `assets[]`에 넣고 본문에서 `![..](assets/NAME.svg)`로 참조. 많이 쓸수록 좋다.
6. **메타.** 문항마다 `tags`(세부 개념 2~4개), `difficulty`(상/중/하), `derived_from`(원 개념 근거 id).
7. **분포 점검.** 난이도 상12~16/중24~28/하8~10, 정답 ①②③④ 각 8~17. 편중되면 재배치.
8. **저장.** 회차별 `<book>/_rounds/mNN.json` (round-data-schema 형식). 그 뒤 validate.py로 점검.

## 산출
- `<book>/_rounds/m01.json`, `m02.json`, `m03.json` ... (문항 배열 + assets SVG)

## 주의
- `id`/`answer`/`has_*`/frontmatter/index/stats는 build.py가 파생하므로 데이터에 넣지 않는다.
- `choices`는 원문자 없이 내용만(빌드가 ①②③④ 부여), 정확히 4개.
