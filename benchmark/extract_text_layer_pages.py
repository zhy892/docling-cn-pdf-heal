"""Export one extracted text string per PDF page for frozen calibration.

The output deliberately contains only the backend name and extracted page text.
Labels remain in a separate manifest, so the exporter cannot accidentally tune
the router from frozen test labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docling_cn_pdf_heal.docling_adapter import extract_pdf_pages


def extract_pages(pdf: Path, backend: str) -> list[str]:
    return extract_pdf_pages(pdf, backend=backend)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export page-level PDF text for development-only threshold calibration"
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--backend", choices=("pypdf", "native-docling"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    pages = extract_pages(args.pdf, args.backend)
    args.output.write_text(
        json.dumps({"backend": args.backend, "pages": pages}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
