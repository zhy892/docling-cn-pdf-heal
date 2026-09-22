"""Run default text-layer, full OCR, and selective OCR baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from docling_cn_pdf_heal.docling_adapter import (
    create_native_docling_converter,
    extract_pages_with_native_docling,
)
from docling_cn_pdf_heal.metrics import binary_detection_metrics, character_error_rate
from docling_cn_pdf_heal.ocr import TesseractOptions, ocr_selected_pages
from docling_cn_pdf_heal.page_ink import (
    estimate_pdf_page_ink,
    retain_nonblank_candidates,
)
from docling_cn_pdf_heal.routing import plan_routes
from docling_cn_pdf_heal.threshold_calibration import load_frozen_threshold


def mean_cer(reference: list[str], hypothesis: list[str]) -> float:
    return sum(character_error_rate(r, h) for r, h in zip(reference, hypothesis)) / len(
        reference
    )


def median_seconds(values: list[float]) -> float:
    return round(median(values), 6)


def page_type_metrics(
    page_types: list[str], predicted: list[bool]
) -> dict[str, dict[str, float | int]]:
    """Expose OCR-route rate separately for each frozen synthetic page type."""
    return {
        page_type: {
            "pages": sum(kind == page_type for kind in page_types),
            "ocr_routed_pages": sum(
                kind == page_type and is_routed
                for kind, is_routed in zip(page_types, predicted)
            ),
            "ocr_route_rate": round(
                sum(
                    kind == page_type and is_routed
                    for kind, is_routed in zip(page_types, predicted)
                )
                / sum(kind == page_type for kind in page_types),
                6,
            ),
        }
        for page_type in sorted(set(page_types))
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("truth", type=Path)
    parser.add_argument("--tessdata-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--labels", type=Path, help="optional JSON with is_damaged page labels"
    )
    parser.add_argument(
        "--repeats", type=int, default=3, help="post-warm-up repetitions (default: 3)"
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        help="development-only calibration evidence; required for frozen test claims",
    )
    args = parser.parse_args()
    if args.repeats < 1:
        raise ValueError("--repeats must be at least 1")
    threshold = load_frozen_threshold(args.calibration) if args.calibration else 0.20
    reference = json.loads(args.truth.read_text(encoding="utf-8"))["pages"]
    options = TesseractOptions(tessdata_dir=args.tessdata_dir)

    # Warm model/module initialization is excluded from the timed runs. The
    # two-page smoke set is for correctness, not a general speed claim.
    # Construct the model-free pipeline once.  Reusing it across warm-up and
    # timed repetitions preserves the extraction algorithm while avoiding
    # converter-configuration startup cost in every measurement.
    converter = create_native_docling_converter()
    extract_pages_with_native_docling(args.pdf, converter=converter)

    native_times: list[float] = []
    full_ocr_times: list[float] = []
    routing_times: list[float] = []
    selected_ocr_times: list[float] = []
    native: list[str] = []
    full_ocr: list[str] = []
    recovered: list[str] = []
    routes = []
    selected_page_nos: list[int] = []

    # Repeat the three complete methods after one warm-up.  Rotating their
    # order avoids systematically giving one method a warmer machine state.
    runners = ("native", "full_ocr", "selective")
    for repeat in range(args.repeats):
        for method in (
            runners[repeat % len(runners) :] + runners[: repeat % len(runners)]
        ):
            if method == "native":
                started = perf_counter()
                native = extract_pages_with_native_docling(args.pdf, converter=converter)
                native_times.append(perf_counter() - started)
            elif method == "full_ocr":
                started = perf_counter()
                full_ocr_map = ocr_selected_pages(
                    args.pdf, list(range(1, len(reference) + 1)), options
                )
                full_ocr = [
                    full_ocr_map[page_no] for page_no in range(1, len(reference) + 1)
                ]
                full_ocr_times.append(perf_counter() - started)
            else:
                started = perf_counter()
                adaptive_source = extract_pages_with_native_docling(
                    args.pdf, converter=converter
                )
                routes = plan_routes(adaptive_source, threshold=threshold)
                routing_times.append(perf_counter() - started)
                candidate_page_nos = [
                    route.page_no for route in routes if route.action == "ocr_fallback"
                ]
                ink_estimates = {}
                for page_no in candidate_page_nos:
                    try:
                        ink_estimates[page_no] = estimate_pdf_page_ink(
                            args.pdf, page_no
                        )
                    except RuntimeError:
                        continue
                selected_page_nos, skipped_blank_page_nos = retain_nonblank_candidates(
                    candidate_page_nos, ink_estimates
                )
                started = perf_counter()
                selected_ocr = ocr_selected_pages(args.pdf, selected_page_nos, options)
                selected_ocr_times.append(perf_counter() - started)
                recovered = list(adaptive_source)
                for page_no, text in selected_ocr.items():
                    recovered[page_no - 1] = text

    output = {
        "document": args.pdf.name,
        "pages": len(reference),
        "routing_threshold": threshold,
        "calibration_evidence": args.calibration.name if args.calibration else None,
        "methods": {
            "docling_native_text_layer": {
                "mean_cer": round(mean_cer(reference, native), 6),
                "median_seconds": median_seconds(native_times),
                "raw_seconds": [round(value, 6) for value in native_times],
                "ocr_pages": 0,
            },
            "full_page_tesseract_ocr": {
                "mean_cer": round(mean_cer(reference, full_ocr), 6),
                "median_seconds": median_seconds(full_ocr_times),
                "raw_seconds": [round(value, 6) for value in full_ocr_times],
                "ocr_pages": len(reference),
            },
            "selective_ocr_fallback": {
                "mean_cer": round(mean_cer(reference, recovered), 6),
                "median_text_layer_and_routing_seconds": median_seconds(routing_times),
                "median_selected_ocr_seconds": median_seconds(selected_ocr_times),
                "median_total_seconds": median_seconds(
                    [
                        routing + ocr
                        for routing, ocr in zip(routing_times, selected_ocr_times)
                    ]
                ),
                "raw_text_layer_and_routing_seconds": [
                    round(value, 6) for value in routing_times
                ],
                "raw_selected_ocr_seconds": [
                    round(value, 6) for value in selected_ocr_times
                ],
                "ocr_pages": len(selected_page_nos),
                "candidate_ocr_pages": len(candidate_page_nos),
                "skipped_blank_pages": skipped_blank_page_nos,
                "ink_estimates": {
                    str(page_no): estimate.to_dict()
                    for page_no, estimate in ink_estimates.items()
                },
                "routes": [route.to_dict() for route in routes],
            },
        },
    }
    if args.labels:
        label_data = json.loads(args.labels.read_text(encoding="utf-8"))
        labels = label_data["is_damaged"]
        predictions = [
            page_no in selected_page_nos for page_no in range(1, len(routes) + 1)
        ]
        output["detection"] = binary_detection_metrics(labels, predictions)
        if "page_type" in label_data:
            output["detection_by_page_type"] = page_type_metrics(
                label_data["page_type"], predictions
            )
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
