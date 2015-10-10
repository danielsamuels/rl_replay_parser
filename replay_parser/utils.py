import struct

import readers


def multi_bits_to_byte(bits, offset=0, num_bytes=4):
    # Split the bits into chunks of 8 and pass them through.

    # 0:8
    # 8:16
    # 16:24
    # 24:32

    bytes_ = []
    for x in xrange(num_bytes):
        left = offset + x * 8
        right = offset + (x + 1) * 8
        bytes_.append(bits_to_byte(bits[left:right][::-1]))

    return ''.join(bytes_)


def bits_to_byte(bits):
    chars = []
    for b in range(len(bits) / 8):
        byte = bits[b*8:(b+1)*8]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)


def debug_bits(replay_file, labels=None):
    if isinstance(replay_file, str):
        byte = replay_file
    else:
        byte = replay_file.read(1)
    output = ()

    for index in xrange(8):
        value = readers.read_bit(byte, index)

        formatted = value.rjust(index+1, '.').ljust(8, '.')
        output = (int(value),) + output

        # if labels and len(labels) == 8:
        #     print('{} = {}: {}'.format(
        #         formatted,
        #         labels[index],
        #         'Set' if formatted == '1' else 'Not set',
        #     ))
        # else:
        #     print(value.rjust(index+1, '.').ljust(8, '.'))

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
