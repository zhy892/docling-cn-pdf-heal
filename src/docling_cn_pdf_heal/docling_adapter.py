"""Model-free Docling text-layer adapter used by the benchmark baseline."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any


def create_native_docling_converter() -> Any:
    """Build the model-free Docling converter used by the native baseline."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import NativePdfPipelineOptions
    from docling.document_converter import DocumentConverter, NativePdfFormatOption

    return DocumentConverter(
        format_options={
            InputFormat.PDF: NativePdfFormatOption(
                pipeline_options=NativePdfPipelineOptions()
            )
        }
    )


def read_pdf_text_layer_pages(path: Path) -> list[str]:
    """Read one text-layer string per page with pypdf, without OCR."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - declared project dependency
        raise RuntimeError("PDF input requires pypdf; reinstall the project") from exc
    return [(page.extract_text() or "") for page in PdfReader(path).pages]


def extract_pages_with_native_docling(
    path: Path, *, converter: Any | None = None
) -> list[str]:
    """Extract page text with Docling's `NativePdfPipeline`.

    The native pipeline is deliberately used for the first baseline because it
    exercises Docling's PDF parser without downloading layout or OCR models.
    It preserves page provenance, allowing the quality router to decide which
    pages should incur an OCR cost later.
    """
    converter = converter or create_native_docling_converter()
    result = converter.convert(path)
    # Initialize every parsed page. Image-only pages have no TextItem and must
    # remain as explicit empty strings so the router can send them to OCR.
    by_page: dict[int, list[str]] = defaultdict(list)
    for page in result.pages:
        by_page[page.page_no]
    for item, _level in result.document.iterate_items():
        text = getattr(item, "text", None)
        provenance = getattr(item, "prov", None)
        if not text or not provenance:
            continue
        for source in provenance:
            by_page[source.page_no].append(text)
            break
    return ["\n".join(by_page[page_no]) for page_no in sorted(by_page)]


def extract_pdf_pages(path: Path, *, backend: str) -> list[str]:
    """Dispatch a PDF text-layer extraction backend without invoking OCR."""
    if backend == "pypdf":
        return read_pdf_text_layer_pages(path)
    if backend == "native-docling":
        return extract_pages_with_native_docling(path)
    raise ValueError(f"unsupported backend: {backend}")
