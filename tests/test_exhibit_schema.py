import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPOSITORY_ROOT / "schemas" / "exhibit.schema.json"
TEMPLATE_PATH = REPOSITORY_ROOT / "exhibits" / "_template" / "exhibit.json"
RELATIONSHIP_LAYERS = {
    "replaced-by": "ecosystem",
    "compatible-with": "protocol",
    "physically-similar": "physical",
    "protocol-carried-over": "protocol",
    "electrically-related": "electrical",
}


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

    def document_with_evidence_summary(self, highest_level, primary_sources):
        document = copy.deepcopy(self.template)
        document["evidence_summary"]["highest_level"] = highest_level
        document["evidence_summary"]["primary_sources"] = primary_sources
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

    def relationship(self, relationship_type):
        relationship = {
            "type": relationship_type,
            "target": "peer-interface",
            "layer": RELATIONSHIP_LAYERS[relationship_type],
            "scope": "limited mode only",
            "requires": [],
            "evidence": ["SRC-001"],
        }
        if relationship_type == "compatible-with":
            relationship["direction"] = "bidirectional"
        return relationship

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

    def test_e1_summary_requires_a_primary_source(self):
        document = self.document_with_evidence_summary("E1", 0)
        errors = list(self.validator.iter_errors(document))
        matching_errors = [
            error
            for error in errors
            if error.validator == "minimum"
            and list(error.absolute_path) == ["evidence_summary", "primary_sources"]
        ]
        self.assertTrue(
            matching_errors,
            f"expected an E1 summary to require a primary source; got {errors!r}",
        )

    def test_primary_source_count_requires_e1_summary(self):
        for highest_level in ("E2", "E3", "E4", "E5"):
            document = self.document_with_evidence_summary(highest_level, 1)
            errors = list(self.validator.iter_errors(document))
            matching_errors = [
                error
                for error in errors
                if error.validator == "const"
                and list(error.absolute_path) == ["evidence_summary", "highest_level"]
            ]
            with self.subTest(highest_level=highest_level):
                self.assertTrue(
                    matching_errors,
                    f"expected primary source count to require E1; got {errors!r}",
                )

    def test_coherent_evidence_summaries_validate(self):
        cases = [
            ("E1", 1),
            ("E1", 3),
            *[(level, 0) for level in ("E2", "E3", "E4", "E5")],
        ]
        for highest_level, primary_sources in cases:
            with self.subTest(
                highest_level=highest_level,
                primary_sources=primary_sources,
            ):
                self.assert_valid(
                    self.document_with_evidence_summary(
                        highest_level,
                        primary_sources,
                    )
                )

    def test_compatible_relationship_accepts_meaningful_directions(self):
        for direction in ("one-way", "bidirectional", "unknown"):
            relationship = self.relationship("compatible-with")
            relationship["direction"] = direction
            with self.subTest(direction=direction):
                self.assert_valid(self.document_with_relationship(relationship))

    def test_all_relationship_types_require_shared_contract_fields(self):
        for relationship_type in RELATIONSHIP_LAYERS:
            for field in ("requires", "evidence"):
                relationship = self.relationship(relationship_type)
                del relationship[field]

                with self.subTest(type=relationship_type, field=field):
                    self.assert_missing_relationship_field(
                        self.document_with_relationship(relationship), field
                    )

    def test_compatible_relationship_requires_direction(self):
        relationship = self.relationship("compatible-with")
        del relationship["direction"]
        self.assert_missing_relationship_field(
            self.document_with_relationship(relationship), "direction"
        )

    def test_compatible_relationship_rejects_not_applicable_direction(self):
        relationship = self.relationship("compatible-with")
        relationship["direction"] = "not-applicable"
        errors = list(
            self.validator.iter_errors(self.document_with_relationship(relationship))
        )
        matching_errors = [
            error
            for error in errors
            if error.validator == "enum"
            and list(error.absolute_path) == ["relationships", 0, "direction"]
        ]
        self.assertTrue(
            matching_errors,
            f"expected compatible direction to be meaningful; got {errors!r}",
        )

    def test_relationship_rejects_empty_evidence(self):
        relationship = self.relationship("compatible-with")
        relationship["evidence"] = []
        errors = list(
            self.validator.iter_errors(self.document_with_relationship(relationship))
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

    def assert_contract_string_rejected(self, field, value, validator_name):
        relationship = self.relationship("compatible-with")
        if field in ("requires", "evidence"):
            relationship[field] = [value]
            expected_path = ["relationships", 0, field, 0]
        else:
            relationship[field] = value
            expected_path = ["relationships", 0, field]

        errors = list(
            self.validator.iter_errors(self.document_with_relationship(relationship))
        )
        matching_errors = [
            error
            for error in errors
            if error.validator == validator_name
            and list(error.absolute_path) == expected_path
        ]
        self.assertTrue(
            matching_errors,
            f"expected {field!r} value {value!r} to fail; got {errors!r}",
        )

    def test_relationship_rejects_empty_contract_strings(self):
        for field in ("target", "scope", "requires", "evidence"):
            with self.subTest(field=field):
                self.assert_contract_string_rejected(field, "", "minLength")

    def test_relationship_rejects_whitespace_contract_strings(self):
        for field in ("target", "scope", "requires", "evidence"):
            with self.subTest(field=field):
                self.assert_contract_string_rejected(field, " \t ", "pattern")

    def test_non_compatible_relationships_do_not_require_direction(self):
        relationship_types = set(RELATIONSHIP_LAYERS) - {"compatible-with"}
        for relationship_type in sorted(relationship_types):
            with self.subTest(type=relationship_type):
                self.assert_valid(
                    self.document_with_relationship(
                        self.relationship(relationship_type)
                    )
                )


if __name__ == "__main__":
    unittest.main()
