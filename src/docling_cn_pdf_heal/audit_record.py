"""Privacy-preserving metadata for locally audited PDFs."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_local_audit_record(
    source: Path,
    *,
    audit_id: str,
    backend: str,
    page_count: int,
    ocr_candidate_pages: list[int],
    skipped_blank_pages: list[int],
) -> dict[str, object]:
    """Return a shareable record without a local path, name, or PDF content."""
    if not audit_id.strip():
        raise ValueError("audit_id must not be empty")
    if page_count < 0:
        raise ValueError("page_count must not be negative")
    if not source.is_file():
        raise FileNotFoundError(source)
    return {
        "audit_id": audit_id,
        "source_sha256": _sha256_file(source),
        "backend": backend,
        "page_count": page_count,
        "ocr_candidate_pages": list(ocr_candidate_pages),
        "skipped_blank_pages": list(skipped_blank_pages),
    }
