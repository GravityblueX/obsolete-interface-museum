import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.validate_source_references import validate_repository


class SourceReferenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository_root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_exhibit(self, name, evidence_lists, sources):
        exhibit_directory = self.repository_root / "exhibits" / name
        exhibit_directory.mkdir(parents=True)
        relationships = [{"evidence": evidence} for evidence in evidence_lists]
        (exhibit_directory / "exhibit.json").write_text(
            json.dumps({"relationships": relationships}),
            encoding="utf-8",
        )
        if sources is not None:
            (exhibit_directory / "sources.md").write_text(
                sources,
                encoding="utf-8",
            )

    def test_matching_source_id_is_valid(self):
        self.write_exhibit(
            "serial",
            [["SRC-001"]],
            "# Sources\n\n### SRC-001 — Original manual\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_dangling_source_id_reports_json_location(self):
        self.write_exhibit(
            "serial",
            [["SRC-404"]],
            "# Sources\n\n### SRC-001 — Original manual\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in exhibits/serial/sources.md'
            ],
            validate_repository(self.repository_root),
        )

    def test_prose_and_fenced_examples_are_not_declarations(self):
        self.write_exhibit(
            "serial",
            [["SRC-404"]],
            "# Sources\n\n"
            "SRC-404 is mentioned in prose only.\n\n"
            "```markdown\n"
            "### SRC-404 — Example heading\n"
            "```\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in exhibits/serial/sources.md'
            ],
            validate_repository(self.repository_root),
        )

    def test_source_id_is_escaped_in_diagnostic(self):
        self.write_exhibit(
            "serial",
            [["SRC-404\nforged diagnostic"]],
            "# Sources\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404\\nforged diagnostic" is not declared in '
                "exhibits/serial/sources.md"
            ],
            validate_repository(self.repository_root),
        )

    def test_duplicate_formal_source_id_is_rejected(self):
        self.write_exhibit(
            "serial",
            [],
            "# Sources\n\n"
            "### SRC-001 — First manual\n\n"
            "### SRC-001 — Second manual\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/sources.md:5: duplicate source ID SRC-001; "
                "first declared at line 3"
            ],
            validate_repository(self.repository_root),
        )

    def test_source_ids_may_be_reused_by_different_exhibits(self):
        sources = "# Sources\n\n### SRC-001 — Local manual\n"
        self.write_exhibit("alpha", [["SRC-001"]], sources)
        self.write_exhibit("beta", [["SRC-001"]], sources)

        self.assertEqual([], validate_repository(self.repository_root))

    def test_source_id_does_not_resolve_across_exhibits(self):
        self.write_exhibit(
            "alpha",
            [],
            "# Sources\n\n### SRC-001 — Alpha manual\n",
        )
        self.write_exhibit(
            "beta",
            [["SRC-001"]],
            "# Sources\n\n### SRC-002 — Beta manual\n",
        )

        self.assertEqual(
            [
                "exhibits/beta/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-001" is not declared in exhibits/beta/sources.md'
            ],
            validate_repository(self.repository_root),
        )

    def test_diagnostics_have_stable_path_and_index_order(self):
        self.write_exhibit("zeta", [["SRC-009"]], "# Sources\n")
        self.write_exhibit(
            "alpha",
            [["SRC-002", "SRC-001"]],
            "# Sources\n",
        )

        self.assertEqual(
            [
                "exhibits/alpha/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-002" is not declared in exhibits/alpha/sources.md',
                "exhibits/alpha/exhibit.json: relationships[0].evidence[1]: "
                'source ID "SRC-001" is not declared in exhibits/alpha/sources.md',
                "exhibits/zeta/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-009" is not declared in exhibits/zeta/sources.md',
            ],
            validate_repository(self.repository_root),
        )

    def test_checked_in_corpus_is_valid(self):
        self.assertEqual([], validate_repository(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
