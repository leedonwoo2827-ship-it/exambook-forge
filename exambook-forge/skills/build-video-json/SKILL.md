---
name: build-video-json
description: 회차 데이터/문항 MD를 compy-ui-mujejip 영상 툴용 lesson JSON(문제 전용, include_lecture=false)으로 변환해 04 폴더에 넣어야 할 때. 문제→보기까지만 담고 정답/해설은 제외한 "문제 영상 대본"을 만든다.
metadata:
  group: 자격시험 파이프라인
  stage: 영상 대본
  produces: 04/lesson_mNN.json
---

# build-video-json (문제 영상 대본 JSON)

## When to use
- 재집필된 회차의 문제를 영상으로 만들 때. 산출물은 `compy-ui-mujejip`의 `[1 대본]` 입력.

## 입력
- 회차 데이터 `<book>/_rounds/mNN.json` (author-questions 산출), 규격 `${CLAUDE_PLUGIN_ROOT}/references/lesson-json-spec.md`.

## 절차
1. 검증: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" --rounds-dir "<book>/_rounds"`.
2. 빌드: `python "${CLAUDE_PLUGIN_ROOT}/scripts/build.py" --book "<book>"`
   (특정 회차만: `--round m01`, 미리보기: `--dry-run`).
   → `02/*.md`와 함께 `04/lesson_mNN.json`을 생성한다.
3. lesson JSON 규칙 확인:
   - `include_lecture: false` (문제 전용: 문제→보기, 정답/해설 렌더 제외).
   - `problem` 블록에 `question`(지문 포함)·`choices`(①②③④)·`answer`·`answer_index`·
     `explanation`·`explanation_speech`·`difficulty`·`tags`.
   - `explanation_speech`는 TTS 자연발화를 위해 기호/영문 약어를 한글 발음으로 풀어쓴다
     (예: `CONNECT BY`→"커넥트 바이", `NVL`→"엔브이엘").
4. 안내: 생성된 `04/lesson_mNN.json`을 영상 툴 `[1 대본]` 탭에 로드 → 저장 → 렌더.

## 산출
- `04/lesson_m01.json`, `lesson_m02.json`, `lesson_m03.json` ...

## 주의
- 렌더(TTS/자막/ffmpeg/MP4)는 이 스킬 범위 밖(사용자가 영상 툴에서 실행). 여기선 JSON까지.
- 강의형(정답·해설 포함) 영상이 필요하면 향후 `include_lecture:true` 옵션으로 재빌드.
