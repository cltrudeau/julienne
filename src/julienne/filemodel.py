from math import log, ceil
from pathlib import Path
import shutil

import tomli

from julienne.parser import parse_content, range_token, chapter_in_range

# ===========================================================================

class DirNode:

    def __init__(self, path):
        self.path = path
        self.children = []

    def info(self):
        print('DirNode')
        print(f'   {self.path}')

    def should_traverse(self, chapter):
        return True

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        new_dir = output_path / rel
        new_dir.mkdir(parents=True, exist_ok=True)


class ConditionalDirNode(DirNode):

    def __init__(self, path, token):
        self.path = path
        self.children = []
        self.lower, self.upper = range_token(token)

    def info(self):
        print(f'ConditionalDirNode {self.lower} - {self.upper}')
        print(f'   {self.path}')

    def should_traverse(self, chapter):
        return chapter_in_range(chapter, True, self.lower, self.upper)

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        new_dir = output_path / rel

        if chapter_in_range(chapter, True, self.lower, self.upper):
            new_dir.mkdir(parents=True, exist_ok=True)


class CopyOnlyFileNode:

    def __init__(self, path):
        self.path = path

    def info(self):
        print('CopyOnlyFileNode')
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        dest = output_path / rel

        shutil.copy2(self.path, dest)


class FileNode:

    def __init__(self, path):
        self.path = path

    def parse_file(self):
        ### Done as a separate step to make testing easier, allows for
        # testing the ._parse_content() method without having an actual file
        self._parse_content(self.path.read_text())

    def _parse_content(self, content):
        """Sets the list of parsed Line objects, one for each line in the 
        given string of content.

        :param content: string to parse
        """
        self.parser = parse_content(content)
        self.lowest = self.parser.lowest
        self.highest = self.parser.highest
        self.all_conditional = self.parser.all_conditional

    def info(self):
        lowest = getattr(self, 'lowest', "Unset")
        highest = getattr(self, 'highest', "Unset")
        all_cond = getattr(self, 'all_conditional', "Unset")

        print('FileNode', lowest, highest, all_cond)
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)

        # If the file is all conditional, only write it in the chapter range,
        # If the file is not all conditional, some parts will appear in every
        # chapter, so write it
        if not self.all_conditional or (self.all_conditional and \
                chapter_in_range(chapter, True, self.lowest, self.highest)):
            # Write file if within chapter range
            dest = output_path / rel
            with open(dest, "w") as f:
                for line in self.parser.lines:
                    content = line.get_content(chapter)
                    if content is not None:
                        f.write(content + "\n")


class ConditionalFileNode(FileNode):
    def __init__(self, path, token):
        self.lower, self.upper = range_token(token)
        super().__init__(path)

    def info(self):
        print(f'ConditionalFileNode {self.lower} - {self.upper}')
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        if not chapter_in_range(chapter, True, self.lower, self.upper):
            return

        super().copy(chapter, base_path, output_path)

# ---------------------------------------------------------------------------

class NodeFilter:
    def __init__(self):
        self.python_files = []
        self.ignore_dirs = []
        self.ignore_substrings = []

        self.ranged_files_map = {}

    def set_python_filter(self, py_globs, base_dir):
        for py_glob in py_globs:
            self.python_files.extend(base_dir.glob(py_glob))

    def set_ranged_file_filter(self, ranged_files, base_path):
        # Loop over all the "ranged_files" maps and track their content
        for spec in ranged_files.values():
            token = spec['range']
            for path in spec['files']:
                ranged_path = _convert_path(base_path, Path(path))
                self.ranged_files_map[ranged_path] = token

    def set_ignore_dirs(self, ignore_dirs, base_path):
        for dirname in ignore_dirs:
            path = _convert_path(base_path, Path(dirname))
            self.ignore_dirs.append(path)

# ===========================================================================
# Node Tree Traversal Methods
# ===========================================================================

def _process_directory(parent, dir_path, node_filter):
    for path in dir_path.iterdir():
        # Skip any paths that are in our ignore_substrings list
        skip = False
        for ignore_substring in node_filter.ignore_substrings:
            if ignore_substring in str(path):
                skip = True

        if skip:
            # Path contained something spec'd in ignore_substrings, ignore it
            continue

        try:
            if path.is_dir():
                if path in node_filter.ignore_dirs:
                    continue
                elif path in node_filter.ranged_files_map.keys():
                    token = node_filter.ranged_files_map[path]
                    node = ConditionalDirNode(path, token)
                else:
                    node = DirNode(path)

                parent.children.append(node)
                _process_directory(node, node.path, node_filter)
            else:
                if path in node_filter.python_files:
                    if path in node_filter.ranged_files_map.keys():
                        token = node_filter.ranged_files_map[path]
                        node = ConditionalFileNode(path, token)
                    else:
                        node = FileNode(path)

                    node.parse_file()
                else:
                    node = CopyOnlyFileNode(path)

                parent.children.append(node)
        except Exception as e:
            raise e.__class__(f"Error parsing {path}. " + str(e))


def _traverse(chapter, node, cmd, *args):
    fn = getattr(node, cmd)
    fn(*args)

    for child in node.children:
        if isinstance(child, DirNode) and child.should_traverse(chapter):
            _traverse(chapter, child, cmd, *args)
        else:
            fn = getattr(child, cmd)
            fn(*args)


def _find_biggest(node, biggest=1):
    result = biggest
    if hasattr(node, "lower") and node.lower > result:
        result = node.lower
    if hasattr(node, "upper") and node.upper != -1 and node.upper > result:
        result = node.upper

    try:
        for child in node.children:
            if isinstance(child, DirNode):
                subresult = _find_biggest(child, result)
                if subresult > result:
                    result = subresult
            elif isinstance(child, FileNode):
                if hasattr(child, 'highest') and child.highest > result:
                    result = child.highest
    except Exception as e:
        raise e.__class__(f"Problem occurred processing {child.path} " + str(e))

    return result

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _convert_path(base_path, path):
    if path.is_absolute():
        return path

    mixed = base_path / path
    return mixed.resolve()

# ===========================================================================

def generate_files(config_file):
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

    # Build the node filter that limits which files and directories
    # participate 
    node_filter = NodeFilter()
    py_globs = config.get('python_globs', ['**/*.py', ])
    node_filter.set_python_filter(py_globs, base_dir)

    ranged_files = config.get('ranged_files', {})
    node_filter.set_ranged_file_filter(ranged_files, base_path)

    ignore_dirs = config.get('ignore_dirs', [])
    node_filter.set_ignore_dirs(ignore_dirs, base_dir)

    node_filter.ignore_substrings = config.get('ignore_substrings', [])

    # Create node structure
    root = DirNode(base_dir)
    _process_directory(root, base_dir, node_filter)

    # DEBUG:
    #_traverse(3, root, 'info')
    #exit()

    ### Generate output
    parent_path = base_dir.parent
    biggest = _find_biggest(root)
    digits = int(ceil(log(biggest+1, 10)))

    prefix = config.get('chapter_prefix', 'ch')
    chapter_map = config.get('chapter_map', {})

    # DEBUG: uncomment to generate a specific chapter
    #num = 5
    #output_path = output_dir / Path(f"ch{num}")
    #_traverse(num, root, 'copy', num, parent_path, output_path)
    #exit()

    for num in range(1, biggest + 1):
        print(f'Creating chapter {num}')

        # If this chapter number is in the map, use the mapped suffix instead
        if str(num) in chapter_map:
            # Filename based on mapped suffix
            filename = f"{prefix}{chapter_map[str(num)]}"
        else:
            # Filename based on chapter number, padded based on largest number
            filename = f"{prefix}{num:0{digits}}"

        # Call the "copy" command, traversing the tree to generate the output
        output_path = output_dir / Path(filename)
        _traverse(num, root, 'copy', num, parent_path, output_path)
