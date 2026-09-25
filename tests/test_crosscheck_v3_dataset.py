import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CrosscheckV3DatasetTests(unittest.TestCase):
    def test_generator_writes_aligned_clean_and_visually_plausible_corrupt_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "v3"
            subprocess.run(
                [
                    sys.executable,
                    "benchmark/generate_crosscheck_v3.py",
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
            )
            layer = json.loads((output_dir / "text_layer.json").read_text(encoding="utf-8"))
            ocr = json.loads((output_dir / "ocr_transcript.json").read_text(encoding="utf-8"))
            labels = json.loads((output_dir / "labels.json").read_text(encoding="utf-8"))

        self.assertEqual(len(layer["pages"]), 8)
        self.assertEqual(layer["pages"], labels["pages"])
        self.assertEqual(len(ocr["pages"]), 8)
        self.assertEqual(labels["is_damaged"].count(True), 4)
        self.assertIn("犌犅／犜", layer["pages"][1])
        self.assertIn("GB/T", ocr["pages"][1])


if __name__ == "__main__":
    unittest.main()
