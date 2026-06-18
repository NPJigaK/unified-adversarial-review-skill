from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "unified-adversarial-review"
SKILL = SKILL_DIR / "SKILL.md"


class SkillPackageTests(unittest.TestCase):
    def test_skill_frontmatter_and_directory_name(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n", 2)[1]
        name = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
        description = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        self.assertIsNotNone(name)
        self.assertIsNotNone(description)
        skill_name = name.group(1).strip()
        skill_description = description.group(1).strip()
        self.assertEqual(skill_name, SKILL_DIR.name)
        self.assertRegex(skill_name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertGreaterEqual(len(skill_description), 1)
        self.assertLessEqual(len(skill_description), 1024)

    def test_standard_collection_layout(self):
        self.assertEqual(SKILL_DIR.parent.name, "skills")
        self.assertFalse((ROOT / "unified-adversarial-review" / "SKILL.md").exists())

    def test_runtime_references_exist(self):
        text = SKILL.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        relative_links = [link for link in links if "://" not in link]
        self.assertTrue(relative_links)
        for link in relative_links:
            target = (SKILL_DIR / link.split("#", 1)[0]).resolve()
            self.assertTrue(target.exists(), link)

    def test_runtime_has_no_absolute_local_paths(self):
        absolute_path = re.compile(
            r"(?m)(?:^|[\s`'\"])(?:[A-Za-z]:[\\/]|/Users/|/home/[^/]+/)"
        )
        for path in SKILL_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}:
                self.assertIsNone(absolute_path.search(path.read_text(encoding="utf-8")), path)

    def test_bundled_legal_and_provenance_files_match_root(self):
        for name in ("LICENSE", "NOTICE", "UPSTREAM.md"):
            self.assertEqual((ROOT / name).read_bytes(), (SKILL_DIR / name).read_bytes(), name)

    def test_codex_metadata_is_explicit_only(self):
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", text)

    def test_readme_install_path_is_standard_collection_layout(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add NPJigaK/unified-adversarial-review-skill", text)
        self.assertIn("skills/unified-adversarial-review/SKILL.md", text)
        self.assertIn("skills/unified-adversarial-review/", text)

    def test_root_markdown_relative_links_resolve(self):
        markdown_link = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        missing = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for match in markdown_link.finditer(text):
                target = match.group(1).strip()
                if (
                    not target
                    or target.startswith("#")
                    or "://" in target
                    or target.startswith("mailto:")
                ):
                    continue
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    missing.append((path, target))
                    continue
                if not resolved.exists():
                    missing.append((path, target))
        self.assertEqual(missing, [])

    def test_generated_archives_are_ignored_and_absent(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.zip", gitignore)
        self.assertIn("*.patch", gitignore)
        generated = [
            path
            for pattern in ("*.zip", "*.patch")
            for path in ROOT.rglob(pattern)
            if ".git" not in path.parts
        ]
        self.assertEqual(generated, [])


if __name__ == "__main__":
    unittest.main()
