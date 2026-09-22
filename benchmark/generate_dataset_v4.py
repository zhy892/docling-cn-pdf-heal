"""Generate deterministic multi-fault text-layer fixtures for CI.

V4 is independent from PDF-based V2. It stress-tests the pure quality and
routing layer across explicit fault families; PDF rendering remains covered by
the native Docling V2 benchmark and must not be confused with this component
fixture.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PAGE_TYPES = (
    "clean",
    "corrupt_tounicode",
    "scanned_image",
    "blank",
    "glyph_identifier",
    "mixed_identifier_shift",
    "double_column_control",
    "table_like_control",
)


def fault_family(page_type: str) -> str:
    return {
        "clean": "clean_control",
        "corrupt_tounicode": "tounicode",
        "scanned_image": "image_only",
        "blank": "blank_control",
        "glyph_identifier": "glyph_marker",
        "mixed_identifier_shift": "plausible_identifier",
        "double_column_control": "layout_control",
        "table_like_control": "layout_control",
    }[page_type]


def split_for_page(page_no: int) -> str:
    if page_no <= 12:
        return "development"
    if page_no <= 24:
        return "test"
    return "holdout"


def page_text(page_type: str, page_no: int) -> str:
    controls = {
        "clean": f"第{page_no}页中文资料归档与质量验证，编号 AIC-2026-{page_no:03d}。",
        "corrupt_tounicode": "\ue001\ue002\ue003\ue004\ue005",
        "scanned_image": "",
        "blank": "",
        "glyph_identifier": "/gid00020 /G27 (cid:123)",
        "mixed_identifier_shift": "ＡＰＩ　ｖ二．零与犌犅／犜标准编号需要人工复核。",
        "double_column_control": "左栏：中文文本层正常。\n右栏：English column remains readable.",
        "table_like_control": "项目 | 版本 | 状态\n质量检查 | v2.0 | 正常\nOCR回退 | v1.0 | 待审计",
    }
    return controls[page_type]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    pages = []
    for page_no in range(1, 33):
        page_type = PAGE_TYPES[(page_no - 1) % len(PAGE_TYPES)]
        text = page_text(page_type, page_no)
        pages.append(text)
        records.append(
            {
                "page_no": page_no,
                "split": split_for_page(page_no),
                "page_type": page_type,
                "fault_family": fault_family(page_type),
                "is_damaged": page_type
                in {"corrupt_tounicode", "scanned_image", "glyph_identifier", "mixed_identifier_shift"},
                "expects_first_stage_candidate": page_type
                in {"corrupt_tounicode", "scanned_image", "blank", "glyph_identifier"},
                "requires_crosscheck_review": page_type == "mixed_identifier_shift",
            }
        )
    (args.output_dir / "all-pages.json").write_text(
        json.dumps({"backend": "fixture", "pages": pages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "manifest.json").write_text(
        json.dumps({"version": "v4-component-fixture", "records": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
