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
import logging
import json

from llvm_installer import LlvmInstaller

from github import Github, GithubException
from github.GitRelease import GitRelease


def main() -> None:
    github_client = Github(login_or_token=os.getenv('GITHUB_TOKEN'))
    repo = github_client.get_repo('yugabyte/build-clang')
    installer = LlvmInstaller()
    valid_tags = []
    for release in repo.get_releases():

        tag_name = release.tag_name
        url_for_tag = installer.get_url_for_tag(tag_name)

        download_urls = []
        for asset in release.get_assets():
            download_urls.append(asset.browser_download_url)
        if url_for_tag in download_urls and url_for_tag + '.sha256' in download_urls:
            logging.info("Found release: %s", url_for_tag)
            valid_tags.append(tag_name)
        else:
            logging.info(
                "Skipping release: %s with tag %s (expected release URLs not found)",
                release, tag_name)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="[%(filename)s:%(lineno)d] %(asctime)s %(levelname)s: %(message)s")

    main()