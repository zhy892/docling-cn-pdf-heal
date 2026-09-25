"""Fail CI if a public source tree contains disallowed binary or secret-like data."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

_TOKEN_RE = re.compile(r"\b(?:ghp|github_pat|sk)-[A-Za-z0-9_\-]{20,}\b|\bghp_[A-Za-z0-9]{20,}\b")
_IGNORED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    reason: str


def _is_allowed_documentation_image(path: Path, root: Path) -> bool:
    """Allow only PNG screenshots committed under docs/images."""
    relative_path = path.relative_to(root)
    return (
        relative_path.parent == Path("docs/images")
        and relative_path.suffix.casefold() == ".png"
    )


def find_unsafe_public_files(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in _IGNORED_PARTS for part in path.parts):
            continue
        if _is_allowed_documentation_image(path, root):
            continue
        if path.suffix.casefold() == ".pdf":
            findings.append(SafetyFinding(path, "pdf_binary_not_allowed"))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(SafetyFinding(path, "non_utf8_file_not_allowed"))
            continue
        if _TOKEN_RE.search(text):
            findings.append(SafetyFinding(path, "github_token_pattern"))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    findings = find_unsafe_public_files(args.root)
    if findings:
        for finding in findings:
            print(f"{finding.path}: {finding.reason}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
