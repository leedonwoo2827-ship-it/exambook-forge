# exambook-forge

기출문제집 1권(OCR 구조화 MD)을 재료로 **자사 N회차 모의고사**를 재집필하고,
**문제 영상 대본(JSON)** 과 **요약원고(HTML)** 까지 만드는 Claude Desktop / Claude Code 플러그인.

- 입력: `ocr-output-*/01/` (문항별 구조화 MD)
- 출력: `02/` 문제 MD · `03/` 요약원고(HTML+MD) · `04/` 문제 영상 대본 `lesson_*.json`
- 다운스트림: [`compy-ui-mujejip`](https://github.com/leedonwoo2827-ship-it/compy-ui-mujejip)가 `04/` JSON을 MP4로 렌더

## 설치

```
/plugin marketplace add leedonwoo2827-ship-it/exambook-forge
/plugin install exambook-forge@exambook-forge
```

설치 후 Claude Desktop 코웍에서 책 루트(예: `D:\00work\ocr-output-260723`) 폴더에 읽기/쓰기 권한을 부여하세요.

## 사용법

| 커맨드 | 하는 일 |
|---|---|
| `/exam-all` | 문제(02) + 영상 대본(04) + 요약원고(03) **한 번에** |
| `/exam-questions` | 문제 일괄: 재집필 MD(02) + 문제 영상 JSON(04) |
| `/exam-summary` | 요약 일괄: 요약원고 HTML+MD(03) |

## 예시 프롬프트

```
SQLD 기출 1회분으로 자사 모의고사 3회차를 만들어줘. /exam-all
```
```
/exam-questions rounds=3 book=D:\00work\ocr-output-260723
```
```
1회분 해설을 모아서 과목별 요약원고 만들어줘. /exam-summary
```
```
방금 만든 3회차 문제만 영상 대본 JSON으로 04 폴더에 만들어줘.
```

> 파이썬 3.11+ 필요(헬퍼 스크립트). 02/03/04 폴더는 없으면 자동 생성됩니다.

## 더 알아보기 (docs/)

- [`docs/architecture.md`](exambook-forge/docs/architecture.md) — 동작 방식(스킬+헬퍼), 레포 구조, 데이터 흐름
- [`docs/pipeline.md`](exambook-forge/docs/pipeline.md) — ocr-output 파이프라인 규약(01→02→03→04), 폴더 매핑
- [`docs/usage.md`](exambook-forge/docs/usage.md) — 상세 사용법, 커맨드 인자, 영상 툴 연동, 검증
- `exambook-forge/references/` — 집필 규칙·포맷 규격·SQLD 개념 풀 등 지식베이스
