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

from llvm_installer import LlvmInstaller
from sys_detection import local_sys_conf


def main() -> None:
    arg_parser = argparse.ArgumentParser(
        prog='llvm-installer',
        description=__doc__)
    arg_parser.add_argument(
        '--llvm-major-version',
        help='LLVM major version of interest',
        required=True)
    arg_parser.add_argument(
        '--print-url',
        action='store_true',
        help='If this is specified, LLVM package download URL is printed to standard output')

    args = arg_parser.parse_args()
    if args.print_url:
        sys_conf = local_sys_conf()
        short_os_name_and_version = sys_conf.short_os_name_and_version()
        installer = LlvmInstaller(
            short_os_name_and_version=short_os_name_and_version,
            architecture=sys_conf.architecture)
        llvm_url = installer.get_llvm_url(major_llvm_version=args.llvm_major_version)
        print(llvm_url)


if __name__ == '__main__':
    main()
