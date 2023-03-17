from difflib import Differ
from filecmp import cmp
from pathlib import Path
from unittest import TestCase

from julienne.filemodel import generate_files

# ============================================================================

class SampleFilesTestCase(TestCase):

    def assert_directory_match(self, expected, output):
        # Validate directory listing is the same
        expected_set = {p.relative_to(expected) for p in expected.rglob('*')}
        output_set = {p.relative_to(output) for p in output.rglob('*')}
        self.assertEqual(expected_set, output_set)

        # Validate files themselves are the same
        for path in expected_set:
            expected_path = expected / path
            output_path = output / path

            if expected_path.is_dir():
                continue

            result = cmp(expected_path, output_path)
            if not result:
                d = Differ()
                expected_text = expected_path.read_text().splitlines(
                    keepends=True)
                output_text = output_path.read_text().splitlines(keepends=True)

                result = d.compare(expected_text, output_text)

                error = f"{path} did not match expectation.\n\n" + \
                    "".join(list(result))
                raise AssertionError(error)

    def test_e2e(self):
        here = Path(__file__).parent
        output = here / Path('data/last_output')

        # Generate results and compare to expected
        path = here / Path('data/sample.toml')
        tree = generate_files(str(path))

        # Verify that the sneaky reference to Chapter 6 is found
        self.assertEqual(6, tree.biggest)

        expected = here / Path('data/expected')

        self.assert_directory_match(expected, output)

    def test_failures(self):
        here = Path(__file__).parent
        path = here / Path('data/fail.toml')

        with self.assertRaises(Exception) as context:
            generate_files(str(path))

        error = context.exception
        self.assertIn("bad_code/bad_marker.py", str(error))
        self.assertIn("Unknown marker type", str(error))

    def test_darkgrey(self):
        here = Path(__file__).parent
        output = here / Path('data/darkgrey/last_output')

        # Generate results and compare to expected
        path = here / Path('data/darkgrey/grey.toml')
        generate_files(str(path))
        expected = here / Path('data/darkgrey/expected')

        self.assert_directory_match(expected, output)
