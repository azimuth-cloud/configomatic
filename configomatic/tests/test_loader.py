"""Tests for loading configuration files in each supported format."""

import pathlib

import pytest

from configomatic import NoSuitableLoader
from configomatic.loader import load_file


def write(path: pathlib.Path, content: str) -> pathlib.Path:
    """Write content to the path, creating parent directories, and return it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_load_json(tmp_path: pathlib.Path) -> None:
    """Test loading a JSON file."""
    path = write(tmp_path / "config.json", '{"a": 1, "b": {"c": "d"}}')
    assert load_file(path) == {"a": 1, "b": {"c": "d"}}


@pytest.mark.parametrize("suffix", [".yaml", ".yml"])
def test_load_yaml(tmp_path: pathlib.Path, suffix: str) -> None:
    """Test loading a YAML file with each supported suffix."""
    path = write(tmp_path / f"config{suffix}", "a: 1\nb:\n  c: d\n")
    assert load_file(path) == {"a": 1, "b": {"c": "d"}}


def test_load_toml(tmp_path: pathlib.Path) -> None:
    """Test loading a TOML file."""
    path = write(tmp_path / "config.toml", 'a = 1\n[b]\nc = "d"\n')
    assert load_file(path) == {"a": 1, "b": {"c": "d"}}


def test_unknown_suffix(tmp_path: pathlib.Path) -> None:
    """Test that an unsupported suffix raises NoSuitableLoader."""
    path = write(tmp_path / "config.ini", "a = 1")
    with pytest.raises(NoSuitableLoader):
        load_file(path)


def test_include_single(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the YAML !include tag loads a single file."""
    # Include paths are resolved relative to the working directory
    monkeypatch.chdir(tmp_path)
    write(tmp_path / "inc.yaml", "value: 1\n")
    path = write(tmp_path / "config.yaml", "section: !include ./inc.yaml\n")
    assert load_file(path) == {"section": {"value": 1}}


def test_include_list_glob_and_exclude(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that !include merges paths and globs in sort order, minus exclusions."""
    monkeypatch.chdir(tmp_path)
    write(tmp_path / "base.json", '{"a": 0, "b": 0, "nested": {"x": 0}}')
    # Globbed files are merged in sort order, so later files win
    write(tmp_path / "includes" / "1.yaml", "a: 1\nnested:\n  y: 1\n")
    write(tmp_path / "includes" / "2.yaml", "a: 2\n")
    write(tmp_path / "includes" / "3.yaml", "b: 3\n")
    path = write(
        tmp_path / "config.yaml",
        "section: !include ./base.json, ./includes/*.yaml, !./includes/3.yaml\n",
    )
    assert load_file(path) == {
        "section": {"a": 2, "b": 0, "nested": {"x": 0, "y": 1}},
    }
