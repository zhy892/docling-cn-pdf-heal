"""Page-level routing based on text-layer quality reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .quality import QualityReport, score_text_quality


@dataclass(frozen=True)
class PageRoute:
    page_no: int
    action: str
    report: QualityReport

    def to_dict(self) -> dict[str, object]:
        return {
            "page_no": self.page_no,
            "action": self.action,
            "quality": self.report.to_dict(),
        }


def plan_routes(
    page_texts: Iterable[str], *, threshold: float = 0.20
) -> list[PageRoute]:
    """Return an auditable per-page decision without executing OCR."""
    routes: list[PageRoute] = []
    for page_no, text in enumerate(page_texts, start=1):
        report = score_text_quality(text, threshold=threshold)
        action = "ocr_fallback" if report.needs_ocr else "keep_text_layer"
        routes.append(PageRoute(page_no=page_no, action=action, report=report))
    return routes
