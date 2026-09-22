"""Development-split calibration for text-layer quality routing thresholds."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import binary_detection_metrics
from .quality import score_text_quality


@dataclass(frozen=True)
class ThresholdCalibration:
    """A reproducible threshold choice made without inspecting frozen test labels."""

    threshold: float
    candidate_count: int
    metrics: dict[str, float | int]
    false_positive_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "threshold": self.threshold,
            "candidate_count": self.candidate_count,
            "metrics": self.metrics,
            "false_positive_rate": self.false_positive_rate,
        }


def calibrate_threshold(
    *, scores: Sequence[float], is_damaged: Sequence[bool]
) -> ThresholdCalibration:
    """Choose a threshold on a development split with deterministic tie-breaking.

    Candidate thresholds are zero plus every observed score.  The selection order
    is highest F1, then lowest false-positive rate, then the highest threshold
    (the least invasive route).  Callers must save this result before evaluating
    a frozen test or holdout split.
    """
    if len(scores) != len(is_damaged):
        raise ValueError("scores and is_damaged must have the same length")
    if not scores:
        raise ValueError("scores must contain at least one development example")
    if any(not 0 <= score <= 1 for score in scores):
        raise ValueError("scores must be between 0 and 1")

    candidates = sorted({0.0, *scores})
    evaluations: list[tuple[float, dict[str, float | int], float]] = []
    negatives = sum(not label for label in is_damaged)
    for threshold in candidates:
        metrics = binary_detection_metrics(
            is_damaged, [score >= threshold for score in scores]
        )
        false_positive_rate = (
            int(metrics["false_positive"]) / negatives if negatives else 0.0
        )
        evaluations.append((threshold, metrics, false_positive_rate))

    threshold, metrics, false_positive_rate = max(
        evaluations,
        key=lambda item: (
            float(item[1]["f1"]),
            -item[2],
            item[0],
        ),
    )
    return ThresholdCalibration(
        threshold=threshold,
        candidate_count=len(candidates),
        metrics=metrics,
        false_positive_rate=round(false_positive_rate, 6),
    )


def calibrate_development_pages(
    *, page_texts: Sequence[str], records: Sequence[dict[str, Any]]
) -> dict[str, object]:
    """Calibrate from manifest records marked ``development`` only.

    The explicit page-number check protects against pairing a manifest label
    with text extracted from another PDF/page. ``test`` and ``holdout`` labels
    are not read for the selection calculation.
    """
    if len(page_texts) != len(records):
        raise ValueError("page_texts and records must have the same length")

    development_page_nos: list[int] = []
    scores: list[float] = []
    labels: list[bool] = []
    for expected_page_no, (text, record) in enumerate(
        zip(page_texts, records), start=1
    ):
        page_no = record.get("page_no")
        if page_no != expected_page_no:
            raise ValueError(
                f"record page_no {page_no!r} does not match input page {expected_page_no}"
            )
        if record.get("split") != "development":
            continue
        label = record.get("is_damaged")
        if not isinstance(label, bool):
            raise TypeError(f"development page {page_no} has no boolean is_damaged")
        development_page_nos.append(page_no)
        scores.append(score_text_quality(text).score)
        labels.append(label)

    calibration = calibrate_threshold(scores=scores, is_damaged=labels)
    return {
        "development_pages": len(development_page_nos),
        "development_page_nos": development_page_nos,
        "calibration": calibration.to_dict(),
    }


def load_frozen_threshold(path: Path) -> float:
    """Load only evidence emitted by the development-only calibration script."""
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("protocol") != "development-only-threshold-calibration-v1":
        raise ValueError("calibration evidence has an unsupported protocol")
    calibration = evidence.get("calibration")
    if not isinstance(calibration, dict):
        raise TypeError("calibration evidence has no calibration object")
    threshold = calibration.get("threshold")
    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
        raise ValueError("calibration evidence has an invalid threshold")
    return float(threshold)
