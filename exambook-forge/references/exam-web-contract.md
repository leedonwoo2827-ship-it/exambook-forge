# 웹(XAMpass) 소비 계약 — `02/` 문제 · `03/` 요약노트

XAMpass 웹(`260729-new`, `scripts/build_check.py`·`exam_meta.py`)이 우리 산출물을 **직접 읽는다.**
아래는 취향이 아니라 **소비 조건**이다. 어기면 웹 빌드가 멈추거나(대부분) 조용히 어긋난다(일부).
출처: 웹팀 편지 `_context/편지-프로덕트2-3.md`(2026-07-31, 코드 실측). 품목 예: 빅분기 필기 `pd_id=bdae-w`.

---

## 1. `02/` (집필) 계약

### 파일명
- `02/mNN-NN.md` (예 `02/m01-07.md`). **`m` 접두어 필수** — `glob("m*.md")`로만 읽는다.
  OCR 산출물 이름 `01-07.md` 를 그대로 두면 **한 건도 안 읽힌다**(build.py가 `mNN-NN.md`로 산출하므로 자동 충족).

### frontmatter (build.py가 `_rounds/*.json`에서 파생 — 아래를 만족해야 함)
- `id` = `f"m{round:02d}-{question_no:02d}"` (예 `m01-07`). DB upsert 축이라 **한 번 들어가면 못 바꾼다.**
- `round` 정수, `round_label` 문자열(‘자사 ’ 접두어는 걷어냄).
- `subject` 과목명(문자열), **`subject_no` 1..N 연속**(과목 축 — 성적표·이론 링크의 유일한 연결).
- `question_no` 회차 내 **1..N 연속(빈칸 없음)** — 번들이 `ceil(question_no/10)`이라 80문항 → `m01-1..m01-8`.
- `answer_index` **0-base**, `answer`(①②③④)와 **반드시 일치**.
- `difficulty` 상/중/하, `tags`(성적표 ‘취약 개념’의 근거).

### 본문 섹션 — 순서 고정: `## 문제` → `## 지문`(없으면 생략) → `## 보기` → `## 해설`
- **`## 지문`은 마크다운 그대로.** 표(`|`)·코드펜스·`![](assets/x.svg)`·`**굵게**`·`` `코드` `` 를 화면이 렌더한다.
  표/코드를 별도 필드로 **쪼개지 않는다**(쪼개면 두 번 렌더됨).
- **`## 보기`의 번호표식(①·1.)은 파서가 뗀다** → 화면이 다시 붙이므로 남겨도 되고, 빌드가 정리한다.
- 도식은 `02/assets/`(SVG 권장). 없으면 그림만 사라지고 경고.

### 웹 빌드가 멈추는 조건(전부 목록으로 찍고 중단)
round/question_no 비정수 · id 규칙 불일치 · `## 문제` 비었음 · 보기 2개 미만 ·
`answer_index` 범위 밖 · `subject`/`subject_no` 없음. → **build.py+validate.py 통과 = 계약 통과.**

### 스스로 확인
```bash
python scripts/exam_meta.py <book>                       # 과목 분포·회차
python scripts/build_check.py --book <book> --pd bdae-w \
       --pd-name "빅데이터분석기사 필기" --src 02 --out /tmp/chk
```
**과목이 N종(빅분기=4)으로 나와야 한다.** 1종이면 `subject`가 전부 같은 값 → 과목필터·성적표가 죽는다.

---

## 2. `03/` (요약노트) 계약

### 읽는 것은 `summary_*.html` 뿐 (`.md`는 무시)
- `03/summary_planning.html`(1과목) · `summary_explore.html`(2) · `summary_modeling.html`(3) ·
  `summary_interpret.html`(4) · (선택)`summary_index.html`. 파일명 **ASCII 권장**(한글이면 리네임되어 추적 곤란).

### `<h1>N과목 · 이름</h1>` 이 과목 번호를 정한다 — 핵심
- 빌드가 `(\d+)\s*과목` 로 `N`을 뽑는다. **그 `N` = `02/`의 `subject_no`.** 안 걸리면 `99`로 밀리고
  라벨이 파일명이 된다(**에러 없이** 틀어짐 → 눈으로 확인해야 함). `<h1>` 없으면 `<title>`, 둘 다 없으면 99.
  예: `<h1>2과목 · 빅데이터 탐색</h1>`.

### self-contained 1파일 (shadow DOM에 `<style>`+`<body>`만 굽는다)
- **금지**: `<link rel="stylesheet">`, `<script>`(인라인·외부 모두 실행 안 됨), 웹폰트·CDN·`fetch()`.
  `body{}` 셀렉터는 `:host`로 치환됨.
- CSS는 `<style>` 안에, 그림은 `03/assets/`에 두고 상대경로(`assets/x.png`) — 빌드가 `theory/assets/`로 고침.
- 인터랙션은 CSS만으로(`<details>`·`:hover`·`:target`).
- 분량: **과목당 ≤ 40KB**(문제집 첫 로드에 통째로 내려감, 카페24 트래픽 한도).

### 스스로 확인
```bash
python scripts/build_check.py --book <book> --pd bdae-w --src 02 --out /tmp/chk
# /tmp/chk/pd/bdae-w/theory.js 의 window.THEORY 에 sub:1,2,3,4 가 다 나오는지, label이 과목명인지 확인
```

---

## 3. 영상(04/·05/)은 웹-only 품목에선 선택
- 웹 빌드는 `05/`가 없으면 `02/`를 직접 읽는다(`--src auto`). 빅분기 필기는 **문제풀이·성적표·이론·게시판이
  04/05 없이 동작**한다. 나중에 영상을 붙여도 번들 이름(`m01-1..m01-8`)이 지금 계산과 같아 `pr_key`가
  안 갈리므로 재임포트 불필요.
- 영상 매핑은 품목별로: `data/youtube_map.bdae-w.json`(품목 간 번들 이름이 겹쳐 한 파일에 두면 섞임).
