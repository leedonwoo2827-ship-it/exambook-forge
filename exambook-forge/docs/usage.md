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

## 영상 툴 연동 (compy-ui-mujejip)
1. `04/lesson_mNN.json`을 영상 툴 `[1 대본]` 탭에 로드 → **[🧩 레슨 저장]**.
2. `include_lecture:false`이므로 문제→보기까지의 **문제 전용 영상**이 만들어진다.
3. 헤더 **⚡ 한 번에 만들기** → 음성/자막/MP4 자동 생성 → `[4 결과]`에서 다운로드.
4. 렌더(TTS/ffmpeg)는 영상 툴에서 실행(플러그인 범위 밖). 음성·자막 수정도 영상 툴 UI에서.

## 검증 체크리스트
- MD: frontmatter 필수 필드, 보기 4개, 정답 인덱스 정합, `_index.json` 개수 = 회차×50
- 분포: 난이도 상12~16/중24~28/하8~10, 정답 ①②③④ 각 8~17
- 영상 JSON: `include_lecture:false`, problem 블록에 tags/explanation_speech 포함
- 요약: HTML 브라우저 렌더 확인, 과목·순서·출처 표기 정합, 인라인 SVG 표시

## hwpx 변환(나중)
- 요약 HTML은 단순 시맨틱 마크업이라 hwpx 변환 친화. SVG는 변환 시 PNG로 래스터화해 치환(원본 유지).
