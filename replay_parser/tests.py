from replay_parser import ReplayParser

import os
from StringIO import StringIO
import struct
import sys
import unittest


class TestReplayParser(unittest.TestCase):

    folder_path = '{}/example_replays/'.format(
        os.path.dirname(os.path.realpath(__file__))
    )

    def test_104_replay(self):
        """
        A replay from version 1.04.
        """

        parser = ReplayParser()

        with open(self.folder_path + '1.04.replay', 'rb') as f:
            response = parser.parse(f)
            self.assertIsInstance(response, dict)
            self.assertEqual(response['header']['Id'], '0AB18BAB4CCE97201B7753A84B358D48')

    def test_105_replay(self):
        """
        A replay from version 1.05.
        """

        parser = ReplayParser()

        with open(self.folder_path + '1.05.replay', 'rb') as f:
            response = parser.parse(f)
            self.assertIsInstance(response, dict)
            self.assertEqual(response['header']['Id'], '56E7708C45ED1CF3B9E51EBF1ADF4431')

    def test_broken_replay(self):
        """
        This replay file was purposefully broken by deleting a large portion
        of the data.
        """

        parser = ReplayParser()

        with open(self.folder_path + 'broken.replay', 'rb') as f:
            with self.assertRaises(struct.error):
                parser.parse(f)

    def test_keyframes_missing_replay(self):
        """
        For some reason, this replay is missing the key frames from when goals
        were scored, so that data is not available to a parser. This is a good
        test to ensure the parser can handle odd scenarios.
        """

        parser = ReplayParser()

        with open(self.folder_path + 'keyframes_missing.replay', 'rb') as f:
            response = parser.parse(f)
            self.assertIsInstance(response, dict)
            self.assertEqual(response['header']['Id'], '50D5031342FF90D9F25BE5A0152E56B8')

    def test_keyframes_2s_replay(self):
        """
        For some reason, this replay is missing the key frames from when goals
        were scored, so that data is not available to a parser. This is a good
        test to ensure the parser can handle odd scenarios.
        """

        parser = ReplayParser()

        with open(self.folder_path + '2s.replay', 'rb') as f:
            response = parser.parse(f)
            self.assertIsInstance(response, dict)
            self.assertEqual(response['header']['Id'], '016D2CB946676AFDC11D29BFD84C9CB3')

    def test_file_attr(self):
        class Obj:
            class File:
                path = self.folder_path + '2s.replay'

            file = File()

        parser = ReplayParser()

        response = parser.parse(Obj())
        self.assertIsInstance(response, dict)
        self.assertEqual(response['header']['Id'], '016D2CB946676AFDC11D29BFD84C9CB3')

    def test_file_str(self):
        parser = ReplayParser(debug=True)
        response = parser.parse(self.folder_path + '2s.replay')

        self.assertIsInstance(response, dict)
        self.assertEqual(response['header']['Id'], '016D2CB946676AFDC11D29BFD84C9CB3')

    def test_file_exception(self):
        parser = ReplayParser()

        with self.assertRaises(TypeError):
            parser.parse(None)

    def test_read_name_table(self):
        parser = ReplayParser()

        # Passing some unusual data into this function will cause it to throw
        # an exception.
        with open(self.folder_path + '2s.replay', 'rb') as f:
            with self.assertRaises(Exception):
                parser._read_name_table(f)

    def test_debug_bits(self):
        parser = ReplayParser()

        data = StringIO()
        data.write(u'\u0001')
        data.seek(0)

        stdout = sys.stdout
        sys.stdout = StringIO()

        bits = parser._debug_bits(data)

        output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = stdout

        self.assertEqual(output, """1.......
.0......
..0.....
...0....
....0...
.....0..
......0.
.......0
""")
        self.assertEqual(bits, (1, 0, 0, 0, 0, 0, 0, 0))

    def test_debug_bits_with_labels(self):
        parser = ReplayParser()

        data = StringIO()
        data.write(u'\u0001')
        data.seek(0)

        stdout = sys.stdout
        sys.stdout = StringIO()

        bits = parser._debug_bits(data, ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])

        output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = stdout

        self.assertEqual(output, """1....... = A: Not set
.0...... = B: Not set
..0..... = C: Not set
...0.... = D: Not set
....0... = E: Not set
.....0.. = F: Not set
......0. = G: Not set
.......0 = H: Not set
""")
        self.assertEqual(bits, (1, 0, 0, 0, 0, 0, 0, 0))

    def test_read_bit(self):
        parser = ReplayParser()
        self.assertEqual(parser._read_bit(u'\u0001', 0), 1)
        self.assertEqual(parser._read_bit(u'\u0001', 1), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 2), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 3), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 4), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 5), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 6), 0)
        self.assertEqual(parser._read_bit(u'\u0001', 7), 0)
