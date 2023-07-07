import logging

from pydantic import BaseModel, Field, validator
from pydantic.utils import deep_update


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
    formatters: dict = Field(default_factory = dict)
    filters: dict = Field(default_factory = dict)
    handlers: dict = Field(default_factory = dict)
    loggers: dict = Field(default_factory = dict)

    @validator("formatters", pre = True, always = True)
    def default_formatters(cls, v):
        return deep_update(
            {
                "default": {
                    "format": "[%(asctime)s] %(name)-20.20s [%(levelname)-8.8s] %(message)s",
                },
            },
            v or {}
        )

    @validator("filters", pre = True, always = True)
    def default_filters(cls, v):
        return deep_update(
            {
                # This filter allows us to send >= WARNING to stderr and < WARNING to stdout
                "less_than_warning": {
                    "()": f"{__name__}.LessThanLevelFilter",
                    "level": "WARNING",
                },
            },
            v or {}
        )

    @validator("handlers", pre = True, always = True)
    def default_handlers(cls, v):
        return deep_update(
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

    @validator("loggers", pre = True, always = True)
    def default_loggers(cls, v):
        return deep_update(
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
        config = self.dict()
        if overrides:
            config = deep_update(config, overrides)
        logging.config.dictConfig(config)
