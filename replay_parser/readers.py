import struct


def read_properties(replay_file):
    results = {}

    while True:
        property_info = read_property(replay_file)

        if property_info:
            results[property_info['name']] = property_info['value']
        else:
            return results


def read_property(replay_file):
    name_length = read_integer(replay_file)

    property_name = read_string(replay_file, name_length)

    if property_name == 'None':
        return None

    type_name = read_string(replay_file)

    value = None

    if type_name == 'IntProperty':
        value_length = read_integer(replay_file, 8)
        value = read_integer(replay_file, value_length)

    elif type_name == 'StrProperty':
        unknown = read_integer(replay_file, 8)
        length = read_integer(replay_file)

        if length < 0:
            length = abs(length) * 2
            value = read_string(replay_file, length)[:-1].decode('utf-16').encode('utf-8')
        else:
            value = read_string(replay_file, length)

    elif type_name == 'FloatProperty':
        length = read_integer(replay_file, 8)
        value = read_float(replay_file, length)

    elif type_name == 'NameProperty':
        unknown = read_integer(replay_file, 8)
        value = read_string(replay_file)

    elif type_name == 'ArrayProperty':
        # I imagine that this is the length of bytes that the data
        # in the "array" actually take up in the file.
        unknown = read_integer(replay_file, 8)
        array_length = read_integer(replay_file)

        value = [
            read_properties(replay_file)
            for x in xrange(array_length)
        ]

    return {'name': property_name, 'value': value}


def read_level_info(replay_file):
    map_names = []
    number_of_maps = read_integer(replay_file)

    for x in xrange(number_of_maps):
        map_names.append(read_string(replay_file))

    return map_names


def read_key_frames(replay_file):
    number_of_key_frames = read_integer(replay_file)

    key_frames = [
        read_key_frame(replay_file)
        for x in xrange(number_of_key_frames)
    ]

    return key_frames


def read_key_frame(replay_file):
    time = read_float(replay_file)
    frame = read_integer(replay_file)
    file_position = read_integer(replay_file)

    return {
        'time': time,
        'frame': frame,
        'file_position': file_position
    }


def read_network_stream(replay_file):
    array_length = read_integer(replay_file)

    return read_unknown(replay_file, array_length)


def read_debug_strings(replay_file):
    array_length = read_integer(replay_file)

    if array_length == 0:
        return []

    debug_strings = []

    unknown = read_integer(replay_file)

    while len(debug_strings) < array_length:
        player_name = read_string(replay_file)
        debug_string = read_string(replay_file)

        debug_strings.append({
            'PlayerName': player_name,
            'DebugString': debug_string,
        })

        if len(debug_strings) < array_length:
            # Seems to be some nulls and an ACK?
            unknown = read_integer(replay_file)

    return debug_strings


def read_goal_ticks(replay_file):
    goal_ticks = []

    num_goals = read_integer(replay_file)

    for x in xrange(num_goals):
        team = read_string(replay_file)
        frame = read_integer(replay_file)

        goal_ticks.append({
            'Team': team,
            'frame': frame,
        })

    return goal_ticks


def read_packages(replay_file):
    num_packages = read_integer(replay_file)

    packages = []

    for x in xrange(num_packages):
        packages.append(read_string(replay_file))

    return packages


def read_objects(replay_file):
    num_objects = read_integer(replay_file)

    objects = []

    for x in xrange(num_objects):
        objects.append(read_string(replay_file))

    return objects


def read_name_table(replay_file):
    name_table_length = read_integer(replay_file)
    table = []

    for x in xrange(name_table_length):
        table.append(read_string(replay_file))

    return table


def read_classes(replay_file):
    class_index_map_length = read_integer(replay_file)

    class_index_map = {}

    for x in xrange(class_index_map_length):
        name = read_string(replay_file)
        integer = read_integer(replay_file)

        class_index_map[integer] = name

    return class_index_map


def read_property_tree(replay_file, objects, classes):
    branches = []

    property_tree_length = read_integer(replay_file)

    for x in xrange(property_tree_length):
        data = {
            'class': read_integer(replay_file),
            'parent_id': read_integer(replay_file),
            'id': read_integer(replay_file),
            'properties': {}
        }

        if data['id'] == data['parent_id']:
            data['id'] = 0

        length = read_integer(replay_file)

        for x in xrange(length):
            index = read_integer(replay_file)
            value = read_integer(replay_file)

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

    return classed


def read_integer(replay_file, length=4, data_read=False):
    number_format = {
        1: '<b',
        2: '<h',
        4: '<i',
        8: '<q',
    }[length]

    if not data_read:
        bytes_read = replay_file.read(length)
    else:
        bytes_read = replay_file

    value = struct.unpack(number_format, bytes_read)[0]

    return value


def read_float(replay_file, length=4, data_read=False):
    number_format = {
        4: '<f',
        8: '<d'
    }[length]

    if not data_read:
        bytes_read = replay_file.read(length)
    else:
        bytes_read = replay_file

    value = struct.unpack(number_format, bytes_read)[0]

    return value


def read_unknown(replay_file, num_bytes):
    bytes_read = replay_file.read(num_bytes)
    return bytes_read


def read_string(replay_file, length=None):
    if not length:
        length = read_integer(replay_file)
    bytes_read = replay_file.read(length)[0:-1]
    return bytes_read


def read_bit(string, index):
    # We subtract the index from 7 because the bits are reversed.
    i, j = divmod(7-index, 8)

    if ord(string[i]) & (1 << j):
        return '1'
    else:
        return '0'
