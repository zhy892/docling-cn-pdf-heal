import unittest

from docling_cn_pdf_heal.routing import plan_routes


class RoutingTests(unittest.TestCase):
    def test_only_damaged_page_is_routed_to_ocr(self) -> None:
        routes = plan_routes(["第一页正常", "第二页 /gid00020 /G27", "第三页正常"])
        self.assertEqual(
            [route.action for route in routes],
            ["keep_text_layer", "ocr_fallback", "keep_text_layer"],
        )
