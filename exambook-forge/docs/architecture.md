# 아키텍처 — 동작 방식 · 레포 구조 · 데이터 흐름

## 스킬 + 헬퍼 스크립트

집필·설계·검수(판단)는 **스킬**이, 반복적·결정적 변환(회차 데이터 → MD/JSON/index/stats, SVG 자산)은
**Python 헬퍼**가 담당한다.

```
1) 스킬이 01/ 문항을 분석 → 회차 데이터 <book>/_rounds/mNN.json 을 "집필"
   (개념·난이도 유지, 표면 전면 재작성, 출제 순서 변경, tags·난이도·SVG·derived_from 포함)
2) validate.py 로 스키마/보기 4개/정답 인덱스/개수/분포 점검
3) build.py 가 _rounds/mNN.json → 02/ 문제 MD + 04/lesson_mNN.json 결정적 생성,
   02/_index.json·difficulty_stats.json 재집계, assets SVG 기록
4) summary-note 스킬이 01/(+02/) 해설을 과목→항목→상세로 종합·중복정돈 → 03/ HTML(기본)+MD
```

회차 데이터(`_rounds/mNN.json`)가 **단일 진실 원천**이며, 여기서 MD·영상 JSON·index·stats가 모두 파생된다.

## 레포 구조

```
exambook-forge/                      ← 플러그인 (marketplace source: ./exambook-forge, CLAUDE_PLUGIN_ROOT)
  .claude-plugin/plugin.json
  commands/    exam-all.md · exam-questions.md · exam-summary.md
  skills/      generate-mockexam/ · author-questions/ · svg-diagram/ · build-video-json/ · summary-note/
  scripts/     build.py · validate.py            (표준 라이브러리만, Python 3.11+)
  references/  ocr-md-format · lesson-json-spec · round-data-schema · sqld-syllabus ·
               authoring-rules · svg-conventions · summary-format
  docs/        architecture · pipeline · usage
.claude-plugin/marketplace.json  ← 마켓플레이스 (레포 루트)
```

## 회차 데이터 위치 (`_rounds`)
- 스킬은 회차 데이터를 **책 루트 아래 `_rounds/mNN.json`** 에 저장한다(`<book>/_rounds/`).
- 이유: 산출물(02/03/04)과 동일한 권한 범위 안에 두어 Claude Desktop 코웍에서 한 번의 폴더 권한으로 처리.
- 로컬 개발 시엔 임의 폴더를 `--rounds-dir`로 지정 가능(레포 내 `rounds/`는 예시/샘플용).

## 확장
- 회차 수: 1회분→3회차(프로토) → 7회분→20회차. `_rounds/`에 회차 JSON을 추가하고 build 재실행.
- 과목 교체: `round_data`의 `subject`/`subject_no`/`subject_default`/`theme`만 바꾸면
  정보처리기사·컴퓨터활용능력 등으로 동일 파이프라인 재사용(`sqld-syllabus.md`에 해당 과목 개념 풀 추가).
