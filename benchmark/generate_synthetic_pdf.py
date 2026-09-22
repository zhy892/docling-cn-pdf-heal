"""Create a redistributable Chinese PDF pair for reproducible fault injection.

The source text is written by the team. The corrupted copy installs an invalid
ToUnicode map that maps Han characters to the private-use area. This produces a
real PDF text-layer extraction fault without shipping third-party documents.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

TEAM_TEXT = [
    "中文 PDF 文本层质量评测样本",
    "本页由团队自主生成，用于验证缺失 ToUnicode 映射后的文本提取行为。",
    "编号：AIC-2026-001；指标：检测精确率、召回率、字符错误率与耗时。",
    "English mixed text: selective OCR fallback should keep clean pages unchanged.",
]

PAGE_TWO_TEXT = [
    "第二页：正常文本层对照页",
    "此页应保持原文本层，不应被错误路由至 OCR。",
]


def create_clean_pdf(path: Path, *, font_path: Path) -> None:
    pdfmetrics.registerFont(TTFont("AICNotoSansSC", str(font_path)))
    canvas = Canvas(str(path), pagesize=A4)
    canvas.setTitle("Synthetic Chinese PDF for text-layer quality testing")
    canvas.setFont("AICNotoSansSC", 16)
    canvas.drawString(72, 780, TEAM_TEXT[0])
    canvas.setFont("AICNotoSansSC", 11)
    y = 735
    for line in TEAM_TEXT[1:]:
        canvas.drawString(72, y, line)
        y -= 32
    canvas.showPage()
    canvas.setFont("AICNotoSansSC", 13)
    canvas.drawString(72, 780, PAGE_TWO_TEXT[0])
    canvas.setFont("AICNotoSansSC", 11)
    canvas.drawString(72, 740, PAGE_TWO_TEXT[1])
    canvas.save()


def inject_corrupt_tounicode(clean_path: Path, corrupt_path: Path) -> int:
    """Map the Chinese codepoints present in this sample to private-use glyphs."""
    reader = PdfReader(clean_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    sample_text = (
        "".join(TEAM_TEXT) + "第二页正常文本层对照页此页应保持原文本层不应被错误路由至"
    )
    han_characters = sorted({ch for ch in sample_text if "\u4e00" <= ch <= "\u9fff"})
    mappings = "\n".join(
        f"<{ord(ch):04X}> <{0xE000 + index:04X}>"
        for index, ch in enumerate(han_characters)
    )
    cmap = f"""/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /AICCorruptToUnicode def
/CMapType 2 def
1 begincodespacerange
<0000> <FFFF>
endcodespacerange
{len(han_characters)} beginbfchar
{mappings}
endbfchar
endcmap
CMapName currentdict /CMap defineresource pop
end
end
""".encode("ascii")
    stream = DecodedStreamObject()
    stream.set_data(cmap)
    cmap_ref = writer._add_object(stream)
    modified_fonts = 0
    for page in writer.pages:
        resources = page.get("/Resources")
        if resources is None:
            continue
        fonts = resources.get("/Font")
        if fonts is None:
            continue
        for font_ref in fonts.values():
            font = font_ref.get_object()
            if font.get("/Subtype") == "/TrueType":
                font[NameObject("/ToUnicode")] = cmap_ref
                modified_fonts += 1
    with corrupt_path.open("wb") as stream:
        writer.write(stream)
    return modified_fonts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--font",
        type=Path,
        required=True,
        help="local Noto Sans SC TrueType font, not copied into the repository",
    )
    args = parser.parse_args()
    if not args.font.is_file():
        raise FileNotFoundError(args.font)
    out_dir = Path(__file__).parent / "generated"
    out_dir.mkdir(exist_ok=True)
    clean_path = out_dir / "clean_chinese.pdf"
    corrupt_path = out_dir / "corrupt_tounicode_chinese.pdf"
    mixed_path = out_dir / "mixed_corrupt_clean_chinese.pdf"
    truth_path = out_dir / "truth_pages.json"
    create_clean_pdf(clean_path, font_path=args.font)
    modified_fonts = inject_corrupt_tounicode(clean_path, corrupt_path)
    clean_reader = PdfReader(clean_path)
    corrupt_reader = PdfReader(corrupt_path)
    mixed_writer = PdfWriter()
    mixed_writer.add_page(corrupt_reader.pages[0])
    mixed_writer.add_page(clean_reader.pages[1])
    with mixed_path.open("wb") as stream:
        mixed_writer.write(stream)
    truth_path.write_text(
        json.dumps(
            {"pages": ["\n".join(TEAM_TEXT), "\n".join(PAGE_TWO_TEXT)]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"clean={clean_path}")
    print(f"corrupt={corrupt_path}")
    print(f"mixed={mixed_path}")
    print(f"fonts_with_corrupt_tounicode={modified_fonts}")


if __name__ == "__main__":
    main()
