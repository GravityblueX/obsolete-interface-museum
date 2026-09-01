import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPOSITORY_ROOT / "schemas" / "exhibit.schema.json"
TEMPLATE_PATH = REPOSITORY_ROOT / "exhibits" / "_template" / "exhibit.json"


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


class ExhibitSchemaRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.template = load_json(TEMPLATE_PATH)

    def document_with_relationship(self, relationship):
        document = copy.deepcopy(self.template)
        document["relationships"] = [relationship]
        return document

    def assert_valid(self, document):
        errors = sorted(
            self.validator.iter_errors(document),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([], errors)

    def assert_missing_relationship_field(self, document, field):
        errors = list(self.validator.iter_errors(document))
        matching_errors = [
            error
            for error in errors
            if error.validator == "required"
            and list(error.absolute_path) == ["relationships", 0]
            and field in error.validator_value
            and field in error.message
        ]
        self.assertTrue(
            matching_errors,
            f"expected relationships[0] to require {field!r}; got {errors!r}",
        )

    def compatible_relationship(self):
        return {
            "type": "compatible-with",
            "target": "peer-interface",
            "layer": "protocol",
            "scope": "limited mode only",
            "requires": [],
            "direction": "bidirectional",
            "evidence": ["SRC-001"],
        }

    def test_schema_declares_draft_2020_12(self):
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            self.schema["$schema"],
        )

    def test_template_validates(self):
        self.assert_valid(self.template)

    def test_checked_in_exhibit_metadata_validates(self):
        exhibit_paths = sorted((REPOSITORY_ROOT / "exhibits").rglob("exhibit.json"))
        self.assertTrue(exhibit_paths, "expected at least one checked-in exhibit.json")

        for exhibit_path in exhibit_paths:
            with self.subTest(path=exhibit_path.relative_to(REPOSITORY_ROOT)):
                self.assert_valid(load_json(exhibit_path))

    def test_complete_compatible_relationship_validates(self):
        self.assert_valid(
            self.document_with_relationship(self.compatible_relationship())
        )

    def test_compatible_relationship_requires_contract_fields(self):
        for field in ("requires", "direction", "evidence"):
            relationship = self.compatible_relationship()
            del relationship[field]

            with self.subTest(field=field):
                self.assert_missing_relationship_field(
                    self.document_with_relationship(relationship), field
                )

    def test_relationship_rejects_empty_evidence(self):
        relationship = self.compatible_relationship()
        relationship["evidence"] = []
        errors = list(
            self.validator.iter_errors(
                self.document_with_relationship(relationship)
            )
        )
        matching_errors = [
            error
            for error in errors
            if error.validator == "minItems"
            and list(error.absolute_path) == ["relationships", 0, "evidence"]
        ]
        self.assertTrue(
            matching_errors,
            f"expected relationships[0].evidence to be non-empty; got {errors!r}",
        )

    def test_relationship_rejects_empty_contract_entries(self):
        for field in ("requires", "evidence"):
            relationship = self.compatible_relationship()
            relationship[field] = [""]
            errors = list(
                self.validator.iter_errors(
                    self.document_with_relationship(relationship)
                )
            )
            matching_errors = [
                error
                for error in errors
                if error.validator == "minLength"
                and list(error.absolute_path)
                == ["relationships", 0, field, 0]
            ]

            with self.subTest(field=field):
                self.assertTrue(
                    matching_errors,
                    f"expected an empty {field!r} entry to fail; got {errors!r}",
                )

    def test_non_compatible_relationship_does_not_require_direction(self):
        relationship = {
            "type": "replaced-by",
            "target": "successor-interface",
            "layer": "ecosystem",
            "scope": "general-purpose host use",
            "requires": [],
            "evidence": ["SRC-002"],
        }
        self.assert_valid(self.document_with_relationship(relationship))


if __name__ == "__main__":
    unittest.main()
