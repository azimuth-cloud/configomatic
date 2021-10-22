import logging

from pydantic import BaseModel, Field


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
    formatters: dict = Field(default_factory = lambda: {
        "default": {
            "format": "[%(levelname)s] %(message)s",
        },
    })
    filters: dict = Field(default_factory = lambda: {
        # This filter allows us to send >= WARNING to stderr and < WARNING to stdout
        "less_than_warning": {
            "()": f"{__name__}.LessThanLevelFilter",
            "level": "WARNING",
        },
    })
    handlers: dict = Field(default_factory = lambda: {
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
    })
    loggers: dict = Field(default_factory = lambda: {
        "": {
            "handlers": ["stdout", "stderr"],
            "level": "INFO",
            "propagate": True
        },
    })

    def apply(self):
        """
        Apply the logging configuration.
        """
        import logging.config
        logging.config.dictConfig(self.dict())
