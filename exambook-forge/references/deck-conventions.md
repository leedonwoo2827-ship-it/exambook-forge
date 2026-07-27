# deck.html 슬라이드 규약 (pressplay 이식 · 밝은 테마)

> 회차별 `05/<회차>/source/deck.html` 을 집필하는 규약. pressplay `DESIGN.md`의 덱 규칙을
> 기출 문제풀이 영상에 맞게 이식하되 **밝은 팔레트를 기본**으로 한다(기존 Pillow 슬라이드가 어두웠던 문제 해소).
> 슬라이드는 **1920×1080 고정**이며 #3(chodangi-mp4)가 각 `.slide`를 캡처해 `images/slide_%02d.png`로 만든다.

## 0. 기본 골격

공유 자산 `_deck.css` / `_deck.js` 를 링크하고, `:root`에 회차/과목 팔레트 4색만 재정의한다.

```html
<!doctype html><html lang="ko"><head>
<meta charset="utf-8"/>
<title>자사 모의고사 01회 — 문제 풀이</title>
<link rel="stylesheet" href="_deck.css"/>
<style>:root{--brand:#2563EB;--brand-2:#60A5FA;--soft:#EFF6FF;--brand-ink:#1E3A8A}</style>
</head><body>
  <div id="deck" data-title="자사 모의고사 01회">
    <section class="slide cover">…</section>
    <section class="slide content">…</section>
    …
  </div>
  <button id="fs">⛶ 전체화면</button>
  <div class="nav"><button id="prev">‹</button><button id="next">›</button></div>
  <script src="_deck.js"></script>
</body></html>
```

## 1. 팔레트 (밝게)

과목/회차별로 `:root` 4색만 교체. 예시(모두 밝은 배경 위 진한 브랜드):

| 과목/톤 | --brand | --brand-2 | --soft | --brand-ink |
|---|---|---|---|---|
| SQLD(파랑, 기본) | `#2563EB` | `#60A5FA` | `#EFF6FF` | `#1E3A8A` |
| 정보처리(청록) | `#0D9488` | `#5EEAD4` | `#F0FDFA` | `#115E59` |
| 컴활(보라) | `#7C3AED` | `#C4B5FD` | `#F5F3FF` | `#5B21B6` |
| 회계/경영(앰버) | `#D97706` | `#FCD34D` | `#FFFBEB` | `#92400E` |

- **배경은 항상 밝게**(카드/슬라이드 `--paper:#FFFFFF` 유지). 코드블록(`pre.sql`)만 어두운 대비.
- 임의 색은 직접 hex. SVG 내부에도 빈 줄 없이 hex 직접 사용.

## 2. 슬라이드 종류 & class

| kind | class | 용도 | 캡처 대응 |
|---|---|---|---|
| 표지 | `.slide.cover` | 회차 타이틀 | `slide_00.png` |
| 과목 섹션 | `.slide.content` (`.tag`=과목) | 과목 전환 헤더 | 섹션 씬 |
| 문제 | `.slide.content` + `.qcard` | 문제+지문+보기 | 문제 씬 |
| 카운트다운 | `.slide.countdown` | "생각할 시간" 5→1 | #3가 54321 오버레이(정적 프레임 대체 가능) |
| 정답·해설 | `.slide.content` + `.answer-badge`+`.explain` | 정답 하이라이트+해설 | 해설 씬 |

## 3. 문항 → 슬라이드 매핑 (회차당 문항 多)

문항 1개 = 최소 2씬(문제 씬 + 해설 씬), `scenes_per_problem`(기본 2)과 대응. 규칙:
- **문제 씬**: `.qcard`에 `.qnum`("N번 문제") · `.qtext`(질문) · 필요 시 `.passage`/`pre.sql`/`table`/`figure`, 그리고 `.choices`(보기).
- **보기 과다**: 보기 총합이 매우 길면(참고형) 보기를 생략하고 "보기는 교재를 참고하세요" 안내(자막/음성은 유지). lesson `hide_choices:true`와 동일 규칙.
- **해설 씬**: `.answer-badge`("정답 ②") + 정답 보기 `.choice.correct` 하이라이트 + `.explain`(해설). 해설이 길면 해설 씬을 여러 장으로 분할(각 씬 = 슬라이드 1장).
- **출처**: `.source-chip`("출처 · 자사 모의고사 01회 7번") 우상단.
- **표/코드/도형**: 본문 텍스트에 섞지 말고 `table`/`pre.sql`/`figure>svg`(SVG는 `svg-diagram` 스킬 산출을 인라인)로 분리 — 렌더가 또렷해진다.

## 4. 컴포넌트 예시

문제 슬라이드:
```html
<section class="slide content">
  <span class="source-chip">출처 · 자사 모의고사 01회 7번</span>
  <div class="qcard">
    <div class="qnum">7번 문제</div>
    <div class="qtext">다음 중 집합 연산자에 대한 설명으로 옳지 않은 것은?</div>
    <pre class="sql">SELECT deptno FROM emp
MINUS
SELECT deptno FROM dept;</pre>
    <ul class="choices">
      <li class="choice"><span class="marker">1</span><span>UNION 은 중복 행을 제거한다.</span></li>
      <li class="choice"><span class="marker">2</span><span>UNION ALL 은 중복을 제거하지 않는다.</span></li>
      <li class="choice"><span class="marker">3</span><span>INTERSECT 는 교집합을 반환한다.</span></li>
      <li class="choice"><span class="marker">4</span><span>MINUS 는 정렬을 보장하지 않는다.</span></li>
    </ul>
  </div>
</section>
```

정답·해설 슬라이드(정답 보기에 `.correct`):
```html
<section class="slide content">
  <div class="s-head"><span class="tag">정답 및 해설</span><h2>7번</h2></div>
  <div class="answer-badge">정답 ②</div>
  <ul class="choices">
    <li class="choice"><span class="marker">1</span><span>UNION 은 중복 행을 제거한다.</span></li>
    <li class="choice correct"><span class="marker">2</span><span>UNION ALL 은 중복을 제거하지 않는다.</span></li>
    …
  </ul>
  <div class="explain">MINUS 는 집합 차집합이며 …</div>
</section>
```

## 5. 규칙 요약 (체크리스트)

- 슬라이드 1장 = 씬 1개(캡처 인덱스와 1:1). 씬 순서 = `images/slide_%02d.png` 순서 = `audio/scene_%02d.wav` 순서.
- 표지/섹션 제외한 본문 슬라이드는 시각요소(카드·표·도형·하이라이트) 최소 1개 포함(불릿만 금지).
- 텍스트는 **자막 원문 표기**(deck 화면=자막). 발음(낭독)은 lesson `explanation_speech`/`review.json.narration_text`가 담당 — deck 에는 넣지 않는다.
- 원문자(①②③④)를 텍스트에 직접 넣지 말고 `.choice .marker`(숫자)로 표기(중복 방지).
- `_deck.css`/`_deck.js` 는 회차 폴더에 함께 복사되므로 상대경로 `href="_deck.css"`/`src="_deck.js"`.
- 자세한 산출 폴더/파일명은 [`pipeline-output-structure.md`](./pipeline-output-structure.md).
