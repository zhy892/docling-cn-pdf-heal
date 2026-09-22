"""Run the V3 OCR/text-layer crosscheck without altering frozen V2 results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docling_cn_pdf_heal.crosscheck import evaluate_crosscheck_detection


def read_pages(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = data.get("pages")
    if not isinstance(pages, list) or not all(isinstance(page, str) for page in pages):
        raise ValueError(f"{path} must contain a string pages array")
    return pages


def rebase_review_pages(result: dict[str, object], offset: int) -> dict[str, object]:
    copied = dict(result)
    copied["manual_review_pages"] = [
        page_no + offset for page_no in result["manual_review_pages"]  # type: ignore[index]
    ]
    return copied


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-layer", type=Path, required=True)
    parser.add_argument("--ocr-transcript", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-characters", type=int, default=12)
    parser.add_argument("--agreement-threshold", type=float, default=0.65)
    args = parser.parse_args()

    text_layer = read_pages(args.text_layer)
    ocr = read_pages(args.ocr_transcript)
    labels = json.loads(args.labels.read_text(encoding="utf-8"))
    damaged = labels.get("is_damaged")
    split = labels.get("split")
    if not isinstance(damaged, list) or not all(isinstance(value, bool) for value in damaged):
        raise ValueError("labels must contain a boolean is_damaged array")
    if not isinstance(split, list) or not all(value in {"development", "test"} for value in split):
        raise ValueError("labels must contain development/test split labels")
    if not (len(text_layer) == len(ocr) == len(damaged) == len(split)):
        raise ValueError("text-layer, OCR, labels, and split page counts must match")

    def evaluate_partition(name: str) -> dict[str, object]:
        indices = [index for index, value in enumerate(split) if value == name]
        if not indices:
            raise ValueError(f"no {name} pages")
        result = evaluate_crosscheck_detection(
            [text_layer[index] for index in indices],
            [ocr[index] for index in indices],
            [damaged[index] for index in indices],
            min_characters=args.min_characters,
            agreement_threshold=args.agreement_threshold,
        )
        # V3 generator uses contiguous splits; reject a non-contiguous split
        # instead of publishing misleading page numbers.
        if indices != list(range(indices[0], indices[-1] + 1)):
            raise ValueError(f"{name} split must be contiguous for page reporting")
        return rebase_review_pages(result, indices[0])

    output = {
        "protocol": labels.get("protocol", "crosscheck-benchmark-v1"),
        "agreement_threshold": args.agreement_threshold,
        "development": evaluate_partition("development"),
        "frozen_test": evaluate_partition("test"),
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
