#!/usr/bin/env python3
import argparse
import sys
import struct

type_to_length_format = {'ui1': (1, 'B'),
                         'si1': (1, 'b'),
                         'ui2': (2, 'H'),
                         'si2': (2, 'h'),
                         'ui4': (4, 'I'),
                         'si4': (4, 'i'),
                         'sf4': (4, 'f'),
                         'ui8': (8, 'Q'),
                         'si8': (8, 'q'),
                         'sf8': (8, 'd')}

"""
Example: To see the Recording Start Time of a MEF file, example.mef:
    mefHeader.py 408 ui8 example.mef
    
You will need to have the MEF2 spec PDF to know the offset and type of the header field to read.
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("offset", help="byte offset into file", type=int)
    p.add_argument("value_type", help="datatype expected at offset")
    p.add_argument("MEF", help="the MEF file to read", type=argparse.FileType('r'))
    args = p.parse_args()

    offset = args.offset
    value_type = args.value_type
    try:
        length_format = type_to_length_format[value_type]
    except KeyError:
        sys.exit('Unknown type: [' + value_type + ']')

    with args.MEF as mef_file:
        mef_file.seek(offset)
        value_bytes = mef_file.read(length_format[0])
        value = struct.unpack('<' + length_format[1], value_bytes)
        print(value[0])


if __name__ == '__main__':
    main()
