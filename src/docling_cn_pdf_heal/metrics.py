"""Text normalization and transparent character-error-rate calculation."""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence


def normalize_for_cer(text: str) -> str:
    """Normalize Unicode and remove layout-only whitespace before CER."""
    normalized = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in normalized if not ch.isspace())


def levenshtein_distance(reference: str, hypothesis: str) -> int:
    """Return edit distance using O(min(n, m)) memory."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for i, reference_char in enumerate(reference, start=1):
        current = [i]
        for j, hypothesis_char in enumerate(hypothesis, start=1):
            substitution = previous[j - 1] + (reference_char != hypothesis_char)
            current.append(min(previous[j] + 1, current[j - 1] + 1, substitution))
        previous = current
    return previous[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    """CER after the documented normalization; returns 0 for two empty texts."""
    normalized_reference = normalize_for_cer(reference)
    normalized_hypothesis = normalize_for_cer(hypothesis)
    if not normalized_reference:
        return 0.0 if not normalized_hypothesis else 1.0
    return levenshtein_distance(normalized_reference, normalized_hypothesis) / len(
        normalized_reference
    )


def binary_detection_metrics(
    truth: Sequence[bool], prediction: Sequence[bool]
) -> dict[str, float | int]:
    """Precision, recall and F1 with all counts exposed for audit."""
    if len(truth) != len(prediction):
        raise ValueError("truth and prediction must have the same length")
    true_positive = sum(t and p for t, p in zip(truth, prediction))
    false_positive = sum(not t and p for t, p in zip(truth, prediction))
    false_negative = sum(t and not p for t, p in zip(truth, prediction))
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }
