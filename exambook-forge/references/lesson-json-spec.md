# 영상 lesson JSON 규격 (compy-ui-mujejip 연동)

`compy-ui-mujejip` 영상 툴(파이프라인 #3)은 lesson JSON을 입력받아 슬라이드/자막/대본 → MP4를 만든다.
`build-video-json` 스킬/헬퍼가 회차별로 `04/lesson_{회차코드}.json` 1개를 생성한다(문제 영상 대본).

> **폴더 매핑**: 02 = 문제 MD · 03 = 요약원고 · **04 = 문제 영상 대본 lesson JSON(+04/assets SVG)**.
> 04는 파이프라인 README에 없던 새 단계이므로, 스킬이 04를 만들 때 책 루트 README에도 04 항목을 추가한다.

> ⚠️ **핵심 원칙(파이프라인 #3 핸드오프):** lesson JSON의 텍스트 필드는 **순수 텍스트**다.
> 마크다운(`**볼드**`, 백틱, 이미지 `![]()`, 코드펜스 ```` ``` ````)을 넣지 않는다 —
> 슬라이드/자막/TTS는 마크다운을 해석하지 않아 그대로 노출/낭독된다. (build.py가 자동 순수화하지만,
> 애초에 깔끔하면 최선. `SELECT *`의 단일 `*`는 보존된다.)

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
  "gap_seconds": 1.5,
  "round": "자사 모의고사 01회",
  "voice": "F2",
  "speed": 1.05,
  "ai_reading": false,
  "blocks": [ ... ]
}
```

| 필드 | 값 | 설명 |
|---|---|---|
| `version` | `"1.0"` | 스키마 버전 |
| `kind` | `"lesson"` | 고정 |
| `chapter` | int | 회차 번호 |
| `title` | str | 영상 제목 |
| `subject` / `theme` | str | 과목/테마 (SQLD면 `"SQLD"`/`"sqld"`; 타 과목은 교체). `theme`가 발음 톤 힌트 |
| `scenes_per_problem` | int | 문항당 씬 수 (문제 씬 + 해설 씬, 기본 2) |
| **`include_lecture`** | bool | **`false` = 문제 전용**(문제→보기까지, 정답/해설 제외). `true`면 section/concept 등도 영상 포함 |
| `countdown_seconds` | int | 문제→해설 사이 카운트다운 54321 (기본 5, 0=끔) |
| `gap_seconds` | num | 해설→다음 문제 간격 (기본 1.5) |
| `round` | str | 회차 표시 (출처 표기용) |
| `voice` | str | TTS 보이스 (기본 `"F2"`) |
| `speed` | num | 낭독 속도 (기본 1.05) |
| `ai_reading` | bool | 자동 발음 변환 사용 여부 (기본 false; 낭독 텍스트를 #2가 직접 발음 표기) |
| `blocks` | array | section / concept / problem 블록 배열 |

> `gap_seconds`/`voice`/`speed`/`ai_reading`는 회차 데이터 루트에서 오버라이드 가능(없으면 위 기본값).

## 블록 종류

### section
```json
{ "kind": "section", "title": "데이터 모델링의 이해", "subtitle": "1과목", "narration": "..." }
```

### problem (핵심)
```json
{
  "kind": "problem",
  "number": 7,
  "type": "multiple_choice",
  "question": "질문만 (순수 텍스트) — 지문/표/SQL은 아래 구조화 필드로 분리",
  "passage": "긴 지문 텍스트 (선택, 순수 텍스트) → 렌더가 '지문 씬'으로 분리",
  "sql": "SELECT ... (선택, 코드 문자열 그대로 → 모노스페이스 코드카드)",
  "table": { "columns": ["COL1"], "rows": [["1"], ["2"]] },
  "choices": ["보기1 내용", "보기2 내용", "보기3 내용", "보기4 내용"],
  "hide_choices": false,
  "answer": "②",
  "answer_index": 1,
  "explanation": "해설 (순수 텍스트, 화면·자막용 원문 표기)",
  "explanation_speech": "정답은 두 번입니다. …(소리나는 대로 발음 표기)",
  "difficulty": "중",
  "tags": ["집합 연산자", "UNION", "MINUS"],
  "assets": ["m01-07-venn.svg"]
}
```

**구조화 필드(A — 렌더가 또렷해짐):**
- **`question`엔 질문만.** 지문·표·SQL은 아래 필드로 분리한다.
- **`passage`(선택)**: 긴 지문 → 렌더가 별도 '지문 씬'으로 담음. 순수 텍스트.
- **`sql`(선택)**: 코드 문자열 그대로(펜스 없이) → 모노스페이스 코드카드.
- **`table`(선택)**: `{"columns":[...],"rows":[[...],...]}` 구조 그대로(마크다운/이미지 대신).
- **`hide_choices`(선택)**: `true`면 문제 화면에서 보기 생략(교재 참고형), TTS는 낭독. 생략 시 길이로 자동 판단.
- **`choices`는 원문자(`①②③④`) 없이 순수 텍스트만** — 렌더러가 번호 부여(넣으면 `① ①` 중복).
- **`answer`/`answer_index`는 계속 유지** — 해설이 여러 페이지여도 정답 선지 배너에 사용.
- **`assets`(선택)**: 참조 SVG 파일명 배열. 파일은 `04/assets/`에 동반 복사(04만 봐도 따라오게).
- **`narration_question`/`narration_answer`(선택)**: 문제/정답 낭독본을 따로 발음 표기로 제공.

> ⚠️ **정답 리드(B):** `explanation_speech`를 주면 그것이 **해설 낭독 전체**가 된다.
> #3는 "정답은 N번입니다"를 **자동으로 붙이지 않는다.** 음성에 정답 안내를 넣고 싶으면
> `explanation_speech`를 **"정답은 N번입니다. …"** 로 시작하게 작성한다.

## MD ↔ lesson problem 매핑

| MD(02, 마크다운 유지) | lesson problem(04, 순수 텍스트) |
|---|---|
| `## 문제` | `question` (질문만, 마크다운 제거) |
| `## 지문` 텍스트 / 표 / SQL | `passage` / `table` / `sql` (구조화 분리) |
| `## 보기` ①②③④ | `choices[]` (**원문자 제거**, 내용만) |
| frontmatter `answer` / `answer_index` | `answer` / `answer_index` |
| `## 해설` | `explanation` (마크다운 제거) |
| 회차 데이터 `explanation_speech`(발음체) | `explanation_speech` |
| frontmatter `difficulty` / `tags` | `difficulty` / `tags[]` |
| 참조 SVG 파일명 | `assets[]` (+ `04/assets/`에 파일 복사) |

## 보이는 텍스트 ↔ 들리는 텍스트 (중요)
- **화면/자막용**(`question`, `explanation`, `choices`): **원문 표기 그대로**. 예: `시각`, `1.2%`, `3,000원`.
- **낭독용**(`explanation_speech`, 선택 `narration_*`): **소리나는 대로 발음 표기**로 #2가 집필.
  예: `시각`→"시깍", `1.2%`→"일 점 이 퍼센트", `3,000원`→"삼천 원", `CONNECT BY`→"커넥트 바이", `NVL`→"엔브이엘".
- 이유: #3의 발음사전은 짧은 어휘/단위만 치환 가능하고, 대소리·소수점·복잡한 수/기호는 규칙으로 불가.
  따라서 **낭독 품질은 #2(집필)가 책임**진다. `ai_reading:false`로 두고 발음 표기를 직접 제공.

## 문제 전용(`include_lecture:false`) 규칙
- 이번 목표는 **문제 전용 영상**이므로 회차 JSON은 `include_lecture:false`.
- `explanation`/`explanation_speech`는 담아 두되(추후 강의형 재사용) 툴이 `false`일 때 렌더에서 제외.

## 지문(표/SQL)·도형 처리
- 표/SQL/긴 지문은 `question`에 섞지 말고 **구조화 필드 `table`/`sql`/`passage`로 분리**한다(위 A).
  멀티 테이블 등 복잡한 경우만 `passage`에 마크다운 표로. (build가 lesson 텍스트 필드의 마크다운·펜스 자동 제거)
- 도형은 SVG를 `assets[]`로 참조하고 파일을 `04/assets/`에 동반한다. 툴이 SVG를 직접 못 받으면
  `build.py --rasterize-svg`(또는 hwpx 흐름)로 PNG 치환(svg-conventions.md).

## 유튜브 업로드 글 (JSON에 넣지 않음)
- 유튜브 설명의 챕터 타임스탬프(00:00 문제1 …)는 **렌더가 끝나야** 알 수 있으므로 #3가
  렌더 후 타임라인 추출 → LLM으로 생성한다. **#2는 유튜브 글을 JSON에 넣지 않는다.**
- 대신 `title`/`subject`/`round`/블록별 `tags`·`difficulty`를 충실히 채워 두면 그 LLM 글의 품질이 올라간다.
