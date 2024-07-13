import re
import time
from typing import Dict

import requests
from bs4 import BeautifulSoup


def get_packages_by_user(username: str) -> list:
    """Parse html to get a list of packages for a given PyPI user.

    The pypi api does not provide a way to get a list of packages for a user, hence crawling the html.

    Steps:
    1) Queries the PyPI user page for the given username.
    2) Parses the html to get the number of projects and the list of packages. This assumes that the number of projects
        listed on the page is in the first <h2> tag, in the form "X project" or "X projects".
    3) Loops over all elements of <a class="package-snippet"> to get the package names.
    4) Ensure that the number of packages found is equal to the number of projects reported. If not, raise an error.
    5) Return the list of package names.

    Step 2 is to avoid having to handle pagination of projects. As of now the user with the most projects I have seen
    has 43, and there was no pagination. If pagination is detected, this function will raise an error.

    Parameters
    ----------
        username: str
            The PyPI username to search for.

    Returns
    -------
        list
            A list of package names
    """
    time.sleep(1)
    url = f"https://pypi.org/user/{username}/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        # Get the reported number of projects maintained by this user, to ensure we later don't miss any
        num_projects_text = soup.find("h2").text.lower()
        num_projects_text = num_projects_text.replace("no projects", "0 projects")

        RE_PROJECT_COUNT = re.compile(r"\s*(?P<num_projects>\d+)\s*project(?:s)?")
        re_num_project_match = RE_PROJECT_COUNT.match(num_projects_text)
        if not re_num_project_match:
            raise ValueError(f"Could not determine the number of projects for user {username}")

        num_projects = int(re_num_project_match.group("num_projects"))
        packages = [a.text.strip().split("\n")[0] for a in soup.find_all("a", class_="package-snippet")]
        # Check for pagination: if num_projects > len(packages) then there are probably more pages
        # which aren't handled here yet
        if len(packages) != num_projects:
            raise ValueError(f"num_projects {num_projects} != num_packages {len(packages)} for user {username}")
        return packages
    raise ValueError(f"Error retrieving project data for user {username}")


def get_pypi_project_info(package_name: str) -> Dict[str, str]:
    """Retrieve relevant information about a PyPI project.

    Parameters
    ----------
        package_name: str
            The name of the package to query.

    Returns
    -------
        Dict[str, str]
            A dictionary containing the following keys:
                - repository_url (may be "Not specified" if no repository or homepage is listed)
                - author
                - author_email
    """
    time.sleep(1)
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Error retrieving project info for {package_name}")

    data = response.json()
    info = data.get("info", {})
    project_urls = info.get("project_urls", {}) or {}
    author = info.get("author")
    author_email = info.get("author_email")
    return {
        "repository_url": project_urls.get("Source", project_urls.get("Homepage", "Not specified")),
        "author": author,
        "author_email": author_email,
    }
