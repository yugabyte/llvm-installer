#!/usr/bin/env python3

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

from llvm_installer import LlvmInstaller, ParsedTag, TagParsingError, get_release_tags_file_path

from github import Github, GithubException
from github.GitRelease import GitRelease


def main() -> None:
    github_token_file_path = os.path.expanduser('~/.github-token')
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token and os.path.exists(github_token_file_path):
        with open(github_token_file_path) as github_token_file:
            github_token = github_token_file.read().strip()

    github_client = Github(login_or_token=github_token)
    repo = github_client.get_repo('yugabyte/build-clang')
    installer = LlvmInstaller()
    valid_tags = []
    output_path = get_release_tags_file_path()
    if not os.path.isdir(os.path.dirname(output_path)):
        raise IOError(f"Directory of the output file {output_path} does not exist")

    for release in repo.get_releases():

        tag_name = release.tag_name
        url_for_tag = installer.get_url_for_tag(tag_name)

        download_urls = []
        for asset in release.get_assets():
            download_urls.append(asset.browser_download_url)
        if url_for_tag in download_urls and url_for_tag + '.sha256' in download_urls:
            logging.info("Found release: %s", url_for_tag)
            try:
                parsed_tag = ParsedTag.from_tag(tag_name)
            except TagParsingError as ex:
                logging.warning("Skipping tag due to error: %s", ex)
                continue

            if parsed_tag.major_version < 12:
                logging.warning("Skipping old release version: %s", parsed_tag)
                continue

            logging.info("Tag: %s", parsed_tag)
            valid_tags.append(parsed_tag)
        else:
            logging.info(
                "Skipping release: %s with tag %s (expected release URLs not found)",
                release, tag_name)
    valid_tags.sort(key=lambda parsed_tag: parsed_tag.get_sort_key())
    json_data = {"parsed_tags": [valid_tag.as_dict() for valid_tag in valid_tags]}

    with open(output_path, 'w') as output_file:
        output_file.write(json.dumps(json_data, sort_keys=True, indent=2) + '\n')
    logging.info(f"Wrote {len(valid_tags)} releases to file: {output_path}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="[%(filename)s:%(lineno)d] %(asctime)s %(levelname)s: %(message)s")

    main()
