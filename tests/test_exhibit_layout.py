import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.validate_exhibit_layout import REQUIRED_FILES, validate_repository


class ExhibitLayoutValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        # The validator canonicalizes its root before enumerating entries.
        # Resolve the fixture root too so path-sensitive mocks stay valid when
        # a hosted runner's temporary directory contains an indirection.
        self.repository_root = Path(self.temporary_directory.name).resolve()
        self.junction_paths = []
        (self.repository_root / "exhibits").mkdir()

    def tearDown(self):
        for junction_path in reversed(self.junction_paths):
            if os.path.lexists(junction_path):
                junction_path.rmdir()
        self.temporary_directory.cleanup()

    def create_windows_junction(self, junction_path, target_path):
        if os.name != "nt":
            self.skipTest("NTFS junctions are only available on Windows")

        result = subprocess.run(
            [
                "cmd.exe",
                "/d",
                "/c",
                "mklink",
                "/J",
                str(junction_path),
                str(target_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"cannot create junction: {result.stdout}{result.stderr}",
        )
        self.junction_paths.append(junction_path)

    def write_valid_exhibit(self, name="serial", exhibit_id=None):
        exhibit_directory = self.repository_root / "exhibits" / name
        exhibit_directory.mkdir()
        for required_name in REQUIRED_FILES:
            required_path = exhibit_directory / required_name
            if required_name == "exhibit.json":
                required_path.write_text(
                    json.dumps({"id": exhibit_id or name}),
                    encoding="utf-8",
                )
            else:
                required_path.write_text(f"# {required_name}\n", encoding="utf-8")
        return exhibit_directory

    def test_required_file_contract_is_exact(self):
        self.assertEqual(
            (
                "README.md",
                "physical.md",
                "electrical.md",
                "protocol.md",
                "host-integration.md",
                "experiment.md",
                "descendants.md",
                "sources.md",
                "exhibit.json",
            ),
            REQUIRED_FILES,
        )

    def test_readme_structure_documents_exact_required_file_contract(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        structure_start = readme.index("## 每个展品的结构")
        structure_end = readme.index("## 第一批展品", structure_start)
        documented_structure = readme[structure_start:structure_end]
        documented_files = tuple(
            line[4:].split("#", 1)[0].strip()
            for line in documented_structure.splitlines()
            if line.startswith(("├── ", "└── "))
        )

        self.assertEqual(REQUIRED_FILES, documented_files)

    def test_direct_directory_without_manifest_cannot_hide(self):
        exhibit_directory = self.write_valid_exhibit("manifestless")
        (exhibit_directory / "exhibit.json").unlink()

        self.assertEqual(
            ["exhibits/manifestless/exhibit.json: required exhibit file is " "missing"],
            validate_repository(self.repository_root),
        )

    def test_missing_companion_file_is_rejected(self):
        exhibit_directory = self.write_valid_exhibit()
        (exhibit_directory / "protocol.md").unlink()

        self.assertEqual(
            ["exhibits/serial/protocol.md: required exhibit file is missing"],
            validate_repository(self.repository_root),
        )

    def test_non_regular_companion_path_is_rejected(self):
        exhibit_directory = self.write_valid_exhibit()
        readme_path = exhibit_directory / "README.md"
        readme_path.unlink()
        readme_path.mkdir()

        self.assertEqual(
            [
                "exhibits/serial/README.md: required exhibit path must be a "
                "regular file"
            ],
            validate_repository(self.repository_root),
        )

    def test_extra_root_file_is_rejected(self):
        exhibit_directory = self.write_valid_exhibit()
        (exhibit_directory / "notes.md").write_text("# Notes\n", encoding="utf-8")

        self.assertEqual(
            [
                "exhibits/serial/notes.md: unexpected exhibit file; exact layout "
                "allows only the nine required root files"
            ],
            validate_repository(self.repository_root),
        )

    def test_any_nested_directory_is_rejected_without_descending(self):
        exhibit_directory = self.write_valid_exhibit()
        nested_directory = exhibit_directory / "draft" / "revision"
        nested_directory.mkdir(parents=True)
        (nested_directory / "notes.txt").write_text("hidden\n", encoding="utf-8")

        self.assertEqual(
            [
                "exhibits/serial/draft: nested exhibit directory is not allowed; "
                "exact layout permits no subdirectories"
            ],
            validate_repository(self.repository_root),
        )

    def test_regular_mode_reparse_companion_path_is_rejected(self):
        exhibit_directory = self.write_valid_exhibit()
        physical_path = exhibit_directory / "physical.md"
        original_lstat = Path.lstat

        def reports_physical_file_as_regular_reparse_point(path):
            result = original_lstat(path)
            if path == physical_path:
                return mock.Mock(
                    st_mode=stat.S_IFREG | 0o644,
                    st_file_attributes=0x0400,
                )
            return result

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_physical_file_as_regular_reparse_point,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            [
                "exhibits/serial/physical.md: reparse-point exhibit file is not "
                "allowed"
            ],
            errors,
        )

    def test_metadata_id_must_match_directory_name(self):
        self.write_valid_exhibit("serial", exhibit_id="parallel")

        self.assertEqual(
            [
                'exhibits/serial/exhibit.json: id "parallel" does not match '
                'exhibit directory "serial" (expected "serial")'
            ],
            validate_repository(self.repository_root),
        )

    def test_template_has_the_documented_id_exception_only(self):
        self.write_valid_exhibit("_template", exhibit_id="template")
        self.assertEqual([], validate_repository(self.repository_root))

        second_template = self.repository_root / "exhibits" / "_template-copy"
        second_template.mkdir()
        for required_name in REQUIRED_FILES:
            source = self.repository_root / "exhibits" / "_template" / required_name
            (second_template / required_name).write_bytes(source.read_bytes())

        self.assertEqual(
            [
                'exhibits/_template-copy/exhibit.json: id "template" does not '
                'match exhibit directory "_template-copy" '
                '(expected "_template-copy")'
            ],
            validate_repository(self.repository_root),
        )

    def test_invalid_and_non_standard_json_are_rejected(self):
        malformed = self.write_valid_exhibit("malformed")
        duplicate = self.write_valid_exhibit("duplicate")
        non_standard = self.write_valid_exhibit("non-standard")
        (malformed / "exhibit.json").write_text(
            '{\n  "id": "malformed",\n', encoding="utf-8"
        )
        (duplicate / "exhibit.json").write_text(
            '{"id":"duplicate","id":"shadow"}', encoding="utf-8"
        )
        (non_standard / "exhibit.json").write_text(
            '{"id":"non-standard","value":NaN}', encoding="utf-8"
        )

        self.assertEqual(
            [
                "exhibits/duplicate/exhibit.json: invalid JSON: duplicate object "
                "key 'id'",
                "exhibits/malformed/exhibit.json:3:1: invalid JSON: Expecting "
                "property name enclosed in double quotes",
                "exhibits/non-standard/exhibit.json: invalid JSON: non-standard "
                "JSON constant 'NaN'",
            ],
            validate_repository(self.repository_root),
        )

    def test_real_symbolic_link_is_rejected_when_supported(self):
        exhibit_directory = self.write_valid_exhibit()
        source_path = self.repository_root / "shared-physical.md"
        source_path.write_text("# Shared\n", encoding="utf-8")
        link_path = exhibit_directory / "physical.md"
        link_path.unlink()
        try:
            link_path.symlink_to(source_path)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symbolic links are unavailable: {error}")

        self.assertEqual(
            [
                "exhibits/serial/physical.md: symbolic-link exhibit file is not "
                "allowed"
            ],
            validate_repository(self.repository_root),
        )

    def test_symbolic_link_policy_is_covered_without_os_capability(self):
        exhibit_directory = self.write_valid_exhibit()
        physical_path = exhibit_directory / "physical.md"
        original_lstat = Path.lstat

        def reports_only_physical_file_as_symlink(path):
            result = original_lstat(path)
            if path == physical_path:
                return mock.Mock(st_mode=stat.S_IFLNK | 0o777)
            return result

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_only_physical_file_as_symlink,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            [
                "exhibits/serial/physical.md: symbolic-link exhibit file is not "
                "allowed"
            ],
            errors,
        )

    def test_direct_symbolic_links_are_rejected_without_following_targets(self):
        direct_entries = [
            self.repository_root / "exhibits" / "broken-link",
            self.repository_root / "exhibits" / "file-link",
        ]
        for entry in direct_entries:
            entry.write_text("placeholder\n", encoding="utf-8")

        original_lstat = Path.lstat

        def reports_direct_entries_as_symlinks(path):
            if path in direct_entries:
                return mock.Mock(st_mode=stat.S_IFLNK | 0o777)
            return original_lstat(path)

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_direct_entries_as_symlinks,
        ), mock.patch.object(Path, "is_dir", autospec=True) as is_dir:
            errors = validate_repository(self.repository_root)

        is_dir.assert_not_called()
        self.assertEqual(
            [
                "exhibits/broken-link: symbolic-link direct exhibit entry is "
                "not allowed",
                "exhibits/file-link: symbolic-link direct exhibit entry is not "
                "allowed",
            ],
            errors,
        )

    def test_real_direct_symbolic_links_are_rejected_when_supported(self):
        source_path = self.repository_root / "shared.md"
        source_path.write_text("# Shared\n", encoding="utf-8")
        file_link = self.repository_root / "exhibits" / "file-link"
        broken_link = self.repository_root / "exhibits" / "broken-link"
        try:
            file_link.symlink_to(source_path)
            broken_link.symlink_to(self.repository_root / "missing.md")
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symbolic links are unavailable: {error}")

        self.assertEqual(
            [
                "exhibits/broken-link: symbolic-link direct exhibit entry is "
                "not allowed",
                "exhibits/file-link: symbolic-link direct exhibit entry is not "
                "allowed",
            ],
            validate_repository(self.repository_root),
        )

    def test_reparse_point_exhibits_root_is_rejected(self):
        exhibits_root = self.repository_root / "exhibits"
        original_lstat = Path.lstat

        def reports_exhibits_root_as_reparse_point(path):
            if path == exhibits_root:
                return mock.Mock(
                    st_mode=stat.S_IFDIR | 0o755,
                    st_file_attributes=0x0400,
                )
            return original_lstat(path)

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_exhibits_root_as_reparse_point,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            ["exhibits: reparse-point exhibits directory is not allowed"],
            errors,
        )

    def test_reparse_point_direct_exhibit_is_rejected(self):
        exhibit_directory = self.write_valid_exhibit()
        original_lstat = Path.lstat

        def reports_exhibit_as_reparse_point(path):
            if path == exhibit_directory:
                return mock.Mock(
                    st_mode=stat.S_IFDIR | 0o755,
                    st_file_attributes=0x0400,
                )
            return original_lstat(path)

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_exhibit_as_reparse_point,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            ["exhibits/serial: reparse-point direct exhibit entry is not " "allowed"],
            errors,
        )

    def test_real_windows_reparse_point_exhibits_root_is_rejected(self):
        exhibits_root = self.repository_root / "exhibits"
        exhibits_root.rmdir()
        external_exhibits = self.repository_root / "external-exhibits"
        external_exhibits.mkdir()
        self.create_windows_junction(exhibits_root, external_exhibits)

        self.assertEqual(
            ["exhibits: reparse-point exhibits directory is not allowed"],
            validate_repository(self.repository_root),
        )

    def test_real_windows_reparse_point_direct_exhibit_is_rejected(self):
        external_exhibit = self.repository_root / "external-exhibit"
        external_exhibit.mkdir()
        (external_exhibit / "exhibit.json").write_text(
            '{"id":"junction"}\n', encoding="utf-8"
        )
        junction_path = self.repository_root / "exhibits" / "junction"
        self.create_windows_junction(junction_path, external_exhibit)

        self.assertEqual(
            ["exhibits/junction: reparse-point direct exhibit entry is not " "allowed"],
            validate_repository(self.repository_root),
        )

    def test_real_windows_nested_junctions_are_pruned_before_descent(self):
        exhibit_directory = self.write_valid_exhibit()
        external_directory = self.repository_root / "external-nested"
        external_directory.mkdir()
        (external_directory / "exhibit.json").write_text(
            '{"id":"escaped"}\n', encoding="utf-8"
        )
        external_junction = exhibit_directory / "external-junction"
        ancestor_loop = exhibit_directory / "ancestor-loop"
        self.create_windows_junction(external_junction, external_directory)
        self.create_windows_junction(ancestor_loop, exhibit_directory)

        probe = (
            "import json, sys; from pathlib import Path; "
            "from scripts.validate_exhibit_layout import validate_repository; "
            "print(json.dumps(validate_repository(Path(sys.argv[1]))))"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe, str(self.repository_root)],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )

        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertEqual(
            [
                "exhibits/serial/ancestor-loop: reparse-point nested exhibit "
                "directory is not allowed",
                "exhibits/serial/external-junction: reparse-point nested exhibit "
                "directory is not allowed",
            ],
            json.loads(result.stdout),
        )

    def test_nested_links_are_rejected_without_traversing_their_contents(self):
        exhibit_directory = self.write_valid_exhibit()
        symbolic_directory = exhibit_directory / "symbolic-directory"
        reparse_directory = exhibit_directory / "reparse-directory"
        for nested_directory in (symbolic_directory, reparse_directory):
            nested_directory.mkdir()
            (nested_directory / "exhibit.json").write_text(
                '{"id":"escaped"}\n', encoding="utf-8"
            )

        original_lstat = Path.lstat

        def reports_nested_link_types(path):
            if path == symbolic_directory:
                return mock.Mock(st_mode=stat.S_IFLNK | 0o777)
            if path == reparse_directory:
                return mock.Mock(
                    st_mode=stat.S_IFDIR | 0o755,
                    st_file_attributes=0x0400,
                )
            return original_lstat(path)

        with mock.patch.object(
            Path,
            "lstat",
            autospec=True,
            side_effect=reports_nested_link_types,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            [
                "exhibits/serial/reparse-directory: reparse-point nested exhibit "
                "directory is not allowed",
                "exhibits/serial/symbolic-directory: symbolic-link nested exhibit "
                "directory is not allowed",
            ],
            errors,
        )

    def test_nested_walk_errors_fail_closed(self):
        self.write_valid_exhibit()

        def walk_with_inspection_error(top, *, topdown, onerror, followlinks):
            self.assertTrue(topdown)
            self.assertFalse(followlinks)
            onerror(OSError("simulated nested scan failure"))
            yield top, [], []

        with mock.patch(
            "scripts.validate_exhibit_layout.os.walk",
            side_effect=walk_with_inspection_error,
        ):
            errors = validate_repository(self.repository_root)

        self.assertEqual(
            [
                "exhibits/serial: cannot inspect nested exhibit layout: "
                "simulated nested scan failure"
            ],
            errors,
        )

    def test_diagnostics_are_sorted_by_repository_path(self):
        zeta = self.write_valid_exhibit("zeta", exhibit_id="wrong")
        alpha = self.write_valid_exhibit("alpha")
        (zeta / "README.md").unlink()
        (alpha / "sources.md").unlink()
        nested = alpha / "z-draft"
        nested.mkdir()
        (nested / "exhibit.json").write_text("{}", encoding="utf-8")

        expected = [
            "exhibits/alpha/sources.md: required exhibit file is missing",
            "exhibits/alpha/z-draft: nested exhibit directory is not allowed; "
            "exact layout permits no subdirectories",
            "exhibits/zeta/README.md: required exhibit file is missing",
            'exhibits/zeta/exhibit.json: id "wrong" does not match exhibit '
            'directory "zeta" (expected "zeta")',
        ]
        self.assertEqual(expected, validate_repository(self.repository_root))
        self.assertEqual(expected, validate_repository(self.repository_root))

    def test_checked_in_template_and_corpus_are_valid(self):
        self.assertEqual([], validate_repository(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
