# 영상 lesson JSON 규격 (compy-ui-mujejip 연동)

`compy-ui-mujejip` 영상 툴은 lesson JSON을 입력받아 슬라이드/자막/대본 → MP4를 만든다.
`build-video-json` 스킬/헬퍼가 회차별로 `04/lesson_{회차코드}.json` 1개를 생성한다(문제 영상 대본).

> **폴더 매핑**: 02 = 문제 MD · 03 = 요약원고 · **04 = 문제 영상 대본 lesson JSON**.
> 04는 파이프라인 README에 없던 새 단계이므로, 스킬이 04를 만들 때 책 루트 README에도 04 항목을 추가한다.

## 루트 필드

```json
{
  "version": "1.0",
  "kind": "lesson",
  "chapter": 1,
  "title": "자사 모의고사 01회 — 문제 풀이(문제 전용)",
  "subject": "SQLD",
  "theme": "sqld",
  "scenes_per_problem": 2,
  "include_lecture": false,
  "countdown_seconds": 5,
  "round": "자사 모의고사 01회",
  "blocks": [ ... ]
}
```

| 필드 | 값 | 설명 |
|---|---|---|
| `version` | `"1.0"` | 스키마 버전 |
| `kind` | `"lesson"` | 고정 |
| `chapter` | int | 회차 번호 |
| `title` | str | 영상 제목 |
| `subject` / `theme` | str | 과목/테마 (SQLD면 `"SQLD"`/`"sqld"`; 타 과목은 교체) |
| `scenes_per_problem` | int | 문항당 씬 수 (기본 2) |
| **`include_lecture`** | bool | **`false` = 문제 전용**(문제→보기까지, 정답/해설 제외). `true` = 정답·해설까지 강의형 |
| `countdown_seconds` | int | 문제 후 카운트다운(자가 풀이용) |
| `round` | str | 회차 표시 (출처 표기용) |
| `blocks` | array | section / concept / problem 블록 배열 |

## 블록 종류

### section
```json
{ "kind": "section", "title": "1과목 데이터 모델링의 이해", "subtitle": "1~10번", "narration": "..." }
```

### concept (선택)
```json
{ "kind": "concept", "heading": "계층형 쿼리 핵심", "bullets": ["START WITH", "CONNECT BY PRIOR"], "narration": "..." }
```

### problem (핵심)
```json
{
  "kind": "problem",
  "number": 7,
  "type": "multiple_choice",
  "question": "문제 지시문 (지문 표/SQL은 여기에 포함하거나 별도 필드로)",
  "choices": ["① ...", "② ...", "③ ...", "④ ..."],
  "answer": "②",
  "answer_index": 1,
  "explanation": "해설 텍스트",
  "explanation_speech": "TTS 낭독용 해설(숫자/영어 읽기 자연스럽게 풀어쓴 버전)",
  "difficulty": "중",
  "tags": ["집합 연산자", "UNION", "MINUS"]
}
```

## MD ↔ lesson problem 매핑

| MD | lesson problem |
|---|---|
| `## 문제` (+ `## 지문`) | `question` |
| `## 보기` ①②③④ | `choices[]` |
| frontmatter `answer` | `answer` |
| frontmatter `answer_index` | `answer_index` |
| `## 해설` | `explanation` |
| (해설의 음성 낭독본) | `explanation_speech` |
| frontmatter `difficulty` | `difficulty` |
| frontmatter `tags` | `tags[]` |

## 문제 전용(`include_lecture:false`) 규칙
- 이번 프로토타입 목표는 **문제 전용 영상**이므로 회차 JSON은 `include_lecture:false`.
- `explanation`/`explanation_speech`는 JSON에 담아 두되(추후 강의형 재사용), 툴이 `false`일 때 렌더에서 제외.
- `explanation_speech`: TTS 자연발화를 위해 숫자·영문을 한글 발음으로 풀어쓴다.
  예: `CONNECT BY` → "커넥트 바이", `NVL` → "엔브이엘", `10.5` → "십 점 오".
  (툴에 자동 발음 변환이 있으나, 애매한 약어·기호는 미리 풀어두면 품질이 좋다.)

## 지문(표/SQL) 처리
- 표/SQL 지문은 `question` 문자열 안에 마크다운/코드로 함께 넣는다(슬라이드 렌더가 텍스트 기반).
- 그림/도형은 SVG를 슬라이드 배경/삽입으로 쓴다. 툴이 SVG를 직접 못 받으면 `build.py`가
  SVG→PNG 래스터화하여 참조를 바꾼다(‑‑rasterize-svg 옵션; svg-conventions.md 참고).
