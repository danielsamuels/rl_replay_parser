import struct

import readers


def debug_bits(replay_file, labels=None):
    if isinstance(replay_file, str):
        byte = replay_file
    else:
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


def pretty_byte_string(bytes_read):
    return ' '.join("{:02x}".format(ord(x)) for x in bytes_read)


def sniff_bytes(replay_file, size):
    b = readers.read_unknown(replay_file, size)

    print("**** BYTES ****")
    print("Bytes: {}".format(pretty_byte_string(b)))
    print('Size:', size)

    if size == 2:
        print("Short: Signed: {} Unsigned: {}".format(struct.unpack('<h', b), struct.unpack('<H', b)))
    else:
        if size == 4:
            print("Integer: Signed: {}, Unsigned: {}".format(struct.unpack('<i', b), struct.unpack('<I', b)))
            print("Float: {}".format(struct.unpack('<f', b)))
        print("String: {}".format(b))
