"""A dependency-free prototype of the proposed Docling quality-report contract.

This module is deliberately not registered as a Docling plugin.  It makes the
proposed, opt-in metadata shape executable and tested before an upstream design
is agreed.  A future upstream implementation should use Docling's own Pydantic
option and result types rather than importing this package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .routing import plan_routes


@dataclass(frozen=True)
class TextLayerQualityCheckOptions:
    """Proposed opt-in configuration, with the upstream-safe default disabled."""

    enabled: bool = False
    score_threshold: float = 0.20

    def __post_init__(self) -> None:
        if not 0 <= self.score_threshold <= 1:
            raise ValueError("score_threshold must be between 0 and 1")


def build_page_quality_metadata(
    page_texts: list[str], options: TextLayerQualityCheckOptions
) -> dict[str, Any]:
    """Return proposed per-page metadata without changing extracted content.

    ``recommend_ocr`` is intentionally a recommendation, not an OCR operation.
    This preserves Docling's current behavior and leaves selected-page OCR to a
    separately reviewed upstream change.
    """
    if not options.enabled:
        return {"enabled": False, "pages": []}

    pages: list[dict[str, Any]] = []
    for route in plan_routes(page_texts, threshold=options.score_threshold):
        record = route.to_dict()
        record["action"] = (
            "recommend_ocr" if route.action == "ocr_fallback" else route.action
        )
        pages.append(record)
    return {
        "enabled": True,
        "score_threshold": options.score_threshold,
        "pages": pages,
    }
