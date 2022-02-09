"""
Module containing configomatic exceptions.
"""

class FileNotFound(RuntimeError):
    """
    Raised when a configuration file is not found.
    """

class RequiredPackageNotAvailable(RuntimeError):
    """
    Raised when a package required to load a particular file format is not available.
    """


class NoSuitableLoader(RuntimeError):
    """
    Raised when there is no suitable loader for a configuration file.
    """
