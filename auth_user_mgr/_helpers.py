# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Helper functions"""

import json
from urllib.parse import urlencode, urlparse


def convert_dict_to_json(data: dict) -> str:
    """Convert a dict to JSON"""
    return json.dumps(data, indent=2)


def remove_path_from_url(url: str) -> str:
    """Remove the path from a URL"""
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def make_url(base_url: str, *uris: str, **params: str):
    """Create an URL based on a base URL, paths and query params"""
    url = base_url.rstrip("/")
    for uri in uris:
        _uri = uri.strip("/")
        url = f"{url}/{_uri}" if _uri else url
    if params:
        url = f"{url}/?{urlencode(params)}"
    return url


def compare_two_lists(list1: list[str], list2: list[str]):
    """
    Compares two lists of strings and returns a tuple containing elements
    missing in each list and common elements.

    Args:
        list1 (list of str): The first list of strings.
        list2 (list of str): The second list of strings.

    Returns:
        tuple: A tuple containing three lists:
            1. The first list contains elements in `list2` that are missing in `list1`.
            2. The second list contains elements that are present in both `list1` and `list2`.
            3. The third list contains elements in `list1` that are missing in `list2`.

    Example:
        >>> list1 = ["apple", "banana", "cherry"]
        >>> list2 = ["banana", "cherry", "date", "fig"]
        >>> compare_lists(list1, list2)
        (['date', 'fig'], ['banana', 'cherry'], ['apple'])
    """
    # Convert lists to sets for easier comparison
    set1, set2 = set(list1), set(list2)

    # Elements in list2 that are missing in list1
    missing_in_list1 = list(set2 - set1)

    # Elements present in both lists
    common_elements = list(set1 & set2)

    # Elements in list1 that are missing in list2
    missing_in_list2 = list(set1 - set2)

    # Return the result as a tuple
    return (missing_in_list1, common_elements, missing_in_list2)
