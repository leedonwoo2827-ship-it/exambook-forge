# 파이프라인 규약 (ocr-output 폴더 단계)

책 루트(`ocr-output-*`)는 단계별 폴더로 앱 간 연결을 맞춘다. exambook-forge는 `01/`을 읽고 `02/03/04/`를 쓴다.

| 폴더 | 단계 | 내용 | 담당 |
|---|---|---|---|
| `00/` | (선택) 원본 | 렌더 이미지/원시 OCR | ocr 툴 |
| `01/` | OCR → 문제 MD | 문항별 구조화 MD (입력) | `260723-ocr` |
| `02/` | 집필 | **자사 모의고사 문제 MD** + `_index.json` + `difficulty_stats.json` + `assets/*.svg` | **exambook-forge** |
| `03/` | 요약 | **요약원고** `summary_*.html`(기본)+`.md` + `assets/*.svg` | **exambook-forge** |
| `04/` | 영상 대본 | **문제 영상 대본** `lesson_*.json` (compy-ui-mujejip 입력) | **exambook-forge** |
| `_rounds/` | (작업) | 회차 데이터 `mNN.json` (build 입력, 단일 진실 원천) | **exambook-forge** |

> `04/`는 원래 파이프라인 README(00~03)에 없던 새 단계다. exambook-forge가 `04/`를 처음 만들 때
> 책 루트 `README.md`에 `04/ | 영상 대본 | 문제 영상 lesson JSON` 행을 추가한다.

## 책 루트 & 권한
- 기본 책 루트: 작업공간 상위의 `ocr-output-260723` 자동 탐색(없으면 사용자에게 경로 질의).
- Claude Desktop 코웍에서 **책 루트 폴더에 읽기/쓰기 권한**을 부여해야 한다.
- 파일 생성 직전 **한 번** "02/03/04에 씁니다" 동의를 받는다(이후 단계에서 반복 질문하지 않음).
- `02/03/04/_rounds`는 없으면 헬퍼/스킬이 자동 생성(미리 만들 필요 없음).

## 파일명 규약
- 문제 MD: `02/mNN-01.md` ~ `mNN-50.md` (자사 회차는 `m` 접두, 원본 기출은 `01-`~`07-`)
- 영상 대본: `04/lesson_mNN.json`
- 요약: `03/summary_{과목}.html` / `.md`
- 회차 데이터: `_rounds/mNN.json`
