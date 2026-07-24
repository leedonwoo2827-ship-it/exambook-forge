# 문항 MD 포맷 규격 (ocr-output 파이프라인)

입력(`01/`)과 출력(`02/`)이 **동일한** 문항 MD 포맷을 쓴다. 한 문항 = MD 파일 1개.

## 파일명
`{회차코드}-{문항2자리}.md`
- 입력 기출: `01-01.md` ~ `07-50.md`
- 출력 자사 모의고사: `m01-01.md` ~ `mNN-50.md` (자사 회차는 `m` 접두)

## YAML frontmatter (필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | str | `{회차코드}-{문항2자리}` (예: `m01-07`) |
| `round` | int | 회차 번호 (자사 1회차 = 1) |
| `round_label` | str | 표시용 (예: `자사 모의고사 01회`) |
| `subject` | str | 과목명 (`데이터 모델링의 이해` / `SQL 기본 및 활용`) |
| `subject_no` | int | 과목 번호 (1 / 2) |
| `question_no` | int | 회차 내 문항 번호 (1~50) |
| `answer` | str | 정답 원문자 (`①②③④` 중 하나) |
| `answer_index` | int | 0-based 정답 인덱스 (`③`이면 2) |
| `difficulty` | str | `상` / `중` / `하` |
| `tags` | list[str] | **키워드(신설)** — 실전 검색·요약노트 연결용 (예: `["계층형 쿼리","CONNECT BY"]`) |
| `derived_from` | str | 원 개념 근거 문항 id (예: `01-18`) — 검수 추적용. `source_pdf`/`source_pages` 대신 사용 |
| `has_figure` | bool | 그림/SVG 포함 여부 |
| `has_sql` | bool | SQL 코드 포함 여부 |
| `has_table` | bool | 표 포함 여부 |
| `authored_by` | str | `claude` (재집필 주체) |
| `verified` | bool | 자동 검증 통과 여부 |
| `reviewed` | bool | 사람 검수 여부 (초기 false) |
| `needs_review` | bool | 검수 필요 표시 |

> 원본에 있던 `source_pdf`/`source_pages`/`ocr_by`는 자사 집필본에 두지 않는다(원본 추적 정보).
> 대신 `derived_from` + `authored_by`를 쓴다.

## 본문 섹션 (고정 순서)

```
## 문제
{문제 지시문}

## 지문
{선택: SQL 코드블록(```sql), GitHub 마크다운 표, 또는 SVG/그림 참조. 없으면 이 섹션 자체를 생략}

## 보기
① {선지1}
② {선지2}
③ {선지3}
④ {선지4}

## 해설
{정답 근거 설명. 필요 시 표 포함}
```

### 규칙
- 보기 번호는 **원문자 `① ② ③ ④`** 로 통일한다(원본의 `1. 2. 3. 4.` 혼용을 정돈).
- 표는 GitHub 마크다운 표. **셀 안 줄바꿈은 `<br>`**.
- SQL은 ` ```sql ... ``` ` 펜스 블록. 보기 자체가 SQL이면 각 보기 아래 펜스 블록으로.
- 그림/도형은 SVG 파일 참조: `![설명](assets/{id}.svg)` (02/ 기준 상대경로). 인라인 SVG도 허용.
- `## 지문`은 표/SQL/그림이 있을 때만 둔다. 순수 개념 문항은 `## 문제`→`## 보기`→`## 해설`.

## 예시 (자사 재집필본)

```markdown
---
id: m01-07
round: 1
round_label: 자사 모의고사 01회
subject: SQL 기본 및 활용
subject_no: 2
question_no: 7
answer: ②
answer_index: 1
difficulty: 중
tags: ["집합 연산자", "UNION", "MINUS", "결과 행 수"]
derived_from: 01-16
has_figure: false
has_sql: true
has_table: true
authored_by: claude
verified: true
reviewed: false
needs_review: true
---

## 문제
다음 세 테이블에 대해 아래 SQL을 수행할 때 반환되는 행의 수는?

## 지문
```sql
SELECT * FROM 사원_서울
UNION
SELECT * FROM 사원_부산
MINUS
SELECT * FROM 퇴사자;
```

**[사원_서울]** / **[사원_부산]** / **[퇴사자]** 표 ...

## 보기
① 2
② 3
③ 4
④ 5

## 해설
UNION으로 중복 제거 합집합을 만든 뒤 MINUS로 퇴사자 행을 뺀다. ...
```
