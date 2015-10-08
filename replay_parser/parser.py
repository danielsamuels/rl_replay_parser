# -*- coding: utf-8 -*-

import pprint
import sys
import struct

import parsers
import readers


class ReplayParser:

    def __init__(self, debug=False):
        self.debug = debug

    def parse(self, replay_file):
        # Work out what type of file we're dealing with.
        if hasattr(replay_file, 'read'):
            replay_file.seek(0)
        elif hasattr(replay_file, 'file'):
            replay_file = open(replay_file.file.path, 'rb')
        elif isinstance(replay_file, str):
            replay_file = open(replay_file, 'rb')
        else:
            raise TypeError("Unable to determine file type.")

        data = {}
        # Length of properties section (+36)
        properties_length = readers.read_integer(replay_file)

        # CRC check.
        crc = readers.read_unknown(replay_file, 4)

        # Version number
        data['version_number'] = '{}.{}'.format(
            readers.read_integer(replay_file),
            readers.read_integer(replay_file)
        )

        # Identifier
        data['version'] = readers.read_string(replay_file)

        data['header'] = readers.read_properties(replay_file)

        if 'Team0Score' not in data['header']:
            data['header']['Team0Score'] = 0

        if 'Team1Score' not in data['header']:
            data['header']['Team1Score'] = 0

        self.number_of_goals = data['header']['Team0Score'] + data['header']['Team1Score']

        if self.number_of_goals == 0 and 'Goals' not in data['header']:
            data['header']['Goals'] = []

        assert replay_file.tell() == properties_length + 8

        # Size of remaining data.
        remaining_length = readers.read_integer(replay_file)

        # TODO: Potentially a CRC check?
        crc_2 = readers.read_unknown(replay_file, 4)

        data['level_info'] = readers.read_level_info(replay_file)

        data['key_frames'] = readers.read_key_frames(replay_file)

        data['network_stream'] = readers.read_network_stream(replay_file)

        print replay_file.tell()

        data['debug_strings'] = readers.read_debug_strings(replay_file)

        data['goal_ticks'] = readers.read_goal_ticks(replay_file)

        data['packages'] = readers.read_packages(replay_file)

        data['objects'] = readers.read_objects(replay_file)

        data['name_table'] = readers.read_name_table(replay_file)

        data['classes'] = readers.read_classes(replay_file)

        data['property_tree'] = readers.read_property_tree(replay_file, data['objects'], data['classes'])

        assert replay_file.tell() == properties_length + remaining_length + 16

        network_data = parsers.parse_network_stream(data['network_stream'])

        # Run some manual parsing operations.
        data = parsers.manual_parse(data, replay_file)

        # data['network_stream'] = self._process_network_stream(data['network_stream'])
        return data


if __name__ == '__main__':  # pragma: no cover
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        results = ReplayParser(debug=False).parse(replay_file)
        try:
            pprint.pprint(results)
        except IOError as e:
            print(e)
        except struct.error as e:
            print(e)
        except Exception as e:
            print(e)
