import shutil

from julienne.parsers import (parse_pound_content, parse_xml_content, 
    range_token, chapter_in_range)

# ===========================================================================
# Base
# ===========================================================================

class _BaseNode:
    def __init__(self, path):
        self.lower = None
        self.upper = None
        self.path = path

# ===========================================================================
# Directory Nodes
# ===========================================================================

class DirNode(_BaseNode):
    """Node for directories in the file tree."""

    def __init__(self, path):
        super().__init__(path)
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
    """Node for directories that participate conditionally."""
    def __init__(self, path, token):
        super().__init__(path)
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

# ===========================================================================
# Copy Only Nodes
# ===========================================================================

class CopyOnlyFileNode(_BaseNode):
    """Node for files that get copied but not parsed"""
    def info(self):
        print('CopyOnlyFileNode')
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        dest = output_path / rel

        shutil.copy2(self.path, dest)


class ConditionalCopyOnlyFileNode(_BaseNode):
    """Node for files that get copied conditionally, but not parsed."""
    def __init__(self, path, token):
        super().__init__(path)
        self.lower, self.upper = range_token(token)

    def info(self):
        print(f'ConditionalCopyOnlyFileNode {self.lower} - {self.upper}')
        print(f'   {self.path}')

    def should_traverse(self, chapter):
        return chapter_in_range(chapter, True, self.lower, self.upper)

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)
        dest = output_path / rel

        if chapter_in_range(chapter, True, self.lower, self.upper):
            shutil.copy2(self.path, dest)

# ===========================================================================
# Parsing Node Base Classes
# ===========================================================================

class _BaseFileNode(_BaseNode):
    def __init__(self, path):
        self.path = path
        self._parser_fn = None

    def parse_file(self):
        ### Done as a separate step to make testing easier, allows for
        # testing the ._parse_content() method without having an actual file
        self._parse_content(self.path.read_text())

    def _parse_content(self, content):
        """Sets the list of parsed Line objects, one for each line in the 
        given string of content.

        :param content: string to parse
        """
        self.parser = self._parser_fn(content)

        self.bottom, self.top, self.biggest = self.parser.get_range()
        self.all_conditional = self.parser.all_conditional

    def info(self):
        bottom = getattr(self, 'bottom', "Unset")
        top = getattr(self, 'top', "Unset")
        all_cond = getattr(self, 'all_conditional', "Unset")

        print(f'{self.__class__.__name__}', bottom, top, all_cond)
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        rel = self.path.relative_to(base_path)

        # If the file is all conditional, only write it in the chapter range,
        # If the file is not all conditional, some parts will appear in every
        # chapter, so write it
        if not self.all_conditional or (self.all_conditional and \
                chapter_in_range(chapter, True, self.bottom, self.top)):
            # Write file if within chapter range
            dest = output_path / rel
            with open(dest, "w") as f:
                for line in self.parser.lines:
                    content = line.get_content(chapter)
                    if content is not None:
                        f.write(content + "\n")

class ConditionalFileNodeMixin:
    def info(self):
        print(f'{self.__class__.__name__} {self.lower} - {self.upper}')
        print(f'   {self.path}')

    def copy(self, chapter, base_path, output_path):
        if not chapter_in_range(chapter, True, self.lower, self.upper):
            return

        super().copy(chapter, base_path, output_path)

# ===========================================================================
# Python File Nodes
# ===========================================================================

class PoundFileNode(_BaseFileNode):
    """Node for Python style files, those with comments that are a #. These
    are parsed and processed for every chapter."""
    def __init__(self, path):
        super().__init__(path)
        self._parser_fn = parse_pound_content


class ConditionalPoundFileNode(ConditionalFileNodeMixin, PoundFileNode):
    """Node for Python style files, those with comments that are a #. These
    are parsed and processed conditionally."""
    def __init__(self, path, token):
        super().__init__(path)
        self.lower, self.upper = range_token(token)

# ===========================================================================
# XML Nodes
# ===========================================================================

class XMLFileNode(_BaseFileNode):
    """Node for XML style files, those with comments that are a <!-- -->.
    These are parsed and processed for every chapter."""
    def __init__(self, path):
        super().__init__(path)
        self._parser_fn = parse_xml_content


class ConditionalXMLFileNode(ConditionalFileNodeMixin, XMLFileNode):
    """Node for XML style files, those with comments that are a <!-- -->.
    These are parsed and processed for conditionally."""
    def __init__(self, path, token):
        super().__init__(path)
        self.lower, self.upper = range_token(token)
