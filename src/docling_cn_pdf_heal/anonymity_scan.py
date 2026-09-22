"""Deterministic preflight checks for competition-material anonymization."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AnonymityFinding:
    term: str
    line: int
    column: int

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


def scan_text_for_terms(
    text: str, forbidden_terms: list[str]
) -> list[AnonymityFinding]:
    """Find all supplied identity terms without embedding personal data in code."""
    if any(not term for term in forbidden_terms):
        raise ValueError("forbidden terms must not contain an empty string")

    findings: list[AnonymityFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line_folded = line.casefold()
        for term in forbidden_terms:
            term_folded = term.casefold()
            start = 0
            while True:
                index = line_folded.find(term_folded, start)
                if index < 0:
                    break
                findings.append(
                    AnonymityFinding(term=term, line=line_no, column=index + 1)
                )
                start = index + len(term_folded)
    return findings
