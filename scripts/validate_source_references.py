#!/usr/bin/env python3
"""Validate relationship evidence against each exhibit's formal source ledger.

A declaration starts at column one and must be the first line of the file or
follow an ASCII space/tab-only blank line.  This deliberately conservative
contract makes ambiguous Markdown placement fail closed without attempting to
implement a complete Markdown block parser.
"""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECLARATION = re.compile(
    r"^###[ \t]+(SRC-[0-9]{3})[ \t]+—[ \t]+([^\n]+)$"
)
INLINE_HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)")
CLOSING_HEADING_HASHES = re.compile(r"(?:^|[ \t]+)#+[ \t]*$")
TAG_NAME = r"[A-Za-z][A-Za-z0-9-]*"
ATTRIBUTE_NAME = r"[A-Za-z_:][A-Za-z0-9_.:-]*"
ATTRIBUTE_VALUE = r'''(?:[^ "'=<>`]+|'[^']*'|"[^"]*")'''
ATTRIBUTE = rf"(?:[ \t]+{ATTRIBUTE_NAME}(?:[ \t]*=[ \t]*{ATTRIBUTE_VALUE})?)"
INLINE_HTML_TAG = re.compile(
    rf"</?{TAG_NAME}(?:{ATTRIBUTE})*[ \t]*/?>"
)
INLINE_LINK = re.compile(
    r"!?\[([^\]\n]*)\]\((?:[^()\n]|\([^()\n]*\))*\)"
)
REFERENCE_LINK = re.compile(r"!?\[([^\]\n]*)\]\[[^\]\n]*\]")
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


def _source_declaration(line: str) -> str | None:
    match = SOURCE_DECLARATION.match(line)
    if match is None:
        return None

    source_id, title = match.groups()
    visible_title = INLINE_HTML_COMMENT.sub("", title)
    visible_title = INLINE_LINK.sub(lambda link: link.group(1), visible_title)
    visible_title = REFERENCE_LINK.sub(lambda link: link.group(1), visible_title)
    visible_title = INLINE_HTML_TAG.sub("", visible_title)
    visible_title = unescape(visible_title)
    visible_title = CLOSING_HEADING_HASHES.sub("", visible_title)
    if not any(character.isalnum() for character in visible_title):
        return None
    return source_id


def _source_declarations(
    source_text: str,
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    declarations: list[tuple[str, int]] = []
    misplaced_declarations: list[tuple[str, int]] = []
    fence_character: str | None = None
    fence_length = 0
    html_end: re.Pattern[str] | None = None

    normalized_source_text = source_text.replace("\r\n", "\n").replace("\r", "\n")
    source_lines = normalized_source_text.split("\n")
    for line_number, line in enumerate(source_lines, start=1):
        fence_match = _fence_match(line)
        if fence_character is not None:
            if fence_match:
                marker, remainder = fence_match.groups()
                if (
                    marker[0] == fence_character
                    and len(marker) >= fence_length
                    and ASCII_BLANK.fullmatch(remainder)
                ):
                    fence_character = None
                    fence_length = 0
            continue

        if html_end is not None:
            if html_end.search(line):
                html_end = None
            continue

        if fence_match:
            marker, _ = fence_match.groups()
            fence_character = marker[0]
            fence_length = len(marker)
            continue

        if HTML_COMMENT_START.match(line):
            if "-->" not in line:
                html_end = re.compile(r"-->")
            continue

        if HTML_PROCESSING_INSTRUCTION_START.match(line):
            if "?>" not in line:
                html_end = re.compile(r"\?>")
            continue

        if HTML_CDATA_START.match(line):
            if "]]>" not in line:
                html_end = re.compile(r"\]\]>")
            continue

        if HTML_DECLARATION_START.match(line):
            if ">" not in line:
                html_end = re.compile(r">")
            continue

        raw_html_match = RAW_HTML_START.match(line)
        if raw_html_match:
            if not RAW_HTML_END.search(line):
                html_end = RAW_HTML_END
            continue

        source_id = _source_declaration(line)
        if source_id is not None:
            previous_line_is_blank = line_number == 1 or bool(
                ASCII_BLANK.fullmatch(source_lines[line_number - 2])
            )
            destination = (
                declarations if previous_line_is_blank else misplaced_declarations
            )
            destination.append((source_id, line_number))

    return declarations, misplaced_declarations


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
    declarations, misplaced_declarations = _source_declarations(source_text)
    for source_id, line_number in misplaced_declarations:
        errors.append(
            f"{relative_source_path}:{line_number}: source declaration {source_id} "
            "must be top-level at the start of a Markdown block; begin the file or "
            "precede it with an ASCII space/tab-only blank line"
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
    """Return stable diagnostics for dangling and duplicate source IDs."""

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
