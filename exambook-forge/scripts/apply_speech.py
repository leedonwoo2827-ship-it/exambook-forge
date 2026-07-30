#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_rounds/mNN.json 의 explanation_speech(만) 교체 패치 적용기.

patch 파일: {"1": "정답은 3번입니다. …", "2": "…", ...}  (키 = question_no 문자열)
다른 필드는 절대 건드리지 않는다.

사용:
  python apply_speech.py --round-file <book>/_rounds/m01.json --patch <patch>/m01.json
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    except Exception: pass

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round-file", required=True)
    ap.add_argument("--patch", required=True)
    args = ap.parse_args()
    rf = Path(args.round_file); pf = Path(args.patch)
    data = json.loads(rf.read_text(encoding="utf-8"))
    patch = json.loads(pf.read_text(encoding="utf-8"))
    n = 0; miss = []
    for q in data.get("questions", []):
        key = str(q.get("question_no"))
        if key in patch:
            q["explanation_speech"] = patch[key]
            n += 1
        else:
            miss.append(key)
    rf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{rf.stem}] explanation_speech {n}개 교체" + (f" · 누락 {miss}" if miss else " · 전체 적용"))
    return 0 if not miss else 1

if __name__ == "__main__":
    raise SystemExit(main())
