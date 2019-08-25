#!/usr/bin/env python3

import sys, os
import re
from argparse import ArgumentParser, FileType
from bootimg import parse_bootimg_for_mkvendor

SUPPORTED_ROM = {
    "cm": "cm.mk",
    "lineageos": "lineage.mk",
    "mokee": "mk___DEVICE__.mk",
    "omnirom": "omni___DEVICE__.mk"
}

"""
Utility functions
"""

def parse_bootimg(bootimg_filename):
    return parse_bootimg_for_mkvendor(open(bootimg_filename, "rb"))


def parse_cmdline():
    parser = ArgumentParser(
        description="Generate device configurations from prebuilt boot/recovery image.",
        epilog="""
        The boot.img argument is the extracted recovery or boot image.
        It should not be provided for devices
        that have non standard boot images (ie, Samsung).
        """
    )
    parser.add_argument(
        "--boot-img",
        "-b",
        help="Path to boot image",
        type=FileType("rb"),
        required=True
    )
    parser.add_argument(
        "--manufacturer",
        "-m",
        help="Device manufacturer name",
        type=str,
        required=True
    )
    parser.add_argument(
        "--device",
        "-d",
        help="Device name",
        type=str,
        required=True
    )
    parser.add_argument(
        "--rom",
        "-r",
        help="Your Android ROM type. Currently supports: %s" % SUPPORTED_ROM.keys(),
        choices=SUPPORTED_ROM.keys(),
        required=True
    )
    return parser.parse_args()

#
# TODO: Function to check kernel processor and abi
#

"""
Workflows
"""


"""
Main entrance
"""

def main():
    args = parse_cmdline()
    print(args)

if __name__ == "__main__":
    main()
