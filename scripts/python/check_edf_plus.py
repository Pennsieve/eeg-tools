#!/usr/bin/env python3

"""Checks EDF+ files for valid annotation time offsets."""

from __future__ import print_function
import sys
import argparse
import struct


def check_file(edf_file, verbose=False):
    """
        Actually check the file.
        Returns True if file is valid.
    """
    header = process_header(edf_file)
    if not header["reserved"].startswith("EDF+"):
        if verbose:
            print("Not EDF+")
        return True
    ann_offset_in_record = header["pre_ann_samples_per_record"] * 2
    ann_length_bytes = header["ann_samples_per_record"] * 2
    edf_file.seek(ann_offset_in_record, 1)
    annotations = edf_file.read(ann_length_bytes)
    if verbose:
        absolute_ann_offset = edf_file.tell() - ann_length_bytes

        while annotations[-2:] == "\x00\x00":
            annotations = annotations[:-1]

        print("First annotation at byte %d: %r" %
              (absolute_ann_offset, annotations))
    return annotations.startswith('+0.') or annotations.startswith('+0\x14')


def process_header(edf_file):
    """Get necessary info from EDF header"""
    fixed_part = edf_file.read(256)
    header_length_bytes = int(fixed_part[184:192])
    reserved = fixed_part[192:236]
    signal_count = int(fixed_part[252:256])
    header = edf_file.read(header_length_bytes - 256)

    labels_struct = header[0:16 * signal_count]
    labels = struct.unpack("16s" * signal_count, labels_struct)
    labels = list(map(str.strip, labels))

    annotation_index = -1
    try:
        annotation_index = labels.index("EDF Annotations")
    except ValueError:
        raise Exception("No 'EDF Annotations' signal in file")

    samples_per_record_offset = (16 + 80 + 5 * 8 + 80) * signal_count
    samples_per_record_struct = header[
        samples_per_record_offset: samples_per_record_offset + (8 * signal_count)]
    samples_per_record = struct.unpack(
        "8s" * signal_count, samples_per_record_struct)
    samples_per_record = list(map(int, samples_per_record))
    pre_ann_samples_per_record = sum(samples_per_record[:annotation_index])
    ann_samples_per_record = samples_per_record[annotation_index]

    header = dict(
        reserved=reserved,
        pre_ann_samples_per_record=pre_ann_samples_per_record,
        ann_samples_per_record=ann_samples_per_record,
    )
    return header


def main():
    """Checks EDF+ files for valid annotation time offsets."""
    parser = argparse.ArgumentParser(
        description="Check EDF+ files for valid annotation time offsets")
    parser.add_argument("edf_files", nargs='+', help="EDF files to check")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_true", help="print extra information")
    arguments = parser.parse_args()

    bad_files = 0
    for edf_file_path in arguments.edf_files:
        with open(edf_file_path, 'rb') as edf_file:
            if arguments.verbose:
                print("Checking", edf_file_path)
            okay = check_file(edf_file, verbose=arguments.verbose)
            if not okay:
                bad_files += 1
                print("Invalid annotation offset:", edf_file_path, file=sys.stderr)
    sys.exit(min(bad_files, 127))


if __name__ == '__main__':
    main()
