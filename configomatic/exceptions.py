"""
Module containing configomatic exceptions.
"""


class FileNotFound(RuntimeError):  # noqa: N818
    """
    Raised when a configuration file is not found.
    """


class RequiredPackageNotAvailable(RuntimeError):  # noqa: N818
    """
    Raised when a package required to load a particular file format is not available.
    """


class NoSuitableLoader(RuntimeError):  # noqa: N818
    """
    Raised when there is no suitable loader for a configuration file.
    """
