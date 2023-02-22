from unittest import TestCase

class BaseParserTestCase(TestCase):

    def assertParser(self, parser, all_conditional, text, lowest, highest):
        self.assertEqual(len(text), len(parser.lines))

        for expected, result in zip(text, parser.lines):
            self.assertEqual(expected, result.content)

        self.assertEqual(all_conditional, parser.all_conditional)

        bottom, top, _ = parser.get_range()
        self.assertEqual(lowest, bottom)
        self.assertEqual(highest, top)
