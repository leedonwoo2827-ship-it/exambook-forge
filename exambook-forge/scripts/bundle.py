#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam-forge bundle builder (파이프라인 05 단계).

04/lesson_mNN.json 을 읽어 pressplay식 per-회차 번들 05/<회차>/ 을 만든다:
  - source/deck.html          : 밝은 HTML 슬라이드 (페이지 분할 완료 — 잘림 없음)
  - source/_deck.css/_deck.js : 공유 덱 자산 복사
  - source/lesson_mNN.json    : lesson JSON 복사(추적)
  - script/mNN_script.json    : 리모션 _series 대본
  - review.json               : 매니페스트 스켈레톤(시간/영상 필드는 #3·리모션이 채움)
  - images/ audio/ subtitles/ draft/ : 빈 폴더(하위 툴이 채움)

핵심 규약: **deck 의 `.slide` 개수 == capture 씬 개수**.
씬 목록은 lesson 이 아니라 **페이지 분할이 끝난 슬라이드 목록에서 파생**하므로 항상 1:1 이다.

페이지 분할(정돈):
  헤드리스 크로미움으로 초안 deck 를 열어 각 블록의 실제 높이를 재고, 슬라이드 안전영역
  (1080 − 상하 패딩 − 푸터)에 맞게 블록을 페이지로 나눈다. 발문/정답은 페이지마다 상단 고정,
  보기 4개는 쪼개지 않는다(퀴즈 필수). 그래도 안 들어가면 `.dense`(축소)로, 그래도 넘치면
  마지막 수단으로만 잘라내고 "…(전체는 교재/웹북 참고)"를 남긴다.

씬 모델(캡처 인덱스와 1:1):
  cover → (과목 section → [문제 페이지 1..n · 카운트다운 · 정답/해설 페이지 1..m · gap] × 문항)
  capture=True 씬(cover/section/problem/answer)만 deck 슬라이드가 있다(순서 = deck 슬라이드 순서).
  capture=False 씬(countdown/gap)은 #3가 생성한다. 규약: references/pipeline-output-structure.md

의존성: 표준 라이브러리 + playwright(페이지 분할용, 없으면 분할 생략하고 경고).
  pip install playwright && python -m playwright install chromium
Python 3.11+.

사용:
  python bundle.py --book D:/00work/ocr-output-260723 --round m01
  python bundle.py --book D:/00work/ocr-output-260723            # 04/의 모든 lesson_*.json
  python bundle.py --book ... --round m01 --chunk 10             # 10문항씩 5편(05/m01-1..m01-5)
  python bundle.py --book ... --round m01 --no-paginate          # 높이 측정 생략(빠른 확인용)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, field
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

TRUNC_NOTE = "…(전체 내용은 교재·웹북을 참고하세요)"


# ============================================================ 마크다운-lite → HTML
_IMG_MD = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_CODE = re.compile(r"`([^`]+)`")
_BULLET = re.compile(r"^([-*•]|\d+[.)])\s+")
_SQLISH = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|WITH)\b", re.I)

# lesson 의 SQL 은 `sql` 필드도 코드펜스도 없이 발문/지문에 맨 텍스트로 들어온다.
# (m01 기준 22문항) → 아래 규칙으로 찾아내 <pre class="sql"> 로 렌더한다.
_SQL_START = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH|MERGE|TRUNCATE)\b", re.I)
_SQL_CONT = re.compile(
    r"^\s*(FROM|WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|UNION|MINUS|INTERSECT|JOIN|LEFT|RIGHT"
    r"|INNER|FULL|CROSS|OUTER|ON|AND|OR|SET|VALUES|START\s+WITH|CONNECT\s+BY|[(),])", re.I)
# 키워드로 시작해도 FROM/VALUES/SET 나 세미콜론이 없으면 SQL 문이 아니라 산문이다
# ("SELECT 절은 ~ 이다" 같은 해설 문장이 코드블록이 되는 것을 막는다).
_SQL_CONFIRM = re.compile(r"\b(FROM|VALUES|SET)\b|;", re.I)


def _sql_run(lines: list[str], i: int) -> tuple[int, str] | None:
    """lines[i] 부터 이어지는 SQL 문 덩어리를 찾아 (다음 인덱스, 코드) 반환. 아니면 None."""
    if not _SQL_START.match(lines[i]):
        return None
    buf: list[str] = []
    j = i
    while j < len(lines):
        ln = lines[j]
        if not ln.strip():
            break
        if j == i or _SQL_START.match(ln) or _SQL_CONT.match(ln) or ln[:1] in " \t":
            buf.append(ln.rstrip())
            j += 1
        else:
            break
    code = "\n".join(buf).strip()
    return (j, code) if _SQL_CONFIRM.search(code) else None


def _md_inline(s: str) -> str:
    """인라인 마크다운(**볼드**·`코드`)만 HTML 로. 단일 `*`(SELECT *)는 보존."""
    s = html.escape(_IMG_MD.sub("", str(s or "")))
    s = _BOLD.sub(r"<strong>\1</strong>", s)
    s = _CODE.sub(r"<code>\1</code>", s)
    return s.strip()


def _md_table(rows: list[str]) -> str:
    """마크다운 표 라인들 → <table>. 두 번째 줄이 구분선(---)이면 첫 줄을 헤더로."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head: list[str] = []
    if len(cells) >= 2 and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells[1]):
        head, cells = cells[0], cells[2:]
    thead = ("<thead><tr>" + "".join(f"<th>{_md_inline(c)}</th>" for c in head) + "</tr></thead>") if head else ""
    tbody = "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in r) + "</tr>" for r in cells)
    return f"<table>{thead}<tbody>{tbody}</tbody></table>"


def _fallback_speech(block_html: str) -> str:
    """표·SQL 처럼 낭독하지 않는 블록만 실린 페이지에서 쓸 짧은 안내 문장.

    비워두면 렌더러가 heading("11번 문제 (2/6)")을 그대로 읽어버린다.
    """
    if "<figure" in block_html:
        return "그림을 확인해 보세요."
    if "<table" in block_html:
        return "표를 확인해 보세요."
    if 'pre class="sql"' in block_html:
        return "SQL 문을 확인해 보세요."
    if "<pre" in block_html:
        return "코드를 확인해 보세요."
    return "이어서 보겠습니다."


def md_blocks(text: str) -> list[tuple[str, str]]:
    """마크다운-lite 텍스트 → [(HTML 블록, 낭독용 평문)] 목록.

    블록 단위로 쪼개 두어야 페이지 분할이 문단 경계에서 깔끔하게 끊긴다.
    지원: 문단, 불릿/번호 목록, 표(`| a | b |`), 코드펜스(```sql), **볼드**, `코드`.
    """
    lines = str(text or "").replace("\r\n", "\n").split("\n")
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        st = lines[i].strip()
        if not st:
            i += 1
            continue

        if st.startswith("```"):                                  # 코드펜스
            lang = st[3:].strip().lower()
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(buf).strip()
            cls = "sql" if (lang == "sql" or _SQLISH.search(code)) else "code"
            out.append((f'<pre class="{cls}">{html.escape(code)}</pre>', ""))
            continue

        if st.startswith("|"):                                    # 표
            buf = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append((_md_table(buf), ""))
            continue

        run = _sql_run(lines, i)                                  # 맨 텍스트 SQL
        if run:
            i, code = run
            out.append((f'<pre class="sql">{html.escape(code)}</pre>', ""))
            continue

        if _BULLET.match(st):                                     # 목록
            buf = []
            while i < len(lines) and _BULLET.match(lines[i].strip()):
                buf.append(_BULLET.sub("", lines[i].strip()))
                i += 1
            lis = "".join(f"<li>{_md_inline(x)}</li>" for x in buf)
            out.append((f"<ul>{lis}</ul>", " ".join(to_speech(x) for x in buf)))
            continue

        buf = []                                                  # 문단
        while i < len(lines):
            cur = lines[i].strip()
            if not cur or cur.startswith(("|", "```")) or _BULLET.match(cur):
                break
            if buf and _sql_run(lines, i):
                break
            buf.append(cur)
            i += 1
        para = " ".join(buf)
        out.append((f"<p>{_md_inline(para)}</p>", to_speech(para)))
    return out


# ============================================================ 슬라이드 모델
@dataclass
class Block:
    """슬라이드 안에서 페이지로 나뉠 수 있는 최소 단위."""
    html: str
    speech: str = ""             # 이 블록을 낭독할 문장(표/SQL 은 읽지 않으므로 빈 값)
    fallback: str = ""           # speech 가 없을 때 그 페이지에 쓸 짧은 안내 낭독
    keep: bool = False           # True 면 절대 버리지 않는다(보기 4개)
    full: bool = False           # 2·3단 배치에서도 전폭을 쓴다(보기)


@dataclass
class Slide:
    kind: str                        # cover | section | problem | answer
    heading: str
    number: int | None = None
    classes: str = "content"
    fixed: list[str] = field(default_factory=list)   # 1페이지 상단 고정 HTML
    cont_idx: list[int] = field(default_factory=list)  # 그중 이어지는 페이지에도 반복할 것의 인덱스
    blocks: list[Block] = field(default_factory=list)
    chips: list[str] = field(default_factory=list)   # 좌상단 칩들(회차·번호 / 과목 / 난이도)
    narration: str = ""                              # 자막/표시용 원문
    speech: str = ""                                 # 낭독용(비면 blocks 에서 생성)
    shrink: int = 0                                  # 0=원본 · 1=dense · 2=dense2(축소)
    cols: int = 1                                    # 본문 단 수(1·2·3) — 긴 표/지문을 옆으로 편다
    ch2: bool = False                                # 보기를 2×2 로 (글씨 안 줄이고 높이 절반)
    page: int = 1
    pages: int = 1


def _strip_brand(s: str) -> str:
    """브랜딩/자사 표기 제거 — '자사 모의고사 01회' → '모의고사 01회'."""
    s = str(s or "")
    s = re.sub(r"\s*EXAM\s*BOOK\s*", " ", s, flags=re.I)
    s = re.sub(r"(^|\s)자사\s+", r"\1", s)
    return re.sub(r"\s{2,}", " ", s).strip()


_LEAD_MARKER = re.compile(r"^\s*(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.)])\s*")


def _strip_lead_marker(s: str) -> str:
    """보기 앞의 원문자(①)·번호(1./1)) 접두 제거 → 렌더러 marker 와 중복 방지."""
    return _LEAD_MARKER.sub("", str(s)).strip()


def _choice_li(i: int, text: str, correct: bool) -> str:
    cls = "choice correct" if correct else "choice"
    return (f'<li class="{cls}"><span class="marker">{i + 1}</span>'
            f'<span>{_md_inline(_strip_lead_marker(text))}</span></li>')


def _choices_ul(choices: list, correct_index: int | None = None) -> str:
    lis = "\n".join(_choice_li(i, str(c), correct_index is not None and i == correct_index)
                    for i, c in enumerate(choices))
    return f'<ul class="choices">\n{lis}\n</ul>'


def _blk(html_: str, speech: str = "", keep: bool = False, full: bool = False) -> Block:
    return Block(html_, speech, _fallback_speech(html_), keep, full)


def _choices_speech(choices: list) -> str:
    return " ".join(f"{i + 1}번, {to_speech(_strip_lead_marker(str(c)))}."
                    for i, c in enumerate(choices))


_XML_DECL = re.compile(r"^\s*<\?xml[^>]*\?>\s*")


def _figure_blocks(assets_dirs: list[Path], names: list) -> list[Block]:
    """문항의 assets(SVG 파일명) → 인라인 <figure> 블록.

    파일 참조가 아니라 SVG 본문을 그대로 심는다(캡처가 file:// 로 열려도 항상 그려지게).
    """
    out: list[Block] = []
    for a in names or []:
        name = str(a.get("name") if isinstance(a, dict) else a)
        if not name.endswith(".svg"):
            name += ".svg"
        path = next((d / name for d in assets_dirs if (d / name).exists()), None)
        if path is None:
            print(f"[warn] 도식 파일을 찾지 못했습니다: {name}")
            continue
        svg = _XML_DECL.sub("", path.read_text(encoding="utf-8")).strip()
        out.append(_blk(f'<figure class="diagram">{svg}</figure>'))
    return out


_HEAVY = ("<table", "<pre", "<figure")


def _glue_labels(blocks: list[Block]) -> list[Block]:
    """'[상품] (분류코드)' 같은 짧은 라벨 문단을 뒤따르는 표/코드/그림과 **한 블록으로** 합친다.

    페이지나 단이 갈릴 때 라벨만 떨어져 나가면 라벨 한 줄짜리 빈 화면이 생긴다.
    같은 페이지에 두는 것만으로는 부족하고(단 흐름이 갈라놓는다) DOM 을 합쳐야 한다.
    """
    out: list[Block] = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        plain = not any(t in b.html for t in _HEAVY) and "<ul" not in b.html
        short = len(re.sub(r"<[^>]+>", "", b.html).strip()) <= 60
        if plain and short and nxt is not None and any(t in nxt.html for t in _HEAVY):
            out.append(Block(b.html + nxt.html,
                             " ".join(x for x in (b.speech, nxt.speech) if x),
                             nxt.fallback or b.fallback))
            i += 2
            continue
        out.append(b)
        i += 1
    return out


def build_slides(lesson: dict, assets_dirs: list[Path] | None = None) -> list[Slide]:
    """lesson → 슬라이드 목록(아직 페이지 분할 전, 문항당 문제 1 + 해설 1)."""
    assets_dirs = assets_dirs or []
    round_label = _strip_brand(lesson.get("round") or lesson.get("title", ""))
    slides: list[Slide] = []

    # 표지 — 브랜딩(eyebrow) 없음
    slides.append(Slide(
        kind="cover", classes="cover", heading=_strip_brand(lesson.get("title", round_label)),
        fixed=[f'<h1>{html.escape(_strip_brand(lesson.get("title", round_label)))}</h1>',
               '<p class="lead">문제 풀이</p>'],
        narration=f"{round_label}. 문제 풀이를 시작합니다."))

    cur_subject = ""                     # 현재 활성 과목(섹션 title) — 문항 칩에 붙인다
    for b in lesson.get("blocks", []):
        kind = b.get("kind")
        if kind == "section":
            sub, ttl = _strip_brand(b.get("subtitle", "")), _strip_brand(b.get("title", ""))
            cur_subject = ttl or sub
            slides.append(Slide(
                kind="section", heading=f"{sub} · {ttl}".strip(" ·"),
                fixed=[f'<div class="s-head"><span class="tag">{html.escape(sub)}</span>'
                       f'<h2>{html.escape(ttl)}</h2></div>'],
                narration=b.get("narration", "")))
            continue
        if kind != "problem":
            continue

        n = b.get("number")
        choices = b.get("choices", []) or []
        ai = b.get("answer_index")
        # 좌상단 칩: [회차·N번] [과목] [난이도] — 과목·난이도는 있을 때만
        diff = str(b.get("difficulty") or "").strip()
        chips = [f"{round_label} · {n}번" if round_label else f"{n}번"]
        if cur_subject:
            chips.append(cur_subject)
        if diff:
            chips.append(f"난이도 {diff}" if not diff.startswith("난이도") else diff)

        # ── 문제 슬라이드: 발문 고정, 지문/SQL/표 → 블록, 보기는 통째로 한 덩어리
        # 발문 안에 SQL·표가 딸려오는 문항이 있다(13·25번 등) → 첫 문단만 발문으로 고정하고
        # 나머지는 흐름 블록으로 내려 페이지 분할 대상이 되게 한다.
        q_parts = md_blocks(b.get("question", "")) or [("<p></p>", "")]
        qtext_html, qtext_speech = q_parts[0]
        qtext_html = re.sub(r"^<p>|</p>$", "", qtext_html)
        # 발문에서 떨어져 나온 블록은 .qbody 로 감싼다 — 안 감싸면 맨 <p>/<ul> 이라
        # 슬라이드 폰트 규칙이 안 걸려 16px 로 쪼그라든다.
        q_blocks: list[Block] = [_blk(f'<div class="qbody">{h_}</div>', sp)
                                 for h_, sp in q_parts[1:]]
        if b.get("passage"):
            for h_, sp in md_blocks(b["passage"]):
                q_blocks.append(_blk(f'<div class="passage">{h_}</div>', sp))
        if b.get("sql"):
            q_blocks.append(_blk(f'<pre class="sql">{html.escape(str(b["sql"]).strip())}</pre>'))
        if b.get("table"):
            t = b["table"]
            cols = "".join(f"<th>{_md_inline(str(c))}</th>" for c in t.get("columns", []))
            rows = "".join("<tr>" + "".join(f"<td>{_md_inline(str(c))}</td>" for c in r) + "</tr>"
                           for r in t.get("rows", []))
            q_blocks.append(_blk(f"<table><thead><tr>{cols}</tr></thead><tbody>{rows}</tbody></table>"))
        q_blocks += _figure_blocks(assets_dirs, b.get("assets"))   # 도식은 지문 뒤·보기 앞
        q_blocks = _glue_labels(q_blocks)
        if choices:
            q_blocks.append(_blk(_choices_ul(choices), _choices_speech(choices),
                                 keep=True, full=True))   # 보기는 단을 나누지 않는다

        slides.append(Slide(
            kind="problem", number=n, heading=f"{n}번 문제",
            chips=chips,
            # 발문만 카드 상단 고정 — "N번 문제"는 좌상단 칩이 대신한다(스크린샷과 일치)
            fixed=[f'<div class="qtext">{qtext_html}</div>'],
            cont_idx=[],          # 이어지는 페이지엔 발문을 반복하지 않는다
                                  # (뚫린 카드 테두리가 "계속"을 보여주고, 그만큼 내용이 더 들어간다)
            blocks=q_blocks,
            narration=b.get("question", ""),
            # 낭독은 발문 문장만 — SQL 을 그대로 읽으면 못 알아듣는다.
            speech=to_speech(b.get("narration_question") or "") or qtext_speech))

        # ── 해설 슬라이드: 정답 배지 + 보기 4개 전부(정답 강조) 고정, 해설(짧음)은 흐름 블록
        # 화면 해설은 짧게, 대본(낭독)은 길게 — 표시/낭독 분리는 speech 로만.
        ans = b.get("answer") or (circled(ai) if isinstance(ai, int) else "")
        fixed = [f'<div class="s-head"><span class="tag">정답 및 해설</span><h2>{n}번</h2></div>',
                 f'<div class="answer-badge">정답 {html.escape(str(ans))}</div>']
        if choices:
            correct = ai if isinstance(ai, int) and 0 <= ai < len(choices) else None
            fixed.append(_choices_ul(choices, correct))
        e_blocks = _glue_labels([_blk(f'<div class="explain">{h_}</div>', sp)
                                 for h_, sp in md_blocks(b.get("explanation", ""))])
        slides.append(Slide(
            kind="answer", number=n, heading=f"{n}번 · 정답 {ans}",
            chips=[f"{round_label} · {n}번" if round_label else f"{n}번"] + ([cur_subject] if cur_subject else []),
            # 이어지는 해설 페이지엔 정답 배지만 남긴다(보기 4개를 매 장 반복하면 높이를 다 먹는다)
            fixed=fixed, cont_idx=[1],
            blocks=e_blocks,
            narration=b.get("explanation", ""),
            speech=to_speech(b.get("narration_answer") or b.get("explanation_speech")
                             or b.get("explanation", ""))))
    return slides


# ============================================================ deck.html 렌더
def _slide_html(s: Slide, si: int) -> str:
    cls = s.classes + ("", " dense", " dense dense2")[min(s.shrink, 2)]
    if s.cols > 1:
        cls += f" cols{min(s.cols, 3)}"
    if s.ch2:
        cls += " ch2"
    if s.pages > 1:
        cls += " paged"
    parts = [f'  <section class="slide {cls}">']
    if s.chips:
        chips = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in s.chips)
        parts.append(f'    <div class="chips">{chips}</div>')
    # 페이지 카운터 칩은 넣지 않는다 — 칩과 겹치고, 이어짐은 카드 뚫린 테두리가 이미 보여준다.
    # (회차·부분 진행은 하단 좌측 푸터 텍스트가 대신)
    body = [f'      <div data-fixed>{h_}</div>' for h_ in s.fixed]
    if s.blocks:
        flow = "".join(f'<div data-fid="{si}-{bi}"{" data-full" if b.full else ""}>{b.html}</div>'
                       for bi, b in enumerate(s.blocks))
        body.append(f'      <div class="flow">{flow}</div>')
    inner = "\n".join(body)
    if s.kind == "problem":
        # 이어지는 쪽 테두리를 뚫어 "다음 장으로 계속"을 보여준다(가운데 페이지는 위아래 다).
        card = "qcard"
        if s.pages > 1:
            card += " open-top" if s.page > 1 else ""
            card += " open-bottom" if s.page < s.pages else ""
        parts.append(f'    <div class="{card}">\n{inner}\n    </div>')
    else:
        parts.append(inner)
    parts.append("  </section>")
    return "\n".join(parts)


def render_deck(lesson: dict, slides: list[Slide]) -> str:
    round_label = _strip_brand(lesson.get("round", ""))
    title = _strip_brand(lesson.get("title", round_label))
    theme = (lesson.get("theme") or "").lower()
    palettes = {
        "sqld": ("#2563EB", "#60A5FA", "#EFF6FF", "#1E3A8A"),
        "teal": ("#0D9488", "#5EEAD4", "#F0FDFA", "#115E59"),
        "purple": ("#7C3AED", "#C4B5FD", "#F5F3FF", "#5B21B6"),
        "amber": ("#D97706", "#FCD34D", "#FFFBEB", "#92400E"),
    }
    pal = palettes.get(theme, palettes["sqld"])
    body = "\n".join(_slide_html(s, i) for i, s in enumerate(slides))
    return (
        '<!doctype html><html lang="ko"><head>\n'
        '<meta charset="utf-8"/>\n'
        f'<title>{html.escape(title)}</title>\n'
        '<link rel="stylesheet" href="_deck.css"/>\n'
        f'<style>:root{{--brand:{pal[0]};--brand-2:{pal[1]};--soft:{pal[2]};--brand-ink:{pal[3]}}}\n'
        '.page-chip{position:absolute;top:48px;right:48px;background:var(--soft);color:var(--brand-ink);'
        'border-radius:999px;padding:12px 28px;font-weight:800;font-size:30px}</style>\n'
        '</head><body>\n'
        f'<div id="deck" data-title="{html.escape(round_label)}">\n{body}\n</div>\n'
        '<button id="fs">⛶ 전체화면</button>\n'
        '<div class="nav"><button id="prev">‹</button><button id="next">›</button></div>\n'
        '<script src="_deck.js"></script>\n'
        '</body></html>\n')


# ============================================================ 높이 측정 · 페이지 분할
MEASURE_JS = r"""
() => {
  const px = (v) => parseFloat(v) || 0;
  return [...document.querySelectorAll('.slide')].map((s, si) => {
    const cs = getComputedStyle(s);
    const foot = s.querySelector('.s-foot');
    // 푸터는 absolute 라 흐름 높이에 안 잡히지만 본문을 가린다 → 안전영역에서 뺀다.
    const footH = foot ? foot.getBoundingClientRect().height + 44 + 24 : 0;
    const availAll = s.clientHeight - px(cs.paddingTop) - px(cs.paddingBottom) - footH;
    let avail = availAll;
    const card = s.querySelector('.qcard');
    if (card) {
      const c = getComputedStyle(card);
      avail -= px(c.paddingTop) + px(c.paddingBottom)
             + px(c.borderTopWidth) + px(c.borderBottomWidth);
    }
    const meas = (el) => {
      const e = getComputedStyle(el);
      return el.getBoundingClientRect().height + px(e.marginTop) + px(e.marginBottom);
    };
    // 실제로 쓴 높이 — 2·3단 배치에서는 블록 높이의 합과 다르므로 직접 잰다.
    // (칩/푸터는 absolute 라 흐름에서 빠진다)
    const used = [...s.children]
      .filter(el => !el.classList.contains('s-foot') && !el.classList.contains('source-chip')
                 && !el.classList.contains('page-chip') && !el.classList.contains('chips'))
      .reduce((a, el) => a + meas(el), 0);
    return {
      si, avail, availAll, used,
      fixed: [...s.querySelectorAll('[data-fixed]')].map(meas),
      blocks: Object.fromEntries([...s.querySelectorAll('[data-fid]')].map(el => [el.dataset.fid, meas(el)])),
      over: Math.max(0, s.scrollHeight - s.clientHeight),
    };
  });
}
"""


def measure_many(html_texts: list[str], workdir: Path) -> list[list[dict]] | None:
    """여러 후보 deck HTML 을 브라우저 한 번으로 재서 각각의 슬라이드 측정값을 돌려준다.

    배치(한 장에 담기) 후보를 여러 개 시도하므로, 매번 크로미움을 띄우면 그것만으로 느려진다.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    for asset in ("_deck.css", "_deck.js"):
        src = DECK_ASSETS / asset
        if src.exists():
            shutil.copy2(src, workdir / asset)
    out: list[list[dict]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for i, text in enumerate(html_texts):
            f = workdir / f"_measure{i}.html"
            f.write_text(text, encoding="utf-8")
            pg.goto(f.as_uri(), wait_until="networkidle")
            try:
                pg.evaluate("document.fonts && document.fonts.ready")
            except Exception:
                pass
            pg.wait_for_timeout(200)
            out.append(pg.evaluate(MEASURE_JS))
        browser.close()
    return out


def measure(html_text: str, workdir: Path) -> list[dict] | None:
    got = measure_many([html_text], workdir)
    return got[0] if got else None


def capture_deck(deck_html: str, images_dir: Path, scenes: list[dict], workdir: Path) -> int:
    """최종 deck 을 헤드리스 크로미움으로 열어 각 .slide 를 PNG(1920×1080)로 저장한다.

    파일명은 capture=True 씬의 scene 인덱스(build_scenes 의 image 필드)와 1:1 로 맞춘다:
    deck 의 k번째 .slide → k번째 capture 씬의 scene 값 → slide_{scene:02d}.png.
    카운트다운/간격(capture=False) 씬은 #3 가 만든다. playwright 없으면 -1 반환.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return -1
    cap_scenes = [s["scene"] for s in scenes if s.get("capture")]
    images_dir.mkdir(parents=True, exist_ok=True)
    for asset in ("_deck.css", "_deck.js"):
        src = DECK_ASSETS / asset
        if src.exists():
            shutil.copy2(src, workdir / asset)
    f = workdir / "_capture.html"
    f.write_text(deck_html, encoding="utf-8")
    n = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto(f.as_uri(), wait_until="networkidle")
        try:
            pg.evaluate("document.fonts && document.fonts.ready")
        except Exception:
            pass
        # 화면 전용 내비/버튼은 캡처에 안 잡히게 제거
        pg.evaluate("['#fs','.nav'].forEach(s=>document.querySelectorAll(s).forEach(e=>e.remove()))")
        pg.wait_for_timeout(200)
        els = pg.query_selector_all(".slide")
        if len(els) != len(cap_scenes):
            print(f"[warn] 캡처 슬라이드 {len(els)} != capture 씬 {len(cap_scenes)} — 순서가 어긋날 수 있음")
        for el, scene in zip(els, cap_scenes):
            el.screenshot(path=str(images_dir / f"slide_{scene:02d}.png"))
            n += 1
        browser.close()
    return n


SAFETY = 24.0   # 측정 오차·마진 겹침 여유(px)


def _fits(mm: dict) -> bool:
    """이 슬라이드 내용이 안전영역 안에 다 들어갔는가(실측 사용 높이 기준)."""
    return float(mm.get("used", 0)) <= float(mm.get("availAll", 0)) - SAFETY


def _paginate_one(s: Slide, m: dict) -> list[Slide]:
    """슬라이드 1장 → 안전영역에 맞춘 페이지 목록. 발문/정답은 페이지마다 반복."""
    fh = [float(x) for x in m["fixed"]]
    # 이어지는 페이지는 고정부를 (거의) 반복하지 않으므로 그만큼 더 담을 수 있다.
    cap_first = m["avail"] - sum(fh) - SAFETY
    cap_cont = m["avail"] - sum(fh[i] for i in s.cont_idx if i < len(fh)) - SAFETY
    heights = {k: float(v) for k, v in m["blocks"].items()}
    if cap_first <= 0 or not s.blocks:
        return [s]

    # "[상품] (분류코드)" 같은 짧은 라벨이 뒤따르는 표와 떨어지면 라벨 한 줄짜리 빈 페이지가 된다
    # → 짧은 문단은 다음 블록과 한 덩어리로 묶어서 페이지에 넣는다.
    GLUE = 160.0
    units: list[tuple[Block, float]] = []
    bi = 0
    while bi < len(s.blocks):
        h = heights.get(f"{m['si']}-{bi}", 0.0)
        b = s.blocks[bi]
        if h < GLUE and bi + 1 < len(s.blocks) and not b.full and not s.blocks[bi + 1].full:
            nxt = s.blocks[bi + 1]
            bi += 1
            h += heights.get(f"{m['si']}-{bi}", 0.0)
            b = Block(b.html + nxt.html, " ".join(x for x in (b.speech, nxt.speech) if x),
                      nxt.fallback or b.fallback, b.keep or nxt.keep)
        units.append((b, h))
        bi += 1

    # 나눠야 할 만큼 덩어리가 많으면 페이지 안에서도 2단으로 흘려 장수를 줄인다.
    s.cols = 2 if len(units) >= 3 else 1
    budget = 0.85 if s.cols > 1 else 1.0     # 단이 좁아지면 블록이 세로로 늘어나는 만큼 보수적으로

    pages: list[list[Block]] = []
    cur: list[Block] = []
    used = 0.0
    for unit, h in units:
        cap = (cap_first if not pages else cap_cont) * s.cols * budget
        if cur and used + h > cap:
            pages.append(cur)
            cur, used = [], 0.0
        cur.append(unit)
        used += h
    if cur:
        pages.append(cur)

    out: list[Slide] = []
    for pi, blks in enumerate(pages):
        fixed = list(s.fixed) if pi == 0 else [s.fixed[i] for i in s.cont_idx if i < len(s.fixed)]
        p = Slide(kind=s.kind, heading=s.heading, number=s.number, classes=s.classes,
                  fixed=fixed, cont_idx=s.cont_idx, blocks=blks, chips=s.chips,
                  shrink=s.shrink, cols=s.cols, ch2=s.ch2,
                  page=pi + 1, pages=len(pages))
        if len(pages) > 1:
            p.heading = f"{s.heading} ({pi + 1}/{len(pages)})"
        out.append(p)

    _assign_speech(s, out)
    return out


def _page_speech(p: Slide) -> str:
    """그 페이지에 실제로 보이는 내용으로 만든 낭독문(비면 안 됨 — heading 낭독 방지)."""
    own = " ".join(b.speech for b in p.blocks if b.speech).strip()
    if own:
        return own
    seen, fb = set(), []
    for b in p.blocks:                       # 같은 안내문 반복 제거
        if b.fallback and b.fallback not in seen:
            seen.add(b.fallback)
            fb.append(b.fallback)
    return " ".join(fb) or "이어서 보겠습니다."


def _assign_speech(s: Slide, pages: list[Slide]) -> None:
    """페이지별 자막/낭독 배정.

    문제: 발문 낭독은 1페이지에서 통째로 (쪼개면 문장이 끊긴다). 이후 페이지는 그 페이지의
          지문·보기를 읽고, 표/SQL 뿐인 페이지는 짧은 안내문.
    해설: 손으로 다듬은 explanation_speech 를 버리지 않도록 표시 분량 비율로 문장 분배.
    """
    if len(pages) == 1:
        pages[0].narration, pages[0].speech = s.narration, s.speech
        return
    if s.kind == "problem":
        for p in pages:
            p.narration = s.narration if p.page == 1 else ""
            p.speech = s.speech if p.page == 1 else _page_speech(p)
        return
    weights = [sum(len(b.speech) for b in p.blocks) for p in pages]
    for p, sp in zip(pages, _split_speech(s.speech, weights)):
        p.narration = s.narration if p.page == 1 else ""
        p.speech = (sp.strip() or _page_speech(p))


_SENT = re.compile(r"(?<=[.!?。])\s+|(?<=다\.)\s*")


def _split_speech(speech: str, weights: list[float]) -> list[str]:
    """낭독문을 페이지별 표시 분량 비율에 맞춰 문장 경계에서 나눈다.

    손으로 다듬은 explanation_speech 를 버리지 않으면서 페이지와 대략 맞추기 위한 것.
    """
    speech = (speech or "").strip()
    n = len(weights)
    if not speech or n <= 1:
        return [speech] + [""] * (n - 1)
    sents = [x for x in _SENT.split(speech) if x and x.strip()]
    if len(sents) < n:
        return [speech] + [""] * (n - 1)     # 문장이 부족하면 쪼개지 않는다
    total_w = sum(weights) or 1.0
    out, idx = [], 0
    for i, w in enumerate(weights):
        take = len(sents) - idx if i == n - 1 else max(1, round(len(sents) * w / total_w))
        take = min(take, len(sents) - idx - (n - 1 - i))
        out.append(" ".join(sents[idx:idx + max(take, 1)]).strip())
        idx += max(take, 1)
    return out


def paginate(lesson: dict, slides: list[Slide], workdir: Path,
             max_rounds: int = 4) -> tuple[list[Slide], list[str]]:
    """측정 → 분할 → 재측정을 반복해 잘림 없는 슬라이드 목록을 만든다.

    남으면 .dense(축소) → 그래도 넘치면 마지막 블록을 잘라내고 안내문을 남긴다.
    Returns (슬라이드 목록, 경고 메시지들).
    """
    warns: list[str] = []
    # 한 장에 담는 것이 최우선(퀴즈는 발문과 보기를 같이 봐야 한다). 덜 손대는 배치부터 시도한다:
    # 보기 2×2(기본) → 축소 → 2단 → 3단. 다 안 되면 그때 페이지를 나눈다.
    # (보기 2×2 는 글씨를 안 줄이고 세로를 절반으로 줄이므로 항상 기본으로 쓴다 — 사용자 요청)
    TIERS = [(1, 0, True), (1, 1, True), (2, 0, True), (2, 1, True), (3, 1, True)]
    candidates = []
    for cols, shrink, ch2 in TIERS:
        for s in slides:
            s.cols, s.shrink, s.ch2 = cols, shrink, ch2
        candidates.append(render_deck(lesson, slides))
    for s in slides:
        s.cols, s.shrink, s.ch2 = 1, 0, False

    measured = measure_many(candidates, workdir)
    if measured is None:
        return slides, ["playwright 가 없어 페이지 분할을 건너뛰었습니다 "
                        "(pip install playwright && python -m playwright install chromium)"]
    m = measured[0]

    fit_at: dict[int, tuple[int, int, bool]] = {}
    for tier, mt in zip(TIERS, measured):
        for i, mm in enumerate(mt):
            if i not in fit_at and _fits(mm):
                fit_at[i] = tier

    out: list[Slide] = []
    for i, (s, mm) in enumerate(zip(slides, m)):
        if i in fit_at:
            s.cols, s.shrink, s.ch2 = fit_at[i]
            out.append(s)
        else:
            s.ch2 = True                    # 나눠야 한다면 보기는 2×2 로 둔다(장수를 줄인다)
            out.extend(_paginate_one(s, measured[1][i]))   # ch2 상태의 실측으로 나눈다

    for _ in range(max_rounds):
        m = measure(render_deck(lesson, out), workdir) or []
        bad = [i for i, mm in enumerate(m) if mm["over"] > 1]
        if not bad:
            return out, warns
        for i in reversed(bad):                      # 뒤에서부터: insert 로 인덱스가 밀리지 않게
            s = out[i]
            if s.shrink < 2:
                s.shrink += 1                        # 1·2차: 축소 모드 단계 상향
            elif len(s.blocks) > 1:
                moved = s.blocks.pop()               # 3차: 마지막 블록을 다음 페이지로
                out.insert(i + 1, Slide(
                    kind=s.kind, heading=s.heading, number=s.number, classes=s.classes,
                    fixed=list(s.fixed), cont_idx=s.cont_idx, blocks=[moved], chips=s.chips,
                    shrink=2, cols=s.cols, ch2=s.ch2, narration="", speech=moved.speech))
            elif not s.blocks[0].keep:
                # 더 쪼갤 수도 줄일 수도 없는 단일 블록(긴 지문/표) — 마지막 수단으로 안내문 대체
                s.blocks = [Block(f'<div class="trunc-note">{TRUNC_NOTE}</div>',
                                  s.blocks[0].speech)]

    m = measure(render_deck(lesson, out), workdir) or []
    for i, mm in enumerate(m):
        if mm["over"] > 1:
            warns.append(f"슬라이드 {i + 1}({out[i].heading}) 가 {int(mm['over'])}px 넘칩니다 — "
                         f"lesson 의 해당 지문/해설을 줄여야 합니다")
    return out, warns


def renumber(slides: list[Slide]) -> None:
    """분할 후 같은 문항의 페이지 번호를 다시 매긴다(문제/해설 각각)."""
    for kind in ("problem", "answer"):
        groups: dict[int | None, list[Slide]] = {}
        for s in slides:
            if s.kind == kind:
                groups.setdefault(s.number, []).append(s)
        for num, g in groups.items():
            base = re.sub(r"\s*\(\d+/\d+\)$", "", g[0].heading)
            for i, s in enumerate(g):
                s.page, s.pages = i + 1, len(g)
                s.heading = base if len(g) == 1 else f"{base} ({i + 1}/{len(g)})"


# ============================================================ 씬 (슬라이드에서 파생 → 항상 1:1)
def build_scenes(lesson: dict, slides: list[Slide]) -> list[dict]:
    """페이지 분할이 끝난 슬라이드 목록 → 전 씬 목록.

    capture 씬은 슬라이드와 1:1(순서 동일). 카운트다운/간격은 무음 씬으로 사이에 끼운다.
    카운트다운은 그 문항의 **마지막 문제 페이지 뒤**(= 보기가 다 보인 뒤)에 온다.
    """
    cd = int(lesson.get("countdown_seconds", 5) or 0)
    gap = float(lesson.get("gap_seconds", 1.5) or 0)
    scenes: list[dict] = []

    for i, s in enumerate(slides):
        scenes.append({
            "kind": s.kind, "capture": True, "heading": s.heading,
            "narration": to_plain(s.narration or s.heading),
            "narration_text": (s.speech or to_speech(s.narration) or s.heading),
            **({"number": s.number} if s.number is not None else {}),
        })
        nxt = slides[i + 1] if i + 1 < len(slides) else None
        last_page = not (nxt and nxt.kind == s.kind and nxt.number == s.number)
        if s.kind == "problem" and last_page and cd > 0:
            scenes.append({"kind": "countdown", "capture": False, "heading": "생각할 시간",
                           "narration": "", "narration_text": "",
                           "countdown_seconds": cd, "number": s.number})
        if s.kind == "answer" and last_page and gap > 0:
            scenes.append({"kind": "gap", "capture": False, "heading": "",
                           "narration": "", "narration_text": "",
                           "gap_seconds": gap, "number": s.number})

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
        "round": _strip_brand(lesson.get("round", "")),
        "subject": lesson.get("subject", ""),
        "theme": lesson.get("theme", ""),
        "voice": lesson.get("voice", "F2"),
        "speed": lesson.get("speed", 1.05),
        # number 는 반드시 남긴다 — #3 가 카운트다운 배경으로 "그 문항의 마지막 문제 슬라이드"를
        # 찾을 때 쓰는 키다. 빠지면 전부 None 으로 뭉쳐 번들 마지막 문제가 배경이 된다.
        "scenes": [
            {k: s[k] for k in (
                "scene", "kind", "capture", "number", "heading", "narration", "narration_text",
                "image", "audio", "durSec", "startSec")
             if k in s} | ({"countdown_seconds": s["countdown_seconds"]} if "countdown_seconds" in s else {})
            for s in scenes
        ],
    }


def build_review(lesson: dict, scenes: list[dict]) -> dict:
    return {
        "title": _strip_brand(lesson.get("title", "")),
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


# ============================================================ chunk
def _active_section(blocks: list[dict], upto: int) -> dict | None:
    sec = None
    for b in blocks[:upto]:
        if b.get("kind") == "section":
            sec = b
    return sec


def chunk_lesson(lesson: dict, per: int) -> list[tuple[str | None, dict]]:
    """lesson을 문항 per개씩 나눈 (코드접미, 부분lesson) 목록. per<=0 또는 분할불필요면 [(None, lesson)]."""
    blocks = lesson.get("blocks", [])
    prob_idx = [i for i, b in enumerate(blocks) if b.get("kind") == "problem"]
    if per <= 0 or len(prob_idx) <= per:
        return [(None, lesson)]
    groups = [prob_idx[i:i + per] for i in range(0, len(prob_idx), per)]
    total = len(groups)
    base_title = str(lesson.get("title", ""))
    out: list[tuple[str | None, dict]] = []
    for gi, g in enumerate(groups):
        start = 0 if gi == 0 else g[0]
        end = groups[gi + 1][0] if gi + 1 < len(groups) else len(blocks)
        part_blocks = list(blocks[start:end])
        if gi > 0 and (not part_blocks or part_blocks[0].get("kind") != "section"):
            sec = _active_section(blocks, start)
            if sec is not None:
                part_blocks = [sec] + part_blocks
        sub = dict(lesson)
        sub["blocks"] = part_blocks
        sub["title"] = f"{base_title} ({gi + 1}/{total})"
        sub["part_index"] = gi + 1
        sub["part_total"] = total
        out.append((f"-{gi + 1}", sub))
    return out


# ============================================================ core
def write_bundle(lesson: dict, code: str, book: Path, do_paginate: bool,
                 do_capture: bool = True) -> None:
    bundle = book / "05" / code
    for sub in BUNDLE_SUBDIRS:
        (bundle / sub).mkdir(parents=True, exist_ok=True)

    assets_dirs = [d for d in (book / "04" / "assets", book / "02" / "assets",
                               book / "03" / "assets") if d.exists()]
    slides = build_slides(lesson, assets_dirs)
    warns: list[str] = []
    if do_paginate:
        with tempfile.TemporaryDirectory(prefix="deck-measure-") as td:
            slides, warns = paginate(lesson, slides, Path(td))
        renumber(slides)

    deck_html = render_deck(lesson, slides)
    scenes = build_scenes(lesson, slides)

    src = bundle / "source"
    (src / f"lesson_{code}.json").write_text(
        json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")  # (부분)lesson 사본
    for asset in ("_deck.css", "_deck.js"):
        a = DECK_ASSETS / asset
        if not a.exists():
            print(f"[warn] 덱 자산 없음: {a}")
            continue
        dst = src / asset
        if dst.exists():
            # 예전 번들의 자산이 읽기 전용으로 남아 있으면 copy2 가 PermissionError 로
            # 죽으면서 뒤 회차까지 통째로 멈춘다 → 쓰기 권한을 풀고 덮어쓴다.
            try:
                dst.chmod(stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
        shutil.copy2(a, dst)
    (src / "deck.html").write_text(deck_html, encoding="utf-8")

    (bundle / "script" / f"{code}_script.json").write_text(
        json.dumps(build_series(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")
    (bundle / "review.json").write_text(
        json.dumps(build_review(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")

    n_cap = sum(1 for s in scenes if s["capture"])
    n_prob = len({s.number for s in slides if s.kind == "problem"})
    extra = sum(1 for s in slides if s.page > 1)
    assert n_cap == len(slides), f"내부 오류: 캡처 씬 {n_cap} != 슬라이드 {len(slides)}"

    # 슬라이드 PNG 캡처 — 번들이 자체 완결되게(#3 는 카운트다운/간격·음성·모션만).
    n_png = 0
    if do_capture:
        with tempfile.TemporaryDirectory(prefix="deck-capture-") as td:
            n_png = capture_deck(deck_html, bundle / "images", scenes, Path(td))
        if n_png < 0:
            warns.append("playwright 가 없어 이미지 캡처를 건너뛰었습니다 "
                         "(pip install playwright && python -m playwright install chromium)")
            n_png = 0

    print(f"[{code}] 문항 {n_prob} · 슬라이드 {len(slides)}(분할로 늘어난 페이지 {extra}) "
          f"· 씬 {len(scenes)}(캡처 {n_cap}) · 이미지 {n_png}장 → 05/{code}/")
    for w in warns:
        print(f"  [warn] {w}")


def process_lesson(lesson_path: Path, book: Path, do_paginate: bool, chunk: int = 0,
                   do_capture: bool = True) -> None:
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    stem = lesson_path.stem
    code = stem[len("lesson_"):] if stem.startswith("lesson_") else stem
    parts = chunk_lesson(lesson, chunk)
    if len(parts) > 1:
        print(f"[{code}] {chunk}문항씩 {len(parts)}편으로 분할")
    for suffix, sub in parts:
        write_bundle(sub, code if suffix is None else f"{code}{suffix}", book, do_paginate, do_capture)


def main() -> int:
    ap = argparse.ArgumentParser(description="exam-forge bundle builder (05 단계)")
    ap.add_argument("--book", required=True, help="책 루트 (예: D:/00work/ocr-output-260723)")
    ap.add_argument("--round", default=None, help="특정 회차코드만 (예: m01)")
    ap.add_argument("--stage04-dir", default=None, help="lesson JSON 폴더 (기본: <book>/04)")
    ap.add_argument("--chunk", type=int, default=0,
                    help="문항 N개씩 여러 편으로 분할(예: 10 → 회차당 5편 05/mNN-1..). 0=분할 안 함")
    ap.add_argument("--no-paginate", action="store_true",
                    help="높이 측정/페이지 분할 생략(빠른 확인용 — 잘릴 수 있음)")
    ap.add_argument("--no-capture", action="store_true",
                    help="슬라이드 PNG 캡처 생략(빠른 확인용 — images/ 안 채움)")
    ap.add_argument("--force", action="store_true", help="(호환용, 무시됨 — deck 는 항상 재생성)")
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
        process_lesson(f, book, not args.no_paginate, args.chunk, not args.no_capture)
    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
