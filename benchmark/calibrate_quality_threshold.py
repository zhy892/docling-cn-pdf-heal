"""Freeze a text-layer routing threshold using a synthetic development split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docling_cn_pdf_heal.threshold_calibration import calibrate_development_pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pages",
        type=Path,
        help="JSON object containing page texts under the 'pages' key",
    )
    parser.add_argument(
        "manifest", type=Path, help="synthetic manifest with split and label fields"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    page_data = json.loads(args.pages.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    page_texts = page_data.get("pages")
    records = manifest.get("records")
    if not isinstance(page_texts, list) or not all(
        isinstance(text, str) for text in page_texts
    ):
        raise ValueError("pages JSON must contain a string list under 'pages'")
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise ValueError("manifest JSON must contain object records")

    result = calibrate_development_pages(page_texts=page_texts, records=records)
    result["protocol"] = "development-only-threshold-calibration-v1"
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
