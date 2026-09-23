import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog import description, leaves, resolve  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_current_installed_leaf_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child = root / "kyb-verification-qcc" / "SKILL.md"
            child.parent.mkdir()
            child.write_text("---\nname: KYB\ndescription: >\n  核验企业主体\n  和受益所有人。\n---\n# Body\n")
            self.assertEqual(leaves(root), [{"name": "kyb-verification-qcc", "description": "核验企业主体 和受益所有人。"}])
            self.assertEqual(resolve(root, "kyb-verification-qcc"), child.resolve())
            with self.assertRaisesRegex(ValueError, "invalid"):
                resolve(root, "../kyb-verification-qcc")

    def test_malformed_installed_leaf_fails_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child = root / "credit-rating-qcc" / "SKILL.md"
            child.parent.mkdir()
            child.write_text("# Missing frontmatter\n")
            with self.assertRaisesRegex(ValueError, "frontmatter"):
                leaves(root)
            child.write_text("---\ndescription: |\n  信用评级\n---\n")
            self.assertEqual(description(child), "信用评级")

    def test_resolve_does_not_depend_on_unrelated_leaf(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            healthy = root / "kyb-verification-qcc" / "SKILL.md"
            healthy.parent.mkdir()
            healthy.write_text("---\ndescription: 企业核验\n---\n")
            broken = root / "credit-rating-qcc" / "SKILL.md"
            broken.parent.mkdir()
            broken.write_text("# Missing frontmatter\n")
            self.assertEqual(resolve(root, "kyb-verification-qcc"), healthy.resolve())
            with self.assertRaisesRegex(ValueError, "frontmatter"):
                resolve(root, "credit-rating-qcc")


if __name__ == "__main__":
    unittest.main()
