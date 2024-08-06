#!/usr/bin/env python3
import optparse
import re

fullIntRegex = re.compile(rb'^\d+ *$')
startIntRegex = re.compile(rb'^\d+')


def try_to_positive_int(str_to_convert, desc):
    int_value = -1
    if fullIntRegex.match(str_to_convert):
        int_value = int(str_to_convert)
    else:
        ignore_tail_match = startIntRegex.match(str_to_convert)
        if ignore_tail_match:
            int_value = int(ignore_tail_match.group())
            print(
                f'Warning: Using {int_value} as {desc}. May be incorrect due to unexpected characters in {str_to_convert!r}')
        else:
            raise ValueError(
                f'Cannot extract {desc} from {str_to_convert!r}')
    if int_value > 0:
        return int_value
    else:
        raise ValueError(f'{int_value} is not positive')


def print_signal_prop(signal_prop, prop_start, length, header, number_of_signals):
    start = prop_start
    end = start + length
    width = len(str(number_of_signals))
    for s in range(number_of_signals):
        print(f'{signal_prop} for signal {s + 1:{width}d}: {header[start:end]!r}')
        start = end
        end += length


def process_file(filename):
    with open(filename, "rb") as file:
        fixed_part = file.read(256)
        print(f'Header for: {filename}')
        print(f'Version: {fixed_part[0:8]!r}')
        print(f'Patient info: {fixed_part[8:88]!r}')
        print(f'Recording info: {fixed_part[88:168]!r}')
        print(f'Start date: {fixed_part[168:176]!r}')
        print(f'Start time: {fixed_part[176:184]!r}')
        header_bytes_str = fixed_part[184:192]
        print(f'Header sz (bytes): {header_bytes_str!r}')
        print(f'Reserved: {fixed_part[192:236]!r}')
        print(f'Number of data records: {fixed_part[236:244]!r}')
        print(f'Data record length (s): {fixed_part[244:252]!r}')
        number_of_signals_str = fixed_part[252:256]
        print(f'Number of signals: {number_of_signals_str!r}')
        header_bytes = try_to_positive_int(header_bytes_str, 'header size')
        number_of_signals = try_to_positive_int(
            number_of_signals_str,
            'number of signals')
        header = file.read(header_bytes - 256)
        # print(f'{header!r}')
        signal_props_length = [('Label', 16),
                               ('Transducer type', 80),
                               ('Physical dim.', 8),
                               ('Physical min.', 8),
                               ('Physical max.', 8),
                               ('Digital min.', 8),
                               ('Digital max.', 8),
                               ('Prefiltering', 80),
                               ('Samples per record', 8),
                               ('Reserved', 32)]
        prop_start = 0
        for p in signal_props_length:
            print_signal_prop(p[0], prop_start, p[1], header, number_of_signals)
            prop_start += (number_of_signals * p[1])


def main():
    p = optparse.OptionParser()
    # p.add_option('--person', '-p', default="world")
    options, arguments = p.parse_args()
    # print 'Hello %s' % options.person

    for f in arguments:
        process_file(f)


if __name__ == '__main__':
    main()
