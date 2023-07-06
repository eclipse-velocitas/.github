import json
import subprocess

GITHUB_ORG = "eclipse-velocitas"
PROJECT_NAME = "Velocitas Backlog"
project_number: str
project_id: str
status_field_id: str
new_single_select_id: str


def get_project_information():
    project_list_command = subprocess.check_output(
        f"gh project list --owner {GITHUB_ORG} --format json", shell=True
    )
    project_list = json.loads(project_list_command)
    for project in project_list["projects"]:
        if project["title"] == PROJECT_NAME:
            global project_id
            project_id = project["id"]
            global project_number
            project_number = project["number"]


def get_project_field_ids() -> None:
    project_field_command = subprocess.check_output(
        f"gh project field-list {project_number} --owner {GITHUB_ORG} --format json",
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


def check_labels(labels) -> bool:
    for label in labels:
        return label["name"] == "bug"
    return False


get_project_information()
get_project_field_ids()

repo_list_command = subprocess.check_output(
    f"gh repo list {GITHUB_ORG} --json name", shell=True
)
repos = json.loads(repo_list_command)

for repo in repos:
    issue_list_command = subprocess.check_output(
        f'gh issue list -R {GITHUB_ORG}/{repo["name"]} --json title,projectItems,url,labels',
        shell=True,
    )
    issues = json.loads(issue_list_command)
    for issue in issues:
        if not issue["projectItems"] and check_labels(issue["labels"]):
            item_add_command = subprocess.check_output(
                f'gh project item-add {project_number} --owner {GITHUB_ORG} --url {issue["url"]} --format json',
                shell=True,
            )
            added_item = json.loads(item_add_command)
            subprocess.check_output(
                f'gh project item-edit --id {added_item["id"]} --field-id {status_field_id} --project-id {project_id} --single-select-option-id {new_single_select_id}',
                shell=True,
            )
            print(f'Added Issue: {added_item["title"]} URL: {added_item["url"]}')
