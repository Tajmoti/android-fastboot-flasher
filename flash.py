#!/usr/bin/env python3
import os
import sys
from enum import Enum
from typing import Iterable, List


class Slot(Enum):
    A = 1
    B = 2


PARTITION_NAMES = [
    "abl",
    "xbl",
    "bluetooth",
    "boot",
    "cda",
    "cmnlib",
    "cmnlib64",
    "devcfg",
    "dsp",
    "hidden",
    "hyp",
    "keymaster",
    "mdtpsecapp",
    "modem",
    "nvdef",
    "pmic",
    "rpm",
    "splash",
    "system",
    "systeminfo",
    "tz",
    "vendor"
]

ERASE_PARTITIONS = [
    "ssd",
    "misc",
    "sti",
    "ddr",
    "securefs",
    "box"
]


def any_match(iterable: Iterable, predicate) -> bool:
    for item in iterable:
        if predicate(item):
            return True
    return False


def first_or_none(iterable: Iterable, predicate):
    for item in iterable:
        if predicate(item):
            return item
    return None


def partition_name_to_image_name(part_name: str) -> str:
    return part_name + ".img"


def execute_command(command: str, dry_run: bool):
    if dry_run:
        print(command)
        return
    os.system(command)


def warn_extra_files(all_files_names: List[str]):
    for real_file in all_files_names:
        if not any_match(PARTITION_NAMES, lambda part_file: real_file == partition_name_to_image_name(part_file)):
            print_err(f"Unused file detected: {real_file}")


def check_missing_files(all_files_names: List[str]):
    for part_name in PARTITION_NAMES:
        part_file = partition_name_to_image_name(part_name)
        if not any_match(all_files_names, lambda real_file: real_file == part_file):
            handle_missing_file(part_file)


def handle_missing_file(file_name: str):
    print_err(f"The file '{file_name} is missing! Enter 'yes' to proceed anyway:")
    result = input()
    if result != "yes":
        print_err(f"Aborting because of missing file '{file_name}'")
        sys.exit(1)


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.stderr.flush()


def get_image_dir() -> str:
    if len(sys.argv) < 2:
        return '.'
    if len(sys.argv) > 2:
        print_usage_and_exit()
    first_arg = sys.argv[1]
    if not os.path.isdir(first_arg):
        print_err(f"'{first_arg}' is not a valid directory!")
        print_usage_and_exit()
    if not first_arg.endswith(os.path.sep):
        first_arg += os.path.sep
    return first_arg


def print_usage_and_exit():
    print_err(f"USAGE: {os.path.basename(__file__)} [image_dir]")
    sys.exit(1)


def flash_file(part_name: str, abs_files: List[str], slot: Slot, dry_run: bool):
    part_file = partition_name_to_image_name(part_name)
    abs_file = first_or_none(abs_files, lambda real_file: real_file.endswith(part_file))
    if abs_file is None:
        return
    suffix = "a" if slot == Slot.A else "b"
    to_flash_part_name = f"{part_name}_{suffix}"
    print(f"Flashing partition '{to_flash_part_name}' with file '{os.path.basename(abs_file)}'")
    command = f"fastboot flash {to_flash_part_name} \"{abs_file}\""
    execute_command(command, dry_run)


def flash_partitions(slot: Slot, files_abs: List[str], dry_run: bool):
    for part_name in PARTITION_NAMES:
        flash_file(part_name, files_abs, slot, dry_run)


def erase_partitions(dry_run: bool):
    for part_name in ERASE_PARTITIONS:
        print(f"Erasing partition '{part_name}'")
        command = f"fastboot erase {part_name}"
        execute_command(command, dry_run)


def wipe_data(dry_run: bool):
    print(f"Wiping data")
    command = f"fastboot -w"
    execute_command(command, dry_run)


def collect_images() -> List[str]:
    image_dir = get_image_dir()
    files_abs = [image_dir + f for f in os.listdir(image_dir) if os.path.isfile(image_dir + f)]
    file_names = list(map(os.path.basename, files_abs))
    warn_extra_files(file_names)
    check_missing_files(file_names)
    return files_abs


def reflash_device(slot_to_flash: Slot, factory_reset: bool):
    only_print = False
    images_abs = collect_images()
    flash_partitions(slot_to_flash, images_abs, only_print)
    erase_partitions(only_print)
    if factory_reset:
        wipe_data(only_print)


if __name__ == "__main__":
    reflash_device(Slot.B, False)
