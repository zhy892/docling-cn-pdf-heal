import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from docling_cn_pdf_heal.threshold_calibration import (
    calibrate_development_pages,
    calibrate_threshold,
    load_frozen_threshold,
)


class ThresholdCalibrationTests(unittest.TestCase):
    def test_calibration_selects_threshold_from_development_labels(self) -> None:
        result = calibrate_threshold(
            scores=[0.01, 0.15, 0.35, 0.80],
            is_damaged=[False, False, True, True],
        )
        self.assertEqual(result.threshold, 0.35)
        self.assertEqual(result.metrics["f1"], 1.0)
        self.assertEqual(result.candidate_count, 5)

    def test_calibration_breaks_f1_tie_by_lower_false_positive_rate(self) -> None:
        result = calibrate_threshold(
            scores=[0.20, 0.30, 0.90], is_damaged=[False, True, True]
        )
        self.assertEqual(result.threshold, 0.30)
        self.assertEqual(result.metrics["false_positive"], 0)

    def test_calibration_rejects_missing_or_misaligned_labels(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            calibrate_threshold(scores=[0.1], is_damaged=[])
        with self.assertRaisesRegex(ValueError, "at least one"):
            calibrate_threshold(scores=[], is_damaged=[])

    def test_development_calibration_excludes_frozen_test_labels(self) -> None:
        result = calibrate_development_pages(
            page_texts=["正常页", "/gid001", "\ufffd", "正常测试页"],
            records=[
                {"page_no": 1, "split": "development", "is_damaged": False},
                {"page_no": 2, "split": "development", "is_damaged": True},
                {"page_no": 3, "split": "development", "is_damaged": True},
                {"page_no": 4, "split": "test", "is_damaged": True},
            ],
        )
        self.assertEqual(result["development_page_nos"], [1, 2, 3])
        self.assertEqual(result["development_pages"], 3)
        self.assertEqual(result["calibration"]["metrics"]["true_positive"], 2)

    def test_development_calibration_rejects_nonsequential_page_numbers(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_no"):
            calibrate_development_pages(
                page_texts=["正常页"],
                records=[{"page_no": 2, "split": "development", "is_damaged": False}],
            )

    def test_calibration_script_writes_development_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "pages.json"
            manifest = root / "manifest.json"
            output = root / "calibration.json"
            pages.write_text(json.dumps({"pages": ["正常页", "/gid001"]}), encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {"records": [
                        {"page_no": 1, "split": "development", "is_damaged": False},
                        {"page_no": 2, "split": "development", "is_damaged": True},
                    ]}
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "benchmark/calibrate_quality_threshold.py",
                    str(pages),
                    str(manifest),
                    "--output",
                    str(output),
                ],
                check=True,
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["protocol"], "development-only-threshold-calibration-v1")
        self.assertEqual(result["development_page_nos"], [1, 2])

    def test_load_frozen_threshold_requires_calibration_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "calibration.json"
            evidence.write_text(
                json.dumps(
                    {
                        "protocol": "development-only-threshold-calibration-v1",
                        "calibration": {"threshold": 0.42},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_frozen_threshold(evidence), 0.42)
            evidence.write_text(
                json.dumps({"calibration": {"threshold": 0.42}}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "protocol"):
                load_frozen_threshold(evidence)


if __name__ == "__main__":
    unittest.main()
