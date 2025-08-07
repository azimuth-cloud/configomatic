# configomatic

This package provides an object that extends the [Pydantic](https://pydantic-docs.helpmanual.io/)
`BaseModel` with functionality that is useful when specifying configuration.

The following configuration sources are supported, in ascending order of precedence:

  * Defaults in the configuration classes
  * Configuration file
    * Specify default configuration file, overridable using an environment variable
    * Multiple formats supported
      * [JSON](https://en.wikipedia.org/wiki/JSON) format supported using the [standard Python module](https://docs.python.org/3/library/json.html)
      * [YAML](https://en.wikipedia.org/wiki/YAML) format supported if [PyYAML](https://pypi.org/project/PyYAML/) is installed
      * [TOML](https://en.wikipedia.org/wiki/TOML) format supported if [toml](https://pypi.org/project/toml/) is installed
  * Environment variables
    * Configurable prefix for variables
    * Nested configuration supported using `__`
  * Arguments

## Defining configuration models

Just define your configuration using Pydantic as you would normally, but use the `configomatic`
base classes instead of `BaseModel`.

`configomatic` supports all the types supported by Pydantic.

```python
from configomatic import Configuration, Section


# Nested configurations inherit from Section
class GrandchildConfig(Section):
    item1: int
    item2: str = "default"


class ChildConfig(Section):
    child: GrandchildConfig
    item3: float = 1.0


# The top-level configuration inherits from Configuration
class MainConfig(
    Configuration,
    # The default path for the configuration file
    default_path = "/etc/mypackage/config.yaml",
    # The environment variable that can be used to specify a different config file
    path_env_var = "MYPACKAGE_CONFIG",
    # The prefix that should be used for environment variable overrides
    env_prefix = "MYPACKAGE"
):
    child: ChildConfig
    item4: str


# Initialise the configuration object
settings = MainConfig(item4 = "test1")


# Access nested settings
print(settings.child.child.item1)
```

## Providing configuration

As well as arguments given when initialising the configuration object, configuration can come
from files and from environment variables.

The configuration from any particular source does not have to be complete as long as the merged
configuration is complete. For example, the config file at the default path may leave some
required items undefined, requiring the remaining items to be specified as environment variables
or arguments.

### Config files

Configuration can be provided using JSON, YAML or TOML files, e.g.:

```json
{
  "item4": "value1",
  "child": {
    "item3": 2.5,
    "child": {
      "item1": 232
    }
  }
}
```

The `Configuration` object defines a default location for this file and an environment
variable that can be used to override it, e.g.:

```sh
export MYPACKAGE_CONFIG=/path/to/my/config.json
```

#### YAML includes

The YAML loader supports a special `!include` tag that allows configuration to be included from
another file.

One use for this functionality is to implement a `conf.d` style pattern. e.g.:

```yaml
# /etc/mypackage/config.yaml
# This file is the entrypoint that is specified in your Configuration class
!include "/etc/mypackage/defaults.yaml,/etc/mypackage/conf.d/*.yaml"


# /etc/mypackage/defaults.yaml
item4: value1
child:
  item3: 2.5
  child:
    item1: 232


# /etc/mypackage/conf.d/01-child-item3.yaml
child:
  item3: 3554.453


# /etc/mypackage/conf.d/02-grandchild.yaml
child:
  child:
    item1: 700000
    item2: notthedefault
```

These config files will be merged together to produce the final configuration.

It can also be used to include sections of config from other files, e.g.:

```yaml
# /etc/mypackage/config.yaml
item4: differentvalue
child:
  child: !include "/etc/mypackage/grandchild.yaml"


# /etc/mypackage/grandchild.yaml
item1: 600000
item2: notthedefault
```

### Environment variable overrides

Individial config items can be overridden using environment variables of the form

```
{PREFIX}__{NAME}__{NESTEDNAME}=value
```

where `__` represents a nested relationship.

For example, the following variables will override config items in the `Configuration` above:

```sh
# Sets item4 on the top-level config object
export MYPACKAGE__ITEM4=value1

# Sets item3 on the child config object
export MYPACKAGE__CHILD__ITEM3=2.665

# Sets item1 on the grandchild config object
export MYPACKAGE__CHILD__CHILD__ITEM1=5600
```

## Logging configuration

`configomatic` includes a special model for configuring logging using Python's
[logging module](https://docs.python.org/3/library/logging.html). To use it, just add a
`LoggingConfiguration` as part of your configuration object:

```python
from pydantic import Field

from configomatic import Configuration, LoggingConfiguration


class MyPackageConfig(
    Configuration,
    default_path = "/etc/mypackage/config.yaml",
    path_env_var = "MYPACKAGE_CONFIG",
    env_prefix = "MYPACKAGE"
):
    # This will use the default logging configuration by default
    logging: LoggingConfiguration = Field(default_factory=LoggingConfiguration)

    item1: int
    item2: str
```

The `LoggingConfiguration` object has a special method that will apply the logging
configuration using `logging.config.dictConfig`:

```python
settings = MyPackageConfig()

settings.logging.apply()
```

This will register all the formatters, filters, handlers and loggers defined in your
settings object so that they are picked up by standard Python loggers.

> [!TIP]
> Execute `LoggingConfiguration.apply()` as early in your program as possible so that the
> formatting, filters and handlers are available before any logging takes place.

### Sensible defaults

`LoggingConfiguration` has sensible defaults that mean in a lot of cases, it is sufficient
to use the default logging configuration:

  * Default formatter called `default` that understands
    [extra](https://docs.python.org/3/library/logging.html#logging.Logger.debug) and
    formats it nicely
  * Default filter called `less_than_warning` that can be used to filter out only log records
    with a level less than `WARNING`
  * Default handlers called `stdout` and `stderr` that use the `default` formatter and
    `less_than_warning` filter to send any logs with a level less than `WARNING` to stdout and
    any logs with a level of `WARNING` or greater to stderr
  * Default root logger that uses the `stdout` and `stderr` handlers to log any records of
    level `INFO` and higher

> [!TIP]
> In particular, the default filters, handlers and root logger are good for containerised
> applications where sending logs to stdout/stderr is encouraged so that log aggregation tools
> can collect them.

### Overridding logging configuration

`LoggingConfiguration` will accept any full _or partial_ configuration that conforms to the
[logging configuration dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema).

For example, to override the log level so that debug messages are produced, I could use
the following YAML:

```yaml
logging:
  loggers:
    "":
      level: DEBUG
```

Or to use JSON-formatted logs with [python-json-logger](https://pypi.org/project/python-json-logger/):

```yaml
logging:
  formatters:
    default:
      (): pythonjsonlogger.json.JsonFormatter
      format: "%(message)s"
```
