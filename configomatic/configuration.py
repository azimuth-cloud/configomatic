"""
Module containing the configuration base classes for configomatic.
"""

import functools
import os
import pathlib
import typing as t

from pydantic import BaseModel

from .exceptions import FileNotFound
from .loader import load_file as default_load_file
from .utils import merge, snake_to_pascal


class Section(
    BaseModel,
    alias_generator = snake_to_pascal,
    populate_by_name = True
):
    """
    Base class for a configuration section.
    """


class ConfigEnvironmentDict(t.TypedDict, total = False):
    """
    TypedDict for configuring the config environment.
    """
    path_env_var: t.Optional[str]
    """An environment variable that may specify the config path"""

    default_path: t.Optional[str]
    """The default configuration path"""

    load_file: t.Optional[t.Callable[[str], t.Dict[str, t.Any]]]
    """The function to use to load the configuration file"""

    env_prefix: t.Optional[str]
    """The prefix to use for environment overrides"""


_config_env_keys = set(ConfigEnvironmentDict.__annotations__.keys())


class ConfigurationMeta(type(BaseModel)):
    """
    Metaclass for a configuration.
    """
    def __new__(
        cls,
        name,
        bases,
        attrs,
        /,
        **kwargs
    ):
        # Config environment configuration is inherited from the bases
        config_env = ConfigEnvironmentDict()
        for base in bases:
            config_env.update(getattr(base, "config_env", None) or {})

        # Then a config_env specified on the child
        config_env.update(attrs.pop("config_env", None) or {})

        # Partition the kwargs into those for the config env and those for Pydantic
        config_env_kwargs = {}
        pydantic_kwargs = {}
        for key, value in kwargs.items():
            if key in _config_env_keys:
                config_env_kwargs[key] = value
            else:
                pydantic_kwargs[key] = value

        # Update the config environment with the keywords
        config_env.update(config_env_kwargs)

        # Add the config env to the model attrs
        # Add a classvar annotation so that Pydantic leaves it alone
        attrs["config_env"] = config_env
        attrs.setdefault("__annotations__", {})["config_env"] = t.ClassVar[ConfigEnvironmentDict]

        return super().__new__(cls, name, bases, attrs, **pydantic_kwargs)


class Configuration(
    BaseModel,
    metaclass = ConfigurationMeta,
    alias_generator = snake_to_pascal,
    populate_by_name = True,
):
    """
    Base class for a configuration.
    """
    config_env = ConfigEnvironmentDict()


    def __init__(self, _use_file = True, _path = None, _use_env = True, **init_kwargs):
        # Work out which configs to use
        configs = []
        # If requested, config from file takes the lowest precedence
        if _use_file:
            configs.append(self._load_file(_path))
        # Followed by config from environment variables, if requested
        if _use_env:
            configs.append(self._load_environ())
        # The highest precedence is given to directly supplied keyword args
        configs.append(init_kwargs)
        super().__init__(**merge(*configs))

    def _load_file(self, path):
        # If no path is given, try the environment variable
        path_env_var = self.config_env.get("path_env_var")
        if not path and path_env_var:
            path = os.environ.get(path_env_var)
        # Any path found by this point is explicitly defined by the user
        explicit_path = bool(path)
        # If we have still not found a path, use the default
        if not path:
            path = self.config_env.get("default_path")
        # Load the specified configuration file
        if path:
            path = pathlib.Path(path)
            if path.is_file():
                load_file = self.config_env.get("load_file") or default_load_file
                return load_file(path) or {}
            elif explicit_path:
                # If the file was explicitly specified by the user, require it to exist
                raise FileNotFound(f"{path} does not exist")
            else:
                # If no path was explicitly specified, don't require the default file to exist
                return {}
        else:
            return {}

    def _load_environ(self):
        # Build a nested dict from environment variables with the specified prefix
        # Nesting is specified using __
        env_vars = {}
        env_prefix = self.config_env.get("env_prefix")
        for env_var, env_val in os.environ.items():
            # Only consider non-empty environment variables
            if not env_val:
                continue
            env_var_parts = env_var.split('__')
            # The first part must match the prefix, but is otherwise thrown away
            if env_prefix:
                if env_var_parts[0].upper() == env_prefix.upper():
                    env_var_parts = env_var_parts[1:]
                else:
                    continue
            # The rest of the parts form a nested dictionary
            nested_vars = functools.reduce(
                lambda vars, part: vars.setdefault(part.lower(), {}),
                env_var_parts[:-1],
                env_vars
            )
            # With the final part, set the value
            nested_vars[env_var_parts[-1].lower()] = env_val
        return env_vars
