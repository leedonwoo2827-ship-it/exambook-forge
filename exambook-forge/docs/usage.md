# 상세 사용법

## 설치 (GitHub)
```
/plugin marketplace add leedonwoo2827-ship-it/exambook-forge
/plugin install exambook-forge@exambook-forge
```
레포/오너 이름이 다르면 `.claude-plugin/marketplace.json`의 `owner.name`과 `<owner>/exambook-forge`를 맞춘다.

## 커맨드 & 인자

| 커맨드 | 인자(선택) | 산출 |
|---|---|---|
| `/exam-all` | `rounds=3` `book=<경로>` `subject=SQLD` | 02 문제 + 04 영상 JSON + 03 요약 |
| `/exam-questions` | `rounds=3` `round=m01` `book=<경로>` | 02 문제 + 04 영상 JSON |
| `/exam-summary` | `book=<경로>` `subject=all` | 03 요약(HTML+MD) |

> 슬라이드/영상 번들(05)은 `build-deck` 스킬로: `04/lesson_mNN.json` → `05/mNN/`(밝은 deck.html + 리모션 _series + review.json).

`/exam-all`이 한 번에 끝나면 좋고, 무거우면 `/exam-questions` → `/exam-summary` 2단계로 나눠 실행.

## 단계별 수동 실행(헬퍼 직접 호출)
```
# 1) 회차 데이터 검증
python "<PLUGIN>/scripts/validate.py" --rounds-dir "<book>/_rounds"
# 2) 빌드(02 문제 MD + 04 영상 대본 JSON + index/stats)
python "<PLUGIN>/scripts/build.py" --book "<book>"
#   특정 회차만: --round m01   /   미리보기: --dry-run
```
`<PLUGIN>` = 설치된 플러그인 루트(스킬에서는 `${CLAUDE_PLUGIN_ROOT}`).

## 긴 영상 분할 (split.py)
한 회차(≈50문항)가 한 편으로 너무 길면(예: 60분) 여러 편으로 쪼갠다. 문항을 균등 분할하고
각 편에 과목 섹션 헤더를 유지, 루트 필드를 복사한다.
```
python "<PLUGIN>/scripts/split.py" --input "<book>/04/lesson_m01.json" --parts 5 --prefix 01
#   → 04/01-1.json ... 04/01-5.json  (각 ~10문항)
#   --outdir 로 출력 폴더 지정, --dry-run 으로 미리보기
```

## 05 번들 만들기 (deck.html 슬라이드 + 리모션 대본)
```
# 04/lesson_mNN.json → 05/mNN/ 골격(deck.html 스텁 + _series + review.json)
python "<PLUGIN>/scripts/bundle.py" --book "<book>" --round m01
#   기존 집필 deck.html 보존(덮어쓰려면 --force)
```
이어서 `build-deck` 스킬로 `05/mNN/source/deck.html`을 [`../references/deck-conventions.md`](../references/deck-conventions.md)에 맞춰 다듬는다(밝은 팔레트, 슬라이드=씬 1:1).

## 영상 툴 연동 (chodangi-mp4 = 일반영상, 리모션 = 키네틱)
1. **일반영상(#3):** `render.bat mNN` → `source/deck.html` 캡처(`images/slide_*.png`) + Supertonic3 자막/음성 + ffmpeg → `05/mNN/draft/mNN.static.mp4` + `mNN.ko.vtt`. **자막·음성 최종 OK는 여기서**(#3 웹 UI 또는 배치 재실행).
2. **리모션영상(클로드 데스크탑):** `05/mNN/script/mNN_script.json`(_series) + `source/`·`images/`·`audio/` → `draft/mNN.motion.mp4`. `review.json.motionVideo` 갱신.
3. `04/lesson_mNN.json`은 #3의 대본/음성 컴파일 입력으로 계속 유지(deck=화면, lesson=텍스트/음성). 렌더는 플러그인 범위 밖.
4. 규약 단일 진실: [`../references/pipeline-output-structure.md`](../references/pipeline-output-structure.md).

## 검증 체크리스트
- MD: frontmatter 필수 필드, 보기 4개, 정답 인덱스 정합, `_index.json` 개수 = 회차×50
- 분포: 난이도 상12~16/중24~28/하8~10, 정답 ①②③④ 각 8~17
- 영상 JSON: `include_lecture:false`, problem 블록에 tags/explanation_speech 포함
- 요약: HTML 브라우저 렌더 확인, 과목·순서·출처 표기 정합, 인라인 SVG 표시

## hwpx 변환(나중)
- 요약 HTML은 단순 시맨틱 마크업이라 hwpx 변환 친화. SVG는 변환 시 PNG로 래스터화해 치환(원본 유지).
