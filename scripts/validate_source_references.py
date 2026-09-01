#!/usr/bin/env python3
"""Validate relationship evidence against each exhibit's source ledger."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DECLARATION = re.compile(
    r"^ {0,3}###[ \t]+(SRC-[0-9]+)[ \t]+—[ \t]+\S.*$"
)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _relative_path(repository_root: Path, path: Path) -> str:
    return path.relative_to(repository_root).as_posix()


def _source_declarations(source_text: str) -> list[tuple[str, int]]:
    declarations: list[tuple[str, int]] = []
    fence_character: str | None = None
    fence_length = 0

    for line_number, line in enumerate(source_text.splitlines(), start=1):
        fence_match = FENCE.match(line)
        if fence_character is not None:
            if fence_match:
                marker, remainder = fence_match.groups()
                if (
                    marker[0] == fence_character
                    and len(marker) >= fence_length
                    and not remainder.strip()
                ):
                    fence_character = None
                    fence_length = 0
            continue

        if fence_match:
            marker, _ = fence_match.groups()
            fence_character = marker[0]
            fence_length = len(marker)
            continue

        declaration_match = SOURCE_DECLARATION.match(line)
        if declaration_match:
            declarations.append((declaration_match.group(1), line_number))

    return declarations


def _declared_source_ids(
    repository_root: Path, source_path: Path
) -> tuple[set[str], list[str]]:
    relative_source_path = _relative_path(repository_root, source_path)
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set(), []
    except (OSError, UnicodeError) as error:
        return set(), [f"{relative_source_path}: cannot read source ledger: {error}"]

    first_declaration_lines: dict[str, int] = {}
    errors: list[str] = []
    for source_id, line_number in _source_declarations(source_text):
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

                displayed_source_id = json.dumps(source_id, ensure_ascii=False)
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
