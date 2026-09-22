"""Selective OCR recovery orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .docling_adapter import extract_pdf_pages
from .ocr import TesseractOptions, ocr_selected_pages
from .page_ink import PageInkEstimate, estimate_pdf_page_ink, retain_nonblank_candidates
from .routing import PageRoute, plan_routes


@dataclass(frozen=True)
class RecoveryResult:
    routes: list[PageRoute]
    recovered_pages: list[str]
    ocr_pages: tuple[int, ...]
    skipped_blank_pages: tuple[int, ...]
    ink_estimates: dict[int, PageInkEstimate]


def recover_pdf(
    path: Path,
    *,
    backend: str = "native-docling",
    threshold: float = 0.20,
    ocr_options: TesseractOptions | None = None,
) -> RecoveryResult:
    """Extract text, OCR only suspicious pages, and return final page text."""
    source_pages = extract_pdf_pages(path, backend=backend)

    routes = plan_routes(source_pages, threshold=threshold)
    candidate_ocr_pages = [
        route.page_no for route in routes if route.action == "ocr_fallback"
    ]
    ink_estimates: dict[int, PageInkEstimate] = {}
    for page_no in candidate_ocr_pages:
        try:
            ink_estimates[page_no] = estimate_pdf_page_ink(path, page_no)
        except RuntimeError:
            # A renderer failure is not evidence that the page is blank.
            # retain_nonblank_candidates therefore fails open for this page.
            continue
    ocr_pages, skipped_blank_pages = retain_nonblank_candidates(
        candidate_ocr_pages, ink_estimates
    )
    recovered = list(source_pages)
    replacements = ocr_selected_pages(
        path, ocr_pages, ocr_options or TesseractOptions()
    )
    for page_no, text in replacements.items():
        recovered[page_no - 1] = text
    return RecoveryResult(
        routes=routes,
        recovered_pages=recovered,
        ocr_pages=tuple(ocr_pages),
        skipped_blank_pages=tuple(skipped_blank_pages),
        ink_estimates=ink_estimates,
    )
