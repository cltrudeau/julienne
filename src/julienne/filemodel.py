from math import log, ceil
from pathlib import Path
import shutil

import tomli

from julienne.parser import Line, range_token, chapter_in_range

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
        print(f'ConditionalDirNode {self.lower}-{self.upper}')
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

        shutil.copy(self.path, dest)


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
        if content and content[-1] == '\n':
            content = content[:-1]

        self.lines = []
        self.all_conditional = True
        block_header = None
        boundary_set = False
        for item in content.split('\n'):
            line = Line(item, block_header)

            block_header = line.block_header
            self.lines.append(line)

            if not line.conditional:
                self.all_conditional = False

            if boundary_set and line.conditional:
                # Check if this line changes the boundary conditions
                if line.lower < self.lowest:
                    self.lowest = line.lower

                if line.upper == -1 or \
                        (line.upper != -1 and line.upper > self.highest):
                    self.highest = line.upper
            else:
                # Boundary not set yet
                if line.conditional:
                    boundary_set = True
                    self.lowest = line.lower
                    self.highest = line.upper

    def info(self):
        print('FileNode', self.lowest, self.highest, self.all_conditional)
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
                for line in self.lines:
                    content = line.get_content(chapter)
                    if content is not None:
                        f.write(content + "\n")

# ---------------------------------------------------------------------------

class NodeFilter:
    def __init__(self):
        self.python_files = []
        self.conditional_dirs = []
        self.conditional_map = {}
        self.ignore_dirs = []

    def set_python_filter(self, py_globs, base_dir):
        for py_glob in py_globs:
            self.python_files.extend(base_dir.glob(py_glob))

    def set_dir_filter(self, subdir, base_path):
        for dir_spec in subdir.values():
            token = dir_spec['range']
            dir_path = _convert_path(base_path, Path(dir_spec['src_dir']))

            self.conditional_dirs.append(dir_path)
            self.conditional_map[dir_path] = token

    def set_ignore_dirs(self, ignore_dirs, base_path):
        for dirname in ignore_dirs:
            path = _convert_path(base_path, Path(dirname))
            self.ignore_dirs.append(path)

# ===========================================================================
# Node Tree Traversal Methods
# ===========================================================================

def _process_directory(parent, dir_path, node_filter):
    for path in dir_path.iterdir():
        try:
            if path.is_dir():
                if path in node_filter.ignore_dirs:
                    continue
                elif path in node_filter.conditional_dirs:
                    token = node_filter.conditional_map[path]
                    node = ConditionalDirNode(path, token)
                else:
                    node = DirNode(path)

                parent.children.append(node)
                _process_directory(node, node.path, node_filter)
            else:
                if path in node_filter.python_files:
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

    try:
        for child in node.children:
            if isinstance(child, DirNode):
                subresult = _find_biggest(child, biggest)
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

    subdir = config.get('subdir', {})
    node_filter.set_dir_filter(subdir, base_path)

    ignore_dirs = config.get('ignore_dirs', [])
    node_filter.set_ignore_dirs(ignore_dirs, base_dir)

    # Create node structure
    root = DirNode(base_dir)
    _process_directory(root, base_dir, node_filter)

    # DEBUG:
    #_traverse(3, root, 'info')

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
