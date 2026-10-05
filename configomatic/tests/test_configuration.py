"""Tests for loading configurations from files, the environment and kwargs."""

import os
import pathlib
import typing as t

import pytest
from pydantic import ValidationError

from configomatic import Configuration, FileNotFound, Section

ENV_PREFIX = "CONFIGOMATICTEST"


@pytest.fixture(autouse=True)
def clean_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove environment variables with the test prefix, so they can't leak in."""
    # Make sure no stray environment variables with the test prefix leak in
    for key in list(os.environ):
        if key.upper().startswith(ENV_PREFIX):
            monkeypatch.delenv(key)


class Inner(Section):
    """Section used to test nested configuration."""

    some_value: int = 0
    other: str = "default"


def write(path: pathlib.Path, content: str) -> pathlib.Path:
    """Write content to the given path and return the path."""
    path.write_text(content)
    return path


def test_load_from_default_path(tmp_path: pathlib.Path) -> None:
    """Test that configuration is loaded from the default path."""
    config_file = write(tmp_path / "config.yaml", "name: fromfile\n")

    class Config(Configuration, default_path=str(config_file)):
        name: str = "default"

    assert Config().name == "fromfile"


def test_missing_default_path_is_ignored(tmp_path: pathlib.Path) -> None:
    """Test that a missing default file is not an error, and field defaults are used."""

    class Config(Configuration, default_path=str(tmp_path / "missing.yaml")):
        name: str = "default"

    assert Config().name == "default"


def test_missing_explicit_path_raises(tmp_path: pathlib.Path) -> None:
    """Test that a missing file given explicitly with _path raises FileNotFound."""

    class Config(Configuration):
        name: str = "default"

    with pytest.raises(FileNotFound):
        Config(_path=str(tmp_path / "missing.yaml"))


def test_explicit_path_overrides_default(tmp_path: pathlib.Path) -> None:
    """Test that _path, as a str or a Path, takes precedence over the default path."""
    default_file = write(tmp_path / "default.yaml", "name: default\n")
    explicit_file = write(tmp_path / "explicit.yaml", "name: explicit\n")

    class Config(Configuration, default_path=str(default_file)):
        name: str = "unset"

    assert Config(_path=str(explicit_file)).name == "explicit"
    assert Config(_path=explicit_file).name == "explicit"


def test_path_env_var(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the path env var takes precedence over the default path."""
    default_file = write(tmp_path / "default.yaml", "name: default\n")
    env_file = write(tmp_path / "env.yaml", "name: fromenvpath\n")
    monkeypatch.setenv(f"{ENV_PREFIX}_PATH", str(env_file))

    class Config(
        Configuration,
        default_path=str(default_file),
        path_env_var=f"{ENV_PREFIX}_PATH",
    ):
        name: str = "unset"

    assert Config().name == "fromenvpath"


def test_missing_path_from_env_var_raises(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that a missing file given by the path env var raises FileNotFound."""
    monkeypatch.setenv(f"{ENV_PREFIX}_PATH", str(tmp_path / "missing.yaml"))

    class Config(Configuration, path_env_var=f"{ENV_PREFIX}_PATH"):
        name: str = "unset"

    with pytest.raises(FileNotFound):
        Config()


def test_empty_file_gives_defaults(tmp_path: pathlib.Path) -> None:
    """Test that an empty configuration file results in the field defaults."""
    config_file = write(tmp_path / "config.yaml", "")

    class Config(Configuration, default_path=str(config_file)):
        name: str = "default"

    assert Config().name == "default"


def test_environment_overrides(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that prefixed environment variables override values from the file."""
    config_file = write(
        tmp_path / "config.yaml",
        "name: fromfile\ninner:\n  other: fromfile\n",
    )
    monkeypatch.setenv(f"{ENV_PREFIX}__NAME", "fromenv")
    # Nesting uses __, the prefix is case-insensitive and the rest is lowercased,
    # so it matches field names rather than aliases
    monkeypatch.setenv(f"{ENV_PREFIX.lower()}__INNER__SOME_VALUE", "2")
    # Empty environment variables are ignored
    monkeypatch.setenv(f"{ENV_PREFIX}__INNER__OTHER", "")

    class Config(Configuration, default_path=str(config_file), env_prefix=ENV_PREFIX):
        name: str = "default"
        inner: Inner = Inner()

    config = Config()
    assert config.name == "fromenv"
    assert config.inner.some_value == 2
    assert config.inner.other == "fromfile"


def test_use_flags(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _use_file and _use_env disable loading from each source."""
    config_file = write(tmp_path / "config.yaml", "name: fromfile\n")
    monkeypatch.setenv(f"{ENV_PREFIX}__NAME", "fromenv")

    class Config(Configuration, default_path=str(config_file), env_prefix=ENV_PREFIX):
        name: str = "default"

    assert Config(_use_env=False).name == "fromfile"
    assert Config(_use_file=False).name == "fromenv"
    assert Config(_use_file=False, _use_env=False).name == "default"


def test_init_kwargs_take_precedence(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that keyword arguments are deep-merged over the file and the environment."""
    config_file = write(tmp_path / "config.yaml", "inner:\n  someValue: 1\n")
    monkeypatch.setenv(f"{ENV_PREFIX}__INNER__OTHER", "fromenv")

    class Config(Configuration, default_path=str(config_file), env_prefix=ENV_PREFIX):
        inner: Inner = Inner()

    config = Config(inner={"someValue": 3})
    # Init kwargs are deep-merged over the file and environment
    assert config.inner.some_value == 3
    assert config.inner.other == "fromenv"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Sources are merged before validation, so an alias key (someValue) and a "
        "field name key (some_value) for the same field are both kept, and the alias "
        "wins regardless of source precedence"
    ),
)
def test_field_name_overrides_alias_from_lower_precedence_source(
    tmp_path: pathlib.Path,
) -> None:
    """Test that a field name key overrides an alias key from a lower source."""
    config_file = write(tmp_path / "config.yaml", "inner:\n  someValue: 1\n")

    class Config(Configuration, default_path=str(config_file)):
        inner: Inner = Inner()

    assert Config(inner={"some_value": 3}).inner.some_value == 3


def test_aliases_and_field_names(tmp_path: pathlib.Path) -> None:
    """Test that fields can be set by their camelCase alias or field name."""
    config_file = write(
        tmp_path / "config.yaml", "inner:\n  someValue: 1\nsomeSetting: 2\n"
    )

    class Config(Configuration, default_path=str(config_file)):
        some_setting: int = 0
        inner: Inner = Inner()

    config = Config()
    assert config.some_setting == 2
    assert config.inner.some_value == 1
    assert Config(_use_file=False, some_setting=5).some_setting == 5


def test_config_env_is_inherited(tmp_path: pathlib.Path) -> None:
    """Test that config_env is inherited and can be overridden in subclasses."""
    base_file = write(tmp_path / "base.yaml", "name: base\n")
    child_file = write(tmp_path / "child.yaml", "name: child\n")

    class Base(Configuration, default_path=str(base_file), env_prefix=ENV_PREFIX):
        name: str = "default"

    class Inherits(Base):
        pass

    class Overrides(Base, default_path=str(child_file)):
        pass

    class OverridesAttr(Base):
        config_env = {"default_path": str(child_file)}  # noqa: RUF012

    assert Inherits().name == "base"
    assert Inherits.config_env["env_prefix"] == ENV_PREFIX
    assert Overrides().name == "child"
    assert Overrides.config_env["env_prefix"] == ENV_PREFIX
    assert OverridesAttr().name == "child"
    # The base is unchanged
    assert Base().name == "base"


def test_pydantic_class_kwargs_are_passed_through() -> None:
    """Test that class keywords not for config_env are passed to pydantic."""

    class Config(Configuration, extra="forbid"):
        name: str = "default"

    with pytest.raises(ValidationError):
        Config(_use_file=False, _use_env=False, unknown="x")


def test_custom_load_file(tmp_path: pathlib.Path) -> None:
    """Test that a custom load_file function is called with the configuration path."""
    config_file = write(tmp_path / "config.custom", "ignored")
    seen: list[pathlib.Path] = []

    def load_file(path: pathlib.Path) -> dict[str, t.Any]:
        seen.append(path)
        return {"name": "custom"}

    class Config(Configuration, default_path=str(config_file), load_file=load_file):
        name: str = "default"

    assert Config().name == "custom"
    assert seen == [config_file]


def test_validation_error(tmp_path: pathlib.Path) -> None:
    """Test that invalid values from the file raise a pydantic ValidationError."""
    config_file = write(tmp_path / "config.yaml", "count: notanint\n")

    class Config(Configuration, default_path=str(config_file)):
        count: int = 0

    with pytest.raises(ValidationError):
        Config()
