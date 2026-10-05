"""Tests for the logging configuration, formatter and filter."""

import json
import logging

import pytest

from configomatic import LoggingConfiguration
from configomatic.logging import DefaultFormatter, LessThanLevelFilter


def make_record(level: int = logging.INFO, **extra: object) -> logging.LogRecord:
    """Return a log record at the given level, with any extra attributes set."""
    record = logging.LogRecord("test", level, __file__, 1, 'say "hi"', None, None)
    record.__dict__.update(extra)
    return record


def test_defaults() -> None:
    """Test that the default formatter, filter, handlers and root logger are present."""
    config = LoggingConfiguration()
    assert "default" in config.formatters
    assert "less_than_warning" in config.filters
    assert set(config.handlers) == {"stdout", "stderr"}
    assert config.loggers[""]["handlers"] == ["stdout", "stderr"]


def test_overrides_are_merged_with_defaults() -> None:
    """Test that given values are deep-merged over the defaults."""
    config = LoggingConfiguration(
        loggers={"": {"level": "DEBUG"}, "mylogger": {"level": "WARNING"}},
    )
    assert config.loggers[""] == {
        "handlers": ["stdout", "stderr"],
        "level": "DEBUG",
        "propagate": True,
    }
    assert config.loggers["mylogger"] == {"level": "WARNING"}


def test_apply(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that records below WARNING go to stdout and the rest to stderr."""
    root = logging.getLogger()
    saved = (root.level, root.handlers[:], root.filters[:])
    try:
        LoggingConfiguration().apply({"loggers": {"": {"level": "DEBUG"}}})
        logger = logging.getLogger("configomatic.test")
        logger.debug("to stdout", extra={"key": 1})
        logger.warning("to stderr")
        out, err = capsys.readouterr()
        assert '"to stdout" key="1"' in out
        assert "to stderr" not in out
        assert '"to stderr"' in err
    finally:
        root.setLevel(saved[0])
        root.handlers[:] = saved[1]
        root.filters[:] = saved[2]


def test_default_formatter() -> None:
    """Test that the formatter adds the quoted message and formatted extras."""
    formatter = DefaultFormatter("%(quotedmessage)s %(formattedextra)s")
    output = formatter.format(make_record(key="value", number=2))
    assert output == json.dumps('say "hi"') + ' key="value" number="2"'


@pytest.mark.parametrize("level", [logging.WARNING, "WARNING", "warning"])
def test_less_than_level_filter(level: int | str) -> None:
    """Test that only records below the level, as an int or name, are allowed."""
    log_filter = LessThanLevelFilter(level)
    assert log_filter.filter(make_record(logging.INFO))
    assert not log_filter.filter(make_record(logging.WARNING))
    assert not log_filter.filter(make_record(logging.ERROR))
