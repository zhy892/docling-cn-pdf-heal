"""Command line interface for scoring extracted page text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit_record import build_local_audit_record
from .crosscheck import compare_page_transcripts
from .docling_adapter import extract_pdf_pages
from .routing import plan_routes


def _read_json_pages(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("pages"), list):
        raise TypeError("input JSON must be an object with a pages array")
    pages = payload["pages"]
    if not all(isinstance(page, str) for page in pages):
        raise ValueError("every pages item must be a string")
    return pages


def _read_pages(path: Path, *, backend: str) -> list[str]:
    if path.suffix.lower() == ".pdf":
        return extract_pdf_pages(path, backend=backend)
    return _read_json_pages(path)


def build_audit_report(
    text_layer_pages: list[str],
    ocr_transcript_pages: list[str],
    *,
    min_characters: int = 12,
    agreement_threshold: float = 0.65,
) -> dict[str, object]:
    """Create a compact, reviewable summary of OCR/text-layer disagreement."""
    page_checks = compare_page_transcripts(
        text_layer_pages,
        ocr_transcript_pages,
        min_characters=min_characters,
        agreement_threshold=agreement_threshold,
    )
    for check in page_checks:
        crosscheck = check["crosscheck"]
        if not isinstance(crosscheck, dict):  # pragma: no cover - internal contract
            raise TypeError("crosscheck result must be a dictionary")
        if not crosscheck["eligible"]:
            check["recommended_action"] = "insufficient_evidence"
        elif crosscheck["needs_ocr"]:
            # OCR is a second measurement, not ground truth. A conflict must
            # remain visible to a human rather than being silently overwritten.
            check["recommended_action"] = "manual_review"
        else:
            check["recommended_action"] = "keep_text_layer"
    eligible_pages = [
        check
        for check in page_checks
        if check["crosscheck"]["eligible"]  # type: ignore[index]
    ]
    disagreement_pages = [
        check["page_no"]
        for check in eligible_pages
        if check["crosscheck"]["needs_ocr"]  # type: ignore[index]
    ]
    manual_review_pages = [
        check["page_no"]
        for check in page_checks
        if check["recommended_action"] == "manual_review"
    ]
    return {
        "pages": len(page_checks),
        "eligible_pages": len(eligible_pages),
        "disagreement_pages": disagreement_pages,
        "manual_review_pages": manual_review_pages,
        "page_checks": page_checks,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan selective OCR from extracted page text"
    )
    parser.add_argument(
        "input",
        type=Path,
        help='PDF or JSON file ({"pages": ["..."]})',
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="OCR only pages selected by the quality router (PDF input only)",
    )
    parser.add_argument("--ocr-lang", default="chi_sim")
    parser.add_argument("--tessdata-dir", type=Path)
    parser.add_argument(
        "--ocr-transcript",
        type=Path,
        help='JSON OCR transcript ({"pages": ["..."]}); enables audit only, no OCR is run',
    )
    parser.add_argument("--crosscheck-min-characters", type=int, default=12)
    parser.add_argument("--crosscheck-agreement-threshold", type=float, default=0.65)
    parser.add_argument("--threshold", type=float, default=0.20)
    parser.add_argument(
        "--audit-id",
        help="privacy-preserving local PDF audit identifier; adds hash and route metadata",
    )
    parser.add_argument(
        "--backend",
        choices=("pypdf", "native-docling"),
        default="pypdf",
        help="PDF text-layer reader; native-docling requires Docling but no model download",
    )
    parser.add_argument("--output", type=Path, help="write JSON report to this path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.recover and args.ocr_transcript:
        raise ValueError("--recover and --ocr-transcript cannot be used together")
    if args.audit_id and args.input.suffix.lower() != ".pdf":
        raise ValueError("--audit-id requires PDF input")
    if args.recover:
        if args.input.suffix.lower() != ".pdf":
            raise ValueError("--recover requires PDF input")
        from .ocr import TesseractOptions
        from .recovery import recover_pdf

        recovered = recover_pdf(
            args.input,
            backend=args.backend,
            threshold=args.threshold,
            ocr_options=TesseractOptions(
                language=args.ocr_lang, tessdata_dir=args.tessdata_dir
            ),
        )
        report = {
            "threshold": args.threshold,
            "ocr_pages": list(recovered.ocr_pages),
            "skipped_blank_pages": list(recovered.skipped_blank_pages),
            "ink_estimates": {
                str(page_no): estimate.to_dict()
                for page_no, estimate in recovered.ink_estimates.items()
            },
            "pages": [route.to_dict() for route in recovered.routes],
            "recovered_page_text": recovered.recovered_pages,
        }
        if args.audit_id:
            report["local_audit"] = build_local_audit_record(
                args.input,
                audit_id=args.audit_id,
                backend=args.backend,
                page_count=len(recovered.routes),
                ocr_candidate_pages=[
                    route.page_no
                    for route in recovered.routes
                    if route.action == "ocr_fallback"
                ],
                skipped_blank_pages=list(recovered.skipped_blank_pages),
            )
    else:
        source_pages = _read_pages(args.input, backend=args.backend)
        routes = plan_routes(source_pages, threshold=args.threshold)
        report = {
            "threshold": args.threshold,
            "pages": [route.to_dict() for route in routes],
        }
        if args.ocr_transcript:
            report["ocr_crosscheck"] = build_audit_report(
                source_pages,
                _read_json_pages(args.ocr_transcript),
                min_characters=args.crosscheck_min_characters,
                agreement_threshold=args.crosscheck_agreement_threshold,
            )
        if args.audit_id:
            report["local_audit"] = build_local_audit_record(
                args.input,
                audit_id=args.audit_id,
                backend=args.backend,
                page_count=len(routes),
                ocr_candidate_pages=[
                    route.page_no for route in routes if route.action == "ocr_fallback"
                ],
                skipped_blank_pages=[],
            )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
