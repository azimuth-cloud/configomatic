import json
import logging

from pydantic import BaseModel, Field, field_validator

from .utils import merge


# Get the reserved keys for a log record
LOG_RECORD_RESERVED_KEYS = set(logging.LogRecord("_", 0, "_", 0, None, None, None).__dict__.keys())


class DefaultFormatter(logging.Formatter):
    """
    Default logging formatter for this operator.
    """
    def format(self, record):
        # Calculate the extra parameters on the log record
        extra = {k: v for k, v in record.__dict__.items() if k not in LOG_RECORD_RESERVED_KEYS}
        # Add a quoted message property to the log record
        record.__dict__["quotedmessage"] = json.dumps(record.getMessage())
        # Add a formatted extra property to the log record
        record.__dict__["formattedextra"] = " ".join(
            k + "=" + json.dumps(str(v))
            for k, v in extra.items()
        )
        return super().format(record)


class LessThanLevelFilter(logging.Filter):
    def __init__(self, level):
        if isinstance(level, int):
            self.level = level
        else:
            self.level = getattr(logging, level.upper())

    def filter(self, record):
        return record.levelno < self.level


class LoggingConfiguration(BaseModel):
    """
    Model for a logging configuration with a sensible default value.
    """
    # See https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = Field(default_factory = dict, validate_default = True)
    filters: dict = Field(default_factory = dict, validate_default = True)
    handlers: dict = Field(default_factory = dict, validate_default = True)
    loggers: dict = Field(default_factory = dict, validate_default = True)

    @field_validator("formatters")
    def default_formatters(cls, v):
        return merge(
            {
                "default": {
                    "()": f"{__name__}.DefaultFormatter",
                    "format": "[%(asctime)s] %(name)-20.20s [%(levelname)-8.8s] %(quotedmessage)s %(formattedextra)s",
                },
            },
            v or {}
        )

    @field_validator("filters")
    def default_filters(cls, v):
        return merge(
            {
                # This filter allows us to send >= WARNING to stderr and < WARNING to stdout
                "less_than_warning": {
                    "()": f"{__name__}.LessThanLevelFilter",
                    "level": "WARNING",
                },
            },
            v or {}
        )

    @field_validator("handlers")
    def default_handlers(cls, v):
        return merge(
            {
                # Handlers for stdout/err with default formatting
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                    "filters": ["less_than_warning"],
                },
                "stderr": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                    "formatter": "default",
                    "level": "WARNING",
                },
            },
            v or {}
        )

    @field_validator("loggers")
    def default_loggers(cls, v):
        return merge(
            {
                # Just set the config for the default logger here
                "": {
                    "handlers": ["stdout", "stderr"],
                    "level": "INFO",
                    "propagate": True
                },
            },
            v or {}
        )

    def apply(self, overrides = None):
        """
        Apply the logging configuration.
        """
        import logging.config
        config = self.model_dump()
        if overrides:
            config = merge(config, overrides)
        logging.config.dictConfig(config)
