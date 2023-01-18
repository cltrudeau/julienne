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

parser.add_argument('-v', '--verbose', help="Print info while processing",
    action='store_true', default=False)

parser.add_argument('-i', '--info', help="Only show info, don't process",
    action='store_true', default=False)

parser.add_argument('-c', '--chapter', help="Only process a specific chapter",
    type=int, default=None)

# ===========================================================================

def main():
    args = parser.parse_args()
    generate_files(args.config_file, args.verbose, args.info, args.chapter)
