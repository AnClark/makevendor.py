#!/usr/bin/env python3

import sys, os
import re, struct
from argparse import ArgumentParser, FileType, Namespace
from bootimg import parse_bootimg_for_mkvendor

"""
======================== CONSTANTS ========================
"""

SUPPORTED_ROM = {
    "cm": "cm.mk",
    "lineageos": "lineage.mk",
    "mokee": "mk___DEVICE__.mk",
    "omnirom": "omni___DEVICE__.mk"
}

"""
======================== GLOBAL PARAMETERS ========================
"""

ARGS = ""               # Parsed argument namespace

"""
======================== UTILITIES ========================
"""

def LOG(msg):
    if ARGS.verbose:
        sys.stderr.write(msg)

def parse_bootimg_for_mkvendor(bootimg):
    ''' parse C8600-compatible bootimg for mkvendor.
        Comparing with its original version, this one kept all bootimg data
        in objects.

        write kernel to kernel[.gz]
        write ramdisk to ramdisk[.gz]
        write second to second[.gz]
        write dtimg to dt.img
        write extra to unknown

        Argument:
            bootimg: File object of opened bootimg
    '''
    latin = lambda x: x.encode('latin')

    result = Namespace(
        metadata = "",
        kernel = b"",
        ramdisk = b"",
        second = b"",
        dtimg = b"",
        kerneldt = b"",
        unknown = b"",
        image_format = {}
    )

    bootimg.seek(0)

    (   magic,
        kernel_size, kernel_addr,
        ramdisk_size, ramdisk_addr,
        second_size, second_addr,
        tags_addr, page_size, dt_size, os_version,
        name, cmdline, id4x8
    ) = struct.unpack('<8s10I16s512s32s', bootimg.read(608))
    bootimg.seek(page_size - 608, 1)

    base = kernel_addr - 0x00008000
    assert magic.decode('latin') == 'ANDROID!', 'Invalid bootimg'
    # assert base == ramdisk_addr - 0x01000000, 'invalid bootimg'
    # assert base == second_addr - 0x00f00000, 'invalid bootimg'
    # assert base == tags_addr - 0x00000100, 'invalid bootimg'

    def say(v):
        b7 = 127
        b4 = 15
        a = (v >> 25) & b7
        b = (v >> 18) & b7
        c = (v >> 11) & b7
        y = ((v >>  4) & b7) + 2000
        m = v & b4
        return '%d.%d.%d %s-%s' % (a, b, c, y, m)

    LOG("================= Bootimg Information =================\n")
    LOG('* kernel_addr=0x%x\n' % kernel_addr)
    LOG('* ramdisk_addr=0x%x\n' % ramdisk_addr)
    LOG('* second_addr=0x%x\n' % second_addr)
    LOG('* tags_addr=0x%x\n' % tags_addr)
    # LOG('base=0x%x\n' % base)
    LOG('* page_size=%d\n' % page_size)
    LOG('* os_version=0x%08x(%s)\n' % (os_version, say(os_version)))
    LOG('* name="%s"\n' % name.decode('latin').strip('\x00'))
    LOG('* cmdline="%s"\n' % cmdline.decode('latin').strip('\x00'))

    while True:
        if bootimg.read(page_size) == struct.pack('%ds' % page_size, latin('')):
            continue
        bootimg.seek(-page_size, 1)
        size = bootimg.tell()
        break

    padding = lambda x: (~x + 1) & (size - 1)
    LOG('* padding_size=%d\n' % size)
    LOG("======================================================\n")

    # OUT1: Write metadata
    metadata = {
        'kernel_addr': kernel_addr,
        'ramdisk_addr': ramdisk_addr,
        'second_addr': second_addr,
        'tags_addr': tags_addr,
        'page_size': page_size,
        'name': name.decode('latin').strip('\x00'),
        'cmdline': cmdline.decode('latin').strip('\x00'),
        'padding_size': size,
        'os_version': os_version,
    }
    result.metadata = metadata
    
    gzname = lambda x: x == struct.pack('3B', 0x1f, 0x8b, 0x08) and '.gz' or ''

    # OUT2: Kernel image & DT image
    kernel = bootimg.read(kernel_size)
    magic = struct.pack('>I', 0xd00dfeed)
    pos = kernel.find(magic)
    if pos > 0:
        result.kernel = kernel[:pos]
        result.kerneldt = kernel[pos:]
    else:
        result.kernel = kernel
    result.image_format["kernel"] = gzname(kernel[:3])
    bootimg.seek(padding(kernel_size), 1)

    # OUT3: Ramdisk
    ramdisk = bootimg.read(ramdisk_size)
    result.ramdisk = ramdisk
    result.image_format["ramdisk"] = gzname(ramdisk[:3])
    bootimg.seek(padding(ramdisk_size), 1)

    # OUT4: Second image
    if second_size:
        second = bootimg.read(second_size)
        result.second = second
        result.image_format["second"] = gzname(second[:3])
        bootimg.seek(padding(second_size), 1)

    # OUT5: DTB
    if dt_size:
        dtimg = bootimg.read(dt_size)
        result.dtimg = dtimg
        bootimg.seek(padding(dt_size), 1)

    # OUT6: Unknown
    unknown = bootimg.read()
    if unknown:
        result.unknown = unknown

    bootimg.close()

    return result


def parse_bootimg():
    return parse_bootimg_for_mkvendor(ARGS.boot_img)


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
    parser.add_argument(
        "--verbose",
        "-v",
        help="Print debug messages",
        action='count'          # Treat as a switch
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
    global ARGS
    ARGS = parse_cmdline()

    # Parse boot image
    LOG("[INFO] Parsing boot image...\n")
    BOOTIMG_DATA = parse_bootimg_for_mkvendor(ARGS.boot_img)

if __name__ == "__main__":
    main()
