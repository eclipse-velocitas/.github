import argparse
import json
import subprocess

from typing import List


project_number: str
project_id: str
status_field_id: str
new_single_select_id: str


def get_project_information(owner: str, project_name: str) -> None:
    project_list_command = subprocess.check_output(
        f"gh project list --owner {owner} --format json", shell=True
    )
    project_list = json.loads(project_list_command)
    for project in project_list["projects"]:
        if project["title"] == project_name:
            global project_id
            project_id = project["id"]
            global project_number
            project_number = project["number"]


def get_project_field_ids(owner: str) -> None:
    project_field_command = subprocess.check_output(
        f"gh project field-list {project_number} --owner {owner} --format json",
        shell=True,
    )
    project_fields = json.loads(project_field_command)
    for field in project_fields["fields"]:
        if field["name"] == "Status":
            global status_field_id
            status_field_id = field["id"]
            for option in field["options"]:
                if option["name"] == "🆕 New":
                    global new_single_select_id
                    new_single_select_id = option["id"]


def check_labels(labels, allowed_labels: List[str]) -> bool:
    if not allowed_labels:  # Add all issues if no labels are specified
        return True

    for label in labels:
        name = label["name"]
        if name in allowed_labels:
            return True
    return False


def add_project_issues(owner: str, project_name: str, allowed_labels: List[str]) -> None:
    get_project_information(owner, project_name)
    get_project_field_ids(owner)

    repo_list_command = subprocess.check_output(
        f"gh repo list {owner} --json name", shell=True
    )
    repos = json.loads(repo_list_command)

    for repo in repos:
        issue_list_command = subprocess.check_output(
            f'gh issue list -R {owner}/{repo["name"]} --json title,projectItems,url,labels',
            shell=True,
        )
        issues = json.loads(issue_list_command)
        for issue in issues:
            if not issue["projectItems"] and check_labels(issue["labels"], allowed_labels):
                item_add_command = subprocess.check_output(
                    f'gh project item-add {project_number} --owner {owner} --url {issue["url"]} --format json',
                    shell=True,
                )
                added_item = json.loads(item_add_command)
                subprocess.check_output(
                    f'gh project item-edit --id {added_item["id"]} --field-id {status_field_id} --project-id {project_id} --single-select-option-id {new_single_select_id}',
                    shell=True,
                )
                print(f'Added Issue: {added_item["title"]} URL: {added_item["url"]}')


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
        nargs='+',
        default=[],
        help='List of allowed labels to check.',
    )
    args = parser.parse_args()
    add_project_issues(args.owner, args.project, args.allowed_labels)


if __name__ == "__main__":
    main()
