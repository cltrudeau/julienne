from math import log, ceil
from pathlib import Path
import tomli

from julienne.parser import Line

# ===========================================================================

class DirNode:

    def __init__(self, path):
        self.path = path
        self.children = []

    def copy(self, chapter, base_path, output_path):
        print(f"DirNode, kids={len(self.children)}")
        print(f"  {self.path}")

        rel = self.path.relative_to(base_path)
        new_dir = output_path / rel
        print("   mkdir ", new_dir)


class CopyOnlyFileNode:

    def __init__(self, path):
        self.path = path

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        dest = output_path / rel

        print(f"CopyOnlyFileNode {rel}")
        print(f"   from {self.path}")
        print(f"     to {dest}")

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
        self.lines = []
        block_header = None
        boundary_set = False
        for item in content.split('\n'):
            line = Line(item, block_header)
            block_header = line.block_header
            self.lines.append(line)

            if boundary_set and line.conditional:
                # Check if this line changes the boundary conditions
                if line.lower < self.lowest:
                    self.lowest = line.lower
                if line.upper != -1 and line.upper > self.highest:
                    self.highest = line.upper
            else:
                # Boundary not set yet
                if line.conditional:
                    boundary_set = True
                    self.lowest = line.lower
                    self.highest = line.upper

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        print("FileNode", f"{rel} Range: {self.lowest}-{self.highest}")

        if self.lowest <= chapter <= self.highest:
            dest = output_path / rel
            print(f"   from {self.path}")
            print(f"     to {dest}")
        else:
            print(f"   skipping {chapter=}")

# ===========================================================================
# Node Tree Traversal Methods
# ===========================================================================

def _process_directory(parent, dir_path, python_files):
    for path in dir_path.iterdir():
        if path.is_dir():
            node = DirNode(path)
            parent.children.append(node)
            _process_directory(node, node.path, python_files)
        else:
            if path in python_files:
                node = FileNode(path)
                node.parse_file()
            else:
                node = CopyOnlyFileNode(path)

            parent.children.append(node)


def _traverse(node, cmd, *args):
    fn = getattr(node, cmd)
    fn(*args)

    for child in node.children:
        if isinstance(child, DirNode):
            _traverse(child, cmd, *args)
        else:
            fn = getattr(child, cmd)
            fn(*args)


def _find_biggest(node, biggest=1):
    result = biggest

    for child in node.children:
        if isinstance(child, DirNode):
            subresult = _find_biggest(child, biggest)
            if subresult > result:
                result = subresult
        elif isinstance(child, FileNode):
            if child.highest > result:
                result = child.highest

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

    # Find python file subset for processing
    py_globs = config.get('python_globs', ['**/*.py', ])
    python_files = []
    for py_glob in py_globs:
        python_files.extend(base_dir.glob(py_glob))

    # Create node structure
    root = DirNode(base_dir)
    _process_directory(root, base_dir, python_files)

    # !!! Generate output goes here
    biggest = _find_biggest(root)
    digits = int(ceil(log(biggest+1, 10)))
    parent_path = base_dir.parent

    for num in range(1, biggest + 1):
        print(30*'-', f"{num=}")
        output_path = output_dir / Path(f"ch{num:0{digits}}")
        _traverse(root, 'copy', num, parent_path, output_path)
