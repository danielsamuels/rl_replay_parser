# -*- coding: utf-8 -*-

import pprint
import re
import sys
import struct


class ReplayParser:

    SERVER_REGEX = r'((EU|USE|USW|OCE|SAM)\d+(-[A-Z][a-z]+)?)'

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
        properties_length = self._read_integer(replay_file)

        # CRC check.
        crc = self._read_unknown(replay_file, 4)

        # Version number
        data['version_number'] = '{}.{}'.format(
            self._read_integer(replay_file),
            self._read_integer(replay_file)
        )

        # Identifier
        data['version'] = self._read_string(replay_file)

        data['header'] = self._read_properties(replay_file)

        if 'Team0Score' not in data['header']:
            data['header']['Team0Score'] = 0

        if 'Team1Score' not in data['header']:
            data['header']['Team1Score'] = 0

        self.number_of_goals = data['header']['Team0Score'] + data['header']['Team1Score']

        if 'Goals' not in data['header']:
            data['header']['Goals'] = []

        assert replay_file.tell() == properties_length + 8

        # Size of remaining data.
        remaining_length = self._read_integer(replay_file)

        # TODO: Potentially a CRC check?
        crc_2 = self._read_unknown(replay_file, 4)

        data['level_info'] = self._read_level_info(replay_file)

        data['key_frames'] = self._read_key_frames(replay_file)

        data['network_stream'] = self._read_network_stream(replay_file)

        data['debug_strings'] = self._read_debug_strings(replay_file)

        data['goal_ticks'] = self._read_goal_ticks(replay_file)

        data['packages'] = self._read_packages(replay_file)

        data['objects'] = self._read_objects(replay_file)

        data['name_table'] = self._read_name_table(replay_file)

        data['classes'] = self._read_classes(replay_file)

        data['property_tree'] = self._read_property_tree(replay_file, data['objects'], data['classes'])

        assert replay_file.tell() == properties_length + remaining_length + 16

        # Run some manual parsing operations.
        data = self.manual_parse(data, replay_file)

        # data['network_stream'] = self._process_network_stream(data['network_stream'])

        if replay_file.file.__class__.__name__ != 'InMemoryUploadedFile':
            replay_file.close()

        return data

    def _read_properties(self, replay_file):
        results = {}

        while True:
            property_info = self._read_property(replay_file)

            if property_info:
                results[property_info['name']] = property_info['value']
            else:
                return results

    def _read_property(self, replay_file):
        name_length = self._read_integer(replay_file)

        property_name = self._read_string(replay_file, name_length)

        if property_name == 'None':
            return None

        type_name = self._read_string(replay_file)

        value = None

        if type_name == 'IntProperty':
            value_length = self._read_integer(replay_file, 8)
            value = self._read_integer(replay_file, value_length)

        elif type_name == 'StrProperty':
            unknown = self._read_integer(replay_file, 8)
            length = self._read_integer(replay_file)

            if length < 0:
                length = abs(length) * 2
                value = self._read_string(replay_file, length)[:-1].decode('utf-16').encode('utf-8')
            else:
                value = self._read_string(replay_file, length)

        elif type_name == 'FloatProperty':
            length = self._read_integer(replay_file, 8)
            value = self._read_float(replay_file, length)

        elif type_name == 'NameProperty':
            unknown = self._read_integer(replay_file, 8)
            value = self._read_string(replay_file)

        elif type_name == 'ArrayProperty':
            # I imagine that this is the length of bytes that the data
            # in the "array" actually take up in the file.
            unknown = self._read_integer(replay_file, 8)
            array_length = self._read_integer(replay_file)

            value = [
                self._read_properties(replay_file)
                for x in xrange(array_length)
            ]
        elif type_name == 'ByteProperty':
            # This could be a new array type.
            # 25 (8) / 15 (4) / Str len 15 / Int (4) - 21 / Str len 21

            self._read_integer(replay_file, 8)
            key_length = self._read_integer(replay_file, 4)
            byte_key = self._read_string(replay_file, length=key_length)
            byte_value = self._read_string(replay_file)

            value = {
                byte_key: byte_value
            }
        elif type_name == 'QWordProperty':
            # 64 bit int, 8 bytes.
            length = self._read_integer(replay_file, 8)
            value = self._read_integer(replay_file, length)
        elif type_name == 'BoolProperty':
            unknown = self._read_integer(replay_file, 8)
            value = self._read_integer(replay_file, 1)

            if value == 0:
                value = False
            elif value == 1:
                value = True
        else:
            raise Exception("Unknown type: {}".format(type_name))

        return {'name': property_name, 'value': value}

    def _read_level_info(self, replay_file):
        map_names = []
        number_of_maps = self._read_integer(replay_file)

        for x in xrange(number_of_maps):
            map_names.append(self._read_string(replay_file))

        return map_names

    def _read_key_frames(self, replay_file):
        number_of_key_frames = self._read_integer(replay_file)

        key_frames = [
            self._read_key_frame(replay_file)
            for x in xrange(number_of_key_frames)
        ]

        return key_frames

    def _read_key_frame(self, replay_file):
        time = self._read_float(replay_file, 4)
        frame = self._read_integer(replay_file)
        file_position = self._read_integer(replay_file)

        return {
            'time': time,
            'frame': frame,
            'file_position': file_position
        }

    def _read_network_stream(self, replay_file):
        array_length = self._read_integer(replay_file)

        network_stream = self._read_unknown(replay_file, array_length)

    def _read_debug_strings(self, replay_file):
        array_length = self._read_integer(replay_file)

        if array_length == 0:
            return []

        debug_strings = []

        unknown = self._read_integer(replay_file)

        while len(debug_strings) < array_length:
            player_name = self._read_string(replay_file)
            debug_string = self._read_string(replay_file)

            debug_strings.append({
                'PlayerName': player_name,
                'DebugString': debug_string,
            })

            if len(debug_strings) < array_length:
                # Seems to be some nulls and an ACK?
                unknown = self._read_integer(replay_file)

        return debug_strings

    def _read_goal_ticks(self, replay_file):
        goal_ticks = []

        num_goals = self._read_integer(replay_file)

        for x in xrange(num_goals):
            team = self._read_string(replay_file)
            frame = self._read_integer(replay_file)

            goal_ticks.append({
                'Team': team,
                'frame': frame,
            })

        return goal_ticks

    def _read_packages(self, replay_file):
        num_packages = self._read_integer(replay_file)

        packages = []

        for x in xrange(num_packages):
            packages.append(self._read_string(replay_file))

        return packages

    def _read_objects(self, replay_file):
        num_objects = self._read_integer(replay_file)

        objects = []

        for x in xrange(num_objects):
            objects.append(self._read_string(replay_file))

        return objects

    def _read_name_table(self, replay_file):
        name_table_length = self._read_integer(replay_file)
        table = []

        for x in xrange(name_table_length):
            table.append(self._read_string(replay_file))

        return table

    def _read_classes(self, replay_file):
        class_index_map_length = self._read_integer(replay_file)

        class_index_map = {}

        for x in xrange(class_index_map_length):
            name = self._read_string(replay_file)
            integer = self._read_integer(replay_file)

            class_index_map[integer] = name

        return class_index_map

    def _read_property_tree(self, replay_file, objects, classes):
        branches = []

        property_tree_length = self._read_integer(replay_file)

        for x in xrange(property_tree_length):
            data = {
                'class': self._read_integer(replay_file),
                'parent_id': self._read_integer(replay_file),
                'id': self._read_integer(replay_file),
                'properties': {}
            }

            if data['id'] == data['parent_id']:
                data['id'] = 0

            length = self._read_integer(replay_file)

            for x in xrange(length):
                index = self._read_integer(replay_file)
                value = self._read_integer(replay_file)

                data['properties'][index] = value

            branches.append(data)

        # Map the property keys against the class list.
        classed = {}

        def map_properties(id):
            for branch in branches:
                if branch['id'] == id:
                    props = {}

                    if branch['parent_id'] > 0:
                        props = map_properties(branch['parent_id'])

                    for k, v in enumerate(branch['properties']):
                        props[v] = objects[k]

                    return props

            return {}

        for branch in branches:
            # {'parent_id': 36, 'properties': {42: 36}, 'class': 43, 'id': 37}
            classed[branch['class']] = {
                'class': classes[branch['class']],
                'properties': map_properties(branch['id'] if branch['id'] > 0 else branch['parent_id'])
            }

        return branches

    # Temporary method while we learn the replay format.
    def manual_parse(self, results, replay_file):
        server_regexp = re.compile(self.SERVER_REGEX)

        replay_file.seek(0)
        search = server_regexp.search(replay_file.read())
        if search:
            results['header']['ServerName'] = search.group()

        return results

    ##################
    # Helper functions
    ##################

    def _debug_bits(self, replay_file, labels=None):
        byte = replay_file.read(1)
        output = ()

        for index in xrange(8):
            i, j = divmod(index, 8)

            if ord(byte[i]) & (1 << j):
                value = '1'
            else:
                value = '0'

            formatted = value.rjust(index+1, '.').ljust(8, '.')
            output = output + (int(value),)

            if labels and len(labels) == 8:
                print('{} = {}: {}'.format(
                    formatted,
                    labels[index],
                    'Set' if formatted == '1' else 'Not set',
                ))
            else:
                print(value.rjust(index+1, '.').ljust(8, '.'))

        return output

    def _read_bit(self, string, index):
        i, j = divmod(index, 8)

        if ord(string[i]) & (1 << j):
            return 1
        else:
            return 0

    def _pretty_byte_string(self, bytes_read):
        return ' '.join("{:02x}".format(ord(x)) for x in bytes_read)

    def _read_integer(self, replay_file, length=4):
        number_format = {
            1: '<b',
            2: '<h',
            4: '<i',
            8: '<q',
        }[length]

        bytes_read = replay_file.read(length)
        value = struct.unpack(number_format, bytes_read)[0]

        return value

    def _read_float(self, replay_file, length):
        number_format = {
            4: '<f',
            8: '<d'
        }[length]

        bytes_read = replay_file.read(length)
        value = struct.unpack(number_format, bytes_read)[0]

        return value

    def _read_unknown(self, replay_file, num_bytes):
        bytes_read = replay_file.read(num_bytes)
        return bytes_read

    def _read_string(self, replay_file, length=None):
        if not length:
            length = self._read_integer(replay_file)
        bytes_read = replay_file.read(length)[0:-1]
        return bytes_read

    def _sniff_bytes(self, replay_file, size):
        b = self._read_unknown(replay_file, size)

        print("**** BYTES ****")
        print("Bytes: {}".format(self._pretty_byte_string(b)))
        print('Size:', size)

        if size == 2:
            print("Short: Signed: {} Unsigned: {}".format(struct.unpack('<h', b), struct.unpack('<H', b)))
        else:
            if size == 4:
                print("Integer: Signed: {}, Unsigned: {}".format(struct.unpack('<i', b), struct.unpack('<I', b)))
                print("Float: {}".format(struct.unpack('<f', b)))
            print("String: {}".format(b))


if __name__ == '__main__':  # pragma: no cover
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        try:
            results = ReplayParser(debug=False).parse(replay_file)
            # pprint.pprint(results)
        except IOError as e:
            print(e)
        except struct.error as e:
            print(e)
        except Exception as e:
            print(e)
