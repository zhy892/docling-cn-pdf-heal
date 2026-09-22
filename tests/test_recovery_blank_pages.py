import unittest
from pathlib import Path
from unittest.mock import patch

from docling_cn_pdf_heal.page_ink import PageInkEstimate
from docling_cn_pdf_heal.recovery import recover_pdf


class RecoveryBlankPageTests(unittest.TestCase):
    @patch("docling_cn_pdf_heal.recovery.ocr_selected_pages")
    @patch("docling_cn_pdf_heal.recovery.estimate_pdf_page_ink")
    @patch("docling_cn_pdf_heal.recovery.extract_pdf_pages")
    def test_visually_blank_empty_page_is_not_sent_to_ocr(
        self, extract_pages, estimate_ink, ocr_selected
    ) -> None:
        extract_pages.return_value = ["", "正常页文本"]
        estimate_ink.return_value = PageInkEstimate(True, 0, 1000, 0.0)
        ocr_selected.return_value = {}

        result = recover_pdf(Path("sample.pdf"))

        self.assertEqual(result.ocr_pages, ())
        self.assertEqual(result.skipped_blank_pages, (1,))
        ocr_selected.assert_called_once_with(Path("sample.pdf"), [], unittest.mock.ANY)

    @patch("docling_cn_pdf_heal.recovery.ocr_selected_pages")
    @patch("docling_cn_pdf_heal.recovery.estimate_pdf_page_ink")
    @patch("docling_cn_pdf_heal.recovery.extract_pdf_pages")
    def test_ink_check_failure_fails_open_to_ocr(
        self, extract_pages, estimate_ink, ocr_selected
    ) -> None:
        extract_pages.return_value = [""]
        estimate_ink.side_effect = RuntimeError("renderer unavailable")
        ocr_selected.return_value = {1: "OCR 文本"}

        result = recover_pdf(Path("sample.pdf"))

        self.assertEqual(result.ocr_pages, (1,))
        self.assertEqual(result.skipped_blank_pages, ())
        self.assertEqual(result.recovered_pages, ["OCR 文本"])


if __name__ == "__main__":
    unittest.main()
