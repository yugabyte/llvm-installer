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

import sys_detection
import re
import logging

from packaging import version

from sys_detection import SHORT_OS_NAME_REGEX_STR, is_compatible_os, local_sys_conf

from typing import Optional, List, Union, Sequence


ARCH_RE_STR = '|'.join(['x86_64', 'aarch64', 'arm64'])

DEFAULT_GITHUB_RELEASE_URL_PREFIX = 'https://github.com/yugabyte/build-clang/releases/download'
DEFAULT_PACKAGE_NAME_PREFIX = 'yb-llvm-'
DEFAULT_PACKAGE_NAME_SUFFIX = '.tar.gz'


TAGS = [
    'v11.1.0-yb-1-1633099975-130bd22e-centos7-x86_64',
    'v11.1.0-yb-1-1633143292-130bd22e-almalinux8-x86_64',
    'v11.1.0-yb-1-1633544021-130bd22e-centos8-aarch64',
    'v11.1.0-yb-1-1647671171-130bd22e-amzn2-aarch64',
    'v12.0.1-yb-1-1633099823-bdb147e6-centos7-x86_64',
    'v12.0.1-yb-1-1633143152-bdb147e6-almalinux8-x86_64',
    'v12.0.1-yb-1-1647674838-bdb147e6-amzn2-aarch64',
    'v12.0.1-yb-1-1648458260-bdb147e6-almalinux8-aarch64',
    'v12.0.1-yb-1-1651704621-bdb147e6-ubuntu20.04-x86_64',
    'v12.0.1-yb-1-1651728697-bdb147e6-ubuntu22.04-x86_64',
    'v13.0.0-yb-1-1639976983-4b60e646-centos8-aarch64',
    'v13.0.1-yb-1-1644383736-191e3a05-centos7-x86_64',
    'v13.0.1-yb-1-1644390288-191e3a05-almalinux8-x86_64',
    'v13.0.1-yb-1-1647678956-191e3a05-amzn2-aarch64',
    'v13.0.1-yb-1-1651706387-191e3a05-ubuntu20.04-x86_64',
    'v13.0.1-yb-1-1651730352-191e3a05-ubuntu22.04-x86_64',
    'v14.0.0-1648363631-329fda39-almalinux8-x86_64',
    'v14.0.0-1648379878-329fda39-amzn2-aarch64',
    'v14.0.0-1648380033-329fda39-almalinux8-aarch64',
    'v14.0.0-1648392050-329fda39-centos7-x86_64',
    'v14.0.3-1651708261-1f914006-ubuntu20.04-x86_64',
    'v14.0.3-1651732108-1f914006-ubuntu22.04-x86_64 ',
]

TAG_RE_STR = ''.join([
    r'^',
    r'v(?P<version>[0-9.]+)',
    r'(-(?P<version_suffix>[a-z0-9-]+))?',
    r'-',
    r'(?P<timestamp>\d+)',
    r'-',
    r'(?P<sha1_prefix>[0-9a-f]+)',
    r'-',
    rf'(?P<short_os_name_and_version>(?:{SHORT_OS_NAME_REGEX_STR})[0-9.]*)',
    r'-',
    rf'(?P<architecture>{ARCH_RE_STR})',
    r'$'
])

TAG_RE = re.compile(TAG_RE_STR)


class ParsedTag:
    tag: str

    version: str
    version_suffix: Optional[str]
    timestamp: str
    sha1: str
    short_os_name_and_version: str
    architecture: str

    ATTR_NAMES = [
        'version',
        'version_suffix',
        'timestamp',
        'sha1_prefix',
        'short_os_name_and_version',
        'architecture',
    ]

    def __init__(self, tag: str) -> None:
        self.tag = tag
        m = TAG_RE.match(tag)
        if not m:
            raise ValueError(
                f"Cannot parse tag: {tag}. Does not match regular expression: {TAG_RE_STR}")
        for k, v in m.groupdict().items():
            assert k in ParsedTag.ATTR_NAMES, \
                f'Unexpected parsed tag group key: {k}, valid keys: {ParsedTag.ATTR_NAMES}'
            setattr(self, k, v)

    def __repr__(self) -> str:
        return 'ParsedTag(%s)' % ', '.join(
            [f'{k}={repr(getattr(self, k))}' for k in ParsedTag.ATTR_NAMES]
        )

    __str__ = __repr__


class LlvmPackageCollection:
    parsed_tags: List[ParsedTag]

    _instance: Optional['LlvmPackageCollection'] = None

    def __init__(self, tags: Sequence[Union[str, ParsedTag]]):
        self.parsed_tags = [
            (tag if isinstance(tag, ParsedTag) else ParsedTag(tag))
            for tag in tags
        ]

    @classmethod
    def get_instance(self) -> 'LlvmPackageCollection':
        if not LlvmPackageCollection._instance:
            LlvmPackageCollection._instance = LlvmPackageCollection(TAGS)
        return LlvmPackageCollection._instance

    def filter(
            self,
            major_llvm_version: int,
            short_os_name_and_version: str,
            architecture: str) -> 'LlvmPackageCollection':
        return LlvmPackageCollection([
            parsed_tag for parsed_tag in self.parsed_tags
            if parsed_tag.version.startswith(str(major_llvm_version) + '.') and
            is_compatible_os(
                parsed_tag.short_os_name_and_version,
                short_os_name_and_version) and
            parsed_tag.architecture == architecture
        ])

    def one_per_line_str(self, indent: int = 4) -> str:
        indent_str = ' ' * indent
        return indent_str + ('\n' + indent_str).join([
            str(parsed_tag) for parsed_tag in self.parsed_tags
        ])

    def __str__(self) -> str:
        return str(self.parsed_tags)

    __repr__ = __str__


class LlvmInstaller:
    major_llvm_version: int
    architecture: str
    short_os_name_and_version: str
    github_release_url_prefix: str
    package_name_prefix: str
    package_name_suffix: str

    def __init__(
            self,
            major_llvm_version: int,
            short_os_name_and_version: Optional[str] = None,
            architecture: Optional[str] = None,
            github_release_url_prefix: Optional[str] = None,
            package_name_prefix: Optional[str] = None,
            package_name_suffix: Optional[str] = None) -> None:

        self.major_llvm_version = major_llvm_version
        self.short_os_name_and_version = (
            short_os_name_and_version or local_sys_conf().short_os_name_and_version()
        )
        self.architecture = architecture or local_sys_conf().architecture

        self.github_release_url_prefix = (
            github_release_url_prefix or DEFAULT_GITHUB_RELEASE_URL_PREFIX)
        if self.github_release_url_prefix.endswith('/'):
            self.github_release_url_prefix = self.github_release_url_prefix[:-1]

        self.package_name_prefix = package_name_prefix or DEFAULT_PACKAGE_NAME_PREFIX
        self.package_name_suffix = package_name_suffix or DEFAULT_PACKAGE_NAME_SUFFIX

    def get_url_for_tag(self, tag: str) -> str:
        return ''.join([
            self.github_release_url_prefix,
            '/',
            tag,
            '/',
            self.package_name_prefix,
            tag,
            self.package_name_suffix
        ])

    def get_llvm_package(self) -> ParsedTag:
        packages = LlvmPackageCollection.get_instance()
        filtered_packages: LlvmPackageCollection = packages.filter(
            major_llvm_version=self.major_llvm_version,
            short_os_name_and_version=self.short_os_name_and_version,
            architecture=self.architecture)
        selection_criteria_str = ", ".join([
            f"major LLVM version {self.major_llvm_version}",
            f"OS/version {self.short_os_name_and_version}",
            f"architecture {self.architecture}",
        ])
        parsed_tags = filtered_packages.parsed_tags
        if not parsed_tags:
            error_msg = f"Could not find an LLVM release for {selection_criteria_str}"
            logging.warning(error_msg + ". Available packages:\n" + packages.one_per_line_str())
            raise ValueError(error_msg)

        if len(parsed_tags) == 1:
            return parsed_tags[0]

        raise ValueError(
            f"Multiple packages found for {selection_criteria_str}: {filtered_packages}")

    def get_llvm_url(self) -> str:
        return self.get_url_for_tag(self.get_llvm_package().tag)
