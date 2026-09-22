import unittest

from docling_cn_pdf_heal.crosscheck import (
    assess_ocr_disagreement,
    compare_page_transcripts,
    evaluate_crosscheck_detection,
)


class OcrCrossCheckTests(unittest.TestCase):
    def test_identifier_loss_is_reviewed_even_when_global_agreement_is_high(self) -> None:
        report = assess_ocr_disagreement(
            "ＡＰＩ　ｖ二．零的兼容性说明应由维护者复核。",
            "API v2.0 的兼容性说明应由维护者复核。",
        )

        self.assertTrue(report.eligible)
        self.assertTrue(report.needs_ocr)
        self.assertGreater(report.agreement, 0.65)
        self.assertEqual(report.reason, "ocr_identifier_disagreement")

    def test_crosscheck_evaluation_uses_independent_labels_and_preserves_review_state(self) -> None:
        result = evaluate_crosscheck_detection(
            [
                "中文 PDF 文本层质量评测，包含验证流程。",
                "犌犅／犜三七一三六－二零一八规定了文件要求和验证流程。",
            ],
            [
                "中文PDF文本层质量评测，包含验证流程。",
                "GB/T 37136-2018规定了文件要求和验证流程。",
            ],
            [False, True],
        )

        self.assertEqual(result["detection"], {
            "true_positive": 1,
            "false_positive": 0,
            "false_negative": 0,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
        })
        self.assertEqual(result["manual_review_pages"], [2])

    def test_crosscheck_evaluation_rejects_misaligned_labels(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_crosscheck_detection(["足够长的中文文本"], ["足够长的中文文本"], [])

    def test_mismatched_cjk_text_is_flagged(self) -> None:
        report = assess_ocr_disagreement(
            "犌犅／犜三七一三六－二零一八规定了文件要求和验证流程。",
            "GB/T 37136-2018规定了文件要求和验证流程。",
        )
        self.assertTrue(report.eligible)
        self.assertTrue(report.needs_ocr)
        self.assertLess(report.agreement, 0.65)
        self.assertEqual(report.reason, "ocr_text_disagreement")

    def test_layout_only_difference_is_not_flagged(self) -> None:
        report = assess_ocr_disagreement(
            "中文 PDF 文本层质量评测，包含验证流程。",
            "中文PDF\n文本层质量评测，包含验证流程。",
        )
        self.assertTrue(report.eligible)
        self.assertFalse(report.needs_ocr)
        self.assertEqual(report.agreement, 1.0)

    def test_short_text_is_explicitly_ineligible(self) -> None:
        report = assess_ocr_disagreement("犌犅", "GB")
        self.assertFalse(report.eligible)
        self.assertFalse(report.needs_ocr)
        self.assertEqual(report.reason, "insufficient_text")

    def test_page_comparison_preserves_page_numbers(self) -> None:
        reports = compare_page_transcripts(
            [
                "中文 PDF 文本层质量评测，包含验证流程。",
                "犌犅／犜三七一三六－二零一八规定了文件要求和验证流程。",
            ],
            [
                "中文PDF文本层质量评测，包含验证流程。",
                "GB/T 37136-2018规定了文件要求和验证流程。",
            ],
        )
        self.assertEqual([entry["page_no"] for entry in reports], [1, 2])
        self.assertFalse(reports[0]["crosscheck"]["needs_ocr"])
        self.assertTrue(reports[1]["crosscheck"]["needs_ocr"])

    def test_page_comparison_rejects_misaligned_inputs(self) -> None:
        with self.assertRaises(ValueError):
            compare_page_transcripts(["第一页足够长的文字用于测试。"], [])


if __name__ == "__main__":
    unittest.main()
