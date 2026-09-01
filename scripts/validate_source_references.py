#!/usr/bin/env python3
"""Validate relationship evidence against each exhibit's formal source ledger.

A declaration uses ``### SRC-NNN — Title`` at column one, starts the title with
a literal letter or number, and begins the file or follows an ASCII
space/tab-only blank line.  This deliberately conservative contract makes
ambiguous Markdown fail closed without implementing a Markdown parser.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECLARATION = re.compile(
    r"^###[ \t]+(SRC-[0-9]{3})[ \t]+—[ \t]+(.*)$"
)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ASCII_BLANK = re.compile(r"^[ \t]*$")
HTML_COMMENT_START = re.compile(r"^ {0,3}<!--")
HTML_PROCESSING_INSTRUCTION_START = re.compile(r"^ {0,3}<\?")
HTML_DECLARATION_START = re.compile(r"^ {0,3}<![A-Z]")
HTML_CDATA_START = re.compile(r"^ {0,3}<!\[CDATA\[")
RAW_HTML_START = re.compile(
    r"^ {0,3}<(pre|script|style|textarea)(?:[ \t>]|$)", re.IGNORECASE
)
RAW_HTML_END = re.compile(
    r"</(?:pre|script|style|textarea)[ \t]*>", re.IGNORECASE
)


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

    normalized_source_text = source_text.replace("\r\n", "\n").replace("\r", "\n")
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
            fence_is_ambiguous = not _is_formal_block_boundary(
                source_lines, line_number
            )
            continue

        if HTML_COMMENT_START.match(line):
            if "-->" not in line:
                html_end = re.compile(r"-->")
                html_opener_line = line_number
                html_is_ambiguous = not _is_formal_block_boundary(
                    source_lines, line_number
                )
            continue

        if HTML_PROCESSING_INSTRUCTION_START.match(line):
            if "?>" not in line:
                html_end = re.compile(r"\?>")
                html_opener_line = line_number
                html_is_ambiguous = not _is_formal_block_boundary(
                    source_lines, line_number
                )
            continue

        if HTML_CDATA_START.match(line):
            if "]]>" not in line:
                html_end = re.compile(r"\]\]>")
                html_opener_line = line_number
                html_is_ambiguous = not _is_formal_block_boundary(
                    source_lines, line_number
                )
            continue

        if HTML_DECLARATION_START.match(line):
            if ">" not in line:
                html_end = re.compile(r">")
                html_opener_line = line_number
                html_is_ambiguous = not _is_formal_block_boundary(
                    source_lines, line_number
                )
            continue

        raw_html_match = RAW_HTML_START.match(line)
        if raw_html_match:
            if not RAW_HTML_END.search(line):
                html_end = RAW_HTML_END
                html_opener_line = line_number
                html_is_ambiguous = not _is_formal_block_boundary(
                    source_lines, line_number
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
) -> tuple[set[str], list[str]]:
    relative_source_path = _relative_path(repository_root, source_path)
    if source_path.is_symlink():
        return set(), [
            f"{relative_source_path}: symbolic-link source ledger is not allowed"
        ]
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set(), []
    except (OSError, UnicodeError) as error:
        return set(), [f"{relative_source_path}: cannot read source ledger: {error}"]

    first_declaration_lines: dict[str, int] = {}
    errors: list[str] = []
    (
        declarations,
        misplaced_declarations,
        invalid_title_declarations,
        ambiguous_block_declarations,
    ) = _source_declarations(source_text)
    for source_id, line_number in misplaced_declarations:
        errors.append(
            f"{relative_source_path}:{line_number}: source declaration {source_id} "
            "must be top-level at the start of a Markdown block; begin the file or "
            "precede it with an ASCII space/tab-only blank line"
        )

    for source_id, line_number in invalid_title_declarations:
        errors.append(
            f"{relative_source_path}:{line_number}: source declaration {source_id} "
            "title must begin with a literal letter or number; Markdown/HTML-"
            "prefixed titles are not supported"
        )

    for source_id, line_number, opener_line in ambiguous_block_declarations:
        errors.append(
            f"{relative_source_path}:{line_number}: source-like heading {source_id} "
            f"is inside an ambiguous Markdown block opened at line {opener_line}; "
            "precede the block opener with an ASCII space/tab-only blank line"
        )

    for source_id, line_number in declarations:
        first_line = first_declaration_lines.get(source_id)
        if first_line is None:
            first_declaration_lines[source_id] = line_number
            continue

        errors.append(
            f"{relative_source_path}:{line_number}: duplicate source ID {source_id}; "
            f"first declared at line {first_line}"
        )

    return set(first_declaration_lines), errors


def validate_repository(repository_root: Path) -> list[str]:
    """Return stable diagnostics for invalid source ledgers and references."""

    repository_root = repository_root.resolve()
    exhibits_root = repository_root / "exhibits"
    exhibit_paths = sorted(
        exhibits_root.rglob("exhibit.json"),
        key=lambda path: _relative_path(repository_root, path),
    )
    errors: list[str] = []

    for exhibit_path in exhibit_paths:
        relative_exhibit_path = _relative_path(repository_root, exhibit_path)
        try:
            document = json.loads(exhibit_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(
                f"{relative_exhibit_path}:{error.lineno}:{error.colno}: invalid JSON: "
                f"{error.msg}"
            )
            continue
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative_exhibit_path}: cannot read metadata: {error}")
            continue

        if not isinstance(document, dict):
            errors.append(
                f"{relative_exhibit_path}: top-level JSON value must be an object"
            )
            continue

        source_path = exhibit_path.with_name("sources.md")
        declared_source_ids, source_errors = _declared_source_ids(
            repository_root, source_path
        )
        errors.extend(source_errors)
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
                errors.append(
                    f"{relative_exhibit_path}: "
                    f"relationships[{relationship_index}].evidence[{evidence_index}]: "
                    f"source ID {displayed_source_id} is not declared in "
                    f"{relative_source_path}"
                )

    return sorted(errors)


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
