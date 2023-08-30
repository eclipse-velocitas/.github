# Copyright (c) 2023 Robert Bosch GmbH
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import subprocess
from typing import List

project_number: str
project_id: str
status_field_id: str = "PVTSSF_lADOBmS-m84AM-x0zgISFug"
new_single_select_id: str = "8f97c9c6"


def get_project_information(owner: str, project_name: str) -> None:
    project_list_command = subprocess.check_output(
        ["gh", "project", "list", "--owner", owner, "--format", "json"]
    )
    project_list = json.loads(project_list_command)
    for project in project_list["projects"]:
        if project["title"] == project_name:
            global project_id
            project_id = project["id"]
            global project_number
            project_number = project["number"]

# This gh cli call has problem when too many issues are in the project
# The internal API call gets a too long response body
# With this function we wanted to get the
# status_field_id and new_single_select_id
# We can hard code this since the fields are IDs
#
# def get_project_field_ids(owner: str) -> None:
#     project_field_command = subprocess.check_output(
#         [
#             "gh",
#             "project",
#             "field-list",
#             str(project_number),
#             "--owner",
#             owner,
#             "--format",
#             "json",
#         ]
#     )
#     project_fields = json.loads(project_field_command)
#     for field in project_fields["fields"]:
#         if field["name"] == "Status": # PVTSSF_lADOBmS-m84AM-x0zgISFug
#             global status_field_id
#             status_field_id = field["id"]
#             for option in field["options"]:
#                 if option["name"] == "🆕 New": # 8f97c9c6
#                     global new_single_select_id
#                     new_single_select_id = option["id"]


def check_labels(labels, allowed_labels: List[str]) -> bool:
    if not allowed_labels:  # Add all issues if no labels are specified
        return True

    for label in labels:
        name = label["name"]
        if name in allowed_labels:
            return True
    return False


def add_project_issues(
    owner: str, project_name: str, allowed_labels: List[str]
) -> None:
    get_project_information(owner, project_name)
    # get_project_field_ids(owner)

    repo_list_command = subprocess.check_output(
        ["gh", "repo", "list", owner, "--json", "name"]
    )
    repos = json.loads(repo_list_command)

    for repo in repos:
        try:
            issue_list_command = subprocess.check_output(
                [
                    "gh",
                    "issue",
                    "list",
                    "-R",
                    f"{owner}/{repo['name']}",
                    "--json",
                    "title,projectItems,url,labels",
                ]
            )
            issues = json.loads(issue_list_command)
            for issue in issues:
                if not issue["projectItems"] and check_labels(
                    issue["labels"], allowed_labels
                ):
                    item_add_command = subprocess.check_output(
                        [
                            "gh",
                            "project",
                            "item-add",
                            str(project_number),
                            "--owner",
                            owner,
                            "--url",
                            issue["url"],
                            "--format",
                            "json",
                        ]
                    )
                    added_item = json.loads(item_add_command)
                    subprocess.check_output(
                        [
                            "gh",
                            "project",
                            "item-edit",
                            "--id",
                            added_item["id"],
                            "--field-id",
                            status_field_id,
                            "--project-id",
                            project_id,
                            "--single-select-option-id",
                            new_single_select_id,
                        ],
                    )
                    print(
                        f'Added Issue: {added_item["title"]} URL: {added_item["url"]}'
                    )
        except Exception as e:
            print(f"Error retrieving issues: {str(e)}")


def main():
    parser = argparse.ArgumentParser("project-issues")
    parser.add_argument(
        "--owner",
        required=True,
        help="Owner of the GitHub Project to add issues to.",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GitHub project name to add issues to.",
    )
    parser.add_argument(
        "--allowed-labels",
        nargs="+",
        default=[],
        help="List of allowed labels to check.",
    )
    args = parser.parse_args()
    add_project_issues(args.owner, args.project, args.allowed_labels)


if __name__ == "__main__":
    main()
