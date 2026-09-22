"""Deterministic, explainable detectors for damaged PDF text layers.

This module intentionally has no OCR or PDF-library dependency. It can be used
inside Docling or by an external orchestration CLI, and every score component is
returned as a named signal for review.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

_GID_RE = re.compile(r"/(?:gid|G)\d+\b", re.IGNORECASE)
_CID_RE = re.compile(r"\(cid:\s*\d+\)", re.IGNORECASE)
_GLYPH_RE = re.compile(r"GLYPH<[^>]*>", re.IGNORECASE)


@dataclass(frozen=True)
class QualityReport:
    """Quality evidence and routing decision for one extracted page."""

    score: float
    needs_ocr: bool
    reasons: tuple[str, ...]
    char_count: int
    non_whitespace_count: int
    glyph_token_count: int
    cid_token_count: int
    replacement_count: int
    private_use_count: int
    control_count: int
    suspicious_ratio: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _is_private_use(ch: str) -> bool:
    codepoint = ord(ch)
    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )


def score_text_quality(text: str, *, threshold: float = 0.20) -> QualityReport:
    """Score extracted text and decide whether the page should be OCRed.

    A score of 0 means no observed corruption signal.  A score of 1 represents
    clear corruption. The default threshold is deliberately conservative:
    explicit glyph/CID markers trigger a fallback on their own, while rare
    private-use/control characters must accumulate before routing a clean page.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    glyph_token_count = len(_GID_RE.findall(text)) + len(_GLYPH_RE.findall(text))
    cid_token_count = len(_CID_RE.findall(text))
    replacement_count = text.count("\ufffd")
    private_use_count = 0
    control_count = 0
    non_whitespace_count = 0
    for ch in text:
        if not ch.isspace():
            non_whitespace_count += 1
        if _is_private_use(ch):
            private_use_count += 1
        elif ch not in "\n\r\t" and unicodedata.category(ch) == "Cc":
            control_count += 1
    char_count = max(len(text), 1)

    # Token markers are much stronger evidence than isolated non-printing chars.
    marker_score = min(1.0, 0.35 * glyph_token_count + 0.35 * cid_token_count)
    character_score = min(
        1.0,
        (replacement_count + private_use_count + control_count) / char_count * 4.0,
    )
    # A visually non-empty PDF page may yield only whitespace when a backend
    # cannot decode its font. Treat that as an explicit route-to-OCR signal.
    empty_text_score = 1.0 if non_whitespace_count == 0 else 0.0
    score = min(1.0, marker_score + character_score + empty_text_score)
    suspicious_ratio = min(
        1.0,
        (replacement_count + private_use_count + control_count) / char_count,
    )

    reasons: list[str] = []
    if non_whitespace_count == 0:
        reasons.append("empty_extracted_text")
    if glyph_token_count:
        reasons.append("glyph_identifier")
    if cid_token_count:
        reasons.append("cid_escape")
    if replacement_count:
        reasons.append("replacement_character")
    if private_use_count:
        reasons.append("private_use_character")
    if control_count:
        reasons.append("embedded_control_character")

    return QualityReport(
        score=round(score, 6),
        needs_ocr=score >= threshold,
        reasons=tuple(reasons),
        char_count=len(text),
        non_whitespace_count=non_whitespace_count,
        glyph_token_count=glyph_token_count,
        cid_token_count=cid_token_count,
        replacement_count=replacement_count,
        private_use_count=private_use_count,
        control_count=control_count,
        suspicious_ratio=round(suspicious_ratio, 6),
    )
