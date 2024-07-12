import re
from urllib.parse import urlparse

import requests


def fetch_issue_details(gh_user: str, repo_name: str, issue_number, github_token=None) -> dict:
    """Fetch issue details using the GitHub API."""
    headers = {"Authorization": f"token {github_token}"} if github_token else {}

    url = f"https://api.github.com/repos/{gh_user}/{repo_name}/issues/{issue_number}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return parse_issue_details(response.json())
    raise ValueError(f"Failed to fetch issue details: {response.status_code}")


def parse_issue_details(issue: dict) -> dict:
    """Parse a GitHub issue metadata to retrieve relevant fields."""
    body = parse_issue_body(issue["body"])
    return {
        "created_at": issue["created_at"],
        "user": issue["user"]["login"],
        "url": issue["html_url"],
        "body": body,
    }


def parse_issue_body(body: str) -> dict:
    """Parse the body of a GitHub issue into a dictionary.

    This function works well with the issue templates, though may run into trouble if users include "### " in their own
    body text.

    Parameters
    ----------
    body: str
        The body of the issue.

    Returns
    -------
        dict
            A dictionary with the issue text keyed by the markdown headers (h3)
    """
    RE_GH_ISSUE_HEADER = re.compile(r"### (?P<key>.+)")
    body_dict = {}
    cur_key = None
    cur_lines = []
    for line in body.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        header_match = RE_GH_ISSUE_HEADER.match(line)
        if header_match:
            if cur_key:
                body_dict[cur_key] = "\n".join(cur_lines)
                cur_lines = []
            cur_key = header_match.group("key")
        else:
            cur_lines.append(line)
    return body_dict


def _sanitize_url(url: str) -> str:
    """Ensure the URL starts with "http://" or "https://", and lowercases the URL since GitHub is case-insensitive."""
    url = url.lower()
    if not url.startswith("http"):
        url = f"https://{url}"
    return url


def is_github_pages_belonging_to_owner(code_repo_url: str, gh_user: str) -> bool:
    """Return True if the URL is a GitHub Pages URL for the GitHub user's account."""
    parsed_url = urlparse(_sanitize_url(code_repo_url))

    # Normalize domain
    hostname = parsed_url.hostname or ""
    hostname = hostname.replace("www.", "")
    return hostname == f"{gh_user}.github.io".lower()


def is_github_repo_belonging_to_owner(code_repo_url: str, gh_user: str) -> bool:
    """Return True if the URL is a GitHub repo associated to the GitHub user's account."""
    parsed_url = urlparse(_sanitize_url(code_repo_url))

    # Normalize domain
    hostname = parsed_url.hostname or ""
    hostname = hostname.replace("www.", "")

    # Check if the domain is github.com
    if hostname != "github.com":
        return False

    # Split the path to analyze its parts
    path_parts = parsed_url.path.strip("/").split("/")

    # Check if the first part of the path is 'gh_user'
    return path_parts and path_parts[0] == gh_user.lower()


def add_issue_comment(comment: str, gh_user: str, repo_name: str, issue_number, github_token=None):
    """Add a comment to a GitHub issue."""
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    url = f"https://api.github.com/repos/{gh_user}/{repo_name}/issues/{issue_number}/comments"
    response = requests.post(url, json={"body": comment}, headers=headers)
    if response.status_code != 201:
        raise ValueError(f"Failed to add comment: {response.status_code}")
    return response.json()


def add_label_to_issue(label: str, gh_user: str, repo_name: str, issue_number, github_token=None):
    """Add a label to a GitHub issue."""
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    url = f"https://api.github.com/repos/{gh_user}/{repo_name}/issues/{issue_number}/labels"
    response = requests.post(url, json=[label], headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Failed to add label: {response.status_code}")
    return response.json()
