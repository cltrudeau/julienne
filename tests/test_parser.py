from unittest import TestCase

from waelstow import noted_raise

from julienne.parsers import parse_pound_content

# ============================================================================

CODE_BLOCK1 = """\
#@+ 3-4
#@- e = "In chapters 3 to 4"  # inline comment
#@- f = "  as a block"\
"""

EXPECTED_BLOCK1 = [
    """e = "In chapters 3 to 4"  # inline comment""",
    """f = "  as a block"\
""",
]


CODE_BLOCK2 = """\
for x in range(10):
    #@+ 1-2 block header with comment
    #@- g= "In chapters 1 and 2"
    h = "In all chapters"\
"""

EXPECTED_BLOCK2 = [
    """for x in range(10):""",
    """    # block header with comment""",
    """    g= "In chapters 1 and 2"\
""",
    """    h = "In all chapters"\
"""
]

CODE_BLOCK3 = """\
#@[ 2- uncommented conditional block
def foo():
    print('Blah de blah')
#@]
"""

EXPECTED_BLOCK3 = [
    """# uncommented conditional block""",
    """def foo():""",
    """    print('Blah de blah')""",
]

# ----------------------------------------------------------------------------

class ParserTestCase(TestCase):

    def assertParser(self, parser, all_conditional, text, lowest, highest):
        self.assertEqual(len(text), len(parser.lines))

        for expected, result in zip(text, parser.lines):
            self.assertEqual(expected, result.content)

        self.assertEqual(all_conditional, parser.all_conditional)
        self.assertEqual(lowest, parser.lowest)
        self.assertEqual(highest, parser.highest)

    def test_line_parsing(self):
        # Test a comment
        text = "# This is a sample file"
        parser = parse_pound_content(text)
        self.assertParser(parser, False, [text,], 1, -1)

        # Test a regular line
        text = 'a = "In all chapters"   # inline comment'
        parser = parse_pound_content(text)
        self.assertParser(parser, False, [text,], 1, -1)

        # Test a full-range conditional line with inline comment
        text = 'b = "In chapters 1-3"   #@= 1-3 comment on conditional'
        expected = 'b = "In chapters 1-3"   # comment on conditional'
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 1, 3)

        # Test lower open range conditional line
        text = 'c = "In chapters 1-2"   #@= -2'
        expected = 'c = "In chapters 1-2"   '
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 1, 2)

        # Test upper open range conditional line
        text = 'd = "In chapters 2 on"  #@= 2-'
        expected = 'd = "In chapters 2 on"  '
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 2, -1)

    def test_bad_parsing(self):
        text = 'x = 3 #@'
        with self.assertRaises(ValueError):
            parse_pound_content(text)

        text = 'x = 3 #@*'
        with self.assertRaises(ValueError):
            parse_pound_content(text)

    def test_block_parsing(self):
        #--- Test a conditional block
        parser = parse_pound_content(CODE_BLOCK1)
        self.assertParser(parser, True, EXPECTED_BLOCK1, 3, 4)

        #--- Test a conditional block inside an indent
        parser = parse_pound_content(CODE_BLOCK2)
        self.assertParser(parser, False, EXPECTED_BLOCK2, 1, 2)

        # Validate the non-conditional parts
        with noted_raise("[chapter={chapter}]"):
            for chapter in range(1, 4):
                content = parser.lines[0].get_content(chapter)
                self.assertIsNotNone(content)
                content = parser.lines[3].get_content(chapter)
                self.assertIsNotNone(content)

                # Line[1] and Line[2] are conditional, showing in 
                # chapters 1-2 only
                if chapter <= 2:
                    content = parser.lines[1].get_content(chapter)
                    self.assertIsNotNone(content)
                    content = parser.lines[2].get_content(chapter)
                    self.assertIsNotNone(content)
                else:
                    content = parser.lines[1].get_content(chapter)
                    self.assertIsNone(content)
                    content = parser.lines[2].get_content(chapter)
                    self.assertIsNone(content)

        # --- Test an uncommented conditional block
        parser = parse_pound_content(CODE_BLOCK3)
        self.assertParser(parser, True, EXPECTED_BLOCK3, 2, -1)
