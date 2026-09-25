"""Clause segmentation and chunking with page/clause mapping.

Legal documents are numbered ("9.", "9.2", "Clause 9.2"). We keep clause numbers so
every retrieved chunk can be cited as "page N, clause X".
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.extraction import ExtractedPage

CLAUSE_START = re.compile(
    r"^\s*(?:(?:Clause|Section|Article)\s+)?"
    r"(?P<num>\d{1,3}(?:\.\d{1,3})+|\d{1,3}[.)])\s+(?P<text>\S.*)$",
    re.IGNORECASE,
)
MAX_CHUNK_CHARS = 1100
HEADING_MAX_LEN = 70


@dataclass
class Clause:
    number: str | None
    section: str | None
    page_start: int
    page_end: int
    text: str
    heading_only: bool = False


@dataclass
class Chunk:
    index: int
    page_number: int
    page_end: int
    section: str | None
    clause: str | None
    content: str


def _norm_num(num: str) -> str:
    return num.rstrip(".)")


def _is_heading(num: str, text: str) -> bool:
    top_level = "." not in _norm_num(num)
    return top_level and len(text) <= HEADING_MAX_LEN and not text.rstrip().endswith((".", ";", ":"))


def segment_clauses(pages: list[ExtractedPage]) -> list[Clause]:
    clauses: list[Clause] = []
    cur: dict | None = None
    section: str | None = None

    def flush() -> None:
        nonlocal cur
        if cur and "\n".join(cur["lines"]).strip():
            clauses.append(
                Clause(
                    cur["num"],
                    cur["section"],
                    cur["page_start"],
                    cur["page_end"],
                    "\n".join(cur["lines"]).strip(),
                    heading_only=cur.get("heading", False) and len(cur["lines"]) == 1,
                )
            )
        cur = None

    for page in pages:
        for raw in page.text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = CLAUSE_START.match(line)
            if m:
                num, text = _norm_num(m.group("num")), m.group("text").strip()
                flush()
                is_heading = _is_heading(m.group("num"), text)
                if is_heading:
                    section = f"{num}. {text.title() if text.isupper() else text}"
                cur = {
                    "heading": is_heading,
                    "num": num,
                    "section": section,
                    "page_start": page.number,
                    "page_end": page.number,
                    "lines": [line],
                }
            else:
                if cur is None:
                    cur = {
                        "num": None,
                        "section": None,
                        "page_start": page.number,
                        "page_end": page.number,
                        "lines": [],
                    }
                cur["lines"].append(line)
                cur["page_end"] = page.number
    flush()
    return clauses


_SENT_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(])")


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    parts, buf = [], ""
    for sent in _SENT_SPLIT.split(text):
        if buf and len(buf) + len(sent) + 1 > MAX_CHUNK_CHARS:
            parts.append(buf.strip())
            buf = sent
        else:
            buf = f"{buf} {sent}".strip()
    if buf:
        parts.append(buf.strip())
    return parts


def build_chunks(pages: list[ExtractedPage]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for clause in segment_clauses(pages):
        if clause.heading_only:  # bare headings add noise; sections carry the title
            continue
        for piece in _split_long(clause.text):
            chunks.append(
                Chunk(
                    index=len(chunks),
                    page_number=clause.page_start,
                    page_end=clause.page_end,
                    section=clause.section,
                    clause=clause.number,
                    content=piece,
                )
            )
    return chunks
