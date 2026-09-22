import unittest
from pathlib import Path
from unittest.mock import patch

from docling_cn_pdf_heal.docling_adapter import (
    extract_pages_with_native_docling,
    extract_pdf_pages,
    read_pdf_text_layer_pages,
)
from reportlab.pdfgen.canvas import Canvas


class _FakeDocument:
    def iterate_items(self):
        return [(_FakeItem("第一页"), 0), (_FakeItem("第二页"), 0)]


class _FakeItem:
    def __init__(self, text: str) -> None:
        self.text = text
        self.prov = [_FakeProvenance(1 if text == "第一页" else 2)]


class _FakeProvenance:
    def __init__(self, page_no: int) -> None:
        self.page_no = page_no


class _FakeResult:
    def __init__(self) -> None:
        self.pages = [_FakePage(1), _FakePage(2)]
        self.document = _FakeDocument()


class _FakePage:
    def __init__(self, page_no: int) -> None:
        self.page_no = page_no


class _FakeConverter:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def convert(self, path: Path) -> _FakeResult:
        self.paths.append(path)
        return _FakeResult()


class DoclingAdapterTests(unittest.TestCase):
    def test_pypdf_reader_returns_one_text_item_per_page(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "two-pages.pdf"
            canvas = Canvas(str(pdf_path))
            canvas.drawString(72, 720, "first")
            canvas.showPage()
            canvas.drawString(72, 720, "second")
            canvas.save()
            self.assertEqual(read_pdf_text_layer_pages(pdf_path), ["first\n", "second\n"])

    @patch("docling_cn_pdf_heal.docling_adapter.extract_pages_with_native_docling")
    def test_backend_dispatches_native_docling_without_cli_dependency(self, native_extract) -> None:
        native_extract.return_value = ["第一页"]

        result = extract_pdf_pages(Path("sample.pdf"), backend="native-docling")

        self.assertEqual(result, ["第一页"])
        native_extract.assert_called_once_with(Path("sample.pdf"))

    def test_caller_supplied_converter_is_reused_without_importing_docling(self) -> None:
        converter = _FakeConverter()

        first = extract_pages_with_native_docling(Path("first.pdf"), converter=converter)
        second = extract_pages_with_native_docling(Path("second.pdf"), converter=converter)

        self.assertEqual(first, ["第一页", "第二页"])
        self.assertEqual(second, ["第一页", "第二页"])
        self.assertEqual(converter.paths, [Path("first.pdf"), Path("second.pdf")])


if __name__ == "__main__":
    unittest.main()
