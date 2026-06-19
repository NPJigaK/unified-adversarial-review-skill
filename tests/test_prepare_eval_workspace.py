import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_eval_workspace.py"


class PrepareEvalWorkspaceTests(unittest.TestCase):
    def test_prepare_eval_workspace_splits_prompts_from_rubrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "workspace"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases",
                    str(ROOT / "evals" / "cases.json"),
                    "--out",
                    str(out_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], "prepared-adversarial-review-eval-workspace")
            self.assertEqual(manifest["source_format"], "portable-agent-skill-evaluation-cases")
            self.assertGreaterEqual(len(manifest["cases"]), 3)

            for case in manifest["cases"]:
                case_dir = out_dir / case["id"]
                prompt = (case_dir / "prompt.md").read_text(encoding="utf-8")
                rubric = json.loads((case_dir / "rubric.json").read_text(encoding="utf-8"))

                self.assertIn("## Review target", prompt)
                self.assertIn("## User request", prompt)
                self.assertIn("## Artifact", prompt)
                self.assertNotIn("acceptance_criteria", prompt)
                self.assertNotIn("must_not_report", prompt)
                self.assertEqual(rubric["id"], case["id"])
                self.assertTrue(rubric["acceptance_criteria"])
                self.assertTrue(rubric["must_not_report"])

    def test_prepare_eval_workspace_rejects_evaluator_sections_in_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "evals", tmp_root / "evals")
            fixture = tmp_root / "evals" / "fixtures" / "refuted-style-only-diff.md"
            fixture.write_text(
                fixture.read_text(encoding="utf-8")
                + "\n## Must not report\n\n- leaked rubric\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases",
                    str(tmp_root / "evals" / "cases.json"),
                    "--out",
                    str(tmp_root / "workspace"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evaluator-only section", result.stderr.lower())

    def test_prepare_eval_workspace_rejects_case_id_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "evals", tmp_root / "evals")
            cases_path = tmp_root / "evals" / "cases.json"
            cases = json.loads(cases_path.read_text(encoding="utf-8"))
            cases["cases"][0]["id"] = "../escape"
            cases_path.write_text(json.dumps(cases), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases",
                    str(cases_path),
                    "--out",
                    str(tmp_root / "workspace"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("case id", result.stderr.lower())
            self.assertFalse((tmp_root / "escape").exists())


if __name__ == "__main__":
    unittest.main()
