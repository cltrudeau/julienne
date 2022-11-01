# parser.py
#   Contains the line parser for conditional content

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

        index = content.find("#:")
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
        if marker.startswith('#::'):
            # Line is a header for a continuing block
            self.block_header = self
            try:
                token, rest = marker[3:].split(' ', 1)
            except ValueError:
                # No space after marker
                token = marker[3:]
                rest = ''
        elif marker.startswith('#:'):
            try:
                token, rest = marker[2:].split(' ', 1)
            except ValueError:
                # No space after marker
                token = marker[2:]
                rest = ''
        else:
            raise ValueError(f"Attempted to parse bad marker *{marker}*")

        if token[0] == '-':
            # No lower bound
            self.lower = 1
            self.upper = token[1:]
        elif '-' in token:
            # Range
            self.lower, self.upper = token.split('-')
        else:
            self.lower = token
            self.upper = token

        if self.upper == '':
            self.upper = -1

        self.lower = int(self.lower)
        self.upper = int(self.upper)

        if rest:
            self.content = f"{content[:index]}# {rest}"
        else:
            self.content = content[:index].rstrip()

    def get_content(self, chapter):
        # if in range
        return self.content

        # not in range
        return ''
