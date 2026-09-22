"""Generate a deterministic 20-page Chinese PDF benchmark with three page types.

This script creates all artifacts locally. Generated PDFs are ignored by Git;
only the generator and manifest schema are published.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

try:  # Supports both `python benchmark/...py` and module-based tests.
    from .generate_synthetic_pdf import inject_corrupt_tounicode
except ImportError:  # pragma: no cover - direct script execution path
    from generate_synthetic_pdf import inject_corrupt_tounicode
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


def lines_for_page(page_no: int) -> list[str]:
    return [
        f"中文 PDF 文本层质量评测，第 {page_no:02d} 页",
        "本页由团队自主生成，覆盖正常文本、损坏映射与纯图像扫描三类输入。",
        f"样本编号：AIC-SYN-{page_no:03d}；验证页面级 OCR 回退是否保持正常页。",
        "English mixed text: reproducible selective OCR benchmark.",
    ]


def make_text_page(path: Path, lines: list[str], font_path: Path) -> None:
    if "AICNotoSansSC" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("AICNotoSansSC", str(font_path)))
    canvas = Canvas(str(path), pagesize=A4)
    canvas.setFont("AICNotoSansSC", 15)
    canvas.drawString(72, 780, lines[0])
    canvas.setFont("AICNotoSansSC", 11)
    y = 735
    for line in lines[1:]:
        canvas.drawString(72, y, line)
        y -= 34
    canvas.save()


def make_scanned_page(text_pdf: Path, scanned_pdf: Path, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    prefix = work_dir / "rendered"
    rendered = subprocess.run(
        ["pdftoppm", "-png", "-r", "250", str(text_pdf), str(prefix)],
        check=False,
        capture_output=True,
        text=True,
    )
    if rendered.returncode:
        raise RuntimeError(rendered.stderr)
    image = next(work_dir.glob("rendered-*.png"))
    canvas = Canvas(str(scanned_pdf), pagesize=A4)
    canvas.drawImage(ImageReader(str(image)), 0, 0, width=A4[0], height=A4[1])
    canvas.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("benchmark/generated-v1")
    )
    args = parser.parse_args()
    if not args.font.is_file():
        raise FileNotFoundError(args.font)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_writer = PdfWriter()
    test_writer = PdfWriter()
    records: list[dict[str, object]] = []
    test_truth: list[str] = []
    # Each four-page block contains 2 clean, 1 corrupt ToUnicode, 1 scanned page.
    page_types = ("clean", "corrupt_tounicode", "scanned_image", "clean")
    with tempfile.TemporaryDirectory(prefix="aic-synth-") as raw_temp:
        temp_dir = Path(raw_temp)
        for page_no in range(1, 21):
            kind = page_types[(page_no - 1) % len(page_types)]
            source = temp_dir / f"source-{page_no}.pdf"
            make_text_page(source, lines_for_page(page_no), args.font)
            selected = source
            if kind == "corrupt_tounicode":
                selected = temp_dir / f"corrupt-{page_no}.pdf"
                inject_corrupt_tounicode(source, selected)
            elif kind == "scanned_image":
                selected = temp_dir / f"scan-{page_no}.pdf"
                make_scanned_page(source, selected, temp_dir / f"render-{page_no}")
            reader = PdfReader(selected)
            all_writer.add_page(reader.pages[0])
            split = (
                "development"
                if page_no <= 8
                else "test"
                if page_no <= 16
                else "holdout"
            )
            record = {
                "page_no": page_no,
                "split": split,
                "page_type": kind,
                "is_damaged": kind != "clean",
                "truth": "\n".join(lines_for_page(page_no)),
            }
            records.append(record)
            if split == "test":
                test_writer.add_page(reader.pages[0])
                test_truth.append(record["truth"])

    full_pdf = args.output_dir / "synthetic_v1_all.pdf"
    test_pdf = args.output_dir / "synthetic_v1_test.pdf"
    with full_pdf.open("wb") as stream:
        all_writer.write(stream)
    with test_pdf.open("wb") as stream:
        test_writer.write(stream)
    (args.output_dir / "manifest.json").write_text(
        json.dumps({"version": "v1", "records": records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "test_truth.json").write_text(
        json.dumps({"pages": test_truth}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "test_labels.json").write_text(
        json.dumps(
            {
                "is_damaged": [
                    record["is_damaged"]
                    for record in records
                    if record["split"] == "test"
                ],
                "page_type": [
                    record["page_type"]
                    for record in records
                    if record["split"] == "test"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"all_pdf={full_pdf}")
    print(f"test_pdf={test_pdf}")
    print(f"manifest={args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
