"""Tests for _helpers.py"""

from auth_user_mgr._helpers import (
    compare_two_lists,
    convert_dict_to_json,
    make_url,
    remove_path_from_url,
)


def test_convert_dict_to_json():
    """Test converting a dictionary to a JSON string"""
    data = {"name": "Alice", "email": "alice@example.com"}
    json_str = convert_dict_to_json(data)
    assert '"name": "Alice"' in json_str
    assert '"email": "alice@example.com"' in json_str


def test_remove_path_from_url():
    """Test removing the path from a URL"""
    assert remove_path_from_url("https://example.com/api/v1/users") == "https://example.com"
    assert remove_path_from_url("http://sub.host:8000/xyz") == "http://sub.host:8000"


def test_make_url_without_query_params():
    """Test creating a URL without query parameters"""
    url = make_url("https://example.com", "api", "v1", "users")
    assert url == "https://example.com/api/v1/users"


def test_make_url_with_query_params():
    """Test creating a URL with query parameters"""
    url = make_url("https://example.com", "flow", "/", itoken="12345")
    assert url == "https://example.com/flow/?itoken=12345"


def test_make_url_with_empty_path_segments():
    """Test creating a URL with empty path segments"""
    url = make_url("https://example.com", "", "v1", "", "users")
    assert url == "https://example.com/v1/users"


def test_compare_two_lists_basic():
    """Test comparing two lists with some common and missing elements"""
    list1 = ["a", "b"]
    list2 = ["b", "c"]
    missing_in_list1, common, missing_in_list2 = compare_two_lists(list1, list2)
    assert sorted(missing_in_list1) == ["c"]
    assert sorted(common) == ["b"]
    assert sorted(missing_in_list2) == ["a"]


def test_compare_two_lists_empty():
    """Test comparing two empty lists"""
    assert compare_two_lists([], []) == ([], [], [])
    assert compare_two_lists(["a"], []) == ([], [], ["a"])
    assert compare_two_lists([], ["b"]) == (["b"], [], [])
