"""
Module containing configomatic exceptions.
"""

class FileNotFound(RuntimeError):
    """
    Raised when a configuration file is not found.
    """


class NoSuitableLoader(RuntimeError):
    """
    Raised when there is no suitable loader for a configuration file.
    """
