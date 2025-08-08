"""
Unit tests for configomatic.logging module.
"""

import json
import logging
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from configomatic.logging import (
    LOG_RECORD_RESERVED_KEYS,
    DefaultFormatter,
    LessThanLevelFilter,
    LoggingConfiguration,
)


class TestLogRecordReservedKeys(unittest.TestCase):
    """Test cases for LOG_RECORD_RESERVED_KEYS constant."""

    def test_log_record_reserved_keys_type(self):
        """Test that LOG_RECORD_RESERVED_KEYS is a set."""
        self.assertIsInstance(LOG_RECORD_RESERVED_KEYS, set)

    def test_log_record_reserved_keys_contains_expected_keys(self):
        """Test that LOG_RECORD_RESERVED_KEYS contains expected LogRecord keys."""
        # Create a test LogRecord to get the expected keys
        record = logging.LogRecord(
            "test", logging.INFO, "test.py", 1, "message", None, None
        )
        expected_keys = set(record.__dict__.keys())

        self.assertEqual(LOG_RECORD_RESERVED_KEYS, expected_keys)


class TestDefaultFormatter(unittest.TestCase):
    """Test cases for DefaultFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = DefaultFormatter()

    def test_default_formatter_inheritance(self):
        """Test that DefaultFormatter inherits from logging.Formatter."""
        self.assertIsInstance(self.formatter, logging.Formatter)

    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with patch.object(
            logging.Formatter, "format", return_value="formatted"
        ) as mock_super_format:
            result = self.formatter.format(record)

            # Check that super().format() was called
            mock_super_format.assert_called_once_with(record)
            self.assertEqual(result, "formatted")

    def test_format_adds_quotedmessage_property(self):
        """Test that format adds quotedmessage property to record."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            self.assertIn("quotedmessage", record.__dict__)
            self.assertEqual(record.quotedmessage, json.dumps("Test message"))

    def test_format_adds_formattedextra_property(self):
        """Test that format adds formattedextra property to record."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            self.assertIn("formattedextra", record.__dict__)
            # With no extra params, should be empty string
            self.assertEqual(record.formattedextra, "")

    def test_format_with_extra_parameters(self):
        """Test formatting with extra parameters."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra parameters
        record.user_id = "12345"
        record.request_id = "abcdef"

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            # Check quotedmessage
            self.assertEqual(record.quotedmessage, json.dumps("Test message"))

            # Check formattedextra contains extra params
            extra_parts = record.formattedextra.split()
            self.assertEqual(len(extra_parts), 2)
            self.assertIn('user_id="12345"', extra_parts)
            self.assertIn('request_id="abcdef"', extra_parts)

    def test_format_extra_params_json_quoted(self):
        """Test that extra parameter values are JSON-quoted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra parameter with special characters
        record.special_chars = 'test "quotes" and \n newlines'

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            expected_value = json.dumps('test "quotes" and \n newlines')
            self.assertEqual(record.formattedextra, f"special_chars={expected_value}")

    def test_format_message_with_args(self):
        """Test formatting message with arguments."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message %s %d",
            args=("hello", 42),
            exc_info=None,
        )

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            # getMessage() should format the message with args
            expected_message = "Test message hello 42"
            self.assertEqual(record.quotedmessage, json.dumps(expected_message))

    def test_format_excludes_reserved_keys_from_extra(self):
        """Test that reserved keys are not included in formattedextra."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add both reserved and extra keys
        record.custom_field = "custom_value"
        record.name = "modified_name"  # This is reserved and should not appear in extra

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            # Only custom_field should be in formattedextra
            self.assertEqual(record.formattedextra, 'custom_field="custom_value"')

    def test_format_multiple_extra_params_ordering(self):
        """Test that multiple extra parameters are formatted correctly."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add multiple extra parameters
        record.param_a = "value_a"
        record.param_b = 123
        record.param_c = True

        with patch.object(logging.Formatter, "format", return_value="formatted"):
            self.formatter.format(record)

            # Check that all parameters are present
            extra_str = record.formattedextra
            self.assertIn('param_a="value_a"', extra_str)
            self.assertIn('param_b="123"', extra_str)  # Numbers are stringified
            self.assertIn('param_c="True"', extra_str)  # Booleans are stringified


class TestLessThanLevelFilter(unittest.TestCase):
    """Test cases for LessThanLevelFilter class."""

    def test_less_than_level_filter_inheritance(self):
        """Test that LessThanLevelFilter inherits from logging.Filter."""
        filter_obj = LessThanLevelFilter(logging.WARNING)
        self.assertIsInstance(filter_obj, logging.Filter)

    def test_init_with_int_level(self):
        """Test initialization with integer level."""
        filter_obj = LessThanLevelFilter(logging.WARNING)
        self.assertEqual(filter_obj.level, logging.WARNING)

    def test_init_with_string_level_uppercase(self):
        """Test initialization with uppercase string level."""
        filter_obj = LessThanLevelFilter("WARNING")
        self.assertEqual(filter_obj.level, logging.WARNING)

    def test_init_with_string_level_lowercase(self):
        """Test initialization with lowercase string level."""
        filter_obj = LessThanLevelFilter("warning")
        self.assertEqual(filter_obj.level, logging.WARNING)

    def test_init_with_string_level_mixed_case(self):
        """Test initialization with mixed case string level."""
        filter_obj = LessThanLevelFilter("Warning")
        self.assertEqual(filter_obj.level, logging.WARNING)

    def test_init_with_all_standard_levels(self):
        """Test initialization with all standard logging levels."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, level_int in test_cases:
            with self.subTest(level=level_str):
                filter_obj = LessThanLevelFilter(level_str)
                self.assertEqual(filter_obj.level, level_int)

    def test_filter_returns_true_for_lower_level(self):
        """Test that filter returns True for records with lower level."""
        filter_obj = LessThanLevelFilter(logging.WARNING)

        # Create a record with INFO level (lower than WARNING)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        self.assertTrue(filter_obj.filter(record))

    def test_filter_returns_false_for_equal_level(self):
        """Test that filter returns False for records with equal level."""
        filter_obj = LessThanLevelFilter(logging.WARNING)

        # Create a record with WARNING level (equal to filter level)
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        self.assertFalse(filter_obj.filter(record))

    def test_filter_returns_false_for_higher_level(self):
        """Test that filter returns False for records with higher level."""
        filter_obj = LessThanLevelFilter(logging.WARNING)

        # Create a record with ERROR level (higher than WARNING)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        self.assertFalse(filter_obj.filter(record))

    def test_filter_with_various_levels(self):
        """Test filter behavior with various level combinations."""
        filter_obj = LessThanLevelFilter(logging.WARNING)

        test_cases = [
            (logging.DEBUG, True),
            (logging.INFO, True),
            (logging.WARNING, False),
            (logging.ERROR, False),
            (logging.CRITICAL, False),
        ]

        for record_level, expected_result in test_cases:
            with self.subTest(record_level=record_level):
                record = logging.LogRecord(
                    name="test",
                    level=record_level,
                    pathname="test.py",
                    lineno=1,
                    msg="Test message",
                    args=(),
                    exc_info=None,
                )

                self.assertEqual(filter_obj.filter(record), expected_result)

    def test_init_with_invalid_string_level(self):
        """Test initialization with invalid string level raises AttributeError."""
        with self.assertRaises(AttributeError):
            LessThanLevelFilter("INVALID_LEVEL")


class TestLoggingConfiguration(unittest.TestCase):
    """Test cases for LoggingConfiguration class."""

    def test_logging_configuration_inheritance(self):
        """Test that LoggingConfiguration inherits from BaseModel."""
        from pydantic import BaseModel

        self.assertTrue(issubclass(LoggingConfiguration, BaseModel))

    def test_default_field_values(self):
        """Test default field values."""
        config = LoggingConfiguration()

        self.assertEqual(config.version, 1)
        self.assertEqual(config.disable_existing_loggers, False)
        self.assertIsInstance(config.formatters, dict)
        self.assertIsInstance(config.filters, dict)
        self.assertIsInstance(config.handlers, dict)
        self.assertIsInstance(config.loggers, dict)

    def test_default_formatters_validator(self):
        """Test default_formatters validator adds default formatter."""
        config = LoggingConfiguration()

        self.assertIn("default", config.formatters)
        default_formatter = config.formatters["default"]
        self.assertIn("()", default_formatter)
        self.assertIn("configomatic.logging.DefaultFormatter", default_formatter["()"])
        self.assertIn("format", default_formatter)

    def test_default_formatters_validator_preserves_existing(self):
        """Test default_formatters validator preserves existing formatters."""
        custom_formatters = {"custom": {"format": "custom format"}}

        config = LoggingConfiguration(formatters=custom_formatters)

        # Should have both default and custom formatters
        self.assertIn("default", config.formatters)
        self.assertIn("custom", config.formatters)
        self.assertEqual(config.formatters["custom"]["format"], "custom format")

    def test_default_formatters_validator_allows_override(self):
        """Test default_formatters validator allows overriding default."""
        custom_formatters = {"default": {"format": "overridden format"}}

        config = LoggingConfiguration(formatters=custom_formatters)

        # Custom default should override the built-in default
        self.assertEqual(config.formatters["default"]["format"], "overridden format")

    def test_default_filters_validator(self):
        """Test default_filters validator adds less_than_warning filter."""
        config = LoggingConfiguration()

        self.assertIn("less_than_warning", config.filters)
        filter_config = config.filters["less_than_warning"]
        self.assertIn("()", filter_config)
        self.assertIn("configomatic.logging.LessThanLevelFilter", filter_config["()"])
        self.assertEqual(filter_config["level"], "WARNING")

    def test_default_filters_validator_preserves_existing(self):
        """Test default_filters validator preserves existing filters."""
        custom_filters = {"custom": {"()": "custom.filter.Class"}}

        config = LoggingConfiguration(filters=custom_filters)

        # Should have both default and custom filters
        self.assertIn("less_than_warning", config.filters)
        self.assertIn("custom", config.filters)
        self.assertEqual(config.filters["custom"]["()"], "custom.filter.Class")

    def test_default_handlers_validator(self):
        """Test default_handlers validator adds stdout and stderr handlers."""
        config = LoggingConfiguration()

        self.assertIn("stdout", config.handlers)
        self.assertIn("stderr", config.handlers)

        stdout_handler = config.handlers["stdout"]
        self.assertEqual(stdout_handler["class"], "logging.StreamHandler")
        self.assertEqual(stdout_handler["stream"], "ext://sys.stdout")
        self.assertEqual(stdout_handler["formatter"], "default")
        self.assertEqual(stdout_handler["filters"], ["less_than_warning"])

        stderr_handler = config.handlers["stderr"]
        self.assertEqual(stderr_handler["class"], "logging.StreamHandler")
        self.assertEqual(stderr_handler["stream"], "ext://sys.stderr")
        self.assertEqual(stderr_handler["formatter"], "default")
        self.assertEqual(stderr_handler["level"], "WARNING")

    def test_default_handlers_validator_preserves_existing(self):
        """Test default_handlers validator preserves existing handlers."""
        custom_handlers = {
            "file": {"class": "logging.FileHandler", "filename": "app.log"}
        }

        config = LoggingConfiguration(handlers=custom_handlers)

        # Should have default and custom handlers
        self.assertIn("stdout", config.handlers)
        self.assertIn("stderr", config.handlers)
        self.assertIn("file", config.handlers)
        self.assertEqual(config.handlers["file"]["filename"], "app.log")

    def test_default_loggers_validator(self):
        """Test default_loggers validator adds root logger configuration."""
        config = LoggingConfiguration()

        self.assertIn("", config.loggers)  # Root logger has empty string as key
        root_logger = config.loggers[""]
        self.assertEqual(root_logger["handlers"], ["stdout", "stderr"])
        self.assertEqual(root_logger["level"], "INFO")
        self.assertEqual(root_logger["propagate"], True)

    def test_default_loggers_validator_preserves_existing(self):
        """Test default_loggers validator preserves existing loggers."""
        custom_loggers = {"myapp": {"level": "DEBUG", "handlers": ["file"]}}

        config = LoggingConfiguration(loggers=custom_loggers)

        # Should have both root and custom loggers
        self.assertIn("", config.loggers)
        self.assertIn("myapp", config.loggers)
        self.assertEqual(config.loggers["myapp"]["level"], "DEBUG")

    def test_apply_method_calls_dict_config(self):
        """Test that apply method calls logging.config.dictConfig."""
        config = LoggingConfiguration()

        with patch("logging.config.dictConfig") as mock_dict_config:
            config.apply()

            # Should be called once with the config dict
            mock_dict_config.assert_called_once()
            called_config = mock_dict_config.call_args[0][0]

            # Verify the config structure
            self.assertEqual(called_config["version"], 1)
            self.assertEqual(called_config["disable_existing_loggers"], False)
            self.assertIn("formatters", called_config)
            self.assertIn("filters", called_config)
            self.assertIn("handlers", called_config)
            self.assertIn("loggers", called_config)

    def test_apply_method_with_overrides(self):
        """Test apply method with overrides parameter."""
        config = LoggingConfiguration()
        overrides = {"version": 2, "loggers": {"custom": {"level": "DEBUG"}}}

        with (
            patch("logging.config.dictConfig") as mock_dict_config,
            patch("configomatic.logging.merge") as mock_merge,
        ):
            # Configure mock_merge to return merged config
            merged_config = {"version": 2, "merged": True}
            mock_merge.return_value = merged_config

            config.apply(overrides=overrides)

            # merge should be called with base config and overrides
            mock_merge.assert_called_once()
            base_config = mock_merge.call_args[0][0]
            override_arg = mock_merge.call_args[0][1]

            self.assertEqual(override_arg, overrides)
            self.assertEqual(base_config["version"], 1)  # Original config

            # dictConfig should be called with merged result
            mock_dict_config.assert_called_once_with(merged_config)

    def test_apply_method_without_overrides(self):
        """Test apply method without overrides parameter."""
        config = LoggingConfiguration()

        with (
            patch("logging.config.dictConfig") as mock_dict_config,
            patch("configomatic.logging.merge") as mock_merge,
        ):
            config.apply()

            # merge should not be called when no overrides
            mock_merge.assert_not_called()

            # dictConfig should be called with base config
            mock_dict_config.assert_called_once()
            called_config = mock_dict_config.call_args[0][0]
            self.assertEqual(called_config["version"], 1)

    def test_custom_field_values(self):
        """Test LoggingConfiguration with custom field values."""
        config = LoggingConfiguration(version=2, disable_existing_loggers=True)

        self.assertEqual(config.version, 2)
        self.assertEqual(config.disable_existing_loggers, True)

    def test_field_validation_errors(self):
        """Test field validation with invalid types."""
        with self.assertRaises(ValidationError):
            LoggingConfiguration(version="invalid")

        with self.assertRaises(ValidationError):
            LoggingConfiguration(disable_existing_loggers="invalid")

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all configuration fields."""
        config = LoggingConfiguration()
        data = config.model_dump()

        expected_fields = {
            "version",
            "disable_existing_loggers",
            "formatters",
            "filters",
            "handlers",
            "loggers",
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_integration_default_configuration(self):
        """Test the complete default configuration structure."""
        config = LoggingConfiguration()
        data = config.model_dump()

        # Verify complete structure
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["disable_existing_loggers"], False)

        # Check formatters
        self.assertIn("default", data["formatters"])

        # Check filters
        self.assertIn("less_than_warning", data["filters"])

        # Check handlers
        self.assertIn("stdout", data["handlers"])
        self.assertIn("stderr", data["handlers"])

        # Check loggers
        self.assertIn("", data["loggers"])  # Root logger

        # Verify handler configuration makes sense
        stdout_handler = data["handlers"]["stdout"]
        self.assertEqual(stdout_handler["formatter"], "default")
        self.assertIn("less_than_warning", stdout_handler["filters"])

        stderr_handler = data["handlers"]["stderr"]
        self.assertEqual(stderr_handler["formatter"], "default")
        self.assertEqual(stderr_handler["level"], "WARNING")


if __name__ == "__main__":
    unittest.main()
