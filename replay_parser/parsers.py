import re

import readers
import utils
import json
import os
import pprint
import struct


SERVER_REGEX = r'((EU|USE|USW|OCE|SAM)\d+(-[A-Z][a-z]+)?)'


def parse_network_stream(replay_file, data):
    # Based on the number of frames and the FPS, we can work out what time the
    # last frame is. TODO: This isn't currently accurate.
    max_time = 2 + data['key_frames'][0]['time'] + data['header']['NumFrames'] / data['header']['RecordFPS']

    replay_file.seek(data['network_stream_offset'])

    data_length = readers.read_integer(replay_file)
    print '{} bytes ({} bits) of network data starting at offset {} and finishing at {}.'.format(
        data_length,
        data_length * 8,
        data['network_stream_offset'],
        data['network_stream_offset'] + data_length + 4
    )

    # We know how many frames there are in the replay, and we have data for
    # some of them. We also know that each frame is at _least_ 64 bytes long,
    # which means that given the starting point of each frame, we can work out
    # which bit locations *cannot* be start frames. This reduces our search.
    invalid_bit_locations = []

    # There are a ton of frames which we know are usable. Get those into a list
    # to begin with.
    frames = []

    for frame in data['key_frames']:
        frames.append(frame['file_position'])
        invalid_bit_locations.extend(range(frame['file_position'] + 1, frame['file_position'] + 64))

    frames.sort()

    print "There are {} frames in total. We know the location of {} of them, leaving {} to find.\n".format(
        data['header']['NumFrames'],
        len(frames),
        data['header']['NumFrames'] - len(frames),
    )

    # Convert the entire network stream into a list of bits. This is just a list
    # of 1s and 0s which represent all of the data. Everything about a
    # particular replay is stored in this data, so we parse it all out! To save
    # time when reprocessing matches, we store the list of bits in a .json file.

    # Create the cache directory if it doesn't exist.
    if not os.path.exists('cache'):
        os.mkdir('cache')

    try:
        # Check to see if we have a cache file for this replay ID already.
        bitstore = json.load(file('cache/{}.json'.format(data['header']['Id'])))
    except IOError:
        # Generate the list of bits.
        bitstore = []

        # Build the entire network stream as a list of bits. (a.k.a. rip RAM)
        for x in xrange(data_length):
            bits = utils.debug_bits(replay_file)
            for bit in bits:
                bitstore.append(bit)

        json.dump(bitstore, file('cache/{}.json'.format(data['header']['Id']), 'w'))

    # Ensure the integrity of the data.
    assert len(bitstore) == data_length * 8

    last_time = last_delta = None
    frame_hits = []

    for offset in (x for x in xrange(len(bitstore)) if x not in invalid_bit_locations):
        # Attempt to read a time and delta from this bit offset. If the data
        # looks good, then we assume this is a new frame (until we establish how
        # frames really work). When we detect a good frame, we then add the next
        # 64 bits to the `invalid_bit_locations` list so we don't try to check
        # them in future iterations. Given that our forloop is iterating over a
        # generator expression, this should work quite nicely.

        time_bits = utils.multi_bits_to_byte(bitstore, offset)
        this_time = readers.read_float(time_bits, data_read=True)

        delta_bits = utils.multi_bits_to_byte(bitstore, offset + 32)
        this_delta = readers.read_float(delta_bits, data_read=True)

        if last_time is not None and (
            this_time < last_time or
            # this_time > max_time or
            this_time != this_time  # Check for 'nan'
        ):
            continue

        if last_delta and (
            this_delta > 0.1 or
            this_delta < 0 or
            # Check the this_delta + last_time isn't absurd.
            this_time - (this_delta + last_time) > 0.01 or
            this_delta != this_delta  # Check for 'nan'
        ):
            continue

        if len(frame_hits) > 0:
            prev_bits = offset - frame_hits[-1] - 1
            print 'Frame has {} bits of data:'.format(prev_bits)

            print ' '.join(
                ''.join(str(el) for el in list(group))
                for group in utils.grouper(
                    bitstore[frame_hits[-1]:frame_hits[-1]+prev_bits], 8, fillvalue=''
                )
            )
            print

        print 'Frame: Position: {} Time: {} Delta: {}.'.format(
            offset,
            this_time,
            this_delta,
        )

        last_time = this_time
        last_delta = this_delta

        print 'Added offset {} to list of frame hits.'.format(offset)
        frame_hits.append(offset)

        if len(frame_hits) == data['header']['NumFrames']:
            print 'Attained all frames.'
            break

        invalid_bit_locations.extend(range(offset + 1, offset + 64))

    assert len(frame_hits) == data['header']['NumFrames']


# Temporary method while we learn the replay format.
def manual_parse(results, replay_file):
    server_regexp = re.compile(SERVER_REGEX)

    replay_file.seek(0)
    search = server_regexp.search(replay_file.read())
    if search:
        results['header']['ServerName'] = search.group()

    return results
