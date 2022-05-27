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

import os
import unittest

from llvm_installer import TAGS, LlvmPackageCollection, LlvmInstaller


class LlvmInstallerTest(unittest.TestCase):
    def test_package_collection(self) -> None:
        pkg_collection = LlvmPackageCollection(TAGS)

    def test_get_url(self) -> None:
        for major_llvm_version in [12, 13, 14]:
            for short_os_name_and_version in ['centos7', 'almalinux8', 'amzn2', 'centos8']:
                for architecture in ['x86_64', 'aarch64']:
                    if short_os_name_and_version == 'amzn2' and architecture == 'x86_64':
                        continue
                    if short_os_name_and_version == 'centos7' and architecture == 'aarch64':
                        continue
                    installer = LlvmInstaller(
                        short_os_name_and_version=short_os_name_and_version,
                        architecture=architecture)
                    llvm_url = installer.get_llvm_url(major_llvm_version=major_llvm_version)
                    # TODO: try to download the URL.
