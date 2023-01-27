import shutil

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


class ConditionalCopyOnlyFileNode:

    def __init__(self, path, token):
        self.path = path
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
