from unittest import TestCase

from julienne.parser import Line
from julienne.filemodel import FileNode

# ============================================================================

BLOCK1 = """\
#::3-4
#>e = "In chapters 3 to 4"  # inline comment
#>f = "  as a block"\
"""

BLOCK2 = """\
for x in range(10):
    #::1-2 block header with comment
    #>g= "In chapters 1 and 2"
    h = "In all chapters"\
"""

# ----------------------------------------------------------------------------

class ParserTestCase(TestCase):
    def assertLine(self, line, conditional, is_block, expected, lower=0,
            upper=0):

        self.assertEqual(expected, line.content)

        if not conditional:
            self.assertFalse(line.conditional)
            self.assertIsNone(line.block_header)
            return

        # Conditional line
        self.assertTrue(line.conditional)
        self.assertEqual(line.lower, lower)
        self.assertEqual(line.upper, upper)

        if is_block:
            self.assertIsNotNone(line.block_header)
        else:
            self.assertIsNone(line.block_header)

    def test_line_parsing(self):
        # Test a comment
        text = "# This is a sample file"
        line = Line(text)
        self.assertLine(line, False, False, text)

        # Test a regular line
        text = 'a = "In all chapters"   # inline comment'
        line = Line(text)
        self.assertLine(line, False, False, text)

        # Test a full-range conditional line with inline comment
        text = 'b = "In chapters 1-3"   #:1-3 comment on conditional'
        expected = 'b = "In chapters 1-3"   # comment on conditional'
        line = Line(text)
        self.assertLine(line, True, False, expected, 1, 3)

        # Test lower open range conditional line
        text = 'c = "In chapters 1-2"   #:-2'
        expected = 'c = "In chapters 1-2"'
        line = Line(text)
        self.assertLine(line, True, False, expected, 1, 2)

        # Test upper open range conditional line
        text = 'd = "In chapters 2 on"  #:2-'
        expected = 'd = "In chapters 2 on"'
        line = Line(text)
        self.assertLine(line, True, False, expected, 2, -1)

    def test_block_parsing(self):
        #--- Test a conditional block
        global BLOCK1
        node = FileNode('')
        node._parse_content(BLOCK1)
        lines = node.lines

        # Block header line has no comment, should be empty
        self.assertIsNotNone(lines[0].block_header)
        self.assertEqual('', lines[0].content)

        expected = 'e = "In chapters 3 to 4"  # inline comment'
        self.assertLine(lines[1], True, True, expected, 3, 4)

        expected = 'f = "  as a block"'
        self.assertLine(lines[2], True, True, expected, 3, 4)

        #--- Test a conditional block inside an indent
        node.lines = []
        node._parse_content(BLOCK2)
        lines = node.lines

        # First line is not conditional
        expected = 'for x in range(10):'
        self.assertLine(lines[0], False, False, expected)

        # 2nd line is block header with comment
        expected = '    # block header with comment'
        self.assertLine(lines[1], True, True, expected, 1, 2)

        # 3rd line is in conditional block
        expected = '    g= "In chapters 1 and 2"'
        self.assertLine(lines[2], True, True, expected, 1, 2)

        # Last line is not conditional
        expected = '    h = "In all chapters"'
        self.assertLine(lines[3], False, False, expected)
