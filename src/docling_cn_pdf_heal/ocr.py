"""A small, auditable Tesseract OCR adapter for selected PDF pages."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TesseractOptions:
    language: str = "chi_sim"
    tessdata_dir: Path | None = None
    dpi: int = 250
    page_segmentation_mode: int = 6
    timeout_seconds: int = 90


def ocr_selected_pages(
    pdf_path: Path, page_numbers: list[int], options: TesseractOptions
) -> dict[int, str]:
    """Render and OCR only 1-indexed `page_numbers` from a PDF."""
    if not page_numbers:
        return {}
    result: dict[int, str] = {}
    with tempfile.TemporaryDirectory(prefix="pdf-heal-ocr-") as temp_dir:
        temp_path = Path(temp_dir)
        for page_no in sorted(set(page_numbers)):
            render_prefix = temp_path / f"page-{page_no}"
            render = subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page_no),
                    "-l",
                    str(page_no),
                    "-png",
                    "-r",
                    str(options.dpi),
                    str(pdf_path),
                    str(render_prefix),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if render.returncode:
                detail = render.stderr.strip() or "unknown pdftoppm error"
                raise RuntimeError(f"PDF rendering failed on page {page_no}: {detail}")
            images = list(temp_path.glob(f"page-{page_no}-*.png"))
            if len(images) != 1:
                raise RuntimeError(f"expected one rendered image for page {page_no}")
            command = [
                "tesseract",
                str(images[0]),
                "stdout",
                "-l",
                options.language,
                "--psm",
                str(options.page_segmentation_mode),
            ]
            if options.tessdata_dir:
                command.extend(["--tessdata-dir", str(options.tessdata_dir)])
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=options.timeout_seconds,
            )
            if completed.returncode:
                detail = completed.stderr.strip() or "unknown Tesseract error"
                raise RuntimeError(f"Tesseract failed on page {page_no}: {detail}")
            result[page_no] = completed.stdout.strip()
    return result
