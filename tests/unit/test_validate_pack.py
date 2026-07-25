from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_pack import check_reserved_trees, iter_secret_scan_files


class SecretScanTraversalTests(unittest.TestCase):
    def test_prunes_local_dependency_trees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = root / "docs" / "record.md"
            ignored = root / ".venv" / "Lib" / "fixture.py"
            vendor = root / "vendor" / "PwnzzAI" / "fixture.py"

            for path in (tracked, ignored, vendor):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")

            scanned = {
                path.relative_to(root).as_posix()
                for path in iter_secret_scan_files(root)
            }

        self.assertEqual(scanned, {"docs/record.md"})

    def test_phase06_runner_has_gate_and_authorization_evidence(self) -> None:
        failures: list[str] = []

        check_reserved_trees(failures)

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
