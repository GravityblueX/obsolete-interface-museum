import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_formal_source_id_is_valid_at_bof_or_after_ascii_blank(self):
        self.write_exhibit(
            "at-bof",
            [["SRC-001"]],
            "### SRC-001 — Original manual\n",
        )
        self.write_exhibit(
            "after-ascii-blank",
            [["SRC-001"]],
            "# Sources\n \t\n### SRC-001 — Original manual ###\n",
        )
        self.write_exhibit(
            "unicode-title",
            [["SRC-002"]],
            "### SRC-002 — 原厂手册\n",
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

    def test_container_fences_do_not_declare_source_ids(self):
        self.write_exhibit(
            "unordered",
            [["SRC-404"]],
            "# Sources\n\n"
            "- ```markdown\n"
            "  ### SRC-404 — Example heading\n"
            "  ```\n",
        )
        self.write_exhibit(
            "ordered",
            [["SRC-405"]],
            "# Sources\n\n"
            "1. ~~~markdown\n"
            "   ### SRC-405 — Example heading\n"
            "   ~~~\n",
        )

        self.assertEqual(
            [
                "exhibits/ordered/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-405" is not declared in '
                "exhibits/ordered/sources.md",
                "exhibits/unordered/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in '
                "exhibits/unordered/sources.md",
            ],
            validate_repository(self.repository_root),
        )

    def test_html_blocks_ignore_or_reject_source_like_headings(self):
        sources_by_exhibit = {
            "comment": ("SRC-401", "<!--\n\n### SRC-401 — Disabled\n-->\n"),
            "pre": ("SRC-402", "<pre>\n\n### SRC-402 — Literal\n</pre>\n"),
            "div": ("SRC-403", "<div>\n### SRC-403 — Literal\n</div>\n"),
            "hgroup": (
                "SRC-404",
                "<hgroup>block text\n### SRC-404 — Literal\n</hgroup>\n",
            ),
        }
        for name, (source_id, sources) in sources_by_exhibit.items():
            self.write_exhibit(name, [[source_id]], sources)

        self.assertEqual(
            [
                "exhibits/comment/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-401" is not declared in '
                "exhibits/comment/sources.md",
                "exhibits/div/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-403" is not declared in exhibits/div/sources.md',
                "exhibits/div/sources.md:2: source declaration SRC-403 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
                "exhibits/hgroup/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in '
                "exhibits/hgroup/sources.md",
                "exhibits/hgroup/sources.md:2: source declaration SRC-404 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
                "exhibits/pre/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-402" is not declared in exhibits/pre/sources.md',
            ],
            validate_repository(self.repository_root),
        )

    def test_hidden_heading_does_not_create_duplicate_source_id(self):
        self.write_exhibit(
            "serial",
            [["SRC-001"]],
            "# Sources\n\n"
            "### SRC-001 — Real manual\n\n"
            "<!--\n"
            "### SRC-001 — Disabled duplicate\n"
            "-->\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_generic_html_with_quoted_angles_fails_closed(self):
        self.write_exhibit(
            "greater",
            [["SRC-404"]],
            '<kbd title=">">\n### SRC-404 — Literal\n\n',
        )
        self.write_exhibit(
            "less",
            [["SRC-405"]],
            '<kbd title="<">\n### SRC-405 — Literal\n\n',
        )

        self.assertEqual(
            [
                "exhibits/greater/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in '
                "exhibits/greater/sources.md",
                "exhibits/greater/sources.md:2: source declaration SRC-404 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
                "exhibits/less/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-405" is not declared in exhibits/less/sources.md',
                "exhibits/less/sources.md:2: source declaration SRC-405 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
            ],
            validate_repository(self.repository_root),
        )

    def test_multiline_html_constructs_suppress_candidates_across_blank_lines(self):
        cases = [
            ("cdata", "SRC-440", "<![CDATA[\n\n", "]]>\n"),
            ("comment", "SRC-441", "<!--\n\n", "-->\n"),
            ("declaration", "SRC-442", "<!DOCTYPE\n\n", ">\n"),
            ("processing-instruction", "SRC-443", "<?target\n\n", "?>\n"),
            ("raw-html", "SRC-444", "<pre>\n\n", "</pre>\n"),
        ]
        for name, source_id, prefix, suffix in cases:
            self.write_exhibit(
                name,
                [[source_id]],
                f"{prefix}### {source_id} — Literal content\n{suffix}",
            )

        self.assertEqual(
            [
                f"exhibits/{name}/exhibit.json: relationships[0].evidence[0]: "
                f'source ID "{source_id}" is not declared in '
                f"exhibits/{name}/sources.md"
                for name, source_id, _, _ in cases
            ],
            validate_repository(self.repository_root),
        )

    def test_source_like_heading_after_paragraph_fails_closed(self):
        self.write_exhibit(
            "serial",
            [],
            "### SRC-001 — First manual\n"
            "Paragraph text\n"
            "<kbd>\n"
            "### SRC-001 — Second manual\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/sources.md:4: source declaration SRC-001 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line"
            ],
            validate_repository(self.repository_root),
        )

    def test_invalid_generic_html_does_not_hide_real_heading(self):
        invalid_tags = {
            "bad-attribute": "<kbd ???>",
            "bad-closing": "</kbd attr=x>",
            "missing-value": "<kbd title=>",
        }
        for index, (name, invalid_tag) in enumerate(invalid_tags.items(), start=1):
            source_id = f"SRC-{413 + index:03d}"
            self.write_exhibit(
                name,
                [[source_id]],
                f"{invalid_tag}\n\n### {source_id} — Real manual\n",
            )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_any_type_one_end_tag_ends_raw_html_block(self):
        self.write_exhibit(
            "serial",
            [["SRC-419"]],
            "<pre>\n" "</script>\n" "\n" "### SRC-419 — Real manual\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_type_one_end_tag_requires_exact_closing_syntax(self):
        cases = {
            "pre-space": ("SRC-484", "</pre >"),
            "pre-tab": ("SRC-485", "</pre\t>"),
            "script-space": ("SRC-486", "</script >"),
        }
        for name in sorted(cases):
            source_id, invalid_end = cases[name]
            self.write_exhibit(
                name,
                [[source_id]],
                "<pre>\n\n"
                "literal content\n"
                f"{invalid_end}\n\n"
                f"### {source_id} — Still raw HTML\n",
            )

        self.assertEqual(
            [
                f"exhibits/{name}/exhibit.json: relationships[0].evidence[0]: "
                f'source ID "{source_id}" is not declared in '
                f"exhibits/{name}/sources.md"
                for name, (source_id, _) in sorted(cases.items())
            ],
            validate_repository(self.repository_root),
        )

    def test_raw_html_tag_matching_uses_ascii_case_folding(self):
        unicode_lookalikes = {
            "dotted-i": ("SRC-487", "<scrİpt>"),
            "dotless-i": ("SRC-488", "<scrıpt>"),
            "long-s": ("SRC-489", "<ſcript>"),
        }
        for name in sorted(unicode_lookalikes):
            source_id, fake_opener = unicode_lookalikes[name]
            self.write_exhibit(
                name,
                [],
                f"### {source_id} — First manual\n\n"
                f"{fake_opener}\n\n"
                f"### {source_id} — Second manual\n",
            )

        self.write_exhibit(
            "ascii-uppercase",
            [["SRC-490"]],
            "<SCRIPT>\n\n### SRC-490 — Literal heading\n",
        )

        self.assertEqual(
            [
                "exhibits/ascii-uppercase/exhibit.json: "
                'relationships[0].evidence[0]: source ID "SRC-490" is not '
                "declared in exhibits/ascii-uppercase/sources.md",
                *[
                    f"exhibits/{name}/sources.md:5: duplicate source ID {source_id}; "
                    "first declared at line 1"
                    for name, (source_id, _) in sorted(unicode_lookalikes.items())
                ],
            ],
            validate_repository(self.repository_root),
        )

    def test_ascii_control_whitespace_starts_raw_html_block(self):
        cases = {
            "form-feed": ("SRC-492", "\f"),
            "vertical-tab": ("SRC-502", "\v"),
        }
        for name in sorted(cases):
            source_id, whitespace = cases[name]
            self.write_exhibit(
                name,
                [[source_id]],
                f"<pre{whitespace}>\n\n### {source_id} — Still raw HTML\n",
            )

        self.assertEqual(
            [
                f"exhibits/{name}/exhibit.json: relationships[0].evidence[0]: "
                f'source ID "{source_id}" is not declared in '
                f"exhibits/{name}/sources.md"
                for name, (source_id, _) in sorted(cases.items())
            ],
            validate_repository(self.repository_root),
        )

    def test_one_leading_bom_is_removed_before_block_scanning(self):
        self.write_exhibit(
            "formal-heading",
            [["SRC-493"]],
            "\ufeff### SRC-493 — Real manual\n",
        )
        self.write_exhibit(
            "duplicate",
            [],
            "\ufeff### SRC-494 — First manual\n\n" "### SRC-494 — Second manual\n",
        )
        self.write_exhibit(
            "fence",
            [["SRC-495"]],
            "\ufeff```markdown\n\n### SRC-495 — Literal heading\n```\n",
        )
        self.write_exhibit(
            "raw-html",
            [["SRC-496"]],
            "\ufeff<pre>\n\n### SRC-496 — Literal heading\n",
        )
        self.write_exhibit(
            "embedded-bom",
            [["SRC-497"]],
            "# Sources\n\n\ufeff### SRC-497 — Not at column one\n",
        )

        self.assertEqual(
            [
                "exhibits/duplicate/sources.md:3: duplicate source ID SRC-494; "
                "first declared at line 1",
                "exhibits/embedded-bom/exhibit.json: "
                'relationships[0].evidence[0]: source ID "SRC-497" is not '
                "declared in exhibits/embedded-bom/sources.md",
                "exhibits/fence/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-495" is not declared in exhibits/fence/sources.md',
                "exhibits/raw-html/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-496" is not declared in '
                "exhibits/raw-html/sources.md",
            ],
            validate_repository(self.repository_root),
        )

    def test_unicode_lookalike_does_not_end_raw_html_block(self):
        self.write_exhibit(
            "serial",
            [["SRC-491"]],
            "<pre>\n\n" "</ſtyle>\n\n" "### SRC-491 — Still raw HTML\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-491" is not declared in exhibits/serial/sources.md'
            ],
            validate_repository(self.repository_root),
        )

    def test_unicode_whitespace_does_not_create_a_formal_boundary(self):
        self.write_exhibit(
            "fence",
            [["SRC-407"]],
            "```markdown\n" "```\u00a0\n" "### SRC-407 — Still fenced\n" "```\n",
        )
        self.write_exhibit(
            "html",
            [["SRC-408"]],
            "<div>\n" "\u00a0\n" "### SRC-408 — Still raw HTML\n" "</div>\n",
        )

        self.assertEqual(
            [
                "exhibits/fence/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-407" is not declared in exhibits/fence/sources.md',
                "exhibits/html/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-408" is not declared in exhibits/html/sources.md',
                "exhibits/html/sources.md:3: source declaration SRC-408 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
            ],
            validate_repository(self.repository_root),
        )

    def test_ascii_whitespace_ends_fence_and_html_block(self):
        self.write_exhibit(
            "fence",
            [["SRC-420"]],
            "```markdown\n" "``` \t\n" "\n" "### SRC-420 — Real manual\n",
        )
        self.write_exhibit(
            "html",
            [["SRC-421"]],
            "<div>\n" " \t\n" "### SRC-421 — Real manual\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_unicode_line_separator_does_not_start_markdown_heading(self):
        self.write_exhibit(
            "serial",
            [["SRC-404"]],
            "Prose before\u2028### SRC-404 — Not an ATX line\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404" is not declared in exhibits/serial/sources.md'
            ],
            validate_repository(self.repository_root),
        )

    def test_backtick_in_info_string_does_not_open_fence(self):
        self.write_exhibit(
            "serial",
            [["SRC-001"]],
            "```foo`bar\n" "\n" "### SRC-001 — Real manual\n" "```\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_source_heading_requires_three_digit_id(self):
        self.write_exhibit(
            "serial",
            [["SRC-1", "SRC-0001"]],
            "### SRC-1 — Short ID\n" "### SRC-0001 — Long ID\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-1" is not declared in exhibits/serial/sources.md',
                "exhibits/serial/exhibit.json: relationships[0].evidence[1]: "
                'source ID "SRC-0001" is not declared in exhibits/serial/sources.md',
            ],
            validate_repository(self.repository_root),
        )

    def test_source_title_must_begin_with_literal_alphanumeric_text(self):
        cases = {
            "cdata": ("SRC-452", "<![CDATA[Manual]]>"),
            "closing-hashes": ("SRC-404", "###"),
            "code-span": ("SRC-454", "`<kbd>`"),
            "comment": ("SRC-405", "<!-- hidden title -->"),
            "declaration": ("SRC-451", "<!DOCTYPE html>"),
            "emphasis": ("SRC-455", "*Manual*"),
            "empty-inline-link": ("SRC-409", "[](https://example.com)"),
            "empty-span": ("SRC-412", '<span title=">Manual"></span>'),
            "empty-title": ("SRC-458", ""),
            "entity": ("SRC-411", "&#32;"),
            "escaped-link-label": ("SRC-453", r"[\]](https://example.com)"),
            "processing-instruction": ("SRC-450", "<?target data?>"),
        }
        for name in sorted(cases):
            source_id, title = cases[name]
            self.write_exhibit(
                name,
                [[source_id]],
                f"### {source_id} — {title}\n",
            )

        expected = []
        for name in sorted(cases):
            source_id, _ = cases[name]
            expected.extend(
                [
                    f"exhibits/{name}/exhibit.json: "
                    "relationships[0].evidence[0]: "
                    f'source ID "{source_id}" is not declared in '
                    f"exhibits/{name}/sources.md",
                    f"exhibits/{name}/sources.md:1: source declaration {source_id} "
                    "title must begin with a literal letter or number; "
                    "Markdown/HTML-prefixed titles are not supported",
                ]
            )

        self.assertEqual(expected, validate_repository(self.repository_root))

    def test_invalid_title_and_placement_are_both_reported(self):
        self.write_exhibit(
            "serial",
            [["SRC-456"]],
            "Paragraph text\n### SRC-456 — `Manual`\n",
        )

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-456" is not declared in exhibits/serial/sources.md',
                "exhibits/serial/sources.md:2: source declaration SRC-456 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
                "exhibits/serial/sources.md:2: source declaration SRC-456 title "
                "must begin with a literal letter or number; "
                "Markdown/HTML-prefixed titles are not supported",
            ],
            validate_repository(self.repository_root),
        )

    def test_literal_title_prefix_may_be_followed_by_markup(self):
        self.write_exhibit(
            "serial",
            [["SRC-457"]],
            "### SRC-457 — Original manual <?target data?> `<kbd>`\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_prose_and_fenced_examples_are_not_declarations(self):
        self.write_exhibit(
            "serial",
            [["SRC-404"]],
            "# Sources\n\n"
            "SRC-404 is mentioned in prose only.\n\n"
            "```markdown\n"
            "\n"
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
        unsafe_source_id = "SRC-404\ud800\u202e"
        self.write_exhibit(
            "serial",
            [[unsafe_source_id]],
            "# Sources\n",
        )

        errors = validate_repository(self.repository_root)
        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-404\\ud800\\u202e" is not declared in '
                "exhibits/serial/sources.md"
            ],
            errors,
        )
        self.assertTrue(errors[0].isascii())

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

    def test_symbolic_link_source_ledger_is_rejected(self):
        self.write_exhibit(
            "alpha",
            [],
            "# Sources\n\n### SRC-001 — Alpha manual\n",
        )
        self.write_exhibit("beta", [["SRC-001"]], None)
        source_link = self.repository_root / "exhibits" / "beta" / "sources.md"
        try:
            source_link.symlink_to(Path("../alpha/sources.md"))
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symbolic links are unavailable: {error}")

        self.assertEqual(
            [
                "exhibits/beta/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-001" is not declared in exhibits/beta/sources.md',
                "exhibits/beta/sources.md: symbolic-link source ledger is not allowed",
            ],
            validate_repository(self.repository_root),
        )

    def test_symbolic_link_policy_does_not_follow_ledger(self):
        self.write_exhibit(
            "serial",
            [["SRC-001"]],
            "# Sources\n\n### SRC-001 — Must not be read\n",
        )
        source_path = self.repository_root / "exhibits" / "serial" / "sources.md"
        original_is_symlink = Path.is_symlink

        def reports_only_source_ledger_as_symlink(path):
            if path == source_path:
                return True
            return original_is_symlink(path)

        with mock.patch.object(
            Path,
            "is_symlink",
            autospec=True,
            side_effect=reports_only_source_ledger_as_symlink,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            [
                "exhibits/serial/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-001" is not declared in exhibits/serial/sources.md',
                "exhibits/serial/sources.md: symbolic-link source ledger is not allowed",
            ],
            errors,
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

    def test_diagnostics_preserve_numeric_relationship_and_evidence_order(self):
        evidence_lists = [
            [f"SRC-{index:03d}" for index in range(11)],
            *[[f"SRC-{100 + index:03d}"] for index in range(1, 11)],
        ]
        self.write_exhibit("serial", evidence_lists, "# Sources\n")

        expected = []
        for relationship_index, evidence in enumerate(evidence_lists):
            for evidence_index, source_id in enumerate(evidence):
                expected.append(
                    "exhibits/serial/exhibit.json: relationships["
                    f"{relationship_index}].evidence[{evidence_index}]: "
                    f'source ID "{source_id}" is not declared in '
                    "exhibits/serial/sources.md"
                )

        self.assertEqual(expected, validate_repository(self.repository_root))

    def test_diagnostics_have_stable_path_and_ledger_line_order(self):
        self.write_exhibit(
            "zeta",
            [["SRC-009"]],
            "### SRC-001 — First manual\n\n" "### SRC-001 — Duplicate manual\n",
        )
        self.write_exhibit(
            "alpha",
            [["SRC-999"]],
            "### SRC-001 — First manual\n"
            "Paragraph text\n"
            "### SRC-002 — `Invalid and misplaced`\n"
            "\n"
            "Filler\n"
            "\n"
            "Filler\n"
            "\n"
            "\n"
            "### SRC-001 — Duplicate manual\n",
        )

        self.assertEqual(
            [
                "exhibits/alpha/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-999" is not declared in exhibits/alpha/sources.md',
                "exhibits/alpha/sources.md:3: source declaration SRC-002 must be "
                "top-level at the start of a Markdown block; begin the file or "
                "precede it with an ASCII space/tab-only blank line",
                "exhibits/alpha/sources.md:3: source declaration SRC-002 title "
                "must begin with a literal letter or number; "
                "Markdown/HTML-prefixed titles are not supported",
                "exhibits/alpha/sources.md:10: duplicate source ID SRC-001; "
                "first declared at line 1",
                "exhibits/zeta/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-009" is not declared in exhibits/zeta/sources.md',
                "exhibits/zeta/sources.md:3: duplicate source ID SRC-001; "
                "first declared at line 1",
            ],
            validate_repository(self.repository_root),
        )

    def test_ambiguous_markdown_predecessors_fail_closed(self):
        cases = [
            ("blockquote", "SRC-430", "> quoted text\n"),
            ("indented-code", "SRC-431", "    literal code\n"),
            ("list", "SRC-432", "- list item\n"),
            ("setext", "SRC-433", "Section title\n---\n"),
            ("thematic", "SRC-434", "***\n"),
            ("type-7", "SRC-435", "<kbd>\n"),
        ]
        for name, source_id, predecessor in cases:
            self.write_exhibit(
                name,
                [[source_id]],
                f"{predecessor}### {source_id} — Ambiguous placement\n",
            )

        expected = []
        for name, source_id, predecessor in cases:
            line_number = predecessor.count("\n") + 1
            expected.extend(
                [
                    f"exhibits/{name}/exhibit.json: "
                    "relationships[0].evidence[0]: "
                    f'source ID "{source_id}" is not declared in '
                    f"exhibits/{name}/sources.md",
                    f"exhibits/{name}/sources.md:{line_number}: source declaration "
                    f"{source_id} must be top-level at the start of a Markdown "
                    "block; begin the file or precede it with an ASCII "
                    "space/tab-only blank line",
                ]
            )

        self.assertEqual(expected, validate_repository(self.repository_root))

    def test_nested_cross_blank_openers_fail_closed(self):
        cases = {
            "cdata": ("SRC-460", "<kbd>\n<![CDATA[\n"),
            "comment": ("SRC-461", "<kbd>\n<!--\n"),
            "declaration": ("SRC-462", "<kbd>\n<!DOCTYPE\n"),
            "fence": ("SRC-463", "<kbd>\n```markdown\n"),
            "processing-instruction": ("SRC-464", "<kbd>\n<?target\n"),
            "raw-html": ("SRC-465", "<div>\n<pre>\n"),
        }
        for name in sorted(cases):
            source_id, ambiguous_prefix = cases[name]
            self.write_exhibit(
                name,
                [],
                f"### {source_id} — First manual\n\n"
                f"{ambiguous_prefix}\n"
                f"### {source_id} — Second manual\n",
            )

        self.assertEqual(
            [
                f"exhibits/{name}/sources.md:6: source-like heading {source_id} "
                "is inside an ambiguous Markdown block opened at line 4; "
                "start the block opener at column one after an ASCII space/tab-only "
                "blank line, or at the first line of the file"
                for name, (source_id, _) in sorted(cases.items())
            ],
            validate_repository(self.repository_root),
        )

    def test_indented_openers_after_list_blanks_fail_closed(self):
        cases = {
            "fence": ("SRC-480", "  ```markdown\n"),
            "raw-html": ("SRC-481", "  <pre>\n"),
        }
        for name in sorted(cases):
            source_id, opener = cases[name]
            self.write_exhibit(
                name,
                [],
                f"### {source_id} — First manual\n\n"
                "- list item\n\n"
                f"{opener}\n"
                f"### {source_id} — Second manual\n",
            )

        self.assertEqual(
            [
                f"exhibits/{name}/sources.md:7: source-like heading {source_id} "
                "is inside an ambiguous Markdown block opened at line 5; "
                "start the block opener at column one after an ASCII space/tab-only "
                "blank line, or at the first line of the file"
                for name, (source_id, _) in sorted(cases.items())
            ],
            validate_repository(self.repository_root),
        )

    def test_indented_openers_at_bof_still_suppress_literal_headings(self):
        self.write_exhibit(
            "fence",
            [["SRC-482"]],
            "  ```markdown\n\n### SRC-482 — Literal heading\n",
        )
        self.write_exhibit(
            "raw-html",
            [["SRC-483"]],
            "  <pre>\n\n### SRC-483 — Literal heading\n",
        )

        self.assertEqual(
            [
                "exhibits/fence/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-482" is not declared in exhibits/fence/sources.md',
                "exhibits/raw-html/exhibit.json: relationships[0].evidence[0]: "
                'source ID "SRC-483" is not declared in '
                "exhibits/raw-html/sources.md",
            ],
            validate_repository(self.repository_root),
        )

    def test_closed_ambiguous_blocks_do_not_hide_later_declarations(self):
        self.write_exhibit(
            "fence",
            [["SRC-470"]],
            "Paragraph text\n"
            "```markdown\n"
            "literal content\n"
            "```\n\n"
            "### SRC-470 — Real manual\n",
        )
        self.write_exhibit(
            "raw-html",
            [["SRC-471"]],
            "Paragraph text\n"
            "<pre>\n"
            "literal content\n"
            "</pre>\n\n"
            "### SRC-471 — Real manual\n",
        )

        self.assertEqual([], validate_repository(self.repository_root))

    def test_checked_in_template_and_corpus_are_valid(self):
        self.assertEqual([], validate_repository(REPOSITORY_ROOT))

    def test_duplicate_json_object_keys_are_rejected_before_reference_checks(self):
        cases = {
            "nested": (
                '{"relationships": [{"evidence": ["SRC-404"], '
                '"evidence": ["SRC-001"]}]}'
            ),
            "top-level": (
                '{"relationships": [{"evidence": ["SRC-404"]}], ' '"relationships": []}'
            ),
        }
        for name, metadata in cases.items():
            exhibit_directory = self.repository_root / "exhibits" / name
            exhibit_directory.mkdir(parents=True)
            (exhibit_directory / "exhibit.json").write_text(
                metadata,
                encoding="utf-8",
            )
            (exhibit_directory / "sources.md").write_text(
                "### SRC-001 — Original manual\n",
                encoding="utf-8",
            )

        self.assertEqual(
            [
                "exhibits/nested/exhibit.json: duplicate JSON object key " '"evidence"',
                "exhibits/top-level/exhibit.json: duplicate JSON object key "
                '"relationships"',
            ],
            validate_repository(self.repository_root),
        )

    def test_duplicate_json_key_is_ascii_escaped_in_diagnostic(self):
        cases = {
            "bidi-override": "\u202e",
            "line-separator": "\u2028",
            "lone-surrogate": "\ud800",
            "next-line": "\u0085",
            "paragraph-separator": "\u2029",
            "quote-and-backslash": 'key"\\',
        }
        for name, key in cases.items():
            exhibit_directory = self.repository_root / "exhibits" / name
            exhibit_directory.mkdir(parents=True)
            rendered_key = json.dumps(key)
            (exhibit_directory / "exhibit.json").write_text(
                f"{{{rendered_key}: 1, {rendered_key}: 2}}",
                encoding="utf-8",
            )
            (exhibit_directory / "sources.md").write_text(
                "### SRC-001 — Original manual\n",
                encoding="utf-8",
            )

        errors = validate_repository(self.repository_root)
        self.assertEqual(
            [
                f"exhibits/{name}/exhibit.json: duplicate JSON object key "
                f"{json.dumps(key)}"
                for name, key in sorted(cases.items())
            ],
            errors,
        )
        for error in errors:
            with self.subTest(error=repr(error)):
                self.assertTrue(error.isascii())
                self.assertEqual([error], error.splitlines())
                error.encode("utf-8")

    def test_non_object_metadata_has_stable_diagnostic(self):
        for index, document in enumerate(([], None, "text", 42)):
            exhibit_directory = self.repository_root / "exhibits" / f"case-{index}"
            exhibit_directory.mkdir(parents=True)
            (exhibit_directory / "exhibit.json").write_text(
                json.dumps(document),
                encoding="utf-8",
            )

        self.assertEqual(
            [
                f"exhibits/case-{index}/exhibit.json: "
                "top-level JSON value must be an object"
                for index in range(4)
            ],
            validate_repository(self.repository_root),
        )


if __name__ == "__main__":
    unittest.main()
