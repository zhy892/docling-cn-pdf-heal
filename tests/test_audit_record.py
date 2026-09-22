import tempfile
import unittest
from pathlib import Path

from docling_cn_pdf_heal.audit_record import build_local_audit_record


class AuditRecordTests(unittest.TestCase):
    def test_record_is_deterministic_and_does_not_expose_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sensitive-source-name.pdf"
            source.write_bytes(b"locally audited bytes")
            record = build_local_audit_record(
                source,
                audit_id="REAL-001",
                backend="native-docling",
                page_count=115,
                ocr_candidate_pages=[3, 7],
                skipped_blank_pages=[9],
            )
        self.assertEqual(record["audit_id"], "REAL-001")
        self.assertEqual(
            record["source_sha256"],
            "11afc0f874aed72f9421799f02fadfc3ae7b81c8a57c05ef09b42d6fb4c09b16",
        )
        self.assertEqual(record["page_count"], 115)
        self.assertEqual(record["ocr_candidate_pages"], [3, 7])
        self.assertEqual(record["skipped_blank_pages"], [9])
        self.assertNotIn("source_path", record)
        self.assertNotIn("source_name", record)

    def test_audit_id_must_not_be_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"x")
            with self.assertRaises(ValueError):
                build_local_audit_record(
                    source,
                    audit_id="",
                    backend="pypdf",
                    page_count=1,
                    ocr_candidate_pages=[],
                    skipped_blank_pages=[],
                )


if __name__ == "__main__":
    unittest.main()
