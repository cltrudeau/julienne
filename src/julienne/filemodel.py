from math import log, ceil
from pathlib import Path
import shutil
import sys

import tomli

from julienne.parsers import range_token
from julienne.nodes import (DirNode, ConditionalDirNode, PoundFileNode,
    ConditionalPoundFileNode, ConditionalCopyOnlyFileNode, CopyOnlyFileNode,
    XMLFileNode, ConditionalXMLFileNode, _BaseFileNode)

# ===========================================================================
# Utilities
# ===========================================================================

def _convert_path(base_path, path):
    if path.is_absolute():
        return path

    mixed = base_path / path
    return mixed.resolve()

def _traverse(chapter, node, cmd, *args):
    fn = getattr(node, cmd)
    fn(*args)

    for child in node.children:
        if isinstance(child, DirNode) and child.should_traverse(chapter):
            _traverse(chapter, child, cmd, *args)
        else:
            fn = getattr(child, cmd)
            fn(*args)


def _walk_node(node):
    if isinstance(node, DirNode):
        for child in node.children:
            yield from _walk_node(child)
    else:
        yield node


def _print_node_contents(node):
    print("***", node.path)
    if isinstance(node, _BaseFileNode):
        for line in node.parser.lines:
            lower = '*' if line.lower is None else str(line.lower)
            upper = '*' if line.upper is None else str(line.upper)
            print(f"{lower:>2}-{upper:2} |", line.content)

# ===========================================================================
# File Tree
# ===========================================================================

class FileTree:
    def __init__(self, config, base_path, base_dir, verbose=False):
        self.base_path = base_path
        self.base_dir = base_dir
        self.verbose = verbose

        # Find the Python style files that participate in the parsing
        self.pound_files = []
        globs = config.get('pound_globs', ['**/*.py', ])
        for pattern in globs:
            self.pound_files.extend(base_dir.glob(pattern))

        # Find the XML style files that participate in the parsing
        self.xml_files = []
        globs = config.get('xml_globs', ['**/*.xml', '**/*.htm', '**/*.html' ])
        for pattern in globs:
            self.xml_files.extend(base_dir.glob(pattern))

        # Find the files that specify a participation range
        self.ranged_files_map = {}
        for spec in config.get('ranged_files', {}).values():
            token = spec['range']
            for path in spec['files']:
                ranged_path = _convert_path(base_path, Path(path))
                self.ranged_files_map[ranged_path] = token

        # Find the directories to skip
        self.skip_dirs = []
        for dirname in config.get('skip_dirs', []):
            path = _convert_path(base_dir, Path(dirname))
            self.skip_dirs.append(path)

        # Other values from the config
        self.skip_patterns = config.get('skip_patterns', [])
        self.prefix = config.get('chapter_prefix', 'ch')
        self.chapter_map = config.get('chapter_map', {})

        # Build the file tree
        self.root = DirNode(self.base_dir)
        self._process_dir_node(self.root, base_dir)
        self._find_biggest()

        if self.verbose:
            print('\n** File tree:')
            _traverse(self.biggest, self.root, 'info')

    def _process_dir_node(self, parent, dir_path):
        for path in dir_path.iterdir():
            # Skip any paths that are in our ignore_substrings list
            skip = False
            for pattern in self.skip_patterns:
                if pattern in str(path):
                    skip = True
                    break

            if skip:
                # Path contained a skip pattern, don't process it
                if self.verbose:
                    print(f"Skipping {path} because of pattern={pattern}")
                continue

            try:
                if path.is_dir():
                    if path in self.skip_dirs:
                        if self.verbose:
                            print(f"Skipping {path} because it is in skip_dirs")

                        continue
                    elif path in self.ranged_files_map.keys():
                        token = self.ranged_files_map[path]
                        node = ConditionalDirNode(path, token)
                    else:
                        node = DirNode(path)

                    parent.children.append(node)
                    self._process_dir_node(node, node.path)
                else:
                    if path in self.pound_files:
                        if path in self.ranged_files_map.keys():
                            token = self.ranged_files_map[path]
                            node = ConditionalPoundFileNode(path, token)
                        else:
                            node = PoundFileNode(path)

                        node.parse_file()
                    elif path in self.xml_files:
                        if path in self.ranged_files_map.keys():
                            token = self.ranged_files_map[path]
                            node = ConditionalXMLFileNode(path, token)
                        else:
                            node = XMLFileNode(path)

                        node.parse_file()
                    elif path in self.ranged_files_map.keys():
                        token = self.ranged_files_map[path]
                        node = ConditionalCopyOnlyFileNode(path, token)
                    else:
                        node = CopyOnlyFileNode(path)

                    parent.children.append(node)
            except Exception as e:
                raise e.__class__(f"Error parsing {path}. " + str(e))

    def _find_biggest(self):
        # Need to find the biggest upper bound, might be in the nodes, in the
        # ranged map, or in the chapter map
        max_node = self._find_biggest_in_nodes(self.root, 1)
        try:
            max_chapter = int(sorted(self.chapter_map.keys())[0])
        except IndexError:
            max_chapter = 1

        max_ranged = 1
        for token in self.ranged_files_map.values():
            lower, upper = range_token(token)
            if lower is not None and lower > max_ranged:
                max_ranged = lower
            if upper is not None and upper > max_ranged:
                max_ranged = upper

        # Find biggest chapter and how many digits are in it for padding
        self.biggest = max(max_node, max_ranged, max_chapter)
        self.digits = int(ceil(log(self.biggest + 1, 10)))

    def _find_biggest_in_nodes(self, node, biggest=1):
        result = biggest
        if node.lower is not None and node.lower > result:
            result = node.lower
        if node.upper is not None and node.upper > result:
            result = node.upper

        try:
            for child in node.children:
                if isinstance(child, DirNode):
                    subresult = self._find_biggest_in_nodes(child, result)
                    if subresult > result:
                        result = subresult
                elif isinstance(child, _BaseFileNode):
                    if child.biggest is not None and child.biggest > result:
                        result = child.biggest

        except Exception as e:
            raise e.__class__(f"Problem occurred processing {child.path} " \
                + str(e))

        return result

    def generate(self, output_dir, single_chapter=None):
        parent_path = self.base_dir.parent

        if single_chapter is not None:
            output_path = output_dir / Path(f"ch{single_chapter}")
            _traverse(single_chapter, self.root, 'copy', single_chapter, 
                parent_path, output_path)
            return

        # Generate whole range of chapters
        for num in range(1, self.biggest + 1):
            print(f'Creating chapter {num}')

            # If this chapter is in the map, use the mapped suffix instead
            if str(num) in self.chapter_map:
                # Filename based on mapped suffix
                filename = f"{self.prefix}{self.chapter_map[str(num)]}"
            else:
                # Filename based chapter number, padded based on largest number
                filename = f"{self.prefix}{num:0{self.digits}}"

            # Call the "copy" command, traversing the tree to generate the
            # output
            output_path = output_dir / Path(filename)
            _traverse(num, self.root, 'copy', num, parent_path, output_path)

# ===========================================================================
# File Generation
# ===========================================================================

def generate_files(config_file, verbose=False, info_only=False, 
        single_chapter=None, debug=''):
    path = Path(config_file)
    path.resolve()
    base_path = path.parent

    config = tomli.loads(path.read_text())

    # Check for / create output directory
    output_dir = _convert_path(base_path, Path(config['output_dir']))
    if output_dir.exists():
        if not output_dir.is_dir():
            raise AttributeError(('The value for "output_dir" in the config '
                'file pointed to an existing path that was not a directory'))
    else:
        output_dir.mkdir()

    # Check for source directory
    base_dir = Path(config['src_dir'])
    base_dir = _convert_path(base_path, Path(config['src_dir']))
    if not base_dir.is_dir():
        raise AttributeError(('The value for "src_dir" in the config file was '
            'not a valid directory'))

    if info_only:
        # If only showing info force verbose
        verbose = True

    # Build the tree and then generate the output
    tree = FileTree(config, base_path, base_dir, verbose)

    if debug:
        # Debug mode, show all the line info for everything in matching files
        match = False
        for node in _walk_node(tree.root):
            if debug in str(node.path):
                match = True
                _print_node_contents(node)

        if not match:
            print(f"!!! No file name matching *{debug}*")
        exit()

    if info_only:
        # Don't generate chapters, you're done
        print('\nLargest chapter detected', tree.biggest)
        print('\n**Info only, no chapters generated**')
        exit()

    # Optionally remove the output directory before processing
    if config.get('delete_output', False):
        print('\n**Removing existing output directory')
        if output_dir.exists():
            shutil.rmtree(output_dir)

    if verbose:
        print('\n**Processing')
    tree.generate(output_dir, single_chapter)

    # Optionally run isort on the output
    if config.get('isort', False):
        print('\n**Calling isort')
        sys.argv = ['isrot', str(output_dir)]
        try:
            # import only if being used
            from isort.main import main as isort_main
            isort_main()
        except SystemExit:
            # black calls quit(), ignore it
            pass

    # Optionally run black on the output
    if config.get('black', False):
        print('\n**Calling black')
        #sys.argv = ['black', str(output_dir), '-l', 80, '--diff']
        sys.argv = ['black', str(output_dir), '-l', 80]
        try:
            import black    # import only if being used
            black.main()
        except SystemExit:
            # black calls quit(), ignore it
            pass

    return tree

# ===========================================================================
# File Display
# ===========================================================================

def display_pound_files(files):
    for filename in files:
        path = Path(filename)
        node = PoundFileNode(path)
        node.parse_file()
        _print_node_contents(node)


def display_xml_files(files):
    for filename in files:
        path = Path(filename)
        node = XMLFileNode(path)
        node.parse_file()
        _print_node_contents(node)
