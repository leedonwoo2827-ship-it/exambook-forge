# 회차 데이터 스키마 (rounds/mNN.json)

스킬이 "집필"하고 `build.py`가 소비하는 **단일 진실 원천**. 한 회차 = JSON 파일 1개.
여기서 MD·lesson JSON·index·stats가 모두 결정적으로 파생된다.

## 파일 위치
`rounds/m01.json`, `rounds/m02.json`, `rounds/m03.json` ...

## 구조

```json
{
  "round_code": "m01",
  "round": 1,
  "round_label": "자사 모의고사 01회",
  "subject_default": "SQLD",
  "theme": "sqld",
  "voice": "F2",
  "speed": 1.05,
  "countdown_seconds": 5,
  "gap_seconds": 1.5,
  "ai_reading": false,
  "questions": [
    {
      "question_no": 1,
      "subject": "데이터 모델링의 이해",
      "subject_no": 1,
      "difficulty": "중",
      "tags": ["분산 데이터베이스", "가용성", "보안"],
      "derived_from": "01-01",
      "question": "문제 지시문 (마크다운)",
      "passage": null,
      "choices": ["선지1", "선지2", "선지3", "선지4"],
      "answer_index": 2,
      "explanation": "해설 (마크다운; 화면·자막용 원문 표기)",
      "explanation_speech": "해설 낭독본 (소리나는 대로 발음 표기)",
      "svg": null
    }
  ]
}
```

루트 옵션(`voice`/`speed`/`countdown_seconds`/`gap_seconds`/`ai_reading`)은 생략 시 기본값
(F2 / 1.05 / 5 / 1.5 / false)이 lesson JSON에 채워진다. `subject_default`→lesson `subject`, `theme`→`theme`.

## 문항 필드

| 필드 | 필수 | 설명 |
|---|---|---|
| `question_no` | ✅ | 회차 내 번호 **1..N 연속(빈칸 없음)** — SQLD 1~50 · 빅분기 필기 1~80 |
| `subject` | ✅ | 과목명(syllabus의 이름을 정확히 — 요약노트 `<h1>N과목·이름</h1>`과 일치) |
| `subject_no` | ✅ | 과목 번호 **1..N 연속** — SQLD 1/2 · 빅분기 필기 1~4 (웹 성적표·이론 링크의 축) |
| `difficulty` | ✅ | `상`/`중`/`하` |
| `tags` | ✅ | 키워드 배열(2~4개 권장) |
| `derived_from` | ✅ | 원 개념 근거 문항 id (검수 추적) |
| `question` | ✅ | **질문만** 넣는다(지문·표·SQL은 아래 구조화 필드로 분리 — 렌더가 지문 씬/코드카드/표로 또렷하게). |
| `passage` | ❌ | 긴 자유 지문 텍스트(멀티 테이블 등 복잡한 경우 마크다운 허용). 렌더는 별도 '지문 씬'으로 분리. |
| `sql` | ❌ | SQL/코드 문자열(펜스 없이 코드만). MD엔 ```sql 블록, lesson엔 `sql` 필드(모노스페이스 코드카드). |
| `table` | ❌ | 구조화 표 `{"columns":[...],"rows":[[...],...]}`. MD엔 마크다운 표, lesson엔 `table` 구조 그대로. |
| `hide_choices` | ❌ | `true`면 문제 화면에서 보기 생략(교재 참고형), TTS는 낭독. 생략 시 렌더가 길이로 자동 판단. |
| `choices` | ✅ | 정확히 **4개** 문자열(원문자 없이 내용만). MD(02)엔 build가 ①②③④ 부여, lesson(04)엔 순수 텍스트 유지 |
| `answer_index` | ✅ | 0-based 정답 인덱스(0~3) |
| `explanation` | ✅ | 해설. **화면·자막용 원문 표기**(시각, 1.2%, 3,000원 그대로) |
| `explanation_speech` | 권장 | **낭독본 — 소리나는 대로 발음 표기**(시각→"시깍", 1.2%→"일 점 이 퍼센트", NVL→"엔브이엘"). 없으면 explanation을 순수화해 대체하지만, 품질을 위해 직접 작성 권장 |
| `narration_question` | ❌ | (선택) 문제 낭독본을 따로 발음 표기로 제공할 때 |
| `narration_answer` | ❌ | (선택) 정답 낭독본을 따로 발음 표기로 제공할 때 |
| `assets` | ❌ | **SVG 자산 배열** `[{"name":"m01-09-erd","svg":"<svg ...>"}]`. build가 `02/assets/NAME.svg`로 저장. **문제/지문/해설 어디서든** `![설명](assets/NAME.svg)`로 참조. 개수 제한 없음 — **많이 쓸수록 좋다**(개념 시각화) |
| `svg` | ❌ | (레거시·단축) 인라인 SVG 문자열 1개. `02/assets/{id}.svg`로 저장되고 **지문에 자동 첨부**. 여러 개/해설 삽입은 `assets` 사용 |

> **SVG는 그림 의존 문항 전용이 아니다.** 조인 벤다이어그램, 계층 트리, 정규화 단계, 윈도우 프레임,
> SQL 실행순서 흐름도, 집합연산 다이어그램 등 **해설의 개념 시각화**에 적극 사용한다.
> 참조는 마크다운(`![..](assets/NAME.svg)`)을 `question`/`passage`/`explanation` 어디에든 넣으면 된다.

## build.py 가 자동 파생하는 것 (집필 시 넣지 말 것)
- `id` = `{round_code}-{question_no:02d}`
- `answer` = `["①","②","③","④"][answer_index]`
- `has_sql` / `has_table` / `has_figure` = question+passage+svg 내용에서 감지
- frontmatter의 `authored_by/verified/reviewed/needs_review`
- 산출 경로: 문제 MD → `02/{id}.md`, 영상 대본 → `04/lesson_{round_code}.json`, SVG → `02/assets/`
- `02/_index.json`, `02/difficulty_stats.json` 재집계
- lesson JSON의 `choices`에 원문자 접두(`① ...`)

## 회차 구성 제약(품질 규칙)
- 과목 비율: `데이터 모델링의 이해` 10 + `SQL 기본 및 활용` 40 = 50 (SQLD 실전 비율 유지)
- 난이도 분포: 상 12~16 / 중 24~28 / 하 8~10 (원본 상15·중26·하9 근방, 회차마다 소폭 변주)
- **출제 순서**: 원본 개념 순서를 그대로 쓰지 말 것 — `derived_from` 순서를 섞어 배치
- 정답 분포: ①②③④가 한쪽에 쏠리지 않게 (각 8~17개 범위)
- 자세한 집필 규칙은 `authoring-rules.md`, 개념 풀은 `sqld-syllabus.md` 참고
