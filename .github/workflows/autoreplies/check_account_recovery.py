"""Parse a GitHub issue to determine the best path forward for account recovery requests.


"""

import os
import sys

import pypi_utils
import gh_utils


PYPI_USER_HEADER = "PyPI Username"


NO_REPO = "None listed"
UNKNOWN_OWERNSHIP = "May not belong to user"
BELONGS = "Belongs to user"


def sanitize_pypi_user(username: str) -> str:
    """Remove any backticks from the username.

    Some users write their usernames like:
    `username`
    for pretty markdown purposes, but we don't want the backticks.
    """
    return username.strip().replace("`", "")


def Xadd_issue_comment(comment: str, gh_user: str, repo_name: str, issue_number, github_token=None):
    print()
    print("Comment")
    print()
    print(comment)
    print()


def Xadd_label_to_issue(label: str, gh_user: str, repo_name: str, issue_number, github_token=None):
    print()
    print("Label")
    print()
    print(label)
    print()


def format_markdown_table(header: list, rows: list) -> str:
    """Format a list of rows into a markdown table."""
    row_strings = []
    row_strings.append(" | ".join(header))
    row_strings.append(" | ".join(["---"] * len(header)))
    for row in rows:
        row_strings.append(" | ".join(row))
    return "\n".join(row_strings)


def format_markdown_package_link(package_name: str) -> str:
    return f"[{package_name}](https://pypi.org/project/{package_name})"


def format_markdown_pypi_user_link(pypi_user: str) -> str:
    return f"[{pypi_user}](https://pypi.org/user/{pypi_user}/)"


def format_markdown_gh_user_link(gh_user: str) -> str:
    return f"[{gh_user}](https://github.com/{gh_user}/)"


if __name__ == "__main__":
    issue_number = os.environ.get("ISSUE_NUMBER", "4343")
    github_token = os.environ.get("GITHUB_TOKEN", None)
    github_issue_owner = os.environ.get("GITHUB_ISSUE_OWNER", "pypi")
    github_issue_repo = os.environ.get("GITHUB_ISSUE_REPO", "support")

    issue_data = gh_utils.fetch_issue_details(
        github_issue_owner, github_issue_repo, issue_number, github_token=github_token
    )

    gh_user = issue_data["user"]
    gh_user_link = format_markdown_gh_user_link(gh_user)

    if PYPI_USER_HEADER not in issue_data["body"]:
        raise ValueError(f"Issue body does not contain expected header: {PYPI_USER_HEADER}")

    pypi_user = sanitize_pypi_user(issue_data["body"]["PyPI Username"])
    pypi_user_link = format_markdown_pypi_user_link(pypi_user)

    try:
        packages = pypi_utils.get_packages_by_user(pypi_user)
    except ValueError as e:
        raise e

    # If the pypi user is not a maintainer for any packages
    if not packages:
        gh_utils.add_issue_comment(
            f"User {pypi_user_link} has no packages",
            github_issue_owner,
            github_issue_repo,
            issue_number,
            github_token=github_token,
        )
        sys.exit()

    # Loop over all packages to see if they belong to the user
    package_ownership = []  # List of [package_name, repo_url, ownership_status]
    for package_name in packages:
        package_md_link = format_markdown_package_link(package_name)
        package = pypi_utils.get_pypi_project_info(package_name)

        # Package has source code repo listed at PyPI
        if "repository_url" not in package:
            package_ownership.append([package_md_link, "", NO_REPO])
            continue

        package_repo = package["repository_url"]

        # Package source code may not belong to the user
        if not (
            gh_utils.is_github_repo_belonging_to_owner(package_repo, gh_user)
            or gh_utils.is_github_pages_belonging_to_owner(package_repo, gh_user)
        ):
            package_ownership.append([package_md_link, package_repo, UNKNOWN_OWERNSHIP])
        else:
            package_ownership.append([package_md_link, package_repo, BELONGS])

    # Add a comment to the issue with the package ownership information
    header = ["Package", "Repository", "Ownership"]
    table = format_markdown_table(header, package_ownership)

    unknown_ownership = [row[1] for row in package_ownership if row[-1] != BELONGS]
    label = None

    if len(unknown_ownership) == 0:
        approval_message = f"All projects maintained by {pypi_user_link} belong to the gh user {gh_user_link}"
        label = "fasttrack"
    else:
        approval_message = f"{len(unknown_ownership)} projects may not belong to the gh user {gh_user_link}"

    comment = f"""\
## Package Ownership

{table}

{approval_message}

## NOTE

This action was performed by a bot. Account recovery requires manual approval by processing by PyPI."""

    gh_utils.add_issue_comment(comment, github_issue_owner, github_issue_repo, issue_number, github_token=github_token)
    if label:
        gh_utils.add_label_to_issue(
            label, github_issue_owner, github_issue_repo, issue_number, github_token=github_token
        )
