import re

import utils

SERVER_REGEX = r'((EU|USE|USW|OCE|SAM)\d+(-[A-Z][a-z]+)?)'


def parse_network_stream(network_data):
    for byte in network_data:
        utils.debug_bits(network_data)
        break


# Temporary method while we learn the replay format.
def manual_parse(results, replay_file):
    server_regexp = re.compile(SERVER_REGEX)

    replay_file.seek(0)
    search = server_regexp.search(replay_file.read())
    if search:
        results['header']['ServerName'] = search.group()

    return results
