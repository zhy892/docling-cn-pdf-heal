import tempfile
import unittest
from pathlib import Path

from scripts.assert_public_repo_safety import find_unsafe_public_files


class PublicRepoSafetyTests(unittest.TestCase):
    def test_flags_pdf_and_token_but_allows_source_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "safe.py").write_text("print('safe')\n", encoding="utf-8")
            (root / "data.json").write_text('{"pages": []}\n', encoding="utf-8")
            (root / "sample.pdf").write_bytes(b"%PDF-1.7\n")
            (root / "bad.txt").write_text("token=ghp_" + "a" * 36, encoding="utf-8")

            findings = find_unsafe_public_files(root)

        self.assertEqual([(finding.path.name, finding.reason) for finding in findings], [
            ("bad.txt", "github_token_pattern"),
            ("sample.pdf", "pdf_binary_not_allowed"),
        ])

    def test_allows_png_assets_only_in_docs_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_dir = root / "docs" / "images"
            image_dir.mkdir(parents=True)

            (image_dir / "result.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (root / "other.png").write_bytes(b"\x89PNG\r\n\x1a\n")

            findings = find_unsafe_public_files(root)

        self.assertEqual(
            [(finding.path.name, finding.reason) for finding in findings],
            [("other.png", "non_utf8_file_not_allowed")],
        )
if __name__ == "__main__":
    unittest.main()
