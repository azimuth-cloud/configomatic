"""
Unit tests for configomatic.exceptions module.
"""

import unittest

from configomatic.exceptions import (
    FileNotFound,
    NoSuitableLoader,
    RequiredPackageNotAvailable,
)


class TestExceptions(unittest.TestCase):
    """Test cases for custom exceptions."""

    def test_file_not_found_inheritance(self):
        """Test that FileNotFound inherits from RuntimeError."""
        self.assertTrue(issubclass(FileNotFound, RuntimeError))

    def test_file_not_found_instantiation(self):
        """Test FileNotFound can be instantiated with a message."""
        message = "Test file not found"
        exception = FileNotFound(message)
        self.assertEqual(str(exception), message)
        self.assertIsInstance(exception, RuntimeError)

    def test_file_not_found_without_message(self):
        """Test FileNotFound can be instantiated without a message."""
        exception = FileNotFound()
        self.assertEqual(str(exception), "")
        self.assertIsInstance(exception, RuntimeError)

    def test_required_package_not_available_inheritance(self):
        """Test that RequiredPackageNotAvailable inherits from RuntimeError."""
        self.assertTrue(issubclass(RequiredPackageNotAvailable, RuntimeError))

    def test_required_package_not_available_instantiation(self):
        """Test RequiredPackageNotAvailable can be instantiated with a message."""
        message = "PyYAML must be installed"
        exception = RequiredPackageNotAvailable(message)
        self.assertEqual(str(exception), message)
        self.assertIsInstance(exception, RuntimeError)

    def test_required_package_not_available_without_message(self):
        """Test RequiredPackageNotAvailable can be instantiated without a message."""
        exception = RequiredPackageNotAvailable()
        self.assertEqual(str(exception), "")
        self.assertIsInstance(exception, RuntimeError)

    def test_no_suitable_loader_inheritance(self):
        """Test that NoSuitableLoader inherits from RuntimeError."""
        self.assertTrue(issubclass(NoSuitableLoader, RuntimeError))

    def test_no_suitable_loader_instantiation(self):
        """Test NoSuitableLoader can be instantiated with a message."""
        message = "No loader for suffix .xyz"
        exception = NoSuitableLoader(message)
        self.assertEqual(str(exception), message)
        self.assertIsInstance(exception, RuntimeError)

    def test_no_suitable_loader_without_message(self):
        """Test NoSuitableLoader can be instantiated without a message."""
        exception = NoSuitableLoader()
        self.assertEqual(str(exception), "")
        self.assertIsInstance(exception, RuntimeError)

    def test_exceptions_can_be_raised_and_caught(self):
        """Test that exceptions can be raised and caught properly."""
        with self.assertRaises(FileNotFound):
            raise FileNotFound("Test message")

        with self.assertRaises(RequiredPackageNotAvailable):
            raise RequiredPackageNotAvailable("Test message")

        with self.assertRaises(NoSuitableLoader):
            raise NoSuitableLoader("Test message")

    def test_exceptions_caught_as_runtime_error(self):
        """Test that exceptions can be caught as RuntimeError."""
        with self.assertRaises(RuntimeError):
            raise FileNotFound("Test message")

        with self.assertRaises(RuntimeError):
            raise RequiredPackageNotAvailable("Test message")

        with self.assertRaises(RuntimeError):
            raise NoSuitableLoader("Test message")


if __name__ == "__main__":
    unittest.main()
