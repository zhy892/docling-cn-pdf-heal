import unittest

from docling_cn_pdf_heal.page_ink import (
    PageInkEstimate,
    _count_dark_pixels,
    estimate_pgm_ink,
    retain_nonblank_candidates,
)


class PageInkTests(unittest.TestCase):
    def test_c_level_dark_pixel_counter_matches_reference_at_fractional_thresholds(self) -> None:
        pixels = bytes([0, 1, 2, 15, 127, 128, 200, 244, 245, 246, 254, 255])
        for threshold in (0.0, 1.5, 127.5, 244.9, 245.0, 255.0):
            with self.subTest(threshold=threshold):
                self.assertEqual(
                    _count_dark_pixels(pixels, threshold),
                    sum(pixel <= threshold for pixel in pixels),
                )
    def test_white_pgm_is_classified_as_blank(self) -> None:
        pgm = b"P5\n4 3\n255\n" + bytes([255] * 12)
        estimate = estimate_pgm_ink(pgm)
        self.assertTrue(estimate.is_blank)
        self.assertEqual(estimate.ink_pixels, 0)

    def test_dark_marks_are_classified_as_visible_ink(self) -> None:
        pgm = b"P5\n40 40\n255\n" + bytes([0] * 100 + [255] * 1500)
        estimate = estimate_pgm_ink(pgm)
        self.assertFalse(estimate.is_blank)
        self.assertEqual(estimate.ink_pixels, 100)

    def test_first_pixel_that_matches_whitespace_byte_is_not_dropped(self) -> None:
        pgm = b"P5\n40 40\n255\n" + bytes([10] * 100 + [255] * 1500)
        estimate = estimate_pgm_ink(pgm)
        self.assertEqual(estimate.ink_pixels, 100)

    def test_only_nonblank_candidates_are_retained(self) -> None:
        white = estimate_pgm_ink(b"P5\n4 3\n255\n" + bytes([255] * 12))
        marked = estimate_pgm_ink(b"P5\n40 40\n255\n" + bytes([0] * 100 + [255] * 1500))
        selected, skipped = retain_nonblank_candidates([1, 2], {1: white, 2: marked})
        self.assertEqual(selected, [2])
        self.assertEqual(skipped, [1])

    def test_missing_estimate_fails_open_to_avoid_silent_miss(self) -> None:
        selected, skipped = retain_nonblank_candidates([1], {})
        self.assertEqual(selected, [1])
        self.assertEqual(skipped, [])


if __name__ == "__main__":
    unittest.main()
