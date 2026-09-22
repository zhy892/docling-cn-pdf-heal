import unittest

from docling_cn_pdf_heal.cli import build_audit_report


class CliAuditTests(unittest.TestCase):
    def test_audit_report_has_transparent_summary_and_page_evidence(self) -> None:
        report = build_audit_report(
            [
                "中文 PDF 文本层质量评测，包含验证流程。",
                "犌犅／犜三七一三六－二零一八规定了文件要求和验证流程。",
            ],
            [
                "中文PDF文本层质量评测，包含验证流程。",
                "GB/T 37136-2018规定了文件要求和验证流程。",
            ],
        )
        self.assertEqual(report["pages"], 2)
        self.assertEqual(report["eligible_pages"], 2)
        self.assertEqual(report["disagreement_pages"], [2])
        self.assertEqual(report["manual_review_pages"], [2])
        self.assertEqual(report["page_checks"][1]["page_no"], 2)
        self.assertEqual(
            report["page_checks"][1]["recommended_action"], "manual_review"
        )

    def test_audit_report_keeps_agreeing_page(self) -> None:
        report = build_audit_report(
            ["中文 PDF 文本层质量评测，包含验证流程。"],
            ["中文PDF文本层质量评测，包含验证流程。"],
        )
        self.assertEqual(report["manual_review_pages"], [])
        self.assertEqual(
            report["page_checks"][0]["recommended_action"], "keep_text_layer"
        )


if __name__ == "__main__":
    unittest.main()
