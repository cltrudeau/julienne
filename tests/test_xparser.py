import textwrap

from waelstow import noted_raise

from tests.base import BaseParserTestCase
from julienne.parsers import parse_xml_content

# ============================================================================

BLOCK1 = """\
<!--@+ 3-4
In chapters 3 to 4 <!-- inline comment -->
as a block
@+-->
"""

EXPECTED_BLOCK1 = [
    "In chapters 3 to 4 <!-- inline comment -->",
    """as a block\
""",
]

BLOCK2 = """\
Some unindented text
    <!--@+ 1-2 block header with comment
    In chapters 1 and 2
    @+-->
    some indented text\
"""

EXPECTED_BLOCK2 = [
    """Some unindented text""",
    """    <!-- block header with comment -->""",
    """    In chapters 1 and 2""",
    """    some indented text\
""",
]

BLOCK3 = """\
<!--@[ 2- uncommented conditional block -->
Some text
    some indented text
<!--@] -->
"""

EXPECTED_BLOCK3 = [
    """<!-- uncommented conditional block -->""", 
    """Some text""", 
    """    some indented text\
"""
]
# ----------------------------------------------------------------------------

class XMLParserTestCase(BaseParserTestCase):

    def test_line_parsing(self):
        # Test a comment
        text = "<!-- sample comment line -->"
        parser = parse_xml_content(text)
        self.assertParser(parser, False, [text,], None, None)

        # Test a regular line
        text = 'Sample text with <!-- inline comment -->'
        parser = parse_xml_content(text)
        self.assertParser(parser, False, [text,], None, None)

        # Test a full-range conditional line with inline comment
        text = 'In chapters 1-3   <!--@= 1-3 comment on conditional -->'
        expected = 'In chapters 1-3   <!-- comment on conditional -->'
        parser = parse_xml_content(text)
        self.assertParser(parser, True, [expected,], 1, 3)

        # Test lower open range conditional line
        text = 'In chapters 1-2   <!--@= -2 -->'
        expected = 'In chapters 1-2   '
        parser = parse_xml_content(text)
        self.assertParser(parser, True, [expected,], 1, 2)

        # Test upper open range conditional line
        text = 'In chapters 2 on  <!--@= 2- -->'
        expected = 'In chapters 2 on  '
        parser = parse_xml_content(text)
        self.assertParser(parser, True, [expected,], 2, None)

    def test_nested_parsing(self):
        data = {
            'a': '12345',
            'b': '2345',
            'c': '3',
            'e': '5',
            'f': '34',
            'g': '3',
            'h': '4',
            'i': '2345',
        }
        code = f"""\
            a = {data['a']}

            <!--@[ 2-

            b = {data['b']}
            c = {data['c']}  <!--@= 3 -->

            <!--@+ 5
            e = {data['e']}
            @+-->

            <!--@[ 3-4

            f = {data['f']}
            g = {data['g']} <!--@= 3 -->

            <!--@+ 4
            h = {data['h']}
            @+-->

            <!--@] -->

            i = {data['i']}

            <!--@] -->
        """
        code = textwrap.dedent(code)
        parser = parse_xml_content(code)

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
        text = 'x = 3 <!--@ -->'
        with self.assertRaises(ValueError):
            parse_xml_content(text)

        text = 'x = 3 <!--@! -->'
        with self.assertRaises(ValueError):
            parse_xml_content(text)

    def test_block_parsing(self):
        #--- Test a conditional block
        parser = parse_xml_content(BLOCK1)
        self.assertParser(parser, True, EXPECTED_BLOCK1, 3, 4)

        #--- Test a conditional block inside an indent
        parser = parse_xml_content(BLOCK2)
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
        parser = parse_xml_content(BLOCK3)
        self.assertParser(parser, True, EXPECTED_BLOCK3, 2, None)
