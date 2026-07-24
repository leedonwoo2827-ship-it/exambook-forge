#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam-forge lesson splitter.

긴 lesson JSON(회차 1편 = 전체 문항)을 여러 편으로 균등 분할한다.
60분짜리 한 편 → 5편(각 ~10문항 ~12분)처럼 영상 길이를 나눌 때 사용.

- 문항(problem) 블록을 파트 수만큼 균등 분할(연속 그룹).
- 각 파트에 직전 과목 섹션(section) 헤더를 이어 붙여 맥락 유지.
- 루트 필드(voice/speed/include_lecture/theme 등)는 그대로 복사, title에 (i/N) 표기.
- 출력: {outdir}/{prefix}-{i}.json (i=1..N)

표준 라이브러리만 사용. Python 3.11+.

사용 예:
  python split.py --input D:/.../04/lesson_m01.json --parts 5
  python split.py --input 04/lesson_m01.json --parts 5 --prefix 01 --outdir 04
    → 04/01-1.json ... 04/01-5.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


def balanced_groups(items: list, n: int) -> list[list]:
    """리스트를 n개 연속 그룹으로 최대한 균등 분할."""
    k, m = divmod(len(items), n)
    out = []
    idx = 0
    for i in range(n):
        size = k + (1 if i < m else 0)
        out.append(items[idx:idx + size])
        idx += size
    return [g for g in out if g]  # 빈 그룹 제거(문항 < 파트 수인 경우)


def active_section(blocks: list[dict], upto: int) -> dict | None:
    sec = None
    for b in blocks[:upto]:
        if b.get("kind") == "section":
            sec = b
    return sec


def split_lesson(data: dict, parts: int) -> list[dict]:
    blocks = data.get("blocks", [])
    prob_idx = [i for i, b in enumerate(blocks) if b.get("kind") == "problem"]
    if not prob_idx:
        raise ValueError("problem 블록이 없습니다.")
    groups = balanced_groups(prob_idx, parts)
    n = len(groups)

    # 각 파트의 블록 범위: 첫 문항 블록 인덱스 ~ 다음 파트 첫 문항 블록 인덱스
    starts = [g[0] for g in groups]
    starts[0] = 0  # 첫 파트는 맨 앞부터(선두 섹션/컨셉 포함)
    ends = starts[1:] + [len(blocks)]

    root = {k: v for k, v in data.items() if k != "blocks"}
    base_title = str(root.get("title", "lesson"))

    lessons = []
    for i in range(n):
        part_blocks = list(blocks[starts[i]:ends[i]])
        # 파트가 섹션으로 시작하지 않으면 직전 과목 섹션 헤더를 이어 붙임
        if i > 0 and (not part_blocks or part_blocks[0].get("kind") != "section"):
            sec = active_section(blocks, starts[i])
            if sec is not None:
                part_blocks = [sec] + part_blocks
        part = dict(root)
        part["title"] = f"{base_title} ({i + 1}/{n})"
        part["part_index"] = i + 1
        part["part_total"] = n
        part["blocks"] = part_blocks
        lessons.append(part)
    return lessons


def main() -> int:
    ap = argparse.ArgumentParser(description="exam-forge lesson splitter")
    ap.add_argument("--input", required=True, help="분할할 lesson JSON 경로")
    ap.add_argument("--parts", type=int, default=5, help="나눌 편 수 (기본 5)")
    ap.add_argument("--outdir", default=None, help="출력 폴더 (기본: 입력 파일과 같은 폴더)")
    ap.add_argument("--prefix", default=None,
                    help="출력 파일 접두 (기본: 입력 파일명에서 lesson_ 제거). 예: 01 → 01-1.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"입력 파일이 없습니다: {src}", file=sys.stderr)
        return 2
    data = json.loads(src.read_text(encoding="utf-8"))

    outdir = Path(args.outdir).resolve() if args.outdir else src.parent
    prefix = args.prefix or src.stem.replace("lesson_", "")

    try:
        lessons = split_lesson(data, args.parts)
    except ValueError as e:
        print(f"분할 실패: {e}", file=sys.stderr)
        return 2

    for i, part in enumerate(lessons, 1):
        nprob = sum(1 for b in part["blocks"] if b.get("kind") == "problem")
        name = f"{prefix}-{i}.json"
        if not args.dry_run:
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / name).write_text(json.dumps(part, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {name}: {nprob}문항, {len(part['blocks'])}블록" + (" (dry-run)" if args.dry_run else ""))
    print(f"완료: {len(lessons)}편 → {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
