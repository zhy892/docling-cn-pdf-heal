"""Generate a v2 synthetic benchmark with an explicit true-blank page class.

v1 remains frozen.  This generator creates a separate benchmark for validating
the visible-ink guard added after v1 was evaluated.
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

PAGE_TYPES = (
    "clean",
    "corrupt_tounicode",
    "scanned_image",
    "blank",
    "clean",
    "clean",
)


def lines_for_page(page_no: int) -> list[str]:
    return [
        f"中文 PDF 文本层质量评测 v2，第 {page_no:02d} 页",
        "本页由团队自主生成，验证质量路由与空白页误报控制。",
        f"样本编号：AIC-SYN-V2-{page_no:03d}；保留正常页文本层。",
        "English mixed text: reproducible selective OCR benchmark.",
    ]


def make_text_page(path: Path, lines: list[str], font_path: Path) -> None:
    if "AICNotoSansSCV2" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("AICNotoSansSCV2", str(font_path)))
    canvas = Canvas(str(path), pagesize=A4)
    canvas.setFont("AICNotoSansSCV2", 15)
    canvas.drawString(72, 780, lines[0])
    canvas.setFont("AICNotoSansSCV2", 11)
    for index, line in enumerate(lines[1:], start=1):
        canvas.drawString(72, 780 - index * 38, line)
    canvas.save()


def make_blank_page(path: Path) -> None:
    canvas = Canvas(str(path), pagesize=A4)
    canvas.showPage()
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


def split_for_page(page_no: int) -> str:
    return "development" if page_no <= 8 else "test" if page_no <= 18 else "holdout"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("benchmark/generated-v2")
    )
    args = parser.parse_args()
    if not args.font.is_file():
        raise FileNotFoundError(args.font)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_writer = PdfWriter()
    test_writer = PdfWriter()
    records: list[dict[str, object]] = []
    test_truth: list[str] = []
    with tempfile.TemporaryDirectory(prefix="aic-synth-v2-") as raw_temp:
        temp_dir = Path(raw_temp)
        for page_no in range(1, 25):
            kind = PAGE_TYPES[(page_no - 1) % len(PAGE_TYPES)]
            source = temp_dir / f"source-{page_no}.pdf"
            lines = lines_for_page(page_no)
            if kind == "blank":
                make_blank_page(source)
                selected = source
                truth = ""
            else:
                make_text_page(source, lines, args.font)
                selected = source
                truth = "\n".join(lines)
                if kind == "corrupt_tounicode":
                    selected = temp_dir / f"corrupt-{page_no}.pdf"
                    inject_corrupt_tounicode(source, selected)
                elif kind == "scanned_image":
                    selected = temp_dir / f"scan-{page_no}.pdf"
                    make_scanned_page(source, selected, temp_dir / f"render-{page_no}")
            reader = PdfReader(selected)
            all_writer.add_page(reader.pages[0])
            split = split_for_page(page_no)
            record = {
                "page_no": page_no,
                "split": split,
                "page_type": kind,
                "is_damaged": kind in {"corrupt_tounicode", "scanned_image"},
                "truth": truth,
            }
            records.append(record)
            if split == "test":
                test_writer.add_page(reader.pages[0])
                test_truth.append(truth)

    with (args.output_dir / "synthetic_v2_all.pdf").open("wb") as stream:
        all_writer.write(stream)
    with (args.output_dir / "synthetic_v2_test.pdf").open("wb") as stream:
        test_writer.write(stream)
    (args.output_dir / "manifest.json").write_text(
        json.dumps({"version": "v2", "records": records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    test_records = [record for record in records if record["split"] == "test"]
    (args.output_dir / "test_truth.json").write_text(
        json.dumps({"pages": test_truth}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "test_labels.json").write_text(
        json.dumps(
            {
                "is_damaged": [record["is_damaged"] for record in test_records],
                "page_type": [record["page_type"] for record in test_records],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"all_pdf={args.output_dir / 'synthetic_v2_all.pdf'}")
    print(f"test_pdf={args.output_dir / 'synthetic_v2_test.pdf'}")
    print(f"manifest={args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
