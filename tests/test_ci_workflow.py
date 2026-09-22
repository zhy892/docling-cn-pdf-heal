import unittest
from pathlib import Path


class CiWorkflowTests(unittest.TestCase):
    def test_ci_runs_locked_tests_and_never_references_real_pdf_inputs(self) -> None:
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn("uv sync --locked", workflow)
        self.assertIn("unittest discover", workflow)
        self.assertIn("generate_dataset_v4.py", workflow)
        self.assertIn("generate_crosscheck_v3.py", workflow)
        self.assertNotIn("real_pdf", workflow.casefold())
        self.assertNotIn("secrets.", workflow.casefold())


if __name__ == "__main__":
    unittest.main()
