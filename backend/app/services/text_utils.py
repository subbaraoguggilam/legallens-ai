"""Tokenisation helpers shared by embeddings, retrieval and analysis."""
from __future__ import annotations

import re

STOPWORDS = frozenset(
    """a an the of to in on at by for with and or but if then than that this these those is are was
    were be been being it its as from into upon per any all each such shall will may can could would
    should do does did not no nor so i me my we our you your he she they them their his her which who
    whom whose what when where why how there here also other either between under over out up""".split()
)

# Query-side expansion so plain-language questions reach legalese in the document.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "fire": ("terminate", "termination", "dismiss", "notice"),
    "fired": ("terminate", "termination", "dismiss", "notice"),
    "quit": ("resign", "terminate", "notice"),
    "leave": ("terminate", "resign", "notice"),
    "resign": ("terminate", "notice", "resignation"),
    "pay": ("salary", "compensation", "remuneration", "payment", "fee"),
    "paid": ("salary", "compensation", "remuneration", "payment"),
    "salary": ("compensation", "remuneration", "payment"),
    "money": ("payment", "salary", "fee", "amount"),
    "rent": ("rental", "lease", "payment"),
    "secret": ("confidential", "confidentiality", "disclose"),
    "confidential": ("confidentiality", "disclose", "disclosure"),
    "invention": ("intellectual", "property", "ownership", "assign"),
    "ideas": ("intellectual", "property", "ownership"),
    "own": ("ownership", "property", "assign"),
    "sue": ("dispute", "court", "arbitration", "jurisdiction"),
    "dispute": ("arbitration", "court", "jurisdiction", "governing"),
    "court": ("jurisdiction", "dispute", "arbitration"),
    "compete": ("non-compete", "restrict", "restraint", "competing"),
    "competitor": ("non-compete", "restrict", "competing"),
    "refund": ("cancellation", "reimburse", "return"),
    "cancel": ("cancellation", "terminate", "refund"),
    "renew": ("renewal", "extend", "term"),
    "long": ("duration", "term", "period"),
    "duration": ("term", "period"),
    "obligation": ("shall", "must", "responsible", "duty"),
    "obligations": ("shall", "must", "responsible", "duty"),
    "duties": ("shall", "must", "responsible", "obligation"),
    "liable": ("liability", "indemnify", "damages"),
    "liability": ("indemnify", "damages", "loss"),
    "privacy": ("personal", "data", "information", "protection"),
    "data": ("personal", "information", "privacy"),
    "immediately": ("without", "notice", "forthwith", "immediate"),
    "notice": ("days", "written", "period"),
}

_TOKEN = re.compile(r"[a-z0-9][a-z0-9'\-]*", re.IGNORECASE)


def stem(tok: str) -> str:
    """Very light suffix stripping (good enough for lexical matching of contracts)."""
    for suf in ("ations", "ation", "ments", "ment", "ities", "ity", "ings", "ing", "ies", "es", "ed", "s", "ly"):
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            return tok[: -len(suf)]
    return tok


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    toks = [t.lower().strip("'-") for t in _TOKEN.findall(text)]
    if not keep_stopwords:
        toks = [t for t in toks if t and t not in STOPWORDS]
    return [stem(t) for t in toks if t]


def expand_query(text: str) -> str:
    extra: list[str] = []
    for tok in re.findall(r"[a-z]+", text.lower()):
        extra.extend(SYNONYMS.get(tok, ()))
    return f"{text} {' '.join(extra)}" if extra else text


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;!?])\s+|\n+", text)
    return [p.strip() for p in parts if p and len(p.strip()) > 3]
