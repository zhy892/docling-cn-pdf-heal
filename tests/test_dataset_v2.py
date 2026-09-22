import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from benchmark.generate_dataset_v2 import make_blank_page, split_for_page


class DatasetV2Tests(unittest.TestCase):
    def test_blank_page_generator_creates_one_real_pdf_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "blank.pdf"
            make_blank_page(output)
            self.assertEqual(len(PdfReader(output).pages), 1)

    def test_split_is_frozen_and_nonoverlapping(self) -> None:
        self.assertEqual(split_for_page(1), "development")
        self.assertEqual(split_for_page(8), "development")
        self.assertEqual(split_for_page(9), "test")
        self.assertEqual(split_for_page(18), "test")
        self.assertEqual(split_for_page(19), "holdout")


if __name__ == "__main__":
    unittest.main()
