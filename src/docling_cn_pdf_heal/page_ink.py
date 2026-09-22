"""Low-resolution visible-ink checks for empty text-layer OCR candidates."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class PageInkEstimate:
    """Visible dark-pixel evidence from a grayscale PGM render."""

    is_blank: bool
    ink_pixels: int
    total_pixels: int
    ink_coverage: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@lru_cache(maxsize=256)
def _dark_pixel_table(max_dark_pixel: int) -> bytes:
    """Return a bytes.translate lookup table for a quantized darkness cutoff."""
    bounded = min(255, max(0, max_dark_pixel))
    return bytes(1 if pixel <= bounded else 0 for pixel in range(256))


def _count_dark_pixels(pixels: bytes, threshold: float) -> int:
    """Count pixels no brighter than threshold using C-level bytes operations."""
    return pixels.translate(_dark_pixel_table(int(threshold))).count(1)


def _next_pgm_token(data: bytes, offset: int) -> tuple[bytes, int]:
    """Read one PGM header token, skipping whitespace and comment lines."""
    while offset < len(data):
        if data[offset] == ord("#"):
            newline = data.find(b"\n", offset)
            offset = len(data) if newline == -1 else newline + 1
        elif chr(data[offset]).isspace():
            offset += 1
        else:
            break
    start = offset
    while offset < len(data) and not chr(data[offset]).isspace():
        offset += 1
    if start == offset:
        raise ValueError("truncated PGM header")
    return data[start:offset], offset


def estimate_pgm_ink(
    pgm: bytes,
    *,
    dark_threshold: int = 245,
    min_ink_pixels: int = 32,
    min_ink_coverage: float = 0.0005,
) -> PageInkEstimate:
    """Classify a binary PGM render as visually blank or visibly nonblank."""
    if not 0 <= dark_threshold <= 255:
        raise ValueError("dark_threshold must be between 0 and 255")
    if min_ink_pixels < 0 or not 0 <= min_ink_coverage <= 1:
        raise ValueError("invalid ink threshold")
    magic, offset = _next_pgm_token(pgm, 0)
    if magic != b"P5":
        raise ValueError("only binary PGM (P5) is supported")
    width_token, offset = _next_pgm_token(pgm, offset)
    height_token, offset = _next_pgm_token(pgm, offset)
    maximum_token, offset = _next_pgm_token(pgm, offset)
    width, height, maximum = int(width_token), int(height_token), int(maximum_token)
    if width <= 0 or height <= 0 or not 0 < maximum <= 255:
        raise ValueError("invalid PGM dimensions or maximum value")
    if offset >= len(pgm) or not chr(pgm[offset]).isspace():
        raise ValueError("PGM header is missing pixel separator")
    # The binary raster may legally begin with a byte such as 0x0A. Consume
    # exactly the header separator, with CRLF treated as one separator.
    if pgm[offset : offset + 2] == b"\r\n":
        offset += 2
    else:
        offset += 1
    pixels = pgm[offset:]
    total_pixels = width * height
    if len(pixels) != total_pixels:
        raise ValueError("PGM pixel payload does not match dimensions")
    scaled_threshold = dark_threshold * maximum / 255
    ink_pixels = _count_dark_pixels(pixels, scaled_threshold)
    coverage = ink_pixels / total_pixels
    is_blank = ink_pixels < min_ink_pixels or coverage < min_ink_coverage
    return PageInkEstimate(
        is_blank=is_blank,
        ink_pixels=ink_pixels,
        total_pixels=total_pixels,
        ink_coverage=round(coverage, 6),
    )


def retain_nonblank_candidates(
    page_numbers: list[int], estimates: dict[int, PageInkEstimate]
) -> tuple[list[int], list[int]]:
    """Skip only candidates proven visually blank; absent evidence fails open."""
    selected: list[int] = []
    skipped: list[int] = []
    for page_no in page_numbers:
        estimate = estimates.get(page_no)
        if estimate is not None and estimate.is_blank:
            skipped.append(page_no)
        else:
            selected.append(page_no)
    return selected, skipped


def estimate_pdf_page_ink(
    pdf_path: Path, page_no: int, *, dpi: int = 72
) -> PageInkEstimate:
    """Render one page at low resolution and estimate whether it has visible ink."""
    if page_no < 1 or dpi < 36:
        raise ValueError("page_no must be positive and dpi must be at least 36")
    with tempfile.TemporaryDirectory(prefix="pdf-heal-ink-") as raw_directory:
        output_prefix = Path(raw_directory) / "page"
        completed = subprocess.run(
            [
                "pdftoppm",
                "-f",
                str(page_no),
                "-l",
                str(page_no),
                "-r",
                str(dpi),
                "-gray",
                "-singlefile",
                str(pdf_path),
                str(output_prefix),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or "unknown pdftoppm error"
            raise RuntimeError(f"pdftoppm failed on page {page_no}: {detail}")
        return estimate_pgm_ink((output_prefix.with_suffix(".pgm")).read_bytes())
