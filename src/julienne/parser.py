# parser.py
#   Contains the line parser for conditional content
from collections import namedtuple
from enum import Enum

# ===========================================================================

ParseMode = Enum('ParseMode', ['NORMAL', 'BLOCK_COMMENT', 'BLOCK_OPEN'])

Marker = namedtuple('Marker', ["jtype", "lower", "upper", "comment"])

ALL_JTYPES = ('=', '+', '-', '[', ']')
RANGED_JTYPES = ('=', '+', '[')

# ===========================================================================

class Parser:
    def __init__(self):
        self.lines = []
        self.all_conditional = True
        self.lowest = None
        self.highest = None
        self.mode = ParseMode.NORMAL
        self.block_header = None

    def add_line(self, text, conditional, lower, upper):
        line = Line(text, conditional, lower, upper)
        self.lines.append(line)

    def add_if_commented(self, text, index, marker):
        line_text = ''
        if marker.comment:
            # Marker line has a comment, preserve leading spaces and insert
            line_text = text[0:index] + f"# {marker.comment}"

        if line_text:
            self.add_line(line_text, True, marker.lower, marker.upper)

    def reset_mode(self):
        self.mode = ParseMode.NORMAL
        self.block_header = None

    def set_mode(self, mode, block_header):
        self.mode = mode
        self.block_header = block_header

    def manage_boundaries(self, lower, upper):
        if self.lowest is None:
            self.lowest = lower
        elif lower < self.lowest:
            self.lowest = lower

        if self.highest is None:
            self.highest = upper
        else:
            if upper == -1 or (upper != -1 and upper > self.highest):
                self.highest = upper

    def fix_boundaries(self):
        if self.lowest is None:
            self.lowest = 1

        if self.highest is None:
            self.highest = -1

# ===========================================================================

chapter_in_range = lambda chapter, conditional, lower, upper: \
    not conditional or (upper == -1 and lower <= chapter) or \
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
        upper = -1

    return int(lower), int(upper)


def parse_marker(text, line_no):
    # First character is the julienne type
    try:
        jtype = text[0]
    except:
        error = f"No marker type after '#@' in line {line_no}"
        raise ValueError

    if jtype not in ALL_JTYPES:
        error = f"Unknown marker type on line {line_no}, *{text}*"
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

def parse_content(content):
    """Parses a multi-line string into a series of lines. Each line may be
    conditional. Returns a list of Line objects along with whether all the
    lines are conditional or not, and the ultimate lower and upper chapter
    boundaries on the content.
    """

    # Strip trailing newlines before parsing
    if content and content[-1] == '\n':
        content = content[:-1]

    parser = Parser()

    # Loop through lines in content
    for line_no, text in enumerate(content.split('\n')):
        index = text.find("#@")
        if index == -1:
            if parser.mode == ParseMode.BLOCK_OPEN:
                # Inside an open block, add conditional line based on parent
                parser.add_line(text, True, parser.block_header.lower,
                    parser.block_header.upper)
            else:
                # No juli comment, keep the line unconditionally
                parser.add_line(text, False, None, None)
                parser.reset_mode()
                parser.all_conditional = False

            continue

        # Found a conditional line, behaviour changes based on the type of
        # conditional
        line_text = ''
        marker = parse_marker(text[index+2:], line_no)

        # Determine line text based on jtype
        if marker.jtype == '=':
            # Inline conditional, just this line, reset to normal mode
            parser.reset_mode()
            line_text = text[:index]
            if marker.comment:
                line_text += f"# {marker.comment}"

            if line_text:
                parser.add_line(line_text, True, marker.lower, marker.upper)
        elif marker.jtype == '+':
            # Header for a block comment
            parser.set_mode(ParseMode.BLOCK_COMMENT, marker)
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

            if line_text:
                parser.add_line(line_text, True, parser.block_header.lower, 
                    parser.block_header.upper)
        elif marker.jtype == '[':
            # Header for an open block 
            parser.set_mode(ParseMode.BLOCK_OPEN, marker)
            parser.add_if_commented(text, index, marker)
        elif marker.jtype == ']':
            # Closing marker for open blocks, reset to normal
            parser.reset_mode()
            parser.add_if_commented(text, index, marker)

        # Manage boundary range
        if marker.jtype == '-':
            # Block Comment body
            parser.manage_boundaries(parser.block_header.lower,
                parser.block_header.upper)
        elif marker.jtype != ']':
            # Boundaries for open block have been processed already, all other
            # jtypes need to have their boundaries checked
            parser.manage_boundaries(marker.lower, marker.upper)

    parser.fix_boundaries()
    return parser

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
