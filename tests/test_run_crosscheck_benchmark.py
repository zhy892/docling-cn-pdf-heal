import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class RunCrosscheckBenchmarkTests(unittest.TestCase):
    def test_runner_reports_development_and_frozen_test_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "v3"
            result_path = root / "result.json"
            subprocess.run(
                [sys.executable, "benchmark/generate_crosscheck_v3.py", "--output-dir", str(data_dir)],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "benchmark/run_crosscheck_benchmark.py",
                    "--text-layer",
                    str(data_dir / "text_layer.json"),
                    "--ocr-transcript",
                    str(data_dir / "ocr_transcript.json"),
                    "--labels",
                    str(data_dir / "labels.json"),
                    "--output",
                    str(result_path),
                ],
                check=True,
            )
            result = json.loads(result_path.read_text())

        self.assertEqual(result["protocol"], "v3-transcript-crosscheck; V2 is unchanged")
        self.assertEqual(result["development"]["detection"]["f1"], 1.0)
        self.assertEqual(result["frozen_test"]["detection"]["f1"], 1.0)
        self.assertEqual(result["frozen_test"]["manual_review_pages"], [5, 7])


if __name__ == "__main__":
    unittest.main()
