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


@dataclass
class Slide:
    kind: str                        # cover | section | problem | answer
    heading: str
    number: int | None = None
    classes: str = "content"
    fixed: list[str] = field(default_factory=list)   # 페이지마다 상단에 반복되는 HTML
    blocks: list[Block] = field(default_factory=list)
    chip: str = ""                                   # 우상단 칩(출처 등)
    narration: str = ""                              # 자막/표시용 원문
    speech: str = ""                                 # 낭독용(비면 blocks 에서 생성)
    shrink: int = 0                                  # 0=원본 · 1=dense · 2=dense2(축소)
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


def _blk(html_: str, speech: str = "", keep: bool = False) -> Block:
    return Block(html_, speech, _fallback_speech(html_), keep)


def _choices_speech(choices: list) -> str:
    return " ".join(f"{i + 1}번, {to_speech(_strip_lead_marker(str(c)))}."
                    for i, c in enumerate(choices))


def build_slides(lesson: dict) -> list[Slide]:
    """lesson → 슬라이드 목록(아직 페이지 분할 전, 문항당 문제 1 + 해설 1)."""
    round_label = _strip_brand(lesson.get("round") or lesson.get("title", ""))
    slides: list[Slide] = []

    # 표지 — 브랜딩(eyebrow) 없음
    slides.append(Slide(
        kind="cover", classes="cover", heading=_strip_brand(lesson.get("title", round_label)),
        fixed=[f'<h1>{html.escape(_strip_brand(lesson.get("title", round_label)))}</h1>',
               '<p class="lead">문제 풀이</p>'],
        narration=f"{round_label}. 문제 풀이를 시작합니다."))

    for b in lesson.get("blocks", []):
        kind = b.get("kind")
        if kind == "section":
            sub, ttl = _strip_brand(b.get("subtitle", "")), _strip_brand(b.get("title", ""))
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

        # ── 문제 슬라이드: 발문 고정, 지문/SQL/표 → 블록, 보기는 통째로 한 덩어리
        q_blocks: list[Block] = []
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
        if choices:
            q_blocks.append(_blk(_choices_ul(choices), _choices_speech(choices), keep=True))

        slides.append(Slide(
            kind="problem", number=n, heading=f"{n}번 문제",
            chip=f"{round_label} {n}번",
            fixed=[f'<div class="qnum">{n}번 문제</div>',
                   f'<div class="qtext">{_md_inline(b.get("question", ""))}</div>'],
            blocks=q_blocks,
            narration=b.get("question", ""),
            speech=to_speech(b.get("narration_question") or b.get("question", ""))))

        # ── 해설 슬라이드: 정답 배지 + 정답 보기만 고정(오답 3개는 빼서 높이 확보), 해설은 분할
        ans = b.get("answer") or (circled(ai) if isinstance(ai, int) else "")
        fixed = [f'<div class="s-head"><span class="tag">정답 및 해설</span><h2>{n}번</h2></div>',
                 f'<div class="answer-badge">정답 {html.escape(str(ans))}</div>']
        if isinstance(ai, int) and 0 <= ai < len(choices):
            fixed.append(f'<ul class="choices">{_choice_li(ai, str(choices[ai]), True)}</ul>')
        e_blocks = [_blk(f'<div class="explain">{h_}</div>', sp)
                    for h_, sp in md_blocks(b.get("explanation", ""))]
        slides.append(Slide(
            kind="answer", number=n, heading=f"{n}번 · 정답 {ans}",
            fixed=fixed, blocks=e_blocks,
            narration=b.get("explanation", ""),
            speech=to_speech(b.get("narration_answer") or b.get("explanation_speech")
                             or b.get("explanation", ""))))
    return slides


# ============================================================ deck.html 렌더
def _slide_html(s: Slide, si: int) -> str:
    cls = s.classes + ("", " dense", " dense dense2")[min(s.shrink, 2)]
    parts = [f'  <section class="slide {cls}">']
    if s.chip:
        parts.append(f'    <span class="source-chip">{html.escape(s.chip)}</span>')
    if s.pages > 1:
        parts.append(f'    <span class="page-chip">{s.page} / {s.pages}</span>')
    body = [f'      <div data-fixed>{h_}</div>' for h_ in s.fixed]
    body += [f'      <div data-fid="{si}-{bi}">{b.html}</div>' for bi, b in enumerate(s.blocks)]
    inner = "\n".join(body)
    if s.kind == "problem":
        parts.append(f'    <div class="qcard">\n{inner}\n    </div>')
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
        '.page-chip{position:absolute;top:48px;left:48px;background:var(--soft);color:var(--brand-ink);'
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
    let avail = s.clientHeight - px(cs.paddingTop) - px(cs.paddingBottom) - footH;
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
    return {
      si, avail,
      fixed: [...s.querySelectorAll('[data-fixed]')].reduce((a, el) => a + meas(el), 0),
      blocks: Object.fromEntries([...s.querySelectorAll('[data-fid]')].map(el => [el.dataset.fid, meas(el)])),
      over: Math.max(0, s.scrollHeight - s.clientHeight),
    };
  });
}
"""


def measure(html_text: str, workdir: Path) -> list[dict] | None:
    """deck HTML 을 헤드리스 크로미움으로 열어 슬라이드별 안전영역·블록 높이를 잰다."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    page_file = workdir / "_measure.html"
    page_file.write_text(html_text, encoding="utf-8")
    for asset in ("_deck.css", "_deck.js"):
        src = DECK_ASSETS / asset
        if src.exists():
            shutil.copy2(src, workdir / asset)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto(page_file.as_uri(), wait_until="networkidle")
        try:
            pg.evaluate("document.fonts && document.fonts.ready")
        except Exception:
            pass
        pg.wait_for_timeout(250)
        data = pg.evaluate(MEASURE_JS)
        browser.close()
    return data


SAFETY = 24.0   # 측정 오차·마진 겹침 여유(px)


def _paginate_one(s: Slide, m: dict) -> list[Slide]:
    """슬라이드 1장 → 안전영역에 맞춘 페이지 목록. 발문/정답은 페이지마다 반복."""
    capacity = m["avail"] - m["fixed"] - SAFETY
    heights = {k: float(v) for k, v in m["blocks"].items()}
    if capacity <= 0 or not s.blocks:
        return [s]

    pages: list[list[Block]] = []
    cur: list[Block] = []
    used = 0.0
    for bi, blk in enumerate(s.blocks):
        h = heights.get(f"{m['si']}-{bi}", 0.0)
        if cur and used + h > capacity:
            pages.append(cur)
            cur, used = [], 0.0
        cur.append(blk)
        used += h
    if cur:
        pages.append(cur)

    out: list[Slide] = []
    for pi, blks in enumerate(pages):
        p = Slide(kind=s.kind, heading=s.heading, number=s.number, classes=s.classes,
                  fixed=list(s.fixed), blocks=blks, chip=s.chip,
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
    m = measure(render_deck(lesson, slides), workdir)
    if m is None:
        return slides, ["playwright 가 없어 페이지 분할을 건너뛰었습니다 "
                        "(pip install playwright && python -m playwright install chromium)"]

    out: list[Slide] = []
    for s, mm in zip(slides, m):
        out.extend(_paginate_one(s, mm))

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
                    fixed=list(s.fixed), blocks=[moved], chip=s.chip, shrink=2,
                    narration="", speech=moved.speech))
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
def write_bundle(lesson: dict, code: str, book: Path, do_paginate: bool) -> None:
    bundle = book / "05" / code
    for sub in BUNDLE_SUBDIRS:
        (bundle / sub).mkdir(parents=True, exist_ok=True)

    slides = build_slides(lesson)
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
        if a.exists():
            shutil.copy2(a, src / asset)
        else:
            print(f"[warn] 덱 자산 없음: {a}")
    (src / "deck.html").write_text(deck_html, encoding="utf-8")

    (bundle / "script" / f"{code}_script.json").write_text(
        json.dumps(build_series(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")
    (bundle / "review.json").write_text(
        json.dumps(build_review(lesson, scenes), ensure_ascii=False, indent=2), encoding="utf-8")

    n_cap = sum(1 for s in scenes if s["capture"])
    n_prob = len({s.number for s in slides if s.kind == "problem"})
    extra = sum(1 for s in slides if s.page > 1)
    assert n_cap == len(slides), f"내부 오류: 캡처 씬 {n_cap} != 슬라이드 {len(slides)}"
    print(f"[{code}] 문항 {n_prob} · 슬라이드 {len(slides)}(분할로 늘어난 페이지 {extra}) "
          f"· 씬 {len(scenes)}(캡처 {n_cap}) → 05/{code}/")
    for w in warns:
        print(f"  [warn] {w}")


def process_lesson(lesson_path: Path, book: Path, do_paginate: bool, chunk: int = 0) -> None:
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    stem = lesson_path.stem
    code = stem[len("lesson_"):] if stem.startswith("lesson_") else stem
    parts = chunk_lesson(lesson, chunk)
    if len(parts) > 1:
        print(f"[{code}] {chunk}문항씩 {len(parts)}편으로 분할")
    for suffix, sub in parts:
        write_bundle(sub, code if suffix is None else f"{code}{suffix}", book, do_paginate)


def main() -> int:
    ap = argparse.ArgumentParser(description="exam-forge bundle builder (05 단계)")
    ap.add_argument("--book", required=True, help="책 루트 (예: D:/00work/ocr-output-260723)")
    ap.add_argument("--round", default=None, help="특정 회차코드만 (예: m01)")
    ap.add_argument("--stage04-dir", default=None, help="lesson JSON 폴더 (기본: <book>/04)")
    ap.add_argument("--chunk", type=int, default=0,
                    help="문항 N개씩 여러 편으로 분할(예: 10 → 회차당 5편 05/mNN-1..). 0=분할 안 함")
    ap.add_argument("--no-paginate", action="store_true",
                    help="높이 측정/페이지 분할 생략(빠른 확인용 — 잘릴 수 있음)")
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
        process_lesson(f, book, not args.no_paginate, args.chunk)
    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
