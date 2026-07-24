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
3. lesson JSON 규칙 확인 (파이프라인 #3 핸드오프 준수):
   - `include_lecture: false` (문제 전용: 문제→보기, 정답/해설 렌더 제외).
   - **모든 텍스트 필드는 순수 텍스트** — `**볼드**`·백틱·이미지 `![]()`·코드펜스 ``` 금지
     (build.py가 자동 순수화; 단일 `*`(SELECT *)는 보존).
   - **`choices`는 원문자(①②③④) 없이 내용만** — 렌더러가 번호 부여(중복 방지).
   - **보이는 텍스트 ↔ 들리는 텍스트**: `question`/`explanation`은 원문 표기(시각, 1.2%),
     `explanation_speech`는 소리나는 대로 발음 표기(시깍, "일 점 이 퍼센트", "커넥트 바이") — #2가 집필.
   - **구조화 필드**: `question`엔 질문만. 지문→`passage`, 표→`table:{columns,rows}`, SQL→`sql`(코드 그대로),
     아주 긴 보기→`hide_choices:true`(화면 생략·TTS 낭독). `answer`/`answer_index`는 유지(정답 배너).
   - **정답 리드**: #3는 "정답은 N번" 자동 삽입 안 함 → 음성에 정답 안내를 넣으려면 `explanation_speech`를
     "정답은 N번입니다. …"로 시작하게 집필.
   - 도형: `assets[]`에 참조 SVG 파일명, 파일은 `04/assets/`에 동반 복사됨.
   - 루트 고정값: `gap_seconds`·`voice`·`speed`·`ai_reading`(회차 데이터로 오버라이드 가능).
   - **유튜브 글은 JSON에 넣지 않는다**(타임스탬프는 렌더 후 #3가 생성). `title`/`subject`/`round`/`tags`/`difficulty`만 충실히.
4. 안내: 생성된 `04/lesson_mNN.json`(+`04/assets/`)을 영상 툴 `[1 대본]` 탭에 로드 → 저장 → 렌더.

## 산출
- `04/lesson_m01.json`, `lesson_m02.json`, `lesson_m03.json` ...

## 주의
- 렌더(TTS/자막/ffmpeg/MP4)는 이 스킬 범위 밖(사용자가 영상 툴에서 실행). 여기선 JSON까지.
- 강의형(정답·해설 포함) 영상이 필요하면 향후 `include_lecture:true` 옵션으로 재빌드.
