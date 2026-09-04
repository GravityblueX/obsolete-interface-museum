#!/usr/bin/env python3
"""Validate the filesystem contract of every direct exhibit directory."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "physical.md",
    "electrical.md",
    "protocol.md",
    "host-integration.md",
    "experiment.md",
    "descendants.md",
    "sources.md",
    "exhibit.json",
)

# ``exhibits/_template`` is the repository's documented scaffold.  Its JSON ID
# is ``template`` because exhibit IDs use the schema's lowercase slug syntax,
# while the leading underscore distinguishes the scaffold from real exhibits.
EXPECTED_ID_OVERRIDES = {"_template": "template"}

# ``FILE_ATTRIBUTE_REPARSE_POINT`` from WinNT.h.  ``stat`` only exposes the
# named constant on Windows, while keeping the numeric value here lets the
# policy be tested on every supported runner.
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


@dataclass(frozen=True)
class _Diagnostic:
    path: str
    kind: int
    message: str


class _DuplicateKeyError(ValueError):
    pass


def _is_reparse_point(path_status: os.stat_result) -> bool:
    return bool(
        getattr(path_status, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT
    )


def _relative_path(repository_root: Path, path: Path) -> str:
    return path.relative_to(repository_root).as_posix()


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise _DuplicateKeyError(f"duplicate object key {key!r}")
        document[key] = value
    return document


def _reject_json_constant(constant: str) -> object:
    raise ValueError(f"non-standard JSON constant {constant!r}")


def _nested_layout_diagnostics(
    repository_root: Path,
    exhibit_directory: Path,
) -> list[_Diagnostic]:
    diagnostics: list[_Diagnostic] = []

    def record_walk_error(error: OSError) -> None:
        error_path = Path(error.filename) if error.filename else exhibit_directory
        try:
            relative_error_path = _relative_path(repository_root, error_path)
        except ValueError:
            relative_error_path = _relative_path(repository_root, exhibit_directory)
        diagnostics.append(
            _Diagnostic(
                relative_error_path,
                4,
                f"{relative_error_path}: cannot inspect nested exhibit layout: {error}",
            )
        )

    for directory, directory_names, file_names in os.walk(
        exhibit_directory,
        topdown=True,
        onerror=record_walk_error,
        followlinks=False,
    ):
        directory_names.sort()
        file_names.sort()
        current_directory = Path(directory)

        for directory_name in directory_names:
            nested_directory = current_directory / directory_name
            relative_nested_directory = _relative_path(
                repository_root, nested_directory
            )
            try:
                nested_status = nested_directory.lstat()
            except OSError as error:
                diagnostics.append(
                    _Diagnostic(
                        relative_nested_directory,
                        4,
                        f"{relative_nested_directory}: cannot inspect nested "
                        f"exhibit directory: {error}",
                    )
                )
                continue

            # A required root entry with a directory-like mode is diagnosed by
            # the exact required-file check below.  Do not descend into it or
            # emit a second, less specific nested-layout diagnostic here.
            if directory_name in REQUIRED_FILES:
                continue

            if stat.S_ISLNK(nested_status.st_mode):
                diagnostics.append(
                    _Diagnostic(
                        relative_nested_directory,
                        4,
                        f"{relative_nested_directory}: symbolic-link nested "
                        "exhibit directory is not allowed",
                    )
                )
                continue
            if _is_reparse_point(nested_status):
                diagnostics.append(
                    _Diagnostic(
                        relative_nested_directory,
                        4,
                        f"{relative_nested_directory}: reparse-point nested "
                        "exhibit directory is not allowed",
                    )
                )
                continue

            diagnostics.append(
                _Diagnostic(
                    relative_nested_directory,
                    4,
                    f"{relative_nested_directory}: nested exhibit directory is not "
                    "allowed; exact layout permits no subdirectories",
                )
            )

        # ``os.walk(..., followlinks=False)`` still follows Windows junctions.
        # Mutating this top-down list prevents traversal after lstat.  Exact
        # layouts permit no subdirectories, so even ordinary directories are
        # diagnosed and pruned here.
        directory_names[:] = []
        for file_name in file_names:
            if file_name in REQUIRED_FILES:
                continue
            unexpected_file = current_directory / file_name
            relative_unexpected_file = _relative_path(repository_root, unexpected_file)
            diagnostics.append(
                _Diagnostic(
                    relative_unexpected_file,
                    4,
                    f"{relative_unexpected_file}: unexpected exhibit file; "
                    "exact layout allows only the nine required root files",
                )
            )

    return diagnostics


def _validate_metadata(
    repository_root: Path,
    exhibit_directory: Path,
    metadata_path: Path,
    diagnostics: list[_Diagnostic],
) -> None:
    relative_metadata_path = _relative_path(repository_root, metadata_path)
    try:
        source = metadata_path.read_text(encoding="utf-8")
        document = json.loads(
            source,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                2,
                f"{relative_metadata_path}:{error.lineno}:{error.colno}: "
                f"invalid JSON: {error.msg}",
            )
        )
        return
    except (_DuplicateKeyError, ValueError) as error:
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                2,
                f"{relative_metadata_path}: invalid JSON: {error}",
            )
        )
        return
    except (OSError, UnicodeError) as error:
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                2,
                f"{relative_metadata_path}: cannot read metadata: {error}",
            )
        )
        return

    if not isinstance(document, dict):
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                3,
                f"{relative_metadata_path}: top-level JSON value must be an object",
            )
        )
        return

    expected_id = EXPECTED_ID_OVERRIDES.get(
        exhibit_directory.name, exhibit_directory.name
    )
    exhibit_id = document.get("id")
    if not isinstance(exhibit_id, str):
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                3,
                f"{relative_metadata_path}: id must be the string "
                f"{json.dumps(expected_id)} to match its exhibit directory",
            )
        )
    elif exhibit_id != expected_id:
        diagnostics.append(
            _Diagnostic(
                relative_metadata_path,
                3,
                f"{relative_metadata_path}: id {json.dumps(exhibit_id)} does not "
                f"match exhibit directory {json.dumps(exhibit_directory.name)} "
                f"(expected {json.dumps(expected_id)})",
            )
        )


def validate_repository(repository_root: Path) -> list[str]:
    """Return stable diagnostics for invalid exhibit layouts."""

    repository_root = repository_root.resolve()
    exhibits_root = repository_root / "exhibits"
    try:
        exhibits_status = exhibits_root.lstat()
    except FileNotFoundError:
        return ["exhibits: required exhibits directory is missing"]
    except OSError as error:
        return [f"exhibits: cannot inspect exhibits directory: {error}"]

    if stat.S_ISLNK(exhibits_status.st_mode):
        return ["exhibits: symbolic-link exhibits directory is not allowed"]
    if _is_reparse_point(exhibits_status):
        return ["exhibits: reparse-point exhibits directory is not allowed"]
    if not stat.S_ISDIR(exhibits_status.st_mode):
        return ["exhibits: required exhibits path must be a directory"]

    diagnostics: list[_Diagnostic] = []
    try:
        direct_entries = sorted(exhibits_root.iterdir(), key=lambda path: path.name)
    except OSError as error:
        return [f"exhibits: cannot enumerate exhibits directory: {error}"]

    exhibit_directories: list[Path] = []
    for entry in direct_entries:
        try:
            entry_status = entry.lstat()
        except OSError as error:
            relative_entry = _relative_path(repository_root, entry)
            diagnostics.append(
                _Diagnostic(
                    relative_entry,
                    0,
                    f"{relative_entry}: cannot inspect direct exhibit entry: {error}",
                )
            )
            continue

        relative_entry = _relative_path(repository_root, entry)
        if stat.S_ISLNK(entry_status.st_mode):
            diagnostics.append(
                _Diagnostic(
                    relative_entry,
                    0,
                    f"{relative_entry}: symbolic-link direct exhibit entry is not allowed",
                )
            )
        elif _is_reparse_point(entry_status):
            diagnostics.append(
                _Diagnostic(
                    relative_entry,
                    0,
                    f"{relative_entry}: reparse-point direct exhibit entry is not allowed",
                )
            )
        elif stat.S_ISDIR(entry_status.st_mode):
            exhibit_directories.append(entry)

    for exhibit_directory in exhibit_directories:
        for required_name in REQUIRED_FILES:
            required_path = exhibit_directory / required_name
            relative_required_path = _relative_path(repository_root, required_path)
            try:
                required_status = required_path.lstat()
            except FileNotFoundError:
                diagnostics.append(
                    _Diagnostic(
                        relative_required_path,
                        0,
                        f"{relative_required_path}: required exhibit file is missing",
                    )
                )
                continue
            except OSError as error:
                diagnostics.append(
                    _Diagnostic(
                        relative_required_path,
                        0,
                        f"{relative_required_path}: cannot inspect required exhibit file: {error}",
                    )
                )
                continue

            if stat.S_ISLNK(required_status.st_mode):
                diagnostics.append(
                    _Diagnostic(
                        relative_required_path,
                        1,
                        f"{relative_required_path}: symbolic-link exhibit file is not allowed",
                    )
                )
                continue
            if _is_reparse_point(required_status):
                diagnostics.append(
                    _Diagnostic(
                        relative_required_path,
                        1,
                        f"{relative_required_path}: reparse-point exhibit file is "
                        "not allowed",
                    )
                )
                continue
            if not stat.S_ISREG(required_status.st_mode):
                diagnostics.append(
                    _Diagnostic(
                        relative_required_path,
                        1,
                        f"{relative_required_path}: required exhibit path must be a regular file",
                    )
                )
                continue

            if required_name == "exhibit.json":
                _validate_metadata(
                    repository_root,
                    exhibit_directory,
                    required_path,
                    diagnostics,
                )

        diagnostics.extend(
            _nested_layout_diagnostics(
                repository_root,
                exhibit_directory,
            )
        )

    ordered_diagnostics = sorted(
        diagnostics,
        key=lambda diagnostic: (
            diagnostic.path,
            diagnostic.kind,
            diagnostic.message,
        ),
    )
    return [diagnostic.message for diagnostic in ordered_diagnostics]


def main() -> int:
    errors = validate_repository(REPOSITORY_ROOT)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(
            f"Exhibit-layout validation failed with {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1

    exhibit_count = sum(
        1
        for path in (REPOSITORY_ROOT / "exhibits").iterdir()
        if path.is_dir() and not path.is_symlink()
    )
    print(f"Validated layout of {exhibit_count} exhibit directory/directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
