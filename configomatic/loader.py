import glob
import json
import pathlib

from pydantic.utils import deep_update

try:
    import yaml
    yaml_available = True
except ImportError:
    yaml_available = False

try:
    import toml
    toml_available = True
except ImportError:
    toml_available = False

from .exceptions import RequiredPackageNotAvailable, NoSuitableLoader


if yaml_available:
    # If YAML is available, add support for inclusion tags to support loading
    # configuration sections from other files

    def include_constructor(loader, node):
        """
        Implements the "!include" tag.

        We allow a single path or a comma-separated list of paths, where each path
        is allowed to be a glob pattern. Paths can be explicitly excluded by prefixing
        the path with "!".

        Examples:

          !include ./include.yaml
          !include ./include1.yaml, include2.yaml
          !include ./includes/*.yaml
          !include ./includes/*.yaml, !./includes/excluded.yaml
        """
        paths = (path.strip() for path in loader.construct_scalar(node).split(","))
        # We use glob rather than pathlib.Path.glob here as we don't know where in
        # the path glob patterns will occur
        included_paths = set()
        excluded_paths = set()
        for path in paths:
            if path.startswith("!"):
                excluded_paths.update(
                    pathlib.Path(p).resolve()
                    for p in glob.iglob(path[1:], recursive = True)
                )
            else:
                included_paths.update(
                    pathlib.Path(p).resolve()
                    for p in glob.iglob(path, recursive = True)
                )
        # Merge the configs in sort order, so overrides are predictable
        return deep_update(*[
            load_file(path)
            for path in sorted(included_paths - excluded_paths)
        ])

    yaml.add_constructor("!include", include_constructor, Loader = yaml.SafeLoader)


class Suffixes:
    """
    Collection of known suffixes for the supported loaders.
    """
    JSON = [".json"]
    YAML = [".yml", ".yaml"]
    TOML = [".toml"]


def load_json(fh):
    """
    Attempts to load configuration as JSON from the given file handle.
    """
    return json.load(fh)


def load_yaml(fh):
    """
    Attempts to load configuration as YAML from the given file handle.
    """
    if yaml_available:
        return yaml.safe_load(fh)
    else:
        raise RequiredPackageNotAvailable("PyYAML must be installed to load YAML files")


def load_toml(fh):
    """
    Attempts to load configuration as TOML from the given file handle.
    """
    if toml_available:
        return toml.load(fh)
    else:
        raise RequiredPackageNotAvailable("toml must be installed to load TOML files")


def load_file(path):
    """
    Attempts to load the specified configuration file.

    This function will try various formats, based on the file suffix.
    The relevant libaries must be installed.
    """
    with path.open() as fh:
        if path.suffix in Suffixes.JSON:
            return load_json(fh)
        elif path.suffix in Suffixes.YAML:
            return load_yaml(fh)
        elif path.suffix in Suffixes.TOML:
            return load_toml(fh)
        else:
            raise NoSuitableLoader(f"no loader for suffix {path.suffix}")
