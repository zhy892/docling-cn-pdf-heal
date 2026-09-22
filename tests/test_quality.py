import unittest

from docling_cn_pdf_heal.metrics import binary_detection_metrics, character_error_rate
from docling_cn_pdf_heal.quality import score_text_quality


class QualityTests(unittest.TestCase):
    def test_clean_chinese_text_is_kept(self) -> None:
        report = score_text_quality("这是正常的中文 PDF 文本层，包含 GB/T 37136-2018。")
        self.assertFalse(report.needs_ocr)
        self.assertEqual(report.score, 0)
        self.assertEqual(report.reasons, ())

    def test_gid_tokens_trigger_fallback(self) -> None:
        report = score_text_quality("/gid00020 /gid00016 /G27")
        self.assertTrue(report.needs_ocr)
        self.assertEqual(report.glyph_token_count, 3)
        self.assertIn("glyph_identifier", report.reasons)

    def test_cid_and_replacement_trigger_fallback(self) -> None:
        report = score_text_quality("(cid:123) \ufffd")
        self.assertTrue(report.needs_ocr)
        self.assertEqual(report.cid_token_count, 1)
        self.assertEqual(report.replacement_count, 1)

    def test_private_use_character_is_explained(self) -> None:
        report = score_text_quality("正常文字\ue001\ue002\ue003")
        self.assertEqual(report.private_use_count, 3)
        self.assertIn("private_use_character", report.reasons)

    def test_whitespace_only_extraction_triggers_fallback(self) -> None:
        report = score_text_quality(" \n\t  \n")
        self.assertTrue(report.needs_ocr)
        self.assertEqual(report.non_whitespace_count, 0)
        self.assertIn("empty_extracted_text", report.reasons)

    def test_empty_extraction_triggers_fallback(self) -> None:
        report = score_text_quality("")
        self.assertTrue(report.needs_ocr)
        self.assertIn("empty_extracted_text", report.reasons)

    def test_cer_ignores_layout_whitespace(self) -> None:
        self.assertEqual(character_error_rate("中文 PDF", "中 文\nPDF"), 0.0)
        self.assertGreater(character_error_rate("中文", "中午"), 0.0)

    def test_detection_metrics_expose_counts(self) -> None:
        metrics = binary_detection_metrics([True, True, False], [True, False, True])
        self.assertEqual(metrics["true_positive"], 1)
        self.assertEqual(metrics["false_positive"], 1)
        self.assertEqual(metrics["false_negative"], 1)
        self.assertEqual(metrics["f1"], 0.5)
