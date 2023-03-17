import argparse
from julienne.filemodel import (generate_files, display_pound_files,
    display_xml_files)

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

parser.add_argument('config_file', help=HELP, nargs="?")

parser.add_argument('-v', '--verbose', help="Print info while processing",
    action='store_true', default=False)

parser.add_argument('-i', '--info', help="Only show info, don't process",
    action='store_true', default=False)

parser.add_argument('-c', '--chapter', help="Only process a specific chapter",
    type=int, default=None)

parser.add_argument('-d', '--debug', type=str, default='',
    help="Show full debug for file names that match the argument")

parser.add_argument('-p', '--parsepy', type=str, nargs='+',
    help="Parse and display (like debug) named Python files")

parser.add_argument('-x', '--parsexml', type=str, nargs='+',
    help="Parse and display (like debug) named XML files")

# ===========================================================================

def main():
    args = parser.parse_args()

    if args.parsepy:
        display_pound_files(args.parsepy)
    elif args.parsexml:
        display_xml_files(args.parsexml)
    else:
        if not args.config_file:
            parser.print_usage()
            print("juli: error: config_file argument required when not using "
                "-p or -x")
            exit()

        generate_files(args.config_file, args.verbose, args.info, args.chapter, 
            args.debug)
