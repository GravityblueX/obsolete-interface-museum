#!/usr/bin/env python3
"""Validate relationship evidence against each exhibit's formal source ledger.

A declaration uses ``### SRC-NNN — Title`` at column one, starts the title with
a literal letter or number, and begins the file or follows an ASCII
space/tab-only blank line.  This deliberately conservative contract makes
ambiguous Markdown fail closed without implementing a Markdown parser.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECLARATION = re.compile(r"^###[ \t]+(SRC-[0-9]{3})[ \t]+—[ \t]+(.*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ASCII_BLANK = re.compile(r"^[ \t]*$")
HTML_COMMENT_START = re.compile(r"^ {0,3}<!--")
HTML_PROCESSING_INSTRUCTION_START = re.compile(r"^ {0,3}<\?")
HTML_DECLARATION_START = re.compile(r"^ {0,3}<![A-Z]")
HTML_CDATA_START = re.compile(r"^ {0,3}<!\[CDATA\[")
RAW_HTML_START = re.compile(
    r"^ {0,3}<(pre|script|style|textarea)(?:[ \t\v\f>]|$)",
    re.IGNORECASE | re.ASCII,
)
RAW_HTML_END = re.compile(r"</(?:pre|script|style|textarea)>", re.IGNORECASE | re.ASCII)


@dataclass(frozen=True)
class _Diagnostic:
    path: str
    location: tuple[int, ...]
    kind: int
    message: str


class _DuplicateJsonKeyError(ValueError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"duplicate JSON object key {key!r}")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise _DuplicateJsonKeyError(key)
        document[key] = value
    return document


def _relative_path(repository_root: Path, path: Path) -> str:
    return path.relative_to(repository_root).as_posix()


def _fence_match(line: str) -> re.Match[str] | None:
    match = FENCE.match(line)
    if match is None:
        return None
    marker, remainder = match.groups()
    if marker[0] == "`" and "`" in remainder:
        return None
    return match


def _source_declaration(line: str) -> tuple[str, bool] | None:
    match = SOURCE_DECLARATION.match(line)
    if match is None:
        return None

    source_id, title = match.groups()
    return source_id, bool(title) and title[0].isalnum()


def _is_formal_block_boundary(source_lines: list[str], line_number: int) -> bool:
    return line_number == 1 or bool(
        ASCII_BLANK.fullmatch(source_lines[line_number - 2])
    )


def _is_unambiguous_block_opener(
    source_lines: list[str], line_number: int, line: str
) -> bool:
    if line_number == 1:
        return True
    return not line.startswith(" ") and _is_formal_block_boundary(
        source_lines, line_number
    )


def _source_declarations(
    source_text: str,
) -> tuple[
    list[tuple[str, int]],
    list[tuple[str, int]],
    list[tuple[str, int]],
    list[tuple[str, int, int]],
]:
    declarations: list[tuple[str, int]] = []
    misplaced_declarations: list[tuple[str, int]] = []
    invalid_title_declarations: list[tuple[str, int]] = []
    ambiguous_block_declarations: list[tuple[str, int, int]] = []
    fence_character: str | None = None
    fence_length = 0
    fence_opener_line = 0
    fence_is_ambiguous = False
    html_end: re.Pattern[str] | None = None
    html_opener_line = 0
    html_is_ambiguous = False

    normalized_source_text = source_text.removeprefix("\ufeff")
    normalized_source_text = normalized_source_text.replace("\r\n", "\n").replace(
        "\r", "\n"
    )
    source_lines = normalized_source_text.split("\n")
    for line_number, line in enumerate(source_lines, start=1):
        fence_match = _fence_match(line)
        if fence_character is not None:
            source_declaration = _source_declaration(line)
            if fence_is_ambiguous and source_declaration is not None:
                source_id, _ = source_declaration
                ambiguous_block_declarations.append(
                    (source_id, line_number, fence_opener_line)
                )
            if fence_match:
                marker, remainder = fence_match.groups()
                if (
                    marker[0] == fence_character
                    and len(marker) >= fence_length
                    and ASCII_BLANK.fullmatch(remainder)
                ):
                    fence_character = None
                    fence_length = 0
                    fence_opener_line = 0
                    fence_is_ambiguous = False
            continue

        if html_end is not None:
            source_declaration = _source_declaration(line)
            if html_is_ambiguous and source_declaration is not None:
                source_id, _ = source_declaration
                ambiguous_block_declarations.append(
                    (source_id, line_number, html_opener_line)
                )
            if html_end.search(line):
                html_end = None
                html_opener_line = 0
                html_is_ambiguous = False
            continue

        if fence_match:
            marker, _ = fence_match.groups()
            fence_character = marker[0]
            fence_length = len(marker)
            fence_opener_line = line_number
            fence_is_ambiguous = not _is_unambiguous_block_opener(
                source_lines, line_number, line
            )
            continue

        if HTML_COMMENT_START.match(line):
            if "-->" not in line:
                html_end = re.compile(r"-->")
                html_opener_line = line_number
                html_is_ambiguous = not _is_unambiguous_block_opener(
                    source_lines, line_number, line
                )
            continue

        if HTML_PROCESSING_INSTRUCTION_START.match(line):
            if "?>" not in line:
                html_end = re.compile(r"\?>")
                html_opener_line = line_number
                html_is_ambiguous = not _is_unambiguous_block_opener(
                    source_lines, line_number, line
                )
            continue

        if HTML_CDATA_START.match(line):
            if "]]>" not in line:
                html_end = re.compile(r"\]\]>")
                html_opener_line = line_number
                html_is_ambiguous = not _is_unambiguous_block_opener(
                    source_lines, line_number, line
                )
            continue

        if HTML_DECLARATION_START.match(line):
            if ">" not in line:
                html_end = re.compile(r">")
                html_opener_line = line_number
                html_is_ambiguous = not _is_unambiguous_block_opener(
                    source_lines, line_number, line
                )
            continue

        raw_html_match = RAW_HTML_START.match(line)
        if raw_html_match:
            if not RAW_HTML_END.search(line):
                html_end = RAW_HTML_END
                html_opener_line = line_number
                html_is_ambiguous = not _is_unambiguous_block_opener(
                    source_lines, line_number, line
                )
            continue

        source_declaration = _source_declaration(line)
        if source_declaration is not None:
            source_id, title_is_valid = source_declaration
            previous_line_is_blank = _is_formal_block_boundary(
                source_lines, line_number
            )
            if not previous_line_is_blank:
                misplaced_declarations.append((source_id, line_number))
            if not title_is_valid:
                invalid_title_declarations.append((source_id, line_number))
            if previous_line_is_blank and title_is_valid:
                declarations.append((source_id, line_number))

    return (
        declarations,
        misplaced_declarations,
        invalid_title_declarations,
        ambiguous_block_declarations,
    )


def _declared_source_ids(
    repository_root: Path, source_path: Path
) -> tuple[set[str], list[_Diagnostic]]:
    relative_source_path = _relative_path(repository_root, source_path)
    if source_path.is_symlink():
        return set(), [
            _Diagnostic(
                relative_source_path,
                (),
                0,
                f"{relative_source_path}: symbolic-link source ledger is not allowed",
            )
        ]
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set(), []
    except (OSError, UnicodeError) as error:
        return set(), [
            _Diagnostic(
                relative_source_path,
                (),
                0,
                f"{relative_source_path}: cannot read source ledger: {error}",
            )
        ]

    first_declaration_lines: dict[str, int] = {}
    diagnostics: list[_Diagnostic] = []
    (
        declarations,
        misplaced_declarations,
        invalid_title_declarations,
        ambiguous_block_declarations,
    ) = _source_declarations(source_text)
    for source_id, line_number in misplaced_declarations:
        diagnostics.append(
            _Diagnostic(
                relative_source_path,
                (line_number,),
                0,
                f"{relative_source_path}:{line_number}: source declaration "
                f"{source_id} must be top-level at the start of a Markdown block; "
                "begin the file or precede it with an ASCII space/tab-only blank "
                "line",
            )
        )

    for source_id, line_number in invalid_title_declarations:
        diagnostics.append(
            _Diagnostic(
                relative_source_path,
                (line_number,),
                1,
                f"{relative_source_path}:{line_number}: source declaration "
                f"{source_id} title must begin with a literal letter or number; "
                "Markdown/HTML-prefixed titles are not supported",
            )
        )

    for source_id, line_number, opener_line in ambiguous_block_declarations:
        diagnostics.append(
            _Diagnostic(
                relative_source_path,
                (line_number,),
                2,
                f"{relative_source_path}:{line_number}: source-like heading "
                f"{source_id} is inside an ambiguous Markdown block opened at "
                f"line {opener_line}; start the block opener at column one after "
                "an ASCII space/tab-only blank line, or at the first line of the "
                "file",
            )
        )

    for source_id, line_number in declarations:
        first_line = first_declaration_lines.get(source_id)
        if first_line is None:
            first_declaration_lines[source_id] = line_number
            continue

        diagnostics.append(
            _Diagnostic(
                relative_source_path,
                (line_number,),
                3,
                f"{relative_source_path}:{line_number}: duplicate source ID "
                f"{source_id}; first declared at line {first_line}",
            )
        )

    return set(first_declaration_lines), diagnostics


def validate_repository(repository_root: Path) -> list[str]:
    """Return stable diagnostics for invalid source ledgers and references."""

    repository_root = repository_root.resolve()
    exhibits_root = repository_root / "exhibits"
    exhibit_paths = sorted(
        exhibits_root.rglob("exhibit.json"),
        key=lambda path: _relative_path(repository_root, path),
    )
    diagnostics: list[_Diagnostic] = []

    for exhibit_path in exhibit_paths:
        relative_exhibit_path = _relative_path(repository_root, exhibit_path)
        try:
            document = json.loads(
                exhibit_path.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_json_object,
            )
        except _DuplicateJsonKeyError as error:
            diagnostics.append(
                _Diagnostic(
                    relative_exhibit_path,
                    (),
                    0,
                    f"{relative_exhibit_path}: duplicate JSON object key "
                    f"{json.dumps(error.key)}",
                )
            )
            continue
        except json.JSONDecodeError as error:
            diagnostics.append(
                _Diagnostic(
                    relative_exhibit_path,
                    (),
                    0,
                    f"{relative_exhibit_path}:{error.lineno}:{error.colno}: "
                    f"invalid JSON: {error.msg}",
                )
            )
            continue
        except (OSError, UnicodeError) as error:
            diagnostics.append(
                _Diagnostic(
                    relative_exhibit_path,
                    (),
                    0,
                    f"{relative_exhibit_path}: cannot read metadata: {error}",
                )
            )
            continue

        if not isinstance(document, dict):
            diagnostics.append(
                _Diagnostic(
                    relative_exhibit_path,
                    (),
                    0,
                    f"{relative_exhibit_path}: top-level JSON value must be an "
                    "object",
                )
            )
            continue

        source_path = exhibit_path.with_name("sources.md")
        declared_source_ids, source_errors = _declared_source_ids(
            repository_root, source_path
        )
        diagnostics.extend(source_errors)
        relative_source_path = _relative_path(repository_root, source_path)

        relationships = document.get("relationships", [])
        if not isinstance(relationships, list):
            continue

        for relationship_index, relationship in enumerate(relationships):
            if not isinstance(relationship, dict):
                continue
            evidence = relationship.get("evidence", [])
            if not isinstance(evidence, list):
                continue

            for evidence_index, source_id in enumerate(evidence):
                if not isinstance(source_id, str):
                    continue
                if source_id in declared_source_ids:
                    continue

                displayed_source_id = json.dumps(source_id)
                diagnostics.append(
                    _Diagnostic(
                        relative_exhibit_path,
                        (relationship_index, evidence_index),
                        1,
                        f"{relative_exhibit_path}: relationships["
                        f"{relationship_index}].evidence[{evidence_index}]: "
                        f"source ID {displayed_source_id} is not declared in "
                        f"{relative_source_path}",
                    )
                )

    ordered_diagnostics = sorted(
        diagnostics,
        key=lambda diagnostic: (
            diagnostic.path,
            diagnostic.location,
            diagnostic.kind,
        ),
    )
    return [diagnostic.message for diagnostic in ordered_diagnostics]


def main() -> int:
    errors = validate_repository(REPOSITORY_ROOT)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(
            f"Source-reference validation failed with {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1

    exhibit_count = len(list((REPOSITORY_ROOT / "exhibits").rglob("exhibit.json")))
    print(f"Validated source references in {exhibit_count} exhibit metadata file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
