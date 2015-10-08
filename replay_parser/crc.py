from binascii import crc32
import os


def _pretty_byte_string(bytes_read):
    return ''.join("{:02x}".format(ord(x)) for x in bytes_read).upper()


def crc2hex(crc):
    res = ''

    for i in range(4):
        t = crc & 0xFF
        crc >>= 8
        res = '%02X%s' % (t, res)
    return res


filename = '2s_snip'
filesize = os.path.getsize(filename)


f = open(filename)
# 615

header_length = f.read(4)
crc = _pretty_byte_string(f.read(4))

# Skip the rest of the inital stuff.
# start_byte = 8
# end_byte = 615
# f.seek(start_byte)
# c = f.read(end_byte - start_byte)

# print crc == crc2hex(crc32(c))

# print crc
# print crc2hex(crc32(c))
# print _pretty_byte_string(c)


for offset in xrange(8, filesize):
    for length in xrange(1, filesize):

        f.seek(offset)

        c = f.read(length)

        check = header_length + c

        if crc2hex(crc32(check)) == crc:
            print offset, length
            break
