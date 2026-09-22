import unittest

from benchmark.generate_dataset_v4 import PAGE_TYPES, fault_family, split_for_page


class DatasetV4Tests(unittest.TestCase):
    def test_v4_covers_eight_explicit_fault_or_control_families(self) -> None:
        self.assertEqual(
            set(PAGE_TYPES),
            {
                "clean",
                "corrupt_tounicode",
                "scanned_image",
                "blank",
                "glyph_identifier",
                "mixed_identifier_shift",
                "double_column_control",
                "table_like_control",
            },
        )
        self.assertEqual(fault_family("glyph_identifier"), "glyph_marker")
        self.assertEqual(fault_family("mixed_identifier_shift"), "plausible_identifier")
        self.assertEqual(fault_family("double_column_control"), "layout_control")

    def test_v4_split_is_fixed_and_nonoverlapping(self) -> None:
        self.assertEqual(split_for_page(1), "development")
        self.assertEqual(split_for_page(12), "development")
        self.assertEqual(split_for_page(13), "test")
        self.assertEqual(split_for_page(24), "test")
        self.assertEqual(split_for_page(25), "holdout")


if __name__ == "__main__":
    unittest.main()
