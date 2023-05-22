# parser.py
#   Contains the line parser for conditional content
from collections import namedtuple
from enum import Enum

# ===========================================================================

ParseMode = Enum('ParseMode', ['NORMAL', 'BLOCK_COMMENT', 'BLOCK_OPEN'])

Marker = namedtuple('Marker', ["jtype", "lower", "upper", "comment"])

ALL_JTYPES = ('@', '=', '+', '-', '[', ']', '*')
RANGED_JTYPES = ('@', '=', '+', '[')

# ===========================================================================

class Parser:
    CONTENT_TYPES = Enum('ParserContentTypes', ['POUND', 'XML'])

    class Context:
        def __init__(self, mode, marker):
            self.mode = mode
            self.marker = marker

    def __init__(self, content_type):
        self.lines = []
        self.all_conditional = True
        self.content_type = content_type

        context = Parser.Context(ParseMode.NORMAL, None)
        self.stack = [context, ]

    # --- Stack and mode methods to deal with nested markers
    def nest(self, mode, marker):
        context = Parser.Context(mode, marker)
        self.stack.append(context)

    def close_nest(self):
        self.stack.pop()

    @property
    def parent_marker(self):
        return self.stack[-1].marker

    @property
    def mode(self):
        return self.stack[-1].mode

    # --- Line management
    def add_line(self, text, conditional, lower, upper):
        line = Line(text, conditional, lower, upper)
        self.lines.append(line)

    def add_if_commented(self, text, index, marker):
        line_text = ''
        if marker.comment:
            # Marker line has a comment, preserve leading spaces and insert
            if self.content_type == self.CONTENT_TYPES.POUND:
                line_text = text[0:index] + f"# {marker.comment}"
            else:
                line_text = text[0:index] + f"<!-- {marker.comment} -->"

        if line_text:
            self.add_line(line_text, True, marker.lower, marker.upper)

    def get_range(self):
        """Returns range information about parsed file as a tuple (bottom,
        top, biggest). Where bottom is the lowest chapter the file uses, top
        is the highest chapter and None indicates limitless, and biggest is the
        largest chapter number mentioned.
        """
        bottom = None
        top = None
        biggest = None

        for line in self.lines:
            if bottom is None:
                bottom = line.lower
            if line.lower is not None and bottom < line.lower:
                bottom = line.lower

            if top is None:
                top = line.upper
            if line.upper is not None and line.upper > top:
                top = line.upper

            if biggest is None:
                if line.lower is not None:
                    biggest = line.lower

                if line.upper is not None:
                    biggest = line.upper
            else:
                if line.lower is not None and line.lower > biggest:
                    biggest = line.lower
                elif line.upper is not None and line.upper > biggest:
                    biggest = line.upper

        return bottom, top, biggest

# ===========================================================================

chapter_in_range = lambda chapter, conditional, lower, upper: \
    not conditional or (upper is None and lower <= chapter) or \
        (lower <= chapter <= upper)


def range_token(token):
    lower = None
    upper = None

    if token[0] == '-':
        # No lower bound
        lower = 1
        upper = token[1:]
    elif '-' in token:
        # Range
        lower, upper = token.split('-')
    else:
        lower = token
        upper = token

    if upper == '':
        upper = None

    if lower is not None:
        lower = int(lower)
    if upper is not None:
        upper = int(upper)

    return lower, upper


def parse_marker(text, line_no):
    # First character is the julienne type
    try:
        jtype = text[0]
    except:
        error = (f"No marker type after '@' in line {line_no}, must be one of"
            ",".join(ALL_JTYPES) )
        raise ValueError

    if jtype not in ALL_JTYPES:
        error = (f"Unknown marker type on line {line_no}, *{text}*, must be"
            "one of '")
        error += ",".join(ALL_JTYPES) + "'"
        raise ValueError(error)

    lower = None
    upper = None
    comment = None
    try:
        # Skip the jtype, remove any spaces between the jtype and the range
        # (if there is one)
        parts = text[1:].lstrip().split(' ', 1)
        if len(parts) > 1:
            comment = parts[1]

        if jtype in RANGED_JTYPES:
            lower, upper = range_token(parts[0])
    except:
        error = f"Bad inline marker on line {line_no}, *{text}*"
        raise ValueError(error)

    return Marker(text[0], lower, upper, comment)

# ---------------------------------------------------------------------------

class Line:
    def __init__(self, content, conditional, lower, upper):
        self.content = content
        self.conditional = conditional
        self.lower = lower
        self.upper = upper

    def get_content(self, chapter):
        # Check if the line should be included, any of:
        #   * not a conditional statement
        #   * chapter is larger than lower and there is no upper bound
        #   * chapter value is between lower and upper bounds
        if self.content is not None and chapter_in_range(chapter, 
                self.conditional, self.lower, self.upper):
            return self.content

        # Line not in chapter range
        return None

# ===========================================================================
# Parsers
# ===========================================================================

# Python (pound-style comment) Parser

def parse_pound_content(content):
    """Parses a multi-line string containing code where the comment character
    is a # into a series of lines. Each line may be conditional. Returns a
    list of Line objects along with whether all the lines are conditional or
    not, and the ultimate lower and upper chapter boundaries on the content.
    """

    # Strip trailing newlines before parsing
    if content and content[-1] == '\n':
        content = content[:-1]

    parser = Parser(Parser.CONTENT_TYPES.POUND)

    # Loop through lines in content
    for line_no, text in enumerate(content.split('\n')):
        index = text.find("#@")
        if index == -1:
            if parser.mode == ParseMode.BLOCK_OPEN:
                # Inside an open block, add conditional line based on parent
                parent = parser.parent_marker
                parser.add_line(text, True, parent.lower, parent.upper)
            else:
                # No juli comment, could be closing the block
                if parser.mode == ParseMode.BLOCK_COMMENT:
                    parser.close_nest()

                if len(parser.stack) == 1:
                    # Not nested, keep the line unconditionally
                    parser.add_line(text, False, None, None)
                    parser.all_conditional = False
                else:
                    # Nested, keep the line using parent's conditions
                    parent = parser.parent_marker
                    parser.add_line(text, True, parent.lower, parent.upper)

            continue

        # Found a conditional line, behaviour changes based on the type of
        # conditional
        line_text = ''
        marker = parse_marker(text[index+2:], line_no)

        # Determine line text based on jtype
        if parser.mode == ParseMode.BLOCK_COMMENT and marker.jtype != '-':
            # Anything besides a "-" marker pops the context stack
            parser.close_nest()

        if marker.jtype == '=':
            # Inline conditional, comment after the code
            line_text = text[:index]
            if marker.comment:
                line_text += f"# {marker.comment}"
            else:
                # Remove any trailing spaces if there was no comment,
                # especially useful if you're running black after
                line_text = line_text.rstrip()

            if line_text:
                parser.add_line(line_text, True, marker.lower, marker.upper)
        elif marker.jtype == '@':
            # Inline conditional, comment before code (code is commented out)
            # For other types, the comment comes after the type and the
            # boundary, in this case the "comment" is the code to be used
            if marker.comment:
                parser.add_line(marker.comment, True, marker.lower,
                    marker.upper)
        elif marker.jtype == '+':
            # Header for a block comment
            parser.nest(ParseMode.BLOCK_COMMENT, marker)
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == '-':
            # Body for a block comment
            if parser.mode != ParseMode.BLOCK_COMMENT:
                error = (f"Block marker found without header on line "
                    f"{line_no} *{text}*")
                raise ValueError(error)

            # Remove the "#@- " token from the text, preserve any leading
            # spaces
            line_text = text[0:index] + text[index+4:]
            parent = parser.parent_marker
            parser.add_line(line_text, True, parent.lower, parent.upper)
        elif marker.jtype == '[':
            # Header for an open block
            parser.nest(ParseMode.BLOCK_OPEN, marker)
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == ']':
            # Closing marker for open blocks, reset to normal
            parser.close_nest()
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == '*':
            # Juli comment, do nothing
            pass

    return parser

# ---------------------------------------------------------------------------
# XML Style parser

def parse_xml_content(content):
    """Parses a multi-line string containing code where the comment markers
    are <!-- -->. Strings are turned into a sequence of lines.  Lines may be
    conditional. Returns a list of Line objects along with whether all the
    lines are conditional or not, and the ultimate lower and upper chapter
    boundaries on the content.
    """

    # Strip trailing newlines before parsing
    if content and content[-1] == '\n':
        content = content[:-1]

    parser = Parser(Parser.CONTENT_TYPES.XML)

    # Loop through lines in content
    for line_no, text in enumerate(content.split('\n')):
        index = text.find("<!--@")
        if index == -1:
            # Check for block comment ending
            pos = text.find("@+-->")
            if pos != -1:
                if parser.mode != ParseMode.BLOCK_COMMENT:
                    error = ("Block closing marker '@+-->' found without "
                        f"opener on line {line_no} *{text}*")
                    raise ValueError(error)

                # Remove the "@+--> " token from the text
                line_text = text[0:pos].strip()

                if line_text:
                    parent = parser.parent_marker
                    parser.add_line(line_text, True, parent.lower, parent.upper)

                parser.close_nest()
                continue

            # No marker, check if we're in an open block mode
            if parser.mode in (ParseMode.BLOCK_OPEN, ParseMode.BLOCK_COMMENT):
                # add conditional line based on parent
                parent = parser.parent_marker
                parser.add_line(text, True, parent.lower, parent.upper)
                continue

            # ELSE: not a juli comment, keep the line unconditionally
            parser.add_line(text, False, None, None)
            parser.all_conditional = False
            continue

        # Found a conditional line, behaviour changes based on the type of
        # conditional, start by removing any closing XML comments, then parse
        # the marker text
        line_text = ''
        closer = text.find("-->")
        if closer != -1:
            text = text[0:closer].rstrip()

        marker = parse_marker(text[index+5:], line_no)

        # Determine line text based on jtype
        if marker.jtype == '=':
            # Inline conditional, just this line
            line_text = text[:index]
            if marker.comment:
                line_text += f"<!-- {marker.comment} -->"

            if line_text:
                parser.add_line(line_text, True, marker.lower, marker.upper)
        elif marker.jtype == '+':
            # Header for a block comment
            parser.nest(ParseMode.BLOCK_COMMENT, marker)
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == '-':
            error = ("Unsupported marker type '-' for XML doc on line"
                f"{line_no} *{text}*")
            raise ValueError(error)
        elif marker.jtype == '[':
            # Header for an open block
            parser.nest(ParseMode.BLOCK_OPEN, marker)
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == ']':
            # Closing marker for open blocks, reset to normal
            parser.close_nest()
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == '*':
            # Juli comment, do nothing
            pass

    return parser
