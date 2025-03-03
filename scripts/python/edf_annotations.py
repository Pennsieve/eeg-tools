#!/usr/bin/env python3

"""Display EDF Annotation information for a given file and data record"""
import sys
import os
import errno
import argparse
import struct


def process_file(edf_file, requested_record=None):
    """Actually read the file"""
    header = process_header(edf_file)
    data_record_count = header["data_record_count"]
    first_record_number = requested_record if requested_record is not None else 1
    last_record_number = requested_record if requested_record is not None else data_record_count
    if first_record_number > last_record_number:
        raise Exception("invalid record number range: [%d, %d]" % (
            first_record_number, last_record_number))

    if first_record_number <= 0 or last_record_number > data_record_count:
        raise Exception("requested range [%d, %d] out of range [1, %d]" % (
            first_record_number, last_record_number, data_record_count))

    bytes_per_record = header["total_samples_per_record"] * 2
    ann_offset_in_record = header["pre_ann_samples_per_record"] * 2
    ann_length_bytes = header["ann_samples_per_record"] * 2
    initial_ann_offset = (first_record_number - 1) * bytes_per_record + ann_offset_in_record
    edf_file.seek(initial_ann_offset, 1)
    for record_number in range(first_record_number, last_record_number + 1):
        annotations = edf_file.read(ann_length_bytes)
        absolute_ann_offset = edf_file.tell() - ann_length_bytes

        while annotations[-2:] == "\x00\x00":
            annotations = annotations[:-1]

        print("%d (%d): %r" %
              (record_number, absolute_ann_offset, annotations))
        # for next time
        edf_file.seek(ann_offset_in_record, 1)


def process_header(edf_file):
    """Get necessary info from EDF header"""
    fixed_part = edf_file.read(256)
    header_length_bytes = int(fixed_part[184:192])
    data_record_count = int(fixed_part[236:244])
    signal_count = int(fixed_part[252:256])
    header = edf_file.read(header_length_bytes - 256)
    labels_struct = header[0:16 * signal_count]

    labels = [label.strip().decode('ascii') for label in struct.unpack("16s" * signal_count, labels_struct)]

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
    total_samples_per_record = sum(samples_per_record)

    header = dict(
        data_record_count=data_record_count,
        pre_ann_samples_per_record=pre_ann_samples_per_record,
        ann_samples_per_record=ann_samples_per_record,
        total_samples_per_record=total_samples_per_record
    )
    return header


def main():
    """Display EDF Annotation information for a given file and data record"""
    parser = argparse.ArgumentParser(
        description="Display EDF annotations in a data record")
    parser.add_argument("edf_file", help="EDF file to read")
    parser.add_argument("--record-number",
                        "-r",
                        dest="record_number",
                        type=int,
                        help="index of the data record to examine")
    arguments = parser.parse_args()

    requested_record = arguments.record_number

    with open(arguments.edf_file, 'rb') as edf_file:
        try:
            process_file(edf_file, requested_record=requested_record)
        except IOError as e:
            # If this script is piped into head or less we get broken pipe errors
            # when writing. This handles that. Adapted from Python 3 'signal' docs.
            if e.errno == errno.EPIPE:
                # Python flushes standard streams on exit; redirect remaining output
                # to devnull to avoid another BrokenPipeError at shutdown
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, sys.stdout.fileno())


if __name__ == '__main__':
    main()
