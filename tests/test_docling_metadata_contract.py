import unittest

from docling_cn_pdf_heal.docling_metadata_contract import (
    TextLayerQualityCheckOptions,
    build_page_quality_metadata,
)


class DoclingMetadataContractTests(unittest.TestCase):
    def test_disabled_option_emits_no_page_decisions(self) -> None:
        result = build_page_quality_metadata(
            ["正常文本", "/gid00020"], TextLayerQualityCheckOptions(enabled=False)
        )

        self.assertEqual(result, {"enabled": False, "pages": []})

    def test_enabled_option_keeps_clean_page_and_recommends_ocr_for_marker(self) -> None:
        result = build_page_quality_metadata(
            ["正常中文文本", "/gid00020"], TextLayerQualityCheckOptions(enabled=True)
        )

        self.assertTrue(result["enabled"])
        self.assertEqual(result["pages"][0]["action"], "keep_text_layer")
        self.assertEqual(result["pages"][1]["action"], "recommend_ocr")
        self.assertEqual(result["pages"][1]["quality"]["reasons"], ("glyph_identifier",))

    def test_threshold_is_part_of_metadata_contract(self) -> None:
        result = build_page_quality_metadata(
            ["正常文本内容正常文本内容正常文本内容\ufffd"],
            TextLayerQualityCheckOptions(enabled=True, score_threshold=0.9),
        )

        self.assertEqual(result["score_threshold"], 0.9)
        self.assertEqual(result["pages"][0]["action"], "keep_text_layer")


if __name__ == "__main__":
    unittest.main()
