# parser.py
#   Contains the line parser for conditional content

# ===========================================================================
# Utilities
# ===========================================================================

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


chapter_in_range = lambda chapter, conditional, lower, upper: \
    not conditional or (upper == -1 and lower <= chapter) or \
        (lower <= chapter <= upper)

# ---------------------------------------------------------------------------

class Line:
    def __init__(self, content, block_header=None):
        self.block_header = block_header

        index = content.find("#>")
        if index >= 0:
            # Continuing from conditional block header
            self.conditional = True
            self.block_header = block_header
            self.lower = block_header.lower
            self.upper = block_header.upper

            # Remove the marker characters from the line
            self.content = f"{content[0:index]}{content[index+2:]}"
            return

        # Not a continuing block line, reset the header
        self.block_header = None

        index = content.find("#@")
        if index == -1:
            # No juli comment, keep the line unconditionally
            self.conditional = False
            self.lower = None
            self.upper = None
            self.content = content
            return

        # Line contains a conditional comment
        self.conditional = True

        marker = content[index:].strip()
        if marker.startswith('#@@'):
            # Line is a header for a continuing block
            self.block_header = self
            try:
                token, rest = marker[3:].split(' ', 1)
                self.content = f"{content[:index]}# {rest}"
            except ValueError:
                # No space after marker, ignore this line
                token = marker[3:]
                self.content = None
        else: # marker is a line marker, just "#@"
            try:
                token, rest = marker[2:].split(' ', 1)
                self.content = f"{content[:index]}# {rest}"
            except ValueError:
                # No space after marker
                token = marker[2:]
                self.content = f"{content[:index]}"

        try:
            self.lower, self.upper = range_token(token)
        except:
            raise ValueError( ("Juli comment marker could not be parsed for "
                f"line ***{content}***"))

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
