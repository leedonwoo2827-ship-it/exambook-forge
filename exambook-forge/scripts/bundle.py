#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam-forge bundle scaffolder (파이프라인 05 단계).

04/lesson_mNN.json 을 읽어 pressplay식 per-회차 번들 05/<회차>/ 을 만든다:
  - source/deck.html          : 밝은 HTML 슬라이드 스텁(집필 시작점, build-deck 스킬이 채움)
  - source/_deck.css/_deck.js : 공유 덱 자산 복사
  - source/lesson_mNN.json    : lesson JSON 복사(추적)
  - script/mNN_script.json    : 리모션 _series 대본
  - review.json               : 매니페스트 스켈레톤(시간/영상 필드는 #3·리모션이 채움)
  - images/ audio/ subtitles/ draft/ : 빈 폴더(하위 툴이 채움)

씬 모델(캡처 인덱스와 1:1):
  cover → (과목 section → [문제 question · 카운트다운 · 정답/해설 answer · gap] × 문항)
  capture=True 씬(cover/section/problem/answer)만 deck 슬라이드가 있다(순서 = deck 슬라이드 순서).
  capture=False 씬(countdown/gap)은 #3가 생성한다. 규약: references/pipeline-output-structure.md

표준 라이브러리만 사용. Python 3.11+.

사용:
  python bundle.py --book D:/00work/ocr-output-260723 --round m01
  python bundle.py --book D:/00work/ocr-output-260723            # 04/의 모든 lesson_*.json
  python bundle.py --book ... --round m01 --force                # 기존 deck.html 덮어쓰기
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import circled, to_plain, to_speech  # noqa: E402  (자막/발음 순수화 재사용)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DECK_ASSETS = PLUGIN_ROOT / "assets" / "slides"
BUNDLE_SUBDIRS = ("source", "images", "audio", "subtitles", "script", "draft")


# ----------------------------------------------------------------------------- 씬 모델
def build_scenes(lesson: dict) -> list[dict]:
    """lesson blocks → 전 씬 목록(인덱스 = slide_%02d/scene_%02d 대응)."""
    cd = int(lesson.get("countdown_seconds", 5) or 0)
    gap = float(lesson.get("gap_seconds", 1.5) or 0)
    round_label = lesson.get("round") or lesson.get("title", "")
    scenes: list[dict] = []

    def add(kind: str, capture: bool, heading: str, narration: str = "",
            narration_text: str = "", **extra) -> None:
        scenes.append({
            "kind": kind, "capture": capture, "heading": heading,
            "narration": to_plain(narration), "narration_text": to_speech(narration_text or narration),
            **extra,
        })

    # 표지
    add("cover", True, lesson.get("title", round_label),
        narration=f"{round_label}. 문제 풀이를 시작합니다.")

    for b in lesson.get("blocks", []):
        kind = b.get("kind")
        if kind == "section":
            add("section", True, f"{b.get('subtitle','')} · {b.get('title','')}".strip(" ·"),
                narration=b.get("narration", ""))
        elif kind == "problem":
            n = b.get("number")
            q = b.get("question", "")
            # 문제 씬
            add("problem", True, f"{n}번 문제", narration=q,
                narration_text=b.get("narration_question") or q, number=n)
            # 카운트다운(생각할 시간) — 무음, #3 생성
            if cd > 0:
                add("countdown", False, "생각할 시간", countdown_seconds=cd, number=n)
            # 정답·해설 씬
            ans = b.get("answer") or circled(b.get("answer_index", 0))
            add("answer", True, f"{n}번 · 정답 {ans}",
                narration=b.get("explanation", ""),
                narration_text=b.get("narration_answer") or b.get("explanation_speech") or b.get("explanation", ""),
                number=n)
            # 간격 — 무음, #3 생성
            if gap > 0:
                add("gap", False, "", gap_seconds=gap, number=n)

    for i, s in enumerate(scenes):
        s["scene"] = i
        s["image"] = f"slide_{i:02d}.png"
        s["audio"] = f"scene_{i:02d}.wav"
        s["durSec"] = 0
        s["startSec"] = 0
    return scenes


def build_series(lesson: dict, scenes: list[dict]) -> dict:
    return {
        "version": "1.0",
        "kind": "series",
        "round": lesson.get("round", ""),
        "subject": lesson.get("subject", ""),
        "theme": lesson.get("theme", ""),
        "voice": lesson.get("voice", "F2"),
        "speed": lesson.get("speed", 1.05),
        "scenes": [
            {k: s[k] for k in (
                "scene", "kind", "capture", "heading", "narration", "narration_text",
                "image", "audio", "durSec", "startSec")
             if k in s} | ({"countdown_seconds": s["countdown_seconds"]} if "countdown_seconds" in s else {})
            for s in scenes
        ],
    }


def build_review(lesson: dict, scenes: list[dict]) -> dict:
    return {
        "title": lesson.get("title", ""),
        "totalSeconds": 0,
        "slides": [
            {
                "index": s["scene"], "heading": s["heading"],
                "narration": s["narration"], "narration_text": s["narration_text"],
                "image": s["image"], "audio": s["audio"],
                "durSec": 0, "startSec": 0, "cues": [],
            }
            for s in scenes
        ],
        "staticVideo": None,
        "staticSubtitles": None,
        "motionVideo": None,
    }


# ----------------------------------------------------------------------------- deck 스텁
_LEAD_MARKER = re.compile(r"^\s*(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.)])\s*")


def _strip_lead_marker(s: str) -> str:
    """보기 앞의 원문자(①)·번호(1./1)) 접두 제거 → 렌더러 marker 와 중복 방지."""
    return _LEAD_MARKER.sub("", str(s)).strip()


def _choices_ul(choices: list, correct_index: int | None = None) -> str:
    lis = []
    for i, c in enumerate(choices):
        cls = "choice correct" if (correct_index is not None and i == correct_index) else "choice"
        text = html.escape(_strip_lead_marker(to_plain(str(c))))
        lis.append(
            f'      <li class="{cls}"><span class="marker">{i+1}</span>'
            f'<span>{text}</span></li>')
    return '    <ul class="choices">\n' + "\n".join(lis) + "\n    </ul>"


def _problem_body(b: dict) -> str:
    parts = []
    if b.get("passage"):
        parts.append(f'    <div class="passage">{html.escape(to_plain(b["passage"]))}</div>')
    if b.get("sql"):
        parts.append(f'    <pre class="sql">{html.escape(str(b["sql"]).strip())}</pre>')
    if b.get("table"):
        t = b["table"]
        cols = "".join(f"<th>{html.escape(str(c))}</th>" for c in t.get("columns", []))
        rows = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
            for r in t.get("rows", []))
        parts.append(f'    <table><thead><tr>{cols}</tr></thead><tbody>{rows}</tbody></table>')
    return ("\n" + "\n".join(parts)) if parts else ""


def build_deck_stub(lesson: dict) -> str:
    round_label = lesson.get("round", "")
    title = lesson.get("title", round_label)
    theme = (lesson.get("theme") or "").lower()
    palettes = {
        "sqld": ("#2563EB", "#60A5FA", "#EFF6FF", "#1E3A8A"),
        "teal": ("#0D9488", "#5EEAD4", "#F0FDFA", "#115E59"),
        "purple": ("#7C3AED", "#C4B5FD", "#F5F3FF", "#5B21B6"),
        "amber": ("#D97706", "#FCD34D", "#FFFBEB", "#92400E"),
    }
    pal = palettes.get(theme, palettes["sqld"])
    slides = [
        '  <section class="slide cover">\n'
        f'    <div class="eyebrow">EXAM BOOK</div>\n'
        f'    <h1>{html.escape(round_label)}</h1>\n'
        f'    <p class="lead">문제 풀이 — 밝은 슬라이드(자동 스텁, build-deck 스킬로 다듬으세요)</p>\n'
        '  </section>',
    ]
    for b in lesson.get("blocks", []):
        if b.get("kind") == "section":
            slides.append(
                '  <section class="slide content">\n'
                f'    <div class="s-head"><span class="tag">{html.escape(b.get("subtitle",""))}</span>'
                f'<h2>{html.escape(b.get("title",""))}</h2></div>\n'
                '  </section>')
        elif b.get("kind") == "problem":
            n = b.get("number")
            src = f'출처 · {round_label} {n}번'
            slides.append(
                '  <section class="slide content">\n'
                f'    <span class="source-chip">{html.escape(src)}</span>\n'
                '    <div class="qcard">\n'
                f'      <div class="qnum">{n}번 문제</div>\n'
                f'      <div class="qtext">{html.escape(to_plain(b.get("question","")))}</div>'
                f'{_problem_body(b)}\n'
                f'{_choices_ul(b.get("choices", []))}\n'
                '    </div>\n'
                '  </section>')
            ans = b.get("answer") or circled(b.get("answer_index", 0))
            slides.append(
                '  <section class="slide content">\n'
                f'    <div class="s-head"><span class="tag">정답 및 해설</span><h2>{n}번</h2></div>\n'
                f'    <div class="answer-badge">정답 {html.escape(str(ans))}</div>\n'
                f'{_choices_ul(b.get("choices", []), b.get("answer_index"))}\n'
                f'    <div class="explain">{html.escape(to_plain(b.get("explanation","")))}</div>\n'
                '  </section>')
    body = "\n".join(slides)
    return (
        '<!doctype html><html lang="ko"><head>\n'
        '<meta charset="utf-8"/>\n'
        f'<title>{html.escape(title)}</title>\n'
        '<link rel="stylesheet" href="_deck.css"/>\n'
        f'<style>:root{{--brand:{pal[0]};--brand-2:{pal[1]};--soft:{pal[2]};--brand-ink:{pal[3]}}}</style>\n'
        '</head><body>\n'
        f'<div id="deck" data-title="{html.escape(round_label)}">\n{body}\n</div>\n'
        '<button id="fs">⛶ 전체화면</button>\n'
        '<div class="nav"><button id="prev">‹</button><button id="next">›</button></div>\n'
        '<script src="_deck.js"></script>\n'
        '</body></html>\n')


# ----------------------------------------------------------------------------- core
def process_lesson(lesson_path: Path, book: Path, force: bool) -> None:
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    stem = lesson_path.stem
    code = stem[len("lesson_"):] if stem.startswith("lesson_") else stem
    bundle = book / "05" / code
    for sub in BUNDLE_SUBDIRS:
        (bundle / sub).mkdir(parents=True, exist_ok=True)

    scenes = build_scenes(lesson)

    # source/
    src = bundle / "source"
    shutil.copy2(lesson_path, src / lesson_path.name)
    for asset in ("_deck.css", "_deck.js"):
        a = DECK_ASSETS / asset
        if a.exists():
            shutil.copy2(a, src / asset)
        else:
            print(f"[warn] 덱 자산 없음: {a}")
    deck_path = src / "deck.html"
    if deck_path.exists() and not force:
        print(f"[skip] deck.html 이미 있음(집필본 보존): {deck_path}  (--force 로 덮어쓰기)")
    else:
        deck_path.write_text(build_deck_stub(lesson), encoding="utf-8")
        print(f"[deck] {deck_path}")

    # script/ (리모션 _series)
    (bundle / "script" / f"{code}_script.json").write_text(
        json.dumps(build_series(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")
    # review.json
    (bundle / "review.json").write_text(
        json.dumps(build_review(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")

    n_cap = sum(1 for s in scenes if s["capture"])
    print(f"[{code}] 씬 {len(scenes)}(캡처 {n_cap}) → 05/{code}/ "
          f"(source·script·review.json)")


def main() -> int:
    ap = argparse.ArgumentParser(description="exam-forge bundle scaffolder (05 단계)")
    ap.add_argument("--book", required=True, help="책 루트 (예: D:/00work/ocr-output-260723)")
    ap.add_argument("--round", default=None, help="특정 회차코드만 (예: m01)")
    ap.add_argument("--stage04-dir", default=None, help="lesson JSON 폴더 (기본: <book>/04)")
    ap.add_argument("--force", action="store_true", help="기존 deck.html 덮어쓰기(집필본 삭제 주의)")
    args = ap.parse_args()

    book = Path(args.book).resolve()
    stage04 = Path(args.stage04_dir).resolve() if args.stage04_dir else (book / "04")
    if not stage04.exists():
        print(f"04 폴더가 없습니다: {stage04}", file=sys.stderr)
        return 2

    files = sorted(stage04.glob("lesson_*.json"))
    if args.round:
        files = [f for f in files if f.stem == f"lesson_{args.round}" or f.stem == args.round]
    if not files:
        print(f"처리할 lesson JSON 이 없습니다: {stage04} (round={args.round})", file=sys.stderr)
        return 2

    for f in files:
        process_lesson(f, book, args.force)
    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
