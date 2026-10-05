"""Tests for the utility functions."""

import pytest

from configomatic.utils import merge, snake_to_pascal


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("name", "name"),
        ("some_name", "someName"),
        ("some_longer_name", "someLongerName"),
    ],
)
def test_snake_to_pascal(name: str, expected: str) -> None:
    """Test converting snake_case names to camelCase."""
    assert snake_to_pascal(name) == expected


def test_merge_deep() -> None:
    """Test that nested dictionaries are merged recursively."""
    defaults = {"a": 1, "b": {"c": 2, "d": 3}}
    overrides = {"b": {"d": 4, "e": 5}, "f": 6}
    assert merge(defaults, overrides) == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}


def test_merge_precedence_is_right_to_left() -> None:
    """Test that later overrides take precedence over earlier ones."""
    assert merge({"a": 1}, {"a": 2}, {"a": 3}) == {"a": 3}


def test_merge_none_keeps_default() -> None:
    """Test that a None override keeps the default value."""
    assert merge({"a": 1, "b": 2}, {"a": None}) == {"a": 1, "b": 2}


def test_merge_non_dict_replaces() -> None:
    """Test that a non-dict override replaces the default value."""
    assert merge({"a": {"b": 1}}, {"a": [1, 2]}) == {"a": [1, 2]}


def test_merge_does_not_mutate() -> None:
    """Test that the inputs are not modified."""
    defaults = {"a": {"b": 1}}
    overrides = {"a": {"c": 2}}
    merge(defaults, overrides)
    assert defaults == {"a": {"b": 1}}
    assert overrides == {"a": {"c": 2}}
