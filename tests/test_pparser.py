import textwrap

from waelstow import noted_raise

from tests.base import BaseParserTestCase
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

class PoundParserTestCase(BaseParserTestCase):

    def test_line_parsing(self):
        # Test a comment
        text = "# This is a sample file"
        parser = parse_pound_content(text)
        self.assertParser(parser, False, [text,], None, None)

        # Test a regular line
        text = 'a = "In all chapters"   # inline comment'
        parser = parse_pound_content(text)
        self.assertParser(parser, False, [text,], None, None)

        # Test a full-range conditional line with inline comment
        text = 'b = "In chapters 1-3"   #@= 1-3 comment on conditional'
        expected = 'b = "In chapters 1-3"   # comment on conditional'
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 1, 3)

        # Test lower open range conditional line
        text = 'c = "In chapters 1-2"   #@= -2'
        expected = 'c = "In chapters 1-2"'
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 1, 2)

        # Test upper open range conditional line
        text = 'd = "In chapters 2 on"  #@= 2-'
        expected = 'd = "In chapters 2 on"'
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected,], 2, None)

        # Test commented out line of code
        text = '#@@ 1-2 count = 4'
        expected = 'count = 4'
        parser = parse_pound_content(text)
        self.assertParser(parser, True, [expected, ], 1, 2)

    def test_nested_parsing(self):
        data = {
            'a': '12345',
            'b': '2345',
            'c': '3',
            'd': '2',
            'e': '5',
            'f': '34',
            'g': '3',
            'h': '4',
            'i': '2345',
        }
        code = f"""\
            a = {data['a']}

            #@[ 2-

            b = {data['b']}

            c = {data['c']}  #@= 3

            #@@ 2 d = {data['d']}

            #@+ 5
            #@- e = {data['e']}

            #@[ 3-4
            f = {data['f']}
            g = {data['g']} #@= 3

            #@+ 4
            #@- h = {data['h']}

            #@]

            i = {data['i']}

            #@]
        """
        code = textwrap.dedent(code)
        parser = parse_pound_content(code)

        for line in parser.lines:
            if line.content == '':
                continue

            #print("Testing ", line.content)
            #print("   ", line.lower, line.upper)

            lower = 1 if line.lower is None else line.lower
            upper = 5 if line.upper is None else line.upper
            for num in range(lower, upper + 1):
                self.assertIn(str(num), line.content)

    def test_bad_parsing(self):
        text = 'x = 3 #@'
        with self.assertRaises(ValueError):
            parse_pound_content(text)

        text = 'x = 3 #@!'
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
        self.assertParser(parser, True, EXPECTED_BLOCK3, 2, None)
