import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas


class ExtractTextLayerPagesTests(unittest.TestCase):
    def test_pypdf_backend_writes_one_text_item_per_pdf_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            output = root / "pages.json"
            pdf = Canvas(str(source))
            pdf.drawString(72, 720, "first page")
            pdf.showPage()
            pdf.drawString(72, 720, "second page")
            pdf.save()

            subprocess.run(
                [
                    sys.executable,
                    "benchmark/extract_text_layer_pages.py",
                    str(source),
                    "--backend",
                    "pypdf",
                    "--output",
                    str(output),
                ],
                check=True,
            )

            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["backend"], "pypdf")
        self.assertEqual(result["pages"], ["first page\n", "second page\n"])


if __name__ == "__main__":
    unittest.main()
