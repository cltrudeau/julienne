import shutil
from filecmp import dircmp
from pathlib import Path
from unittest import TestCase

from julienne.filemodel import generate_files

# ============================================================================

class SampleFilesTestCase(TestCase):
    def test_e2e(self):
        here = Path(__file__).parent

        # Remove files from last run, create output directory
        output = here / Path('data/last_output')
        if output.exists():
            shutil.rmtree(output)

        output.mkdir(parents=True)

        # Generate results and compare to expected
        path = here / Path('data/sample.toml')
        generate_files(str(path))
        expected = here / Path('data/expected')
        result = dircmp(output, expected)
        self.assertEqual(result.diff_files, [])

    def test_failures(self):
        here = Path(__file__).parent
        path = here / Path('data/fail.toml')

        with self.assertRaises(Exception) as context:
            generate_files(str(path))

        error = context.exception
        self.assertIn("bad_code/bad_marker.py", str(error))
        self.assertIn("Unknown marker type", str(error))
