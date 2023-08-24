# Copyright (c) Yugabyte, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations
# under the License.


"""
The command-line entry point to the llvm-installer Python module.
"""

import argparse
import logging
import os
import subprocess
import sys
import time

# TODO: figure out why py.typed from downloadutil is not being respected.
from downloadutil.download_config import DownloadConfig  # type: ignore
from downloadutil.downloader import Downloader  # type: ignore

from llvm_installer import LlvmInstaller
from sys_detection import local_sys_conf

from typing import Optional


def install(llvm_url: str, once: bool, verbose: bool) -> None:
    archive_name = os.path.basename(llvm_url)
    install_dir_name = None
    for extension in ['.zip', '.tar.gz']:
        if archive_name.endswith(extension):
            install_dir_name = archive_name[:-len(extension)]
            break
    if not install_dir_name:
        raise ValueError("Could not determine installation directory name from URL %s" % llvm_url)

    install_parent_dir = '/opt/yb-build/llvm'
    install_dir = os.path.join(install_parent_dir, install_dir_name)

    # We create a "flag file" to indicate that the installation has successfuly completed. Another
    # approach would have been to extract to a temporary directory and then try to atomically move
    # it into place. That would require a bit more error handling.
    flag_file_path = os.path.join(install_dir, '.llvm_installation_finished')
    if once and os.path.exists(flag_file_path):
        logging.info("LLVM is already installed in %s" % install_dir)
        return

    start_time_sec = time.time()
    config = DownloadConfig(verbose=verbose)
    downloader = Downloader(config=config)
    logging.info("Downloading %s", llvm_url)
    downloaded_path = downloader.download_url(
        llvm_url,
        verify_checksum=True,
        download_parent_dir_path=install_parent_dir)
    download_time_sec = time.time() - start_time_sec
    logging.info("Downloaded in %.3f sec", download_time_sec)
    extract_start_time_sec = time.time()
    logging.info("Extracting %s in %s", archive_name, install_parent_dir)
    subprocess.check_call(['tar', 'xzf', archive_name], cwd=install_parent_dir)
    extract_time_sec = time.time() - extract_start_time_sec
    logging.info("Extracted in %.3f sec", extract_time_sec)

    with open(flag_file_path, 'w') as output_file:
        pass

    if os.path.exists(downloaded_path):
        try:
            os.remove(downloaded_path)
        except FileNotFoundError as ex:
            # Someone else deleted the file (but it should not really happen).
            pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[llvm-installer %(filename)s:%(lineno)d] %(asctime)s %(levelname)s: %(message)s")

    arg_parser = argparse.ArgumentParser(
        prog='llvm-installer',
        description=__doc__)
    arg_parser.add_argument(
        '--llvm-major-version', '--major-version',
        help='LLVM major version')
    arg_parser.add_argument(
        '--print-url',
        action='store_true',
        help='If this is specified, LLVM package download URL is printed to standard output. '
             'Please use the print-url command instead of this flag.')
    arg_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output')

    subparsers = arg_parser.add_subparsers(help='command', dest='command')

    install_subparser = subparsers.add_parser(
        "install",
        help="Install a particular version of LLVM. Note that currently this is not safe in case "
             "multiple concurrent processes are trying to install the same version.")
    install_subparser.add_argument(
        '--once',
        action='store_true',
        help="Only install the given version of LLVM once. If it has already been installed, "
             "do not install it again.")

    subparsers.add_parser(
        "print-url",
        help="Print the download URL of the chosen LLVM version")

    if len(sys.argv) == 1:
        arg_parser.print_help(sys.stderr)
        sys.exit(1)

    args = arg_parser.parse_args()
    command: Optional[str] = args.command

    sys_conf = local_sys_conf()
    short_os_name_and_version = sys_conf.short_os_name_and_version()
    installer = LlvmInstaller(
        short_os_name_and_version=short_os_name_and_version,
        architecture=sys_conf.architecture)

    should_print_url = command == 'print-url' or args.print_url

    should_install = command == 'install'

    if should_print_url or should_install:
        if not args.llvm_major_version:
            raise ValueError("--llvm-major-version not specified\n")
        llvm_url = installer.get_llvm_url(major_llvm_version=args.llvm_major_version)

    if should_print_url:
        print(llvm_url)
        return

    if should_install:
        install(llvm_url, once=args.once, verbose=args.verbose)


if __name__ == '__main__':
    main()
