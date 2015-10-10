import re

import readers
import utils
import json
import os
import pprint


SERVER_REGEX = r'((EU|USE|USW|OCE|SAM)\d+(-[A-Z][a-z]+)?)'


def parse_network_stream(replay_file, data):
    print data['header']['NumFrames']
    replay_file.seek(data['network_stream_offset'])

    data_length = readers.read_integer(replay_file)
    print '{} bytes of network data starting at offset {} and finishing at {}.\n'.format(
        data_length,
        data['network_stream_offset'],
        data['after_network_stream_offset'],
    )

    # There are a ton of frames which we know are usable. Get those into a list
    # to begin with.
    frames = []
    frames.extend([frame['file_position'] for frame in data['key_frames']])
    frames.sort()

    # Create the cache directory if it doesn't exist.
    if not os.path.exists('cache'):
        os.mkdir('cache')

    # Build the entire network stream as a list of bits. (a.k.a. rip RAM)
    try:
        print 'Loading JSON.'
        bitstore = json.load(file('cache/{}.json'.format(data['header']['Id'])))
        print 'Loaded JSON.'
    except IOError:
        print 'Unable to load JSON, generating instead.'
        bitstore = []

        for x in xrange(data_length):
            bits = utils.debug_bits(replay_file)
            for bit in bits:
                bitstore.append(bit)

        json.dump(bitstore, file('cache/{}.json'.format(data['header']['Id']), 'w'))
        print 'JSON dumped.'

    # Read the first 4 bytes.
    for frame in frames:
        # Read the first 4 bytes from the bitstring. Each byte needs to have
        # it's bit order reversed.
        print 'Frame: Position: {} Time: {} Delta: {}'.format(
            frame,
            readers.read_float(utils.multi_bits_to_byte(bitstore, frame), data_read=True),
            readers.read_float(utils.multi_bits_to_byte(bitstore, frame + 32), data_read=True),
        )

    # bytes_ = utils.bits_to_byte(bitstore)
    # print utils.pretty_byte_string(biterinos)

    # print readers.read_float(biterinos, data_read=True)


    exit()


    for frame in frames:
        frame = frame + data['network_stream_offset']
        replay_file.seek(frame)

        print 'Frame: {}\t Time: {}\t Delta: {}'.format(
            frame,
            readers.read_float(replay_file, 4),
            readers.read_float(replay_file, 4),
        )

    exit()


    frames = []

    initial_time = readers.read_float(replay_file, 4)
    initial_delta = readers.read_float(replay_file, 4)

    # Read 64 bytes and turn them into one long string of bits.
    bitstore = []

    for x in range(64):
        bits = utils.debug_bits(replay_file)
        for bit in bits:
            bitstore.append(bit)

    print bitstore
    # print initial_time, initial_delta
    # print utils.debug_bits(replay_file)


# Temporary method while we learn the replay format.
def manual_parse(results, replay_file):
    server_regexp = re.compile(SERVER_REGEX)

    replay_file.seek(0)
    search = server_regexp.search(replay_file.read())
    if search:
        results['header']['ServerName'] = search.group()

    return results
