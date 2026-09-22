"""Generate a separate transcript benchmark for visually plausible corruption.

V2 remains frozen for first-stage routing.  V3 evaluates the optional second
measurement: OCR/text-layer disagreement, whose output is manual review rather
than automatic text replacement.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


OCR_PAGES = [
    "中文 PDF 文本层质量评测，包含验证流程与审计记录。",
    "GB/T 37136-2018规定了文件要求和验证流程。",
    "课程资料应保留页码、版本和来源信息。",
    "编号 AIC-2026-042 的归档记录已经完成。",
    "GB/T 7714-2015给出了参考文献著录规则。",
    "技术报告包含测试方法、结果和局限性。",
    "API v2.0 的兼容性说明应由维护者复核。",
    "知识库导入前需要完成文本层质量检查。",
]

TEXT_LAYER_PAGES = [
    OCR_PAGES[0],
    "犌犅／犜三七一三六－二零一八规定了文件要求和验证流程。",
    OCR_PAGES[2],
    "编号犃犐犆－二零二六－零四二的归档记录已经完成。",
    "犌犅／犜七七一四－二零一五给出了参考文献著录规则。",
    OCR_PAGES[5],
    "ＡＰＩ　ｖ二．零的兼容性说明应由维护者复核。",
    OCR_PAGES[7],
]

IS_DAMAGED = [False, True, False, True, True, False, True, False]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "text_layer.json", {"pages": TEXT_LAYER_PAGES})
    write_json(args.output_dir / "ocr_transcript.json", {"pages": OCR_PAGES})
    write_json(
        args.output_dir / "labels.json",
        {
            "pages": TEXT_LAYER_PAGES,
            "is_damaged": IS_DAMAGED,
            "split": ["development"] * 4 + ["test"] * 4,
            "protocol": "v3-transcript-crosscheck; V2 is unchanged",
        },
    )


if __name__ == "__main__":
    main()
