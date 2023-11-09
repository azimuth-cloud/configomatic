import functools


def snake_to_pascal(name):
    """
    Converts a snake_case name to pascalCase.
    """
    first, *rest = name.split("_")
    return "".join([first] + [part.capitalize() for part in rest])


def merge(defaults, *overrides):
    """
    Returns a new dictionary obtained by deep-merging multiple sets of overrides
    into defaults, with precedence from right to left.
    """
    def merge2(defaults, overrides):
        if isinstance(defaults, dict) and isinstance(overrides, dict):
            merged = defaults.copy()
            for key, value in overrides.items():
                if key in defaults:
                    merged[key] = merge2(defaults[key], value)
                else:
                    merged[key] = value
            return merged
        else:
            return overrides if overrides is not None else defaults
    return functools.reduce(merge2, overrides, defaults)
