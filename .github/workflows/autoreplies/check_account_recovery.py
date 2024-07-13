"""Parse a GitHub issue to automatically aggregate package ownership information to facilitate account recovery.

Steps
1) finds all PyPI packages maintained by the user
2) checks each PyPI package to see if its source code repository listed at PyPI belongs to the github user
3) adds a comment to the issue summarizing the package ownership information

If the github user owns the source code repositories for all of the PyPI packages, or is an administrator for the github
organization that owns them, then the issue is automatically labeled with "fasttrack".

Environment Variables
---------------------
GITHUB_ISSUE_OWNER
    The owner (e.g., "pypi") of the issue repository

GITHUB_ISSUE_REPO
    The repository (e.g., "support") where the issue is located

ISSUE_NUMBER
    The number of the issue to process

GITHUB_TOKEN
    (Optional) A GitHub token with permissions to comment on the issue and read the repository.
"""

import os
import sys

import pypi_utils
import gh_utils


# Issue body headers
PYPI_USER_HEADER = "PyPI Username"

# Ownership status levels
BELONGS = 0
ORG_ADMIN = 1
ORG_MEMBER = 2
UNKNOWN_OWERNSHIP = 3
NO_REPO = 4

# This notice indicates that the final determination of account recovery rests with the PyPI team
BOT_NOTICE = (
    "### NOTE\n\n"
    "_This action was performed automatically by a bot and **does not guarantee account recovery**. Account recovery"
    " requires manual approval processing by the PyPI team._"
)


def sanitize_pypi_user(username: str) -> str:
    """Remove any backticks from the username.

    Some users write their usernames like:
    `username`
    for pretty markdown purposes, but we don't want the backticks.
    """
    return username.strip().replace("`", "")


def format_markdown_table(rows: list) -> str:
    """Format a list of rows into a markdown table.

    Parameters
    ----------
    rows: list
        A list of rows to format into a table. Each row should be [package_link, repo_url, ownership_level] where
        ownership_level is an int indicating which column to mark with an "X".
    """
    header = ["Package", "Repository", "Owner", "Admin", "Member", "Unknown", "No Repo"]
    row_strings = []
    row_strings.append(" | ".join(header))
    row_strings.append(" | ".join(["---"] * 2 + [":-:"] * (len(header) - 2)))
    for row in rows:
        row_fields = [""] * len(header)
        row_fields[0] = row[0]
        row_fields[1] = row[1]
        row_fields[2 + row[2]] = "X"
        row_strings.append(" | ".join(row_fields))
    return "\n".join(row_strings)


def format_markdown_package_link(package_name: str) -> str:
    return f"[{package_name}](https://pypi.org/project/{package_name})"


def format_markdown_pypi_user_link(pypi_user: str) -> str:
    return f"[{pypi_user}](https://pypi.org/user/{pypi_user}/)"


def format_markdown_gh_user_link(gh_user: str) -> str:
    return f"[{gh_user}](https://github.com/{gh_user}/)"


def X_add_issue_comment(
    comment: str, github_issue_owner: str, github_issue_repo: str, issue_number: str, github_token: str = None
):
    print()
    print(comment)
    print()


if __name__ == "__main__":
    issue_number = os.environ.get("ISSUE_NUMBER", "4386")
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
        # gh_utils.add_issue_comment(
        X_add_issue_comment(
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
        pypi_package_link = format_markdown_package_link(package_name)
        package = pypi_utils.get_pypi_project_info(package_name)

        # Package has source code repo listed at PyPI
        if "repository_url" not in package:
            package_ownership.append([pypi_package_link, "", NO_REPO])
            continue

        package_repo_url = package["repository_url"]

        # Package source repo directly belongs to the gh_user
        if gh_utils.does_user_own_repo(package_repo_url, gh_user):
            package_ownership.append([pypi_package_link, package_repo_url, BELONGS])
            continue

        # If package source repo belongs to an organization - check if the gh_user is a member or admin
        org_status = gh_utils.get_user_role_in_org(package_repo_url, gh_user)
        if org_status == "admin":
            package_ownership.append([pypi_package_link, package_repo_url, ORG_ADMIN])
        elif org_status == "member":
            package_ownership.append([pypi_package_link, package_repo_url, ORG_MEMBER])

        # Otherwise the source repo may not belong to the gh_user
        else:
            package_ownership.append([pypi_package_link, package_repo_url, UNKNOWN_OWERNSHIP])

    # Add a comment to the issue with the package ownership information
    table = format_markdown_table(package_ownership)

    # Count how many packages are not owned or administered by the user
    num_unverified = len([row for row in package_ownership if row[2] > ORG_ADMIN])

    if num_unverified == 0:
        label = "fasttrack"
    else:
        label = ""

    comment = "\n\n".join(["### Package Ownership", table, BOT_NOTICE])

    try:
        # gh_utils.add_issue_comment(
        #    comment, github_issue_owner, github_issue_repo, issue_number, github_token=github_token
        # )
        X_add_issue_comment(comment, github_issue_owner, github_issue_repo, issue_number, github_token=github_token)
    except Exception as e:
        print(f"Failed to add comment to issue {issue_number}: {e}")
        print("Comment:")
        print(comment)

    if label and False:
        try:
            gh_utils.add_label_to_issue(
                label, github_issue_owner, github_issue_repo, issue_number, github_token=github_token
            )
        except Exception as e:
            print(f"Failed to add label to issue {issue_number}: {e}")
