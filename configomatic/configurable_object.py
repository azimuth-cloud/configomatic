"""
Module containing the configurable object base class.
"""

from functools import reduce
import json
import os

from pydantic import BaseModel, BaseConfig
from pydantic.utils import deep_update


class ConfigurableObject(BaseModel):
    """
    Base class for a configurable object.
    """
    class Config(BaseConfig):
        # An environment variable that may specify the config path
        path_env_var = None
        # The default configuration path
        default_path = None
        # The function to use to load the configuration file
        load_file = json.load
        # The prefix to use for environment overrides
        env_prefix = None

    __config__ = Config

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
        super().__init__(**deep_update(*configs))

    def _load_file(self, path):
        # If no path is given, try the environment variable
        if not path and self.__config__.path_env_var:
            path = os.environ.get(self.__config__.path_env_var)
        # Any path found by this point is explicitly defined by the user
        explicit_path = bool(path)
        # If we have still not found a path, use the default
        if not path:
            path = self.__config__.default_path
        # Load the specified configuration file
        if path:
            try:
                with open(path) as fh:
                    return self.__config__.load_file(fh)
            except FileNotFoundError:
                if explicit_path:
                    # If the file was explicitly specified by the user, require it to exist
                    raise
                else:
                    # If no path was explicitly specified, don't require the default file to exist
                    return {}
        else:
            return {}

    def _load_environ(self):
        # Build a nested dict from environment variables with the specified prefix
        # Nesting is specified using __
        env_vars = {}
        for env_var, env_val in os.environ.items():
            env_var_parts = env_var.split('__')
            # The first part must match the prefix, but is otherwise thrown away
            if self.__config__.env_prefix:
                if env_var_parts[0].upper() == self.__config__.env_prefix:
                    env_var_parts = env_var_parts[1:]
                else:
                    continue
            # The rest of the parts form a nested dictionary
            nested_vars = reduce(
                lambda vars, part: vars.setdefault(part.lower(), {}),
                env_var_parts[:-1],
                env_vars
            )
            # With the final part, set the value
            nested_vars[env_var_parts[-1].lower()] = env_val
        return env_vars
