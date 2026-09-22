"""Assert expected first-stage routing for deterministic V4 component fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docling_cn_pdf_heal.routing import plan_routes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pages = json.loads(args.pages.read_text(encoding="utf-8"))["pages"]
    records = json.loads(args.manifest.read_text(encoding="utf-8"))["records"]
    if len(pages) != len(records):
        raise ValueError("pages and manifest record counts must match")
    routes = plan_routes(pages)
    mismatches = [
        {
            "page_no": record["page_no"],
            "page_type": record["page_type"],
            "expected_candidate": record["expects_first_stage_candidate"],
            "actual_candidate": route.action == "ocr_fallback",
        }
        for route, record in zip(routes, records)
        if (route.action == "ocr_fallback") != record["expects_first_stage_candidate"]
    ]
    args.output.write_text(
        json.dumps(
            {
                "version": "v4-first-stage-fixture-check",
                "pages": len(routes),
                "mismatches": mismatches,
                "crosscheck_only_pages": [
                    record["page_no"] for record in records if record["requires_crosscheck_review"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if mismatches:
        raise SystemExit("V4 first-stage fixture mismatch")


if __name__ == "__main__":
    main()
