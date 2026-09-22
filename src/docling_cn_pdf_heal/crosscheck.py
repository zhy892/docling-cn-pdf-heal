"""Optional OCR/text-layer disagreement check for visually plausible corruption.

This is an audit signal, not a language-model guess: callers provide an OCR
transcript for a page and decide how to obtain it.  The normal routing path
therefore remains fast and does not OCR clean pages merely to score them.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .metrics import binary_detection_metrics, character_error_rate, normalize_for_cer

_IDENTIFIER_RE = re.compile(r"[a-z]+\d*|\d+(?:\.\d+)?", re.IGNORECASE)


def _identifier_tokens(text: str) -> set[str]:
    """Return normalized technical identifier fragments, excluding bare letters."""
    return {
        token.casefold()
        for token in _IDENTIFIER_RE.findall(normalize_for_cer(text))
        if len(token) >= 2 or token.isdigit()
    }


@dataclass(frozen=True)
class OcrCrossCheckReport:
    """Auditable result of comparing one text layer with one OCR transcript."""

    eligible: bool
    needs_ocr: bool
    agreement: float | None
    text_layer_char_count: int
    ocr_char_count: int
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_ocr_disagreement(
    text_layer: str,
    ocr_text: str,
    *,
    min_characters: int = 12,
    agreement_threshold: float = 0.65,
) -> OcrCrossCheckReport:
    """Flag a sufficiently long text-layer/OCR mismatch.

    The comparison is whitespace-insensitive and NFKC-normalized, matching the
    documented CER calculation. Short snippets are intentionally ineligible:
    they are too unstable for a routing decision. A caller should surface this
    result in a review report rather than treating OCR as unquestioned truth.
    """
    if min_characters < 1:
        raise ValueError("min_characters must be at least 1")
    if not 0 <= agreement_threshold <= 1:
        raise ValueError("agreement_threshold must be between 0 and 1")

    normalized_layer = normalize_for_cer(text_layer)
    normalized_ocr = normalize_for_cer(ocr_text)
    layer_count = len(normalized_layer)
    ocr_count = len(normalized_ocr)
    if min(layer_count, ocr_count) < min_characters:
        return OcrCrossCheckReport(
            eligible=False,
            needs_ocr=False,
            agreement=None,
            text_layer_char_count=layer_count,
            ocr_char_count=ocr_count,
            reason="insufficient_text",
        )

    agreement = max(0.0, 1.0 - character_error_rate(normalized_layer, normalized_ocr))
    global_disagreement = agreement < agreement_threshold
    # A short version/standard identifier can be semantically important while
    # contributing little to whole-page CER. This remains a review signal only.
    identifier_disagreement = bool(
        _identifier_tokens(normalized_ocr) - _identifier_tokens(normalized_layer)
    )
    needs_ocr = global_disagreement or identifier_disagreement
    return OcrCrossCheckReport(
        eligible=True,
        needs_ocr=needs_ocr,
        agreement=round(agreement, 6),
        text_layer_char_count=layer_count,
        ocr_char_count=ocr_count,
        reason=(
            "ocr_text_disagreement"
            if global_disagreement
            else "ocr_identifier_disagreement"
            if identifier_disagreement
            else "agreement_acceptable"
        ),
    )


def compare_page_transcripts(
    text_layer_pages: list[str],
    ocr_pages: list[str],
    *,
    min_characters: int = 12,
    agreement_threshold: float = 0.65,
) -> list[dict[str, object]]:
    """Compare aligned page transcripts while retaining one-based page numbers."""
    if len(text_layer_pages) != len(ocr_pages):
        raise ValueError("text-layer and OCR transcript page counts must match")
    return [
        {
            "page_no": page_no,
            "crosscheck": assess_ocr_disagreement(
                text_layer,
                ocr_text,
                min_characters=min_characters,
                agreement_threshold=agreement_threshold,
            ).to_dict(),
        }
        for page_no, (text_layer, ocr_text) in enumerate(
            zip(text_layer_pages, ocr_pages), start=1
        )
    ]


def evaluate_crosscheck_detection(
    text_layer_pages: list[str],
    ocr_pages: list[str],
    is_damaged: list[bool],
    *,
    min_characters: int = 12,
    agreement_threshold: float = 0.65,
) -> dict[str, object]:
    """Evaluate crosscheck review recommendations against separate labels.

    OCR is treated as an independent measurement, not replacement text.  A
    disagreement becomes a `manual_review` recommendation, and labels are used
    only after recommendations are produced to compute auditable metrics.
    """
    if len(text_layer_pages) != len(is_damaged):
        raise ValueError("text-layer and label page counts must match")
    page_checks = compare_page_transcripts(
        text_layer_pages,
        ocr_pages,
        min_characters=min_characters,
        agreement_threshold=agreement_threshold,
    )
    predictions = [
        bool(entry["crosscheck"]["needs_ocr"])  # type: ignore[index]
        for entry in page_checks
    ]
    manual_review_pages = [
        entry["page_no"]
        for entry in page_checks
        if entry["crosscheck"]["needs_ocr"]  # type: ignore[index]
    ]
    return {
        "pages": len(page_checks),
        "manual_review_pages": manual_review_pages,
        "detection": binary_detection_metrics(is_damaged, predictions),
        "page_checks": page_checks,
    }
