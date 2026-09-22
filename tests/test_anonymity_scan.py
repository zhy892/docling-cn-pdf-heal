import unittest

from docling_cn_pdf_heal.anonymity_scan import scan_text_for_terms


class AnonymityScanTests(unittest.TestCase):
    def test_scan_reports_line_and_column_for_forbidden_term(self) -> None:
        findings = scan_text_for_terms(
            "第一行\n学校名称出现在第二行", ["学校名称", "指导教师"]
        )

        self.assertEqual(
            [finding.to_dict() for finding in findings],
            [{"term": "学校名称", "line": 2, "column": 1}],
        )

    def test_scan_is_case_insensitive_and_reports_each_line_once_per_term(self) -> None:
        findings = scan_text_for_terms("GitHub github\nGITHUB", ["github"])

        self.assertEqual(
            [(finding.line, finding.column) for finding in findings],
            [(1, 1), (1, 8), (2, 1)],
        )

    def test_scan_rejects_empty_forbidden_term(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            scan_text_for_terms("内容", [""])


if __name__ == "__main__":
    unittest.main()
