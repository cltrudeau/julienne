import argparse
from julienne.filemodel import generate_files

# ===========================================================================

DESCRIPTION = """\
Generates multiple versions of a Python project, slicing each version based on
special tokens in the code comments. Lines or blocks of code can be in all
versions, or only show up in a subset.
"""

parser = argparse.ArgumentParser(description=DESCRIPTION)


HELP = """\
Configuration file that describes the Python project that is to be split into
versions.
"""

parser.add_argument('config_file', help=HELP)

# ===========================================================================

def main():
    args = parser.parse_args()
    generate_files(args.config_file)
