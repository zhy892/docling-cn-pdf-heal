"""Chinese PDF text-layer quality checks and selective OCR routing."""

from .crosscheck import OcrCrossCheckReport, assess_ocr_disagreement
from .quality import QualityReport, score_text_quality
from .threshold_calibration import ThresholdCalibration, calibrate_threshold

__version__ = "0.4.0"

__all__ = [
    "OcrCrossCheckReport",
    "QualityReport",
    "ThresholdCalibration",
    "assess_ocr_disagreement",
    "calibrate_threshold",
    "score_text_quality",
]
